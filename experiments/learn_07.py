import json
import time
import ollama
import trafilatura
import json

url = "https://in.linkedin.com/jobs/view/data-scientist-at-infosys-4407343227"
page_text = trafilatura.extract(trafilatura.fetch_url(url))

if not page_text:
    raise SystemExit("could not read the page")

SKILL_IDS = ["python", "sql", "statistics", "data_analysis", "data_visualization",
             "machine_learning", "deep_learning", "nlp", "llm_genai", "mlops",
             "data_engineering", "communication"]

# A FORM with one field per skill. Each field is filled once, so repeating is impossible.
schema = {
    "type": "object",
    "properties": {
        skill_id: {
            "type": "object",
            "properties": {
                "importance": {"type": "string", "enum": ["high", "medium", "low", "not_mentioned"]},
                "quote": {"type": "string"},
            },
            "required": ["importance", "quote"],
        }
        for skill_id in SKILL_IDS
    },
    "required": SKILL_IDS,
}

prompt = (
    "Read this job page. For each skill id, say how important it is for the job: "
    "high = required or central, medium = preferred, low = mentioned briefly, "
    "not_mentioned = the page does not ask for it.\n\n"
    "For each skill, copy the exact sentence from the page that proves it into 'quote'. If the skill is not_mentioned, leave quote empty."
    "PAGE:\n" + page_text
)

print("calling the model...")
start = time.time()
client = ollama.Client(timeout=420)
reply = client.chat(
    model="qwen3:8b",
    messages=[{"role": "user", "content": prompt}],
    format=schema,
    think=False,
    options={"temperature": 0.2, "num_predict": 400},
)
print("model finished in", round(time.time() - start), "seconds")

try:
    answer = json.loads(reply.message.content)
    for skill, level in answer.items():
        if level != "not_mentioned":
            print(skill, "-", level)
except json.JSONDecodeError:
    print("The answer was cut off or not valid JSON")
    print(reply.message.content)

import re

def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)   # punctuation becomes a space
    return re.sub(r"\s+", " ", text).strip()    # many spaces become one

for skill_id in SKILL_IDS:
    quote = answer[skill_id]["quote"]
    if answer[skill_id]["importance"] == "not_mentioned":
        print(skill_id, "-> not mentioned")
    elif normalize(quote) == "":
        print(skill_id, "-> NO PROOF given, we throw this away")
    elif normalize(quote) in normalize(page_text):
        print(skill_id, "-> VERIFIED")
    else:
        print(skill_id, "-> NOT FOUND, we throw this away")