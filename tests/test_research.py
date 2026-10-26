"""Tests for agent/research.py that need NO internet and NO Ollama.
They replace the model and the web with small fakes, so we can check our own logic.

Run from the project folder:
    python -m unittest discover tests -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent"))
import research  # noqa: E402

PAGE_A = "We need a data scientist with strong SQL and Python. Experience with machine learning is a plus."
PAGE_B = "Our team values clear communication and statistics knowledge. Tableau dashboards are used daily."


def tool_call(name, **args):
    return NS(message=NS(content="", tool_calls=[NS(function=NS(name=name, arguments=args))]))


def plain_reply(text=""):
    return NS(message=NS(content=text, tool_calls=None))


class FakeWorld:
    """Fake model + fake web. The model follows a script of replies."""

    def __init__(self, replies, extraction):
        self.replies, self.extraction, self.calls = list(replies), extraction, 0

    def chat(self, **kwargs):
        self.calls += 1
        if kwargs.get("format"):  # the extraction call asks for JSON
            return NS(message=NS(content=json.dumps({"skills": self.extraction}), tool_calls=None))
        return self.replies.pop(0)

    def search(self, query):
        return [
            {"title": "Blocked", "href": "https://www.interviewquery.com/x", "body": "b"},
            {"title": "A", "href": "https://a.example.com/job", "body": "a"},
            {"title": "B", "href": "https://b.example.com/job", "body": "b"},
        ]

    def fetch(self, url):
        return {"https://a.example.com/job": PAGE_A, "https://b.example.com/job": PAGE_B}.get(url)


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        research.CACHE_DIR = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def install(self, world):
        research.ollama.chat = world.chat
        research.do_search = world.search
        research.do_fetch = world.fetch

    # ---- pure logic -------------------------------------------------------
    def test_verify_drops_a_quote_that_is_not_on_the_page(self):
        raw = [
            {"skill": "sql", "importance": "high", "quote": "strong SQL and Python"},
            {"skill": "deep_learning", "importance": "high", "quote": "expert in neural networks"},  # invented
        ]
        skills, dropped = research.verify_and_merge(raw, {"u1": PAGE_A}, {}, ["sql", "deep_learning"])
        self.assertEqual([s["skill"] for s in skills], ["sql"])
        self.assertEqual(dropped, ["deep_learning"])
        self.assertEqual(skills[0]["sources"], ["u1"])

    def test_quote_matching_ignores_case_and_punctuation(self):
        raw = [{"skill": "sql", "importance": "high", "quote": "STRONG sql, and python!"}]
        skills, _ = research.verify_and_merge(raw, {"u1": PAGE_A}, {}, ["sql"])
        self.assertEqual(len(skills), 1)

    def test_base_profile_fills_skills_the_pages_did_not_mention(self):
        raw = [{"skill": "sql", "importance": "medium", "quote": "strong SQL and Python"}]
        skills, _ = research.verify_and_merge(raw, {"u1": PAGE_A}, {"sql": "high", "statistics": "high"}, ["sql", "statistics"])
        by_skill = {s["skill"]: s for s in skills}
        self.assertEqual(by_skill["sql"]["basis"], "web")
        self.assertEqual(by_skill["statistics"]["basis"], "base_profile")
        self.assertEqual(by_skill["statistics"]["sources"], [])

    def test_unknown_skill_ids_are_ignored(self):
        raw = [{"skill": "cooking", "importance": "high", "quote": "strong SQL and Python"}]
        skills, _ = research.verify_and_merge(raw, {"u1": PAGE_A}, {}, ["sql"])
        self.assertEqual(skills, [])

    def test_blocked_domain_detection(self):
        self.assertTrue(research.is_blocked("https://www.interviewquery.com/guides/x"))
        self.assertFalse(research.is_blocked("https://example.com/interviewquery.com"))

    # ---- the agent loop ----------------------------------------------------
    def test_agent_stops_after_two_pages_and_skips_blocked_sites(self):
        world = FakeWorld(
            [tool_call("search_web", query="x"),
             tool_call("read_page", url="https://www.interviewquery.com/x"),  # blocked
             tool_call("read_page", url="https://a.example.com/job"),
             tool_call("read_page", url="https://b.example.com/job")],
            extraction=[])
        self.install(world)
        evidence = research.Evidence()
        research.gather_evidence("Data Scientist", None, evidence)
        self.assertEqual(len(evidence.pages), 2)
        self.assertEqual(world.calls, 4)  # the loop stopped by itself, no extra model call
        self.assertEqual([a["read"] for a in evidence.attempts], [False, True, True])

    def test_guardrail_sends_the_model_back_when_it_stops_early(self):
        world = FakeWorld(
            [plain_reply("I think I know the answer."),   # tries to stop with no pages -> nudged
             tool_call("search_web", query="x"),
             tool_call("read_page", url="https://a.example.com/job"),
             tool_call("read_page", url="https://b.example.com/job")],
            extraction=[])
        self.install(world)
        evidence = research.Evidence()
        research.gather_evidence("Data Scientist", None, evidence)
        self.assertEqual(len(evidence.pages), 2)

    # ---- the whole step ----------------------------------------------------
    def test_full_flow_with_cache(self):
        world = FakeWorld(
            [tool_call("search_web", query="x"),
             tool_call("read_page", url="https://a.example.com/job"),
             tool_call("read_page", url="https://b.example.com/job")],
            extraction=[
                {"skill": "sql", "importance": "high", "quote": "strong SQL and Python"},
                {"skill": "communication", "importance": "medium", "quote": "values clear communication"},
                {"skill": "deep_learning", "importance": "high", "quote": "invented quote that is not there"},
            ])
        self.install(world)
        first = research.research("data_scientist", "Acme")
        self.assertFalse(first["cached"])
        self.assertIn("deep_learning", first["dropped_unverified"])
        self.assertTrue(all(s["skill"] != "deep_learning" or s["basis"] == "base_profile" for s in first["skills"]))
        self.assertEqual(sum(p["read"] for p in first["pages_read"]), 2)

        calls_before = world.calls
        second = research.research("data_scientist", "Acme")  # served from cache, no model call
        self.assertTrue(second["cached"])
        self.assertEqual(world.calls, calls_before)

    def test_pasted_job_description_skips_the_web(self):
        world = FakeWorld([], extraction=[{"skill": "python", "importance": "high", "quote": "strong SQL and Python"}])
        self.install(world)
        result = research.research("data_scientist", None, PAGE_A)
        self.assertEqual(world.calls, 1)  # only the extraction call
        self.assertEqual(result["pages_read"], [{"url": "pasted job description", "read": True}])

    def test_no_pages_falls_back_to_the_role_profile(self):
        world = FakeWorld([plain_reply("done")] * 4, extraction=[])
        self.install(world)
        research.PAGES_WANTED = 2
        result = research.research("data_analyst", None)
        self.assertTrue(result["warnings"])
        self.assertTrue(all(s["basis"] == "base_profile" for s in result["skills"]))

    def test_unknown_role_gives_a_clear_error(self):
        with self.assertRaises(ValueError):
            research.research("astronaut")


if __name__ == "__main__":
    unittest.main()
