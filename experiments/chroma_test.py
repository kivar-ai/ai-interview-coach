"""See RAG with your own eyes: index our questions, then search them.

What this shows
  1. INDEXING (done once): turn each question into numbers (an embedding) and store it in Chroma.
  2. LOOKUP BY TAG: get all questions for one skill. No meaning-search needed. Used for the test.
  3. SEARCH BY MEANING: a student's free-text doubt finds the closest questions. Used for "Ask a doubt".

Setup (inside the project's .venv):
    pip install chromadb sentence-transformers
Run:
    python experiments/chroma_test.py

The first run downloads a small embedding model (about 130 MB). After that it works offline.
"""

import csv
from pathlib import Path

import chromadb

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "questions_sample.csv"
DB_PATH = ROOT / "chroma_db"          # git-ignored: it is rebuilt from the CSV any time
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
# BGE models work best when the SEARCH text (not the stored text) starts with this sentence.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

_model = None


def embed(texts, is_query=False):
    """Turn a list of texts into a list of number-lists (embeddings)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print(f"Loading embedding model {EMBED_MODEL} (the first run downloads it)...")
        _model = SentenceTransformer(EMBED_MODEL)
    if is_query:
        texts = [QUERY_PREFIX + t for t in texts]
    return _model.encode(texts, normalize_embeddings=True).tolist()


def load_rows():
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def build_index(rows):
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_or_create_collection("questions", metadata={"hnsw:space": "cosine"})
    # We search on question + ideal answer together, so a doubt like "Explain LEFT JOIN"
    # can match the answer text too. We STORE the question as the document and keep the
    # ideal answer and rubric as metadata, ready for grading.
    searchable = [r["question"] + "\n" + r["ideal_answer"] for r in rows]
    collection.upsert(  # upsert = insert new, update existing. Safe to re-run.
        ids=[r["id"] for r in rows],
        embeddings=embed(searchable),
        documents=[r["question"] for r in rows],
        metadatas=[
            {"skill": r["skill"], "difficulty": r["difficulty"],
             "ideal_answer": r["ideal_answer"], "rubric": r["rubric"]}
            for r in rows
        ],
    )
    return collection


def lookup_by_skill(collection, skill):
    result = collection.get(where={"skill": skill})
    return list(zip(result["ids"], result["documents"]))


def search_by_meaning(collection, text, k=2, skill=None):
    result = collection.query(
        query_embeddings=embed([text], is_query=True),
        n_results=k,
        where={"skill": skill} if skill else None,
    )
    hits = []
    for qid, doc, dist in zip(result["ids"][0], result["documents"][0], result["distances"][0]):
        hits.append((qid, doc, 1 - dist))  # cosine distance -> similarity (higher = closer)
    return hits


def main():
    rows = load_rows()
    collection = build_index(rows)
    print(f"\nIndexed {collection.count()} questions into Chroma ({DB_PATH.name}/).")

    print("\n--- 1) LOOKUP BY TAG: all questions for skill = sql ---")
    for qid, question in lookup_by_skill(collection, "sql"):
        print(f"  {qid}: {question}")

    doubts = [
        "Explain LEFT JOIN",
        "my model works on training data but fails on new data",
        "how do I let an LLM use my own documents",
        "who won the cricket match",  # off-topic on purpose: look at the low similarity
    ]
    print("\n--- 2) SEARCH BY MEANING (similarity: higher = closer, 1.0 = identical) ---")
    for doubt in doubts:
        print(f"\n  Student asks: {doubt!r}")
        for qid, question, similarity in search_by_meaning(collection, doubt):
            print(f"    {similarity:.2f}  {qid}: {question}")

    print("\nLook at the numbers: relevant doubts should score clearly higher than the off-topic one.")
    print("Similarity scores are never exactly 0, so later we pick a minimum value from")
    print("numbers like these, below which the coach says 'I don't have this yet'.")


if __name__ == "__main__":
    main()
