import ollama
from ddgs import DDGS

MAX_STEPS = 4          # our rule: the model gets at most 4 turns

def search_web(query: str) -> str:
    """Search the web and return the top results with title, link and a short snippet."""
    results = DDGS().text(query, max_results=5)
    lines = [f"{r['title']} | {r['href']} | {r['body'][:150]}" for r in results]
    return "\n".join(lines)

# a lookup table: tool name -> the real function. Our code uses it to run what the model asks for
tools_available = {"search_web": search_web}

client = ollama.Client(timeout=180)
messages = [{
    "role": "user",
    "content": "What skills does a Data Scientist job at Infosys need? Search first, then answer using only what the search results say.",
}]

for step in range(1, MAX_STEPS + 1):
    reply = client.chat(
        model="qwen3:8b",
        messages=messages,
        tools=[search_web],
        think=False,
        options={"temperature": 0.2, "num_predict": 500},
    )
    messages.append(reply.message)

    if not reply.message.tool_calls:          # no tool asked for, so this is the answer
        print(f"step {step}: the model answered, so we stop")
        print(reply.message.content)
        break

    for call in reply.message.tool_calls:     # the model may ask for more than one
        name = call.function.name
        args = call.function.arguments
        print(f"step {step}: the model asked for {name} with {args}")
        result = tools_available[name](**args)
        messages.append({"role": "tool", "tool_name": name, "content": result})
else:
    print("we hit the step limit and stopped the model ourselves")

result = tools_available[name](**args)

print("Search results returned by DuckDuckGo:")
print(result)