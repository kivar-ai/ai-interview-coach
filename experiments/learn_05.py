from ddgs import DDGS
import trafilatura

BLOCKED = ("interviewquery.com", "dataford.io", "foundit.in", "ziprecruiter.com")

results = DDGS().text("data scientist skills Infosys", max_results=8)

pages = {}   # url -> clean text

for item in results:
    url = item["href"]

    if any(site in url for site in BLOCKED):
        print("skip (known blocked):", url)
        continue

    downloaded = trafilatura.fetch_url(url)
    text = trafilatura.extract(downloaded) if downloaded else None

    if not text:
        print("could not read:", url)
        continue

    pages[url] = text
    print("read OK:", url, len(text), "characters")

    if len(pages) == 3:
        break

print()
print("pages collected:", len(pages))