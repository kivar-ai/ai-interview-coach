import trafilatura

urls = [
    "https://in.linkedin.com/jobs/view/data-scientist-at-infosys-4407343227",
    "https://www.gravityer.com/jobs/data-scientist-infosys",
]
for url in urls:
    text = trafilatura.extract(trafilatura.fetch_url(url)) or ""
    i = text.lower().find("statistical")
    print("\n---", url)
    print(text[max(0, i - 100): i + 250] if i >= 0 else "the word 'statistical' is not on this page")