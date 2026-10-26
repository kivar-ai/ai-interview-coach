import json
import time
import ollama
import trafilatura

url = "https://in.linkedin.com/jobs/view/data-scientist-at-infosys-4407343227"
text = trafilatura.extract(trafilatura.fetch_url(url))
if not text:
    raise SystemExit("could not read the page")

SKILL_IDS = ["python", "sql", "statistics", "data_analysis", "data_visualization",
             "machine_learning", "deep_learning", "nlp", "llm_genai", "mlops",
             "data_engineering", "communication"]

# A FORM with one field per skill. Each field is filled once, so repeating is impossible.
schema = {
    "type": "object",
    "properties": {
        skill_id: {"type": "string", "enum": ["high", "medium", "low", "not_mentioned"]}
        for skill_id in SKILL_IDS
    },
    "required": SKILL_IDS,
}

prompt = (
    "Read this job page. For each skill id, say how important it is for the job: "
    "high = required or central, medium = preferred, low = mentioned briefly, "
    "not_mentioned = the page does not ask for it.\n\n"
    "PAGE:\n" + text
)

print("calling the model...")
start = time.time()
client = ollama.Client(timeout=180)
reply = client.chat(
    model="qwen3:8b",
    messages=[{"role": "user", "content": prompt}],
    format=schema,
    think=False,
    options={"temperature": 0.2, "num_predict": 400},
)
print("model finished in", round(time.time() - start), "seconds")

try:
    data = json.loads(reply.message.content)
    for skill, level in data.items():
        if level != "not_mentioned":
            print(skill, "-", level)
except json.JSONDecodeError:
    print("The answer was cut off or not valid JSON")
    print(reply.message.content)