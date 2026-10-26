import ollama
import trafilatura
from ddgs import DDGS

MAX_STEPS = 6          # raised from 4, because the model now has more it can do

def search_web(query: str) -> str:
    """Search the web and return the top results with title, link and a short snippet."""
    results = DDGS().text(query, max_results=5)
    lines = [f"{r['title']} | {r['href']} | {r['body'][:150]}" for r in results]
    return "\n".join(lines)

# CHANGE 1: a second tool, the download-and-clean step from learn_04
def read_page(url: str) -> str:
    """Open a web page by its link and return its main text."""
    downloaded = trafilatura.fetch_url(url)
    text = trafilatura.extract(downloaded) if downloaded else None
    if not text:
        return "Could not read this page. Try another link."
    return text[:3000]

# CHANGE 2: the lookup table now has both tools
tools_available = {"search_web": search_web, "read_page": read_page}

client = ollama.Client(timeout=180)
messages = [{
    "role": "user",
    # CHANGE 3: the question now asks for a page to be read
    "content": "What skills does a Data Scientist job at Infosys need? Search first, then read at least one page, then answer using only what the pages say.",
}]

pages_read = 0

for step in range(1, MAX_STEPS + 1):
    reply = client.chat(
        model="qwen3:8b",
        messages=messages,
        tools=[search_web, read_page],       # CHANGE 4: both buttons on the menu
        think=False,
        options={"temperature": 0.2, "num_predict": 500},
    )
    messages.append(reply.message)

    if not reply.message.tool_calls:
        print(f"step {step}: the model answered, so we stop")
        print(reply.message.content)
        break

    for call in reply.message.tool_calls:
        name = call.function.name
        args = call.function.arguments
        print(f"step {step}: the model asked for {name} with {args}")
        result = tools_available[name](**args)
        if name == "read_page" and not result.startswith("Could not"):
            pages_read += 1             # CHANGE 5: we count the pages truly read
        print(f"         tool gave back {len(result)} characters")
        messages.append({"role": "tool", "tool_name": name, "content": result})
else:
    print("we hit the step limit and stopped the model ourselves")

print("pages really read:", pages_read)