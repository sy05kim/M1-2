"""Optional DEMONSTRATION-only 120 synthetic records; not original SECOM data."""
import argparse
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.firestore_db import get_db
from services.data_summary import invalidate_summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    if not args.confirm:
        print("Will create 120 SYNTHETIC samples with IDs demo_0000..0119; pass --confirm to proceed")
        return
    db = get_db(); batch = db.batch()
    now = datetime.now(timezone.utc).isoformat()
    for i in range(120):
        day = date(2008, 7, 1) + timedelta(days=i)
        row = {"date": day.isoformat(), "recorded_at": f"{day.isoformat()}T00:00:00",
               "value": round(3010+45*math.sin(i/9)+0.15*i, 3),
               "memo": "합성 데모 데이터 (실제 SECOM 측정치 아님)",
               "quality_label": 1 if i % 17 == 0 else -1,
               "created_at": now, "updated_at": now}
        batch.set(db.collection("data").document(f"demo_{i:04d}"), row)
    batch.commit(); invalidate_summary()
    print("Created 120 labeled SYNTHETIC demo records")


if __name__ == "__main__": main()
