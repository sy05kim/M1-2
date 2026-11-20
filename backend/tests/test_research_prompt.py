import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.research_prompt import system_context


class ResearchPromptTests(unittest.TestCase):
    def test_hypothesis_and_observation_are_distinguished(self):
        prompt = system_context({"dataset": "SECOM / sensor_001", "count": 100, "trend": {"label": "유지"}})
        self.assertIn("관찰", prompt)
        self.assertIn("가능한 가설", prompt)
        self.assertIn("추가 검증", prompt)
        self.assertIn('"count": 100', prompt)
        self.assertIn("익명 변수", prompt)


if __name__ == "__main__":
    unittest.main()
