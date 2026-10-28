import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent"))
import grader  # noqa: E402

POINTS = ["A keeps matching rows", "B keeps all left rows", "C becomes NULL", "D gives an example"]


class GraderTests(unittest.TestCase):
    def test_all_yes_gives_full_marks(self):
        self.assertEqual(grader.score_from_marks(["yes"] * 4), 10)

    def test_halves_round_up(self):
        self.assertEqual(grader.score_from_marks(["yes", "no", "no", "no"]), 3)      # 2.5 becomes 3

    def test_partly_counts_half(self):
        self.assertEqual(grader.score_from_marks(["yes", "partly", "no", "no"]), 4)  # 3.75 becomes 4

    def test_no_marks_gives_zero(self):
        self.assertEqual(grader.score_from_marks([]), 0)

    def test_missed_points_are_everything_not_fully_covered(self):
        result = grader.missed_points(POINTS, ["yes", "partly", "no", "yes"])
        self.assertEqual(result, ["B keeps all left rows", "C becomes NULL"])

    def test_feedback_names_what_was_missed(self):
        text = grader.build_feedback(POINTS, ["yes", "no", "no", "no"])
        self.assertIn("B keeps all left rows", text)

class FakeClient:
    """Pretends to be the model. It always answers with the text we give it."""
    def __init__(self, reply_text):
        self.reply_text = reply_text

    def chat(self, **kwargs):
        return NS(message=NS(content=self.reply_text))


class JudgeTests(unittest.TestCase):
    def test_empty_answer_never_calls_the_model(self):
        grader._client = FakeClient("this would crash if it were used")
        self.assertEqual(grader.judge_points("Q", POINTS, "   "), ["no"] * 4)

    def test_a_yes_without_real_words_becomes_no(self):
        reply = json.dumps({
            "point_1": {"student_said": "inner join keeps matching rows", "mark": "yes"},
            "point_2": {"student_said": "it keeps everything on the left", "mark": "yes"},  # not in the answer
            "point_3": {"student_said": "", "mark": "yes"},                                  # empty words
            "point_4": {"student_said": "", "mark": "no"},
        })
        grader._client = FakeClient(reply)
        marks = grader.judge_points("Q", POINTS, "Inner join keeps matching rows only.")
        self.assertEqual(marks, ["yes", "no", "no", "no"])

    def test_an_unreadable_model_answer_raises_an_error(self):
        grader._client = FakeClient("not json at all")
        with self.assertRaises(ValueError):
            grader.judge_points("Q", POINTS, "some answer")

class GradeAnswerTests(unittest.TestCase):
    def test_result_has_exactly_the_contract_fields(self):
        question = {"id": "q_x", "text": "Q", "skill": "sql", "rubric": POINTS}
        reply = json.dumps({
            "point_1": {"student_said": "inner join keeps matching rows", "mark": "yes"},
            "point_2": {"student_said": "", "mark": "no"},
            "point_3": {"student_said": "", "mark": "no"},
            "point_4": {"student_said": "", "mark": "no"},
        })
        grader._client = FakeClient(reply)
        result = grader.grade_answer("q_x", "Inner join keeps matching rows.", question=question)
        self.assertEqual(sorted(result), ["feedback", "max_score", "missed_points", "score"])
        self.assertEqual(result["score"], 3)
        self.assertEqual(len(result["missed_points"]), 3)

if __name__ == "__main__":
    unittest.main()