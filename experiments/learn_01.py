import ollama

reply = ollama.chat(
    model="qwen3:8b",
    messages=[{"role": "user", "content": "Name 3 skills a Machine learning needs. One line."}],
    think=False,
)
print(reply.message.content)