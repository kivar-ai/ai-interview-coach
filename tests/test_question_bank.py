import sys
import unittest
from pathlib import Path
import random

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent"))
import question_bank  # noqa: E402


class FakeCollection:
    """Pretends to be Chroma, with three sql questions and nothing else."""
    ROWS = [("q_sql_002", "WHERE vs HAVING?", {"difficulty": "medium"}),
            ("q_sql_001", "INNER vs LEFT JOIN?", {"difficulty": "easy"}),
            ("q_sql_003", "Window functions?", {"difficulty": "hard"})]

    def get(self, where=None):
        rows = self.ROWS if where["skill"] == "sql" else []
        return {"ids": [r[0] for r in rows], "documents": [r[1] for r in rows], "metadatas": [r[2] for r in rows]}


def pick(skills):
    return question_bank.pick_questions(skills, FakeCollection())


class PickTests(unittest.TestCase):
    def test_more_important_skills_get_more_questions(self):
        self.assertEqual(len(pick([{"skill": "sql", "importance": "high"}])), 3)
        self.assertEqual(len(pick([{"skill": "sql", "importance": "low"}])), 1)

    def test_medium_skill_gets_an_easy_then_a_medium_question(self):
        picked = pick([{"skill": "sql", "importance": "medium"}])
        self.assertEqual([q["question_id"] for q in picked], ["q_sql_001", "q_sql_002"])

    def test_a_skill_without_questions_is_skipped_and_numbers_continue(self):
        picked = pick([{"skill": "nlp", "importance": "high"}, {"skill": "sql", "importance": "low"}])
        self.assertEqual([(q["number"], q["question_id"]) for q in picked], [(1, "q_sql_001")])

    def test_no_answers_or_rubric_reach_the_student(self):
        picked = pick([{"skill": "sql", "importance": "low"}])
        self.assertEqual(sorted(picked[0]), ["number", "question_id", "skill", "text"])

class SpreadTests(unittest.TestCase):
    QUESTIONS = [("e1", "t", "easy"), ("e2", "t", "easy"), ("m1", "t", "medium"), ("h1", "t", "hard")]

    def test_three_questions_get_one_of_each_level(self):
        chosen = question_bank.spread_pick(self.QUESTIONS, 3, random.Random(1))
        self.assertEqual([q[2] for q in chosen], ["easy", "medium", "hard"])

    def test_a_missing_level_uses_the_nearest_one(self):
        questions = [("e1", "t", "easy"), ("h1", "t", "hard"), ("h2", "t", "hard")]
        chosen = question_bank.spread_pick(questions, 2, random.Random(1))
        self.assertEqual([q[2] for q in chosen], ["easy", "hard"])

    def test_never_more_than_the_bank_has(self):
        chosen = question_bank.spread_pick([("e1", "t", "easy")], 3, random.Random(1))
        self.assertEqual(len(chosen), 1)

    def test_same_seed_gives_the_same_choice(self):
        a = question_bank.spread_pick(self.QUESTIONS, 3, random.Random(5))
        b = question_bank.spread_pick(self.QUESTIONS, 3, random.Random(5))
        self.assertEqual(a, b)

if __name__ == "__main__":
    unittest.main()