import trafilatura

url = "https://www.interviewquery.com/guides/infosys-data-scientist"

downloaded = trafilatura.fetch_url(url)

if downloaded is None:
    print("Could not download this page")
else:
    print("raw page length:", len(downloaded))
    text = trafilatura.extract(downloaded)
    print("clean text length:", len(text))
    print(text[:500])