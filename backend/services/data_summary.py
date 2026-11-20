"""Pure summarization logic + short cache for Firestore read/cost control."""
import statistics
import time
from collections import defaultdict
from datetime import date, timedelta
from threading import Lock

_CACHE = {"expires": 0.0, "summary": None}
_LOCK = Lock()


def summarize_rows(rows: list[dict]) -> dict:
    ordered = sorted(rows, key=lambda x: (x.get("recorded_at") or x.get("date") or "", x.get("id", "")))
    vals = [float(row["value"]) for row in ordered if isinstance(row.get("value"), (int, float))]
    if not vals:
        return {
            "dataset": "SECOM / sensor_001 (단위 미공개)", "period": None, "count": 0,
            "metrics": {"total": None, "average": None, "max": None, "min": None},
            "trend": {"label": "데이터 부족", "change_pct": None, "method": "최근 20개와 직전 20개 관측 평균 비교"},
            "variability": {"label": "데이터 부족", "previous_30_std": None,
                            "latest_30_std": None, "change_pct": None,
                            "method": "최근 30개와 직전 30개 관측의 모집단 표준편차 비교"},
            "quality": {"labeled_count": 0, "pass_count": 0, "fail_count": 0, "fail_rate_pct": None},
            "weekly_quality": {"highest": None, "lowest": None, "recent": []},
            "outliers": {"iqr_lower": None, "iqr_upper": None, "count": 0},
            "cautions": ["검사 시각은 균일한 간격의 센서 수집 시각이 아닙니다.", "익명 변수 단위와 불량 원인은 확인되지 않았습니다."],
        }
    first = ordered[0].get("date")
    last = ordered[-1].get("date")
    count = len(vals)
    metrics = {"total": round(sum(vals), 4), "average": round(statistics.mean(vals), 4),
               "max": round(max(vals), 4), "min": round(min(vals), 4)}
    trend_label, pct = "데이터 부족", None
    if count >= 40:
        prev_avg = statistics.mean(vals[-40:-20]); last_avg = statistics.mean(vals[-20:])
        if abs(prev_avg) > 1e-12:
            pct = round((last_avg - prev_avg) / abs(prev_avg) * 100, 2)
            trend_label = "상승" if pct > 2 else "하락" if pct < -2 else "유지"
        else:
            trend_label = "유지" if abs(last_avg) < 1e-12 else "상승/하락(기준 0)"
    # A 30-observation window is not a 30-day window; the timestamps are irregular.
    variability = {"label": "데이터 부족", "previous_30_std": None,
                   "latest_30_std": None, "change_pct": None,
                   "method": "최근 30개와 직전 30개 관측의 모집단 표준편차 비교 (±10% 이내 유지: 설명용 기준)"}
    if count >= 60:
        prev_sd = statistics.pstdev(vals[-60:-30])
        latest_sd = statistics.pstdev(vals[-30:])
        pct_sd = round((latest_sd - prev_sd) / prev_sd * 100, 2) if prev_sd > 1e-12 else None
        if pct_sd is None:
            vol_label = "유지" if latest_sd < 1e-12 else "비교 어려움"
        else:
            vol_label = "증가" if pct_sd > 10 else "감소" if pct_sd < -10 else "유지"
        variability.update({"label": vol_label, "previous_30_std": round(prev_sd, 4),
                            "latest_30_std": round(latest_sd, 4), "change_pct": pct_sd})
    labeled = [r.get("quality_label") for r in ordered if r.get("quality_label") in (-1, 1)]
    n_pass = labeled.count(-1); n_fail = labeled.count(1)
    by_week = defaultdict(lambda: {"count": 0, "fail_count": 0})
    for row in ordered:
        label = row.get("quality_label")
        if label not in (-1, 1):
            continue
        day = date.fromisoformat(row["date"])
        sunday = (day + timedelta(days=6-day.weekday())).isoformat()
        by_week[sunday]["count"] += 1
        by_week[sunday]["fail_count"] += int(label == 1)
    weeks = [
        {"week_ending": end, "count": v["count"], "fail_count": v["fail_count"],
         "fail_rate_pct": round(100*v["fail_count"]/v["count"], 3)}
        for end, v in sorted(by_week.items())
    ]
    highest = max(weeks, key=lambda x:x["fail_rate_pct"]) if weeks else None
    lowest = min(weeks, key=lambda x:x["fail_rate_pct"]) if weeks else None
    sorted_vals = sorted(vals)
    def percentile(p):
        index = (len(sorted_vals)-1)*p
        left = int(index); right = min(left+1, len(sorted_vals)-1)
        return sorted_vals[left] + (sorted_vals[right] - sorted_vals[left])*(index-left)
    q1,q3 = percentile(.25), percentile(.75)
    iqr = q3 - q1
    lower, upper = (q1-1.5*iqr, q3+1.5*iqr) if iqr>0 else (None, None)
    n_outliers = sum(1 for val in vals if (val<lower or val>upper)) if lower is not None else 0
    return {
        "dataset": "SECOM / sensor_001 (단위 미공개)",
        "period": f"{first} ~ {last}", "count": count,
        "metrics": metrics,
        "trend": {"label": trend_label, "change_pct": pct, "method": "최근 20개와 직전 20개 관측 평균 비교 (±2% 이내 유지: 설명용 기준)"},
        "variability": variability,
        "quality": {"labeled_count": len(labeled), "pass_count": n_pass, "fail_count": n_fail,
                    "fail_rate_pct": round(n_fail / len(labeled) * 100, 3) if labeled else None},
        "weekly_quality": {"highest": highest, "lowest": lowest, "recent": weeks[-8:]},
        "outliers": {"iqr_lower": round(lower, 4) if lower is not None else None,
                     "iqr_upper": round(upper, 4) if upper is not None else None, "count": n_outliers},
        "cautions": ["검사 시각은 균일한 간격의 센서 수집 시각이 아닙니다.",
                     "sensor_001은 익명 변수로 단위가 알려져 있지 않습니다.",
                     "관측 통계만으로 불량 원인이나 공정 안정성을 단정할 수 없습니다.",
                     "IQR 이상치는 검토 후보이며 관리한계나 실제 불량을 뜻하지 않습니다.",
                     "주별 불량률은 표본 수에 따라 크게 달라질 수 있습니다.",
                     "최근 추세 및 변동성 변화의 임계값은 설명용이며 공정 관리한계가 아닙니다."],
    }


def invalidate_summary() -> None:
    with _LOCK:
        _CACHE["expires"] = 0
        _CACHE["summary"] = None


def get_summary() -> dict:
    with _LOCK:
        if _CACHE["summary"] is not None and time.monotonic() < _CACHE["expires"]:
            return _CACHE["summary"]
    from services.firestore_db import get_db  # Import only for actual Firestore usage
    rows = [{**s.to_dict(), "id": s.id} for s in get_db().collection("data").stream()]
    result = summarize_rows(rows)
    with _LOCK:
        _CACHE["summary"] = result
        _CACHE["expires"] = time.monotonic() + 300
    return result
