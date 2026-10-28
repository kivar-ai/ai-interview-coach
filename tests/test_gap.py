import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent"))
import gap  # noqa: E402

ROWS = [{"skill": "sql", "score": 5, "max_score": 10},
        {"skill": "sql", "score": 10, "max_score": 10},
        {"skill": "python", "score": 0, "max_score": 10}]
RESEARCH = [{"skill": "sql", "importance": "high"},
            {"skill": "python", "importance": "medium"},
            {"skill": "nlp", "importance": "low"}]


def report():
    return gap.build_report(RESEARCH, {"sql": "advanced"}, ROWS)


def entry(skill):
    return next(s for s in report()["skills"] if s["skill"] == skill)


class GapTests(unittest.TestCase):
    def test_measured_score_is_the_average_in_percent(self):
        self.assertEqual(gap.measured_scores(ROWS), {"sql": 75, "python": 0})

    def test_halves_round_up(self):
        rows = [{"skill": "sql", "score": s, "max_score": 10} for s in (1, 1, 1, 2)]    # 12.5 on average
        self.assertEqual(gap.measured_scores(rows), {"sql": 13})

    def test_gap_is_target_minus_measured(self):
        self.assertEqual(entry("sql")["gap"], 15)          # high needs 90, measured 75
        self.assertEqual(entry("python")["gap"], 70)       # medium needs 70, measured 0

    def test_gap_is_never_below_zero(self):
        rows = [{"skill": "python", "score": 10, "max_score": 10}]
        result = gap.build_report([{"skill": "python", "importance": "low"}], {}, rows)
        self.assertEqual(result["skills"][0]["gap"], 0)

    def test_untested_skill_has_no_score_and_no_gap(self):
        self.assertIsNone(entry("nlp")["measured_score"])
        self.assertIsNone(entry("nlp")["gap"])

    def test_top_gaps_are_the_biggest_tested_gaps_first(self):
        self.assertEqual(report()["top_gaps"], ["python", "sql"])

    def test_self_rating_is_copied_and_missing_is_none(self):
        self.assertEqual(entry("sql")["self_rating"], "advanced")
        self.assertIsNone(entry("python")["self_rating"])


if __name__ == "__main__":
    unittest.main()