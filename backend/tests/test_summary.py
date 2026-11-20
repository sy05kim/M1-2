import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from models import DataPayload, ChatRequest
from pydantic import ValidationError
from services.data_summary import summarize_rows


class SummaryTests(unittest.TestCase):
    def test_empty(self):
        result = summarize_rows([])
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["trend"]["label"], "데이터 부족")

    def test_increasing_and_quality(self):
        rows = []
        for i in range(100):
            rows.append({"date": (date(2026, 1, 1) + timedelta(days=i)).isoformat(),
                         "value": 100 + i, "quality_label": 1 if i < 5 else -1})
        result = summarize_rows(rows)
        self.assertEqual(result["count"], 100)
        self.assertEqual(result["metrics"]["average"], 149.5)
        self.assertEqual(result["quality"]["fail_rate_pct"], 5.0)
        self.assertEqual(result["trend"]["label"], "상승")

    def test_recent_variability(self):
        rows = []
        for i in range(60):
            # First 30 have small spread, latest 30 have large spread.
            value = (100 + (i % 2)) if i < 30 else (100 + 30 * (i % 2))
            rows.append({"date": (date(2026, 1, 1) + timedelta(days=i)).isoformat(),
                         "value": value})
        result = summarize_rows(rows)
        self.assertEqual(result["variability"]["label"], "증가")
        self.assertGreater(result["variability"]["latest_30_std"],
                           result["variability"]["previous_30_std"])
        self.assertEqual(result["quality"]["labeled_count"], 0)

    def test_variability_requires_sixty_observations(self):
        rows = [{"date": "2026-01-01", "value": float(i)} for i in range(59)]
        self.assertEqual(summarize_rows(rows)["variability"]["label"], "데이터 부족")

    def test_validation(self):
        with self.assertRaises(ValidationError):
            DataPayload(date=date(2026, 1, 1), value=float("nan"))
        with self.assertRaises(ValidationError):
            DataPayload(date=date(2026, 1, 1), value=4.5, quality_label=0)
        with self.assertRaises(ValidationError):
            ChatRequest(question=" ")


if __name__ == "__main__":
    unittest.main()
