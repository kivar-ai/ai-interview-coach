import chromadb

client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_collection("questions")

result = collection.get(ids=["q_sql_001"])
meta = result["metadatas"][0]

print("question:", result["documents"][0])
print("skill:", meta["skill"])
print("ideal answer:", meta["ideal_answer"])
rubric_points = [point.strip() for point in meta["rubric"].split("|")]
print("rubric points:", len(rubric_points))
for point in rubric_points:
    print(" -", point)