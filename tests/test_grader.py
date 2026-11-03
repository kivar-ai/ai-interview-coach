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

def box(said, mark):
    """One model reply for ONE rubric point."""
    return json.dumps({"student_said": said, "mark": mark})


class FakeClient:
    """Pretends to be the model. It answers with the replies we give it, one per call, in order."""
    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []

    def chat(self, **kwargs):
        self.prompts.append(kwargs["messages"][0]["content"])
        return NS(message=NS(content=self.replies.pop(0)))


class JudgeTests(unittest.TestCase):
    def test_empty_answer_never_calls_the_model(self):
        grader._client = FakeClient(["this would crash if it were used"])
        self.assertEqual(grader.judge_points("Q", POINTS, "   "), ["no"] * 4)

    def test_a_yes_without_real_words_becomes_no(self):
        grader._client = FakeClient([
            box("inner join keeps matching rows", "yes"),
            box("it keeps everything on the left", "yes"),   # not in the answer
            box("", "yes"),                                   # empty words
            box("", "no"),
        ])
        marks = grader.judge_points("Q", POINTS, "Inner join keeps matching rows only.")
        self.assertEqual(marks, ["yes", "no", "no", "no"])

    def test_an_unreadable_model_answer_raises_an_error(self):
        grader._client = FakeClient(["not json at all"])
        with self.assertRaises(ValueError):
            grader.judge_points("Q", POINTS, "some answer")

    def test_a_quote_with_one_changed_word_still_counts(self):
        grader._client = FakeClient([
            box("compare training performance with validation performance", "yes"),
            box("", "no"),
            box("", "no"),
            box("", "no"),
        ])
        answer = "You can spot it by comparing training performance with validation performance."
        self.assertEqual(grader.judge_points("Q", POINTS, answer)[0], "yes")

    def test_each_point_gets_its_own_model_call_with_only_that_point(self):
        client = FakeClient([box("", "no")] * 4)
        grader._client = client
        grader.judge_points("Q", POINTS, "some answer")
        self.assertEqual(len(client.prompts), 4)
        self.assertIn(POINTS[0], client.prompts[0])
        self.assertNotIn(POINTS[1], client.prompts[0])


class GradeAnswerTests(unittest.TestCase):
    def test_result_has_exactly_the_contract_fields(self):
        question = {"id": "q_x", "text": "Q", "skill": "sql", "rubric": POINTS}
        grader._client = FakeClient([
            box("inner join keeps matching rows", "yes"),
            box("", "no"),
            box("", "no"),
            box("", "no"),
        ])
        result = grader.grade_answer("q_x", "Inner join keeps matching rows.", question=question)
        self.assertEqual(sorted(result), ["feedback", "max_score", "missed_points", "score"])
        self.assertEqual(result["score"], 3)
        self.assertEqual(len(result["missed_points"]), 3)


if __name__ == "__main__":
    unittest.main()