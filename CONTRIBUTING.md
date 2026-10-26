# How we work in this repository

## The three contracts (agree first, change only together)
1. `data/skills.json` - the fixed skill list
2. `docs/QUESTION_FORMAT.md` - the question file format
3. `docs/API_CONTRACT.md` - what the screen sends and receives

A change to a contract needs a pull request approved by **all three** of us.

## One task at a time
1. Pick one issue from the project board. Put your name on it.
2. Make your own branch from `main`:
   ```
   git checkout main
   git pull
   git checkout -b feature/short-name
   ```
3. Work, then save your work:
   ```
   git add .
   git commit -m "Short clear message about what changed"
   git push -u origin feature/short-name
   ```
4. Open a **pull request** on GitHub. Say what you changed and how to check it.
5. A teammate reviews it. After approval, merge it into `main`.

## Rules
- Never work directly on `main`.
- Never commit passwords, keys, `.env`, `chroma_db/` or student data.
- Run `python tools/validate_data.py` before committing any data file.
- Stuck or blocked? Say so in the group chat the same day, and say what you are waiting for.
- Keep tasks small enough to finish in 1 to 2 days.

## Folders
| Folder | What lives there |
|---|---|
| `agent/` | the research agent and the controller (AI core) |
| `backend/` | the FastAPI app |
| `frontend/` | the React screens |
| `data/` | skills, roles, question files |
| `docs/` | contracts and guides |
| `tools/` | small helper scripts, such as the data validator |
| `experiments/` | learning and test scripts |
