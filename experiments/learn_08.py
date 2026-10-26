import ollama

def search_web(query: str) -> str:
    """Search the web for a query and return the top results."""
    # CHANGE 1: the fake result now has real-looking facts
    return "Infosys Data Scientist job: needs Python, SQL and machine learning. Communication is a plus."

client = ollama.Client(timeout=180)

# CHANGE 2: the question lives in a list called messages, so we can add to it later
messages = [{
    "role": "user",
    "content": "What skills does a Data Scientist job at Infosys need? Use the tool if you need to.",
}]

reply = client.chat(
    model="qwen3:8b",
    messages=messages,
    tools=[search_web],
    think=False,
    options={"temperature": 0.2, "num_predict": 300},
)

print("text:", reply.message.content)
print("tool calls:", reply.message.tool_calls)

# CHANGE 3: everything below is new
call = reply.message.tool_calls[0]
query = call.function.arguments["query"]
result = search_web(query)          # OUR code runs the tool, not the model
print("we ran the tool, it gave:", result)

messages.append(reply.message)      # remember what the model asked
messages.append({"role": "tool", "tool_name": "search_web", "content": result})

final = client.chat(
    model="qwen3:8b",
    messages=messages,
    tools=[search_web],
    think=False,
    options={"temperature": 0.2, "num_predict": 300},
)
print("final answer:", final.message.content)