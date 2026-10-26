import ollama
import trafilatura
from ddgs import DDGS

MAX_STEPS = 10
PAGES_WANTED = 2       # CHANGE 1: our rules, written as numbers in code
MAX_NUDGES = 2
BLOCKED_DOMAINS = ("interviewquery.com", "dataford.io", "foundit.in", "ziprecruiter.com")

pages = {}             # CHANGE 2: web link -> page text. This is our evidence box

def search_web(query: str) -> str:
    """Search the web and return the top results with title, link and a short snippet."""
    results = DDGS().text(query, max_results=10)
    results = [r for r in results if not any(d in r["href"] for d in BLOCKED_DOMAINS)][:5]
    lines = [f"{r['title']} | {r['href']} | {r['body'][:150]}" for r in results]
    return "\n".join(lines)

def read_page(url: str) -> str:
    """Open a web page by its link and return its main text."""
    if any(domain in url for domain in BLOCKED_DOMAINS):       # CHANGE 3: blocked sites
        return "Could not read this page. Try another link."
    downloaded = trafilatura.fetch_url(url)
    text = trafilatura.extract(downloaded) if downloaded else None
    if not text:
        return "Could not read this page. Try another link."
    pages[url] = text[:3000]                                    # CHANGE 4: keep the evidence
    return text[:3000]

tools_available = {"search_web": search_web, "read_page": read_page}

client = ollama.Client(timeout=180)
messages = [{
    "role": "user",
    "content": "What skills does a Data Scientist job at Infosys need? Search first, then read two different pages, then answer using only what the pages say.",
}]

nudges = 0

for step in range(1, MAX_STEPS + 1):
    reply = client.chat(
        model="qwen3:8b",
        messages=messages,
        tools=[search_web, read_page],
        think=False,
        options={"temperature": 0.2, "num_predict": 500},
    )
    messages.append(reply.message)

    if not reply.message.tool_calls:                  # the model wants to answer
        if len(pages) >= PAGES_WANTED:
            print(f"step {step}: the model answered after enough pages")
            break
        if nudges < MAX_NUDGES:                       # CHANGE 5: the guardrail
            nudges += 1
            print(f"step {step}: GUARDRAIL, the model tried to answer with only {len(pages)} page(s). Sending it back.")
            messages.append({
                "role": "user",
                "content": f"You have read only {len(pages)} page(s). Open {PAGES_WANTED} different pages with read_page before you answer.",
            })
            continue
        print(f"step {step}: the model would not read enough pages, we give up")
        break

    for call in reply.message.tool_calls:
        name = call.function.name
        args = call.function.arguments
        print(f"step {step}: the model asked for {name} with {args}")
        result = tools_available[name](**args)
        print(f"         tool gave back {len(result)} characters")
        messages.append({"role": "tool", "tool_name": name, "content": result})

    if len(pages) >= PAGES_WANTED:                    # CHANGE 6: our code ends the loop
        print(f"step {step}: enough pages, OUR code ends the loop. The model writes no answer.")
        break
else:
    print("we hit the step limit and stopped the model ourselves")

print("\npages really read:", len(pages))
for url in pages:
    print(" -", url)