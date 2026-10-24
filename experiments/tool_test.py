"""Tool-calling test for AI Interview Coach.

What this checks: given a question, does the model
  1. call the RIGHT tool when it needs one,
  2. NOT call a tool when it doesn't need one,
  3. use the tool result to write a final answer?

The tools are tiny on purpose:
  - get_date    : real (returns today's date)
  - search_web  : FAKE (returns canned text), so we test the model's
                  decisions, not the internet.

Run (inside the project's .venv):
    python experiments/tool_test.py
"""

import time
from datetime import datetime

import ollama

MODEL = "qwen3:8b"
THINK = False  # Qwen3 can "think" before answering. False = faster. Try True later and compare.
MAX_STEPS = 4  # safety limit so the loop can never run forever


# ---------- Tools ----------
# The docstrings matter: the model reads them to decide when to use each tool.

def get_date() -> str:
    """Get today's date.

    Returns:
        Today's date as text, for example 'Sunday, 25 October 2026'.
    """
    return datetime.now().strftime("%A, %d %B %Y")


def search_web(query: str) -> str:
    """Search the web and return short result snippets.

    Args:
        query: What to search for.

    Returns:
        A few text snippets from search results.
    """
    q = query.lower()
    if "data scientist" in q:
        return "Data scientist roles ask for Python, SQL, statistics, machine learning and communication."
    if "machine learning" in q or "ml engineer" in q:
        return "ML engineer interviews cover ML algorithms, model deployment, Python and system design."
    if "data analyst" in q:
        return "Data analyst interviews focus on SQL, Excel, dashboards, statistics and business thinking."
    if "llm" in q:
        return "LLM engineer roles ask for prompting, RAG, fine-tuning basics, Python and evaluation."
    if "mlops" in q:
        return "MLOps roles ask for Docker, CI/CD, monitoring, cloud basics and model serving."
    return "General result: no specific information found for this query."


TOOLS = {"get_date": get_date, "search_web": search_web}


# ---------- The agent loop ----------
# Ask the model -> if it asks for a tool, run it -> give the result back -> repeat.

def run_case(question: str):
    messages = [{"role": "user", "content": question}]
    used = []  # names of tools the model called

    for _ in range(MAX_STEPS):
        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=list(TOOLS.values()),
            think=THINK,
        )
        message = response.message
        messages.append(message)

        if not message.tool_calls:  # model gave a final answer
            return used, message.content or ""

        for call in message.tool_calls:
            name = call.function.name
            args = call.function.arguments
            used.append(name)

            func = TOOLS.get(name)
            if func is None:
                result = f"Unknown tool: {name}"
            else:
                try:
                    result = func(**args)
                except Exception as error:  # bad arguments from the model
                    result = f"Tool error: {error}"

            messages.append({"role": "tool", "tool_name": name, "content": str(result)})

    return used, "(stopped: too many steps)"


# ---------- Test cases: (question, tools we EXPECT it to use) ----------

CASES = [
    ("What is today's date?", {"get_date"}),
    ("What day of the week is it today?", {"get_date"}),
    ("Search the web for skills needed for a data scientist job.", {"search_web"}),
    ("What does a machine learning engineer interview usually ask?", {"search_web"}),
    ("Find recent interview topics for a data analyst role.", {"search_web"}),
    ("What is overfitting? Answer in one sentence.", set()),
    ("What does SQL stand for?", set()),
    ("Look up what skills an LLM engineer needs and also tell me today's date.", {"search_web", "get_date"}),
    ("Explain what a tool call is, in one sentence.", set()),
    ("Search for MLOps engineer requirements.", {"search_web"}),
]


def main():
    print(f"Model: {MODEL} | think={THINK} | cases: {len(CASES)}\n")
    passed = 0
    total_seconds = 0.0

    for number, (question, expected) in enumerate(CASES, start=1):
        start = time.time()
        used, answer = run_case(question)
        seconds = time.time() - start
        total_seconds += seconds

        ok = set(used) == expected and bool(answer.strip()) and not answer.startswith("(stopped")
        passed += ok

        print(f"[{number}] {'PASS' if ok else 'FAIL'}  ({seconds:.0f}s)  {question}")
        print(f"     expected tools: {sorted(expected) or 'none'} | used: {used or 'none'}")
        print(f"     answer: {answer.strip()[:150]}\n")

    print("=" * 60)
    print(f"Passed {passed} of {len(CASES)}")
    print(f"Average time per question: {total_seconds / len(CASES):.0f} seconds")
    print("Rule of thumb: 8 or more out of 10 is good enough to build on.")


if __name__ == "__main__":
    main()