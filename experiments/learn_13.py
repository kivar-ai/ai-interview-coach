import json
import chromadb
import ollama

db = chromadb.PersistentClient(path="chroma_db")
collection = db.get_collection("questions")
result = collection.get(ids=["q_sql_001"])
question = result["documents"][0]
rubric_points = [p.strip() for p in result["metadatas"][0]["rubric"].split("|")]

student_answer = "INNER JOIN gives only the matching rows from both tables. LEFT JOIN is similar but it also keeps the unmatched ones."

# one yes/no box per rubric point: a form, like the skills form
keys = [f"point_{i}" for i in range(1, len(rubric_points) + 1)]
schema = {"type": "object", "properties": {k: {"type": "string", "enum": ["yes", "partly", "no"]} for k in keys}, "required": keys}

checklist = "\n".join(f"{k}: {point}" for k, point in zip(keys, rubric_points))
prompt = f"""You are marking a student's interview answer.
Question: {question}
Student answer: {student_answer}

For each point below, answer "yes" if the student clearly states it, "partly" if they hint at it or say it vaguely, and "no" if it is missing.
{checklist}"""

llm = ollama.Client(timeout=180)
reply = llm.chat(
    model="qwen3:8b",
    messages=[{"role": "user", "content": prompt}],
    format=schema,
    think=False,
    options={"temperature": 0.2, "num_predict": 200},
)
marks = json.loads(reply.message.content)

weights = {"yes": 1, "partly": 0.5, "no": 0}
total = sum(weights[marks[k]] for k in keys)
score = int(10 * total / len(keys) + 0.5)       # halves round up
for k, point in zip(keys, rubric_points):
    print(f"{marks[k]:7}", point)
print("score:", score, "out of 10")