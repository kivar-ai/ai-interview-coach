import json
import ollama

schema = {
    "type": "object",
    "properties": {
        "skills": {"type": "array", "items": {"type": "string", "enum": ["python", "sql", "statistics", "machine_learning"]}}
    },
    "required": ["skills"],
}

reply = ollama.chat(
    model="qwen3:8b",
    messages=[{"role": "user", "content": "What is the capital of France?"}],
    format=schema,
    think=False,
)

print(reply.message.content)
data = json.loads(reply.message.content)
print(data["skills"])
print(len(data["skills"]))