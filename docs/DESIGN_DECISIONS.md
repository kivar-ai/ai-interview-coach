# Design decisions

Why the project is built the way it is. Each decision has the problem, the choice and the reason.

## The one rule

> **The model judges. The code decides.**

A language model is good at reading text and bad at being trusted. So the model is only allowed to do two things: fill in a form about a web page, and mark one rubric point at a time. Everything else (picking questions, adding up scores, deciding the gaps, writing every sentence the student reads) is plain code that behaves the same way every time.

## Where does everything on screen come from?

| What the student sees | Where it comes from | Why it can be trusted |
|---|---|---|
| "Proven on the web" next to a skill | A quote copied from a real job page | Code checked the quote is on that page. Unproven skills are dropped |
| "Standard role profile" | `data/roles.json` | Written by us, labelled as a fallback |
| The questions | `data/questions_*.csv` | Written by us, checked by `tools/validate_data.py` |
| A score for an answer | Rubric points marked yes, partly or no | Each mark needs a quote from the student's own answer that code can verify |
| The feedback sentences | Templates filled with our data | The model writes none of them |
| The gap | `target - measured`, never below 0 | Fixed formula in `agent/gap.py` |
| The study tasks | The rubric points the student missed | Taken from our own rubric |
| The study links | `data/resources.json` | Checked by hand, never invented |

## Decisions

### 1. An agent with a leash (research)

- **Problem:** the coach should read real job posts, but a free-running model can wander, loop or stop too early.
- **Choice:** the model picks what to search and read, but code stops it after **2 pages are read** or **10 model calls**. If it tries to finish early, a guardrail sends it back to the tools, at most twice.
- **Why:** we keep the useful part of an agent (it chooses sources) and remove the risk (it cannot run away).

### 2. Proof or it is dropped

- **Problem:** a model can invent a skill and a convincing quote.
- **Choice:** one model call lists skills with a quote. Code keeps a skill **only if the quote appears in a page we read**. Skills the pages did not mention are filled in from the role profile and labelled `base_profile`.
- **Why:** the screen can honestly say "Proven on the web", and a thin page can never leave a hole.

### 3. Cache the research

- **Problem:** research takes 3 to 5 minutes.
- **Choice:** save the result per role and company in `data/research_cache`. The first student waits, everyone after gets it instantly.
- **Side effect:** the cached jobs make good demos, because they work without internet.

### 4. One model call per rubric point

- **Problem:** asking the model to grade a whole answer in one go was not reliable enough, and it was too generous on wrong answers.
- **Choice:** one narrow question per rubric point: "did the student cover this point? Quote their words." Temperature 0, so the same answer gets the same mark.
- **Why:** a narrow question is easier to answer correctly and to check. The cost is time: 4 rubric points means 4 model calls.

### 5. Verify the quote, demote the mark

- **Choice:** if the model says "yes" or "partly" but the quote it gives is not really in the student's answer, code changes the mark to "no".
- **Why:** the model has to show evidence. Without it, no credit.

### 6. A golden set to measure the grader

- **Problem:** "it seems to work" is not a measurement.
- **Choice:** `data/golden_answers.csv` holds 30 answers with known scores (strong, partial and wrong). `tools/golden_check.py` runs the real grader and counts how many land within 1 point.
- **Result:** the one-call-per-point grader reached **28 of 30**. Adding an extra field to the prompt made a test subset worse (3 of 6), so we undid it.
- **Limit:** the answers were written by us, not real students. Real student answers should be added later.

### 7. Grade in the background

- **Problem:** marking takes 1 to 2 minutes per answer. A browser request cannot wait that long, and the student should not stare at a spinner.
- **Choice:** saving an answer replies `202 grading` straight away. A background task marks it, **one at a time** (`GRADE_LOCK`), because the CPU runs the model once. The screen asks `GET /test/results` every 5 seconds.
- **Known limit:** the waiting list lives in memory, so a backend restart loses jobs that were still waiting.

### 8. The CSV is the truth, Chroma is a copy

- **Choice:** questions are written in CSV files (easy to edit in Excel or Google Sheets, easy to review in git). `python agent\question_bank.py` rebuilds Chroma from them whenever you like.
- **Why:** nobody edits a vector database by hand, and a lost Chroma folder costs nothing.
- **Honest note:** today the grader fetches a rubric **by question id**. The meaning-based search that Chroma also supports is not used yet. It is ready for the "ask a doubt" feature.

### 9. SQLite for the students

- **Choice:** one file, `data/coach.db`, no server to install.
- **Limits:** one writer at a time and one machine only. Both are fine for a demo and a few hundred students.
- **Switching later:** only `backend/db.py` talks to the database, so that is the one file to change.

### 10. The interviewer lives in the browser

- **Choice:** the face is an SVG drawing, and the voice is the browser's built-in speech. The backend knows nothing about it.
- **Why:** no cloud service, no extra install, and it cannot affect grading.

### 11. Open source only

| Need | Tool |
|---|---|
| Language model | Ollama running `qwen3:8b` on the student's own machine |
| Web search | `ddgs` (DuckDuckGo) |
| Reading pages | `trafilatura` |
| Question store | Chroma, with the `BAAI/bge-small-en-v1.5` embedding model |
| Backend | FastAPI and uvicorn |
| Database | SQLite |
| Screen | React and Vite |

## What we chose not to build (yet)

| Idea | Why it waits |
|---|---|
| Answering by voice | Needs a speech-to-text model such as Whisper. It would compete with the grader for the same CPU, and spoken answers are messier than typed ones |
| A live, back-and-forth mock interview | Marking takes about a minute, so the interviewer cannot react to each answer |
| A talking video avatar | Needs a strong graphics card |
| Public hosting | The model needs a powerful machine, and one laptop marks one answer at a time |

## Roadmap

1. Questions for the 7 skills that have none (Data Analysis, Data Visualization and Communication matter most for analysts), and more for LLM and GenAI, which has only 1
2. Recover waiting answers after a restart, and keep the test across a page refresh
3. A time limit on research
4. Score only the latest attempt, so practice shows real improvement
5. Faster grading: a faster model or a GPU
6. Report ranking that also weighs importance, not only gap size
7. More golden answers, from real students
8. Review `data/roles.json` against real job posts
9. A progress screen and the "ask a doubt" feature
