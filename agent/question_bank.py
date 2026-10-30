"""Question bank: loads our questions from data/questions_*.csv and files them in Chroma.

The CSV files are the truth. Chroma is rebuilt from them, so running this again is always safe.
"""

import argparse
import csv
import random
import json
from pathlib import Path

import chromadb

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DB_PATH = ROOT / "chroma_db"
COLLECTION = "questions"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"

_model = None

PER_IMPORTANCE = {"high": 3, "medium": 2, "low": 1}   # how many questions each skill gets
DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}

def embed(texts):
    """Turn a list of texts into a list of number-lists (embeddings)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print(f"Loading embedding model {EMBED_MODEL}...")
        _model = SentenceTransformer(EMBED_MODEL)
    return _model.encode(texts, normalize_embeddings=True).tolist()


def load_rows(data_dir=DATA):
    """Read every questions_*.csv file in the data folder."""
    rows = []
    for path in sorted(Path(data_dir).glob("questions_*.csv")):
        with open(path, encoding="utf-8", newline="") as f:
            rows.extend(csv.DictReader(f))
    return rows


def index_questions(rows=None):
    """File all questions in Chroma. New ones are added, changed ones are updated, removed ones are deleted."""
    rows = load_rows() if rows is None else rows
    ids = [r["id"] for r in rows]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"These question ids appear more than once: {', '.join(duplicates)}")

    collection = chromadb.PersistentClient(path=str(DB_PATH)).get_or_create_collection(
        COLLECTION, metadata={"hnsw:space": "cosine"})

    stale = set(collection.get()["ids"]) - set(ids)       # in Chroma, but no longer in any CSV
    if stale:
        collection.delete(ids=sorted(stale))
    if rows:
        collection.upsert(
            ids=ids,
            embeddings=embed([r["question"] + "\n" + r["ideal_answer"] for r in rows]),
            documents=[r["question"] for r in rows],
            metadatas=[{"skill": r["skill"], "difficulty": r["difficulty"],
                        "ideal_answer": r["ideal_answer"], "rubric": r["rubric"]} for r in rows],
        )
    return collection

RANK = {"easy": 0, "medium": 1, "hard": 2}
# which difficulty each pick should aim for, by how many questions the skill gets
SPREAD = {1: ["easy"], 2: ["easy", "medium"], 3: ["easy", "medium", "hard"]}


def spread_pick(questions, wanted, rng):
    """questions: list of (id, text, difficulty). Returns up to `wanted` of them,
    one per difficulty in SPREAD. If a level has no question, the nearest level is used.
    Inside a level the choice is random."""
    remaining = sorted(questions, key=lambda q: q[0])
    chosen = []
    for target in SPREAD.get(wanted, ["easy"])[:wanted]:
        if not remaining:
            break
        nearest = min(abs(RANK[q[2]] - RANK[target]) for q in remaining)
        candidates = [q for q in remaining if abs(RANK[q[2]] - RANK[target]) == nearest]
        pick = rng.choice(candidates)
        chosen.append(pick)
        remaining.remove(pick)
    return chosen

def pick_questions(research_skills, collection=None, rng=None):
    """research_skills: the skills list from research(), like [{"skill": "sql", "importance": "high"}, ...]
    Returns the test questions in the format of GET /test in docs/API_CONTRACT.md. No answers, no rubric."""
    if collection is None:
        collection = chromadb.PersistentClient(path=str(DB_PATH)).get_collection(COLLECTION)
    if rng is None:
        rng = random.Random()
    picked = []
    for item in research_skills:
        result = collection.get(where={"skill": item["skill"]})
        questions = [
            (question_id, text, meta["difficulty"])
            for question_id, text, meta in zip(result["ids"], result["documents"], result["metadatas"])
        ]
        wanted = PER_IMPORTANCE.get(item["importance"], 1)
        for question_id, text, _difficulty in spread_pick(questions, wanted, rng):
            picked.append({"question_id": question_id, "skill": item["skill"], "text": text})
    for number, question in enumerate(picked, start=1):
        question["number"] = number
    return picked

def main():
    parser = argparse.ArgumentParser(description="Index the question bank, or pick test questions.")
    parser.add_argument("--pick", help="a saved research result in data/research_cache, without .json, "
                                       "for example data_scientist__infosys")
    args = parser.parse_args()

    if args.pick:
        path = DATA / "research_cache" / f"{args.pick}.json"
        research = json.loads(path.read_text(encoding="utf-8"))
        for q in pick_questions(research["skills"]):
            print(f"{q['number']:2}. [{q['skill']}] {q['text']}")
        return

    collection = index_questions()
    counts = {}
    for meta in collection.get()["metadatas"]:
        counts[meta["skill"]] = counts.get(meta["skill"], 0) + 1
    print(f"Indexed {collection.count()} questions")
    for skill, number in sorted(counts.items()):
        print(f"  {skill:20} {number}")


if __name__ == "__main__":
    main()