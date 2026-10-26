"""Checks our shared data files against the contracts.

Run from the project folder:
    python tools/validate_data.py

It checks:
  - data/skills.json is well formed
  - data/roles.json only uses real skill ids and valid importance levels
  - every question file in data/ (questions*.csv) has the right columns and valid values

Exit code 0 = all good. Exit code 1 = problems found (they are printed).
Later we will run this automatically on GitHub for every pull request.
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

REQUIRED_COLUMNS = ["id", "skill", "difficulty", "question", "ideal_answer", "rubric", "source"]
DIFFICULTIES = {"easy", "medium", "hard"}
MIN_RUBRIC_POINTS = 3

errors = []


def error(message):
    errors.append(message)


def load_skills():
    with open(DATA / "skills.json", encoding="utf-8") as f:
        data = json.load(f)
    ids = [s["id"] for s in data["skills"]]
    if len(ids) != len(set(ids)):
        error("skills.json: duplicate skill ids")
    return set(ids), set(data["levels_importance"])


def check_roles(skill_ids, importance_levels):
    with open(DATA / "roles.json", encoding="utf-8") as f:
        roles = json.load(f)["roles"]
    for role_id, role in roles.items():
        for skill, level in role["skills"].items():
            if skill not in skill_ids:
                error(f"roles.json: role '{role_id}' uses unknown skill '{skill}'")
            if level not in importance_levels:
                error(f"roles.json: role '{role_id}' skill '{skill}' has invalid level '{level}'")
    return len(roles)


def check_questions(path, skill_ids):
    seen_ids = set()
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            error(f"{path.name}: missing columns {missing}")
            return 0
        count = 0
        for line, row in enumerate(reader, start=2):  # line 1 is the header
            count += 1
            where = f"{path.name} line {line} (id={row.get('id')!r})"
            for column in REQUIRED_COLUMNS:
                if not (row.get(column) or "").strip():
                    error(f"{where}: '{column}' is empty")
            if row["id"] in seen_ids:
                error(f"{where}: duplicate id")
            seen_ids.add(row["id"])
            if row["skill"] not in skill_ids:
                error(f"{where}: unknown skill '{row['skill']}' (must be an id from skills.json)")
            if row["difficulty"] not in DIFFICULTIES:
                error(f"{where}: difficulty must be one of {sorted(DIFFICULTIES)}")
            points = [p for p in row["rubric"].split("|") if p.strip()]
            if len(points) < MIN_RUBRIC_POINTS:
                error(f"{where}: rubric needs at least {MIN_RUBRIC_POINTS} points separated by '|'")
    return count


def main():
    skill_ids, importance_levels = load_skills()
    role_count = check_roles(skill_ids, importance_levels)
    files = sorted(DATA.glob("questions*.csv"))
    total = sum(check_questions(path, skill_ids) for path in files)

    if errors:
        print(f"Found {len(errors)} problem(s):")
        for message in errors:
            print("  -", message)
        sys.exit(1)
    print(f"OK: {len(skill_ids)} skills, {role_count} roles, {total} questions in {len(files)} file(s).")


if __name__ == "__main__":
    main()
