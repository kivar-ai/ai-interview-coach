from ddgs import DDGS

results = DDGS().text("data scientist skills Infosys", max_results=5)
for number, item in enumerate(results, start=1):
    print(number, item["title"])
    print("   ", item["href"])
    print("   ", item["body"][:100])