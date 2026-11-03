r"""Run the grader on our golden answers and compare with the human expected score.

Usage, from the project root (Ollama must be running):
    python tools\golden_check.py              (all answers)
    python tools\golden_check.py --kind wrong  (only the wrong ones)
"""
import argparse
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
import grader  # noqa: E402

GOLDEN = ROOT / "data" / "golden_answers.csv"
TOLERANCE = 1          # a score within 1 point of the human score counts as agreement


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", help="only run answers of this kind: full, half or wrong")
    args = parser.parse_args()

    with open(GOLDEN, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if args.kind:
        rows = [r for r in rows if r["kind"] == args.kind]

    agreed = 0
    by_kind = {}               # kind -> [agreed, total]
    print(f"{'id':6} {'question':24} {'kind':6} {'expected':>8} {'got':>4}  result")
    for row in rows:
        expected = int(row["expected"])
        started = time.time()
        try:
            result = grader.grade_answer(row["question_id"], row["answer"])
        except Exception as error:
            print(f"{row['id']:6} {row['question_id']:24} {row['kind']:6} {expected:>8} {'-':>4}  ERROR: {error}")
            continue
        got = result["score"]
        ok = abs(got - expected) <= TOLERANCE
        agreed += ok
        tally = by_kind.setdefault(row["kind"], [0, 0])
        tally[0] += ok
        tally[1] += 1
        seconds = round(time.time() - started)
        print(f"{row['id']:6} {row['question_id']:24} {row['kind']:6} {expected:>8} {got:>4}  "
              f"{'OK' if ok else 'DISAGREE'} ({seconds}s)")
        if not ok:
            print(f"       missed: {result['missed_points']}")

    print()
    for kind, (good, total) in by_kind.items():
        print(f"  {kind:6} agreed {good} of {total}")
    print(f"\nThe grader agreed with the human on {agreed} of {len(rows)} answers (within {TOLERANCE} point).")


if __name__ == "__main__":
    main()
