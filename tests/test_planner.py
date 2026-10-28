import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent"))
import planner  # noqa: E402

REPORT = {"top_gaps": ["python", "sql"]}
MISSED = {"python": ["List is mutable", "Tuple is immutable"],
          "sql": ["Handles NULL", "Gives an example", "Third point", "Fourth point"]}
RESOURCES = {"sql": [{"title": "SQL tutorial", "url": "https://example.com/sql"}]}
NAMES = {"python": "Python", "sql": "SQL"}


def plan(report=REPORT):
    return planner.build_plan(report, MISSED, RESOURCES, NAMES)["steps"]


class PlannerTests(unittest.TestCase):
    def test_one_step_per_gap_in_order(self):
        self.assertEqual([(s["order"], s["skill"]) for s in plan()], [(1, "python"), (2, "sql")])

    def test_tasks_come_from_the_missed_points(self):
        self.assertEqual(plan()[0]["tasks"][:2], ["Revise: List is mutable", "Revise: Tuple is immutable"])

    def test_at_most_three_missed_points_per_step(self):
        revise = [t for t in plan()[1]["tasks"] if t.startswith("Revise:")]
        self.assertEqual(len(revise), 3)

    def test_links_come_only_from_our_list(self):
        self.assertEqual(plan()[0]["resources"], [])                      # python is not in RESOURCES
        self.assertEqual(plan()[1]["resources"][0]["url"], "https://example.com/sql")

    def test_no_gaps_gives_an_empty_plan(self):
        self.assertEqual(plan({"top_gaps": []}), [])


if __name__ == "__main__":
    unittest.main()