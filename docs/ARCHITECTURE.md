# Architecture

How the AI Interview Coach fits together. Read the pictures first, the notes second.

## 1. The system in one picture

```mermaid
flowchart LR
    subgraph Browser["Browser  (localhost:5173)"]
      UI["React screens"]
    end
    subgraph Server["Backend  (localhost:8000, FastAPI)"]
      API["backend/main.py"]
      DB["backend/db.py"]
      AG["agent/*.py"]
    end
    subgraph Store["Stored on your machine"]
      SQL[("SQLite<br/>data/coach.db<br/>students, tests, answers")]
      CH[("Chroma<br/>chroma_db<br/>question copy")]
      JS["JSON and CSV files<br/>roles, skills, resources,<br/>questions, research_cache"]
    end
    LLM["Ollama<br/>qwen3:8b"]
    WEB["The web<br/>search and job pages"]

    UI <-->|"HTTP + JSON"| API
    API --> DB --> SQL
    API --> AG
    AG --> CH
    AG --> JS
    AG --> LLM
    AG --> WEB
```

The browser only draws screens and sends requests. The backend decides and saves. The two are separate programs, which is why they run in two terminals.

## 2. Two kinds of data

| | Reference data | Student data |
|---|---|---|
| What it is | The menu: roles, skills, questions, study links, saved research | The people: profiles, tests, answers |
| Lives in | `data/*.json`, `data/*.csv`, `data/research_cache/` | SQLite, `data/coach.db` |
| Written by | The team, by hand (research cache: by the agent) | The app, while students use it |
| In git | Yes | No |

`chroma_db/` is a third thing: a **built copy** of the questions CSVs, made for fast lookup. It can always be rebuilt with `python agent\question_bank.py`.

## 3. Step by step

### 3.1 Profile

```mermaid
sequenceDiagram
    participant S as ProfileScreen
    participant A as App.jsx
    participant B as backend/main.py
    participant D as SQLite
    A->>B: GET /options
    B-->>A: roles and skills (from roles.json, skills.json)
    A->>S: options as props
    S->>B: POST /profile (name, role, company, self-ratings)
    B->>B: check role and skill ids
    B->>D: save the student
    B-->>S: student_id
    S->>A: onSaved(student)
    A->>A: screen = research
```

Every later request carries the `student_id`. It is the key that ties research, tests, answers and reports to one person. It lives only in browser memory, so a page refresh forgets it.

### 3.2 Job research

```mermaid
sequenceDiagram
    participant R as ResearchScreen
    participant B as backend/main.py
    participant C as research_cache
    participant G as agent/research.py
    R->>B: POST /research (student_id)
    B->>C: saved result for this role and company?
    alt found
        C-->>R: 200 result (instant)
    else not found
        B-->>R: 202 working
        B->>G: run in the background
        loop every 5 seconds
            R->>B: POST /research
            B-->>R: 202 working
        end
        G->>C: save the result
        R->>B: POST /research
        B-->>R: 200 result
    end
```

### 3.3 Skill test and saving answers

```mermaid
sequenceDiagram
    participant T as TestScreen
    participant B as backend/main.py
    participant Q as question_bank.py
    participant D as SQLite
    T->>B: GET /test (student_id)
    B->>Q: pick questions for the researched skills
    Q-->>B: questions
    B->>D: create the test
    B-->>T: test_id and questions (no rubric, no ideal answer)
    loop each question
        T->>B: POST /test/answer
        B->>D: save the answer as pending
        B-->>T: 202 grading
    end
```

The rubric and ideal answer never leave the backend.

### 3.4 Grading in the background

```mermaid
sequenceDiagram
    participant B as backend/main.py
    participant G as agent/grader.py
    participant C as Chroma
    participant M as Ollama model
    participant D as SQLite
    participant T as TestScreen
    B->>G: grade the answer (one at a time, GRADE_LOCK)
    G->>C: rubric for this question id
    loop each rubric point
        G->>M: question, ONE point, student answer
        M-->>G: student_said and mark
        G->>G: is the quote really in the answer?
    end
    G->>G: add up the score, write the feedback
    G->>D: answer becomes done (or failed)
    loop every 5 seconds
        T->>B: GET /test/results
        B->>D: read statuses
        B-->>T: graded count and finished flag
    end
```

### 3.5 Gap report and study plan

```mermaid
flowchart LR
    P[("Profile<br/>self-rating")] --> R
    S[("Research<br/>job_needs")] --> R
    A[("Graded answers<br/>measured score")] --> R
    R["agent/gap.py<br/>build_report"] --> G["GET /report<br/>gap map and top 3 gaps"]
    G --> N["agent/planner.py<br/>build_plan"]
    M[("Missed rubric points<br/>from graded answers")] --> N
    L[("data/resources.json<br/>checked links")] --> N
    N --> Pl["GET /plan<br/>study steps"]
```

Nothing here is stored. The report and plan are computed again on every request.

### 3.6 Practice round

```mermaid
flowchart LR
    Plan["Plan screen<br/>Start a practice round"] --> E["GET /practice"]
    E --> T3["top gaps from the report"]
    T3 --> Pick["pick_questions<br/>importance medium"]
    Pick --> New["new test row in SQLite"]
    New --> Same["same TestScreen, same grading,<br/>same polling"]
    Same --> Rep["updated gap report"]
```

The practice round reuses the test machinery. It only changes which questions are picked, and adds the voiced interviewer in the browser.

## 4. Inside the research agent

```mermaid
flowchart TB
    Start["role and company"] --> Cache{"saved result?"}
    Cache -->|yes| Done["return it"]
    Cache -->|no| G1["1. GATHER<br/>model uses search_web and read_page"]
    G1 --> Stop["CODE stops it after 2 pages are read<br/>or after 10 model calls"]
    Stop --> G2["2. EXTRACT<br/>one model call lists skills,<br/>importance and a quote from the page"]
    G2 --> G3["3. VERIFY (code)<br/>keep a skill only if its quote<br/>appears in a page we read"]
    G3 --> G4["4. MERGE (code)<br/>add base-profile skills the pages missed"]
    G4 --> Save["save to research_cache and return"]

    classDef agent fill:#ffe9a8,stroke:#b58900,color:#182024
    classDef model fill:#e3f1eb,stroke:#0e6b52,color:#182024
    classDef code fill:#eef1f5,stroke:#5b6770,color:#182024
    class G1 agent
    class G2 model
    class Stop,G3,G4 code
```

Tools used: `ddgs` for search, `trafilatura` to read pages, Ollama for the model. If the model tries to stop early, a guardrail sends it back to the tools, at most twice. Each skill in the result is labelled `web` (proven by a quote) or `base_profile` (from `data/roles.json`).

## 5. Inside the grader

```mermaid
flowchart TB
    In["student answer"] --> Empty{"empty?"}
    Empty -->|yes| Zero["every point is no<br/>score 0, no model call"]
    Empty -->|no| Rub["rubric for the question,<br/>fetched from Chroma by id"]
    Rub --> Loop["for each rubric point"]
    Loop --> Call["ONE model call<br/>question + one point + answer<br/>returns student_said and mark"]
    Call --> Check{"quote really in<br/>the student's answer?"}
    Check -->|"no, and mark was yes or partly"| Dem["demote to no"]
    Check -->|yes| Keep["keep the mark"]
    Dem --> Sum
    Keep --> Sum["CODE adds up the marks<br/>score out of 10"]
    Zero --> Sum
    Sum --> Fb["CODE writes the feedback<br/>from templates and missed points"]
    Fb --> Out["answer becomes done<br/>in SQLite"]

    classDef model fill:#e3f1eb,stroke:#0e6b52,color:#182024
    classDef code fill:#eef1f5,stroke:#5b6770,color:#182024
    class Call model
    class Zero,Rub,Dem,Keep,Sum,Fb,Out,Check code
```

An answer with 4 rubric points means 4 model calls, one after another. That is the reason marking takes 1 to 2 minutes on a CPU. Temperature is 0, so the same answer gets the same marks.

**How we know the grader is good.** `data/golden_answers.csv` holds 30 answers whose right score we already know. `tools/golden_check.py` runs the grader on them and checks it lands within 1 point. One call per rubric point scored 28 of 30. The answers were written by us, not by real students, so this is a good sign and not a guarantee.

## 6. How the gap is worked out (`agent/gap.py`)

| Importance | Target score |
|---|---|
| high | 90 |
| medium | 70 |
| low | 50 |

- **Measured score** = the average of the skill's graded answers, in percent, halves rounded up. A skill with no graded answer is "not tested".
- **Gap** = target minus measured score, never below 0.
- **Top gaps** = up to 3 skills that were tested and are below their target, biggest gap first.

Worked example: SQL is high need and scored 77, so the gap is 90 - 77 = 13. Python is medium need and scored 80, so the gap is max(0, 70 - 80) = 0, which means "on target".

The plan (`agent/planner.py`) takes each top gap and adds up to 3 tasks, each "Revise: " followed by a rubric point the student missed, plus one practice task. Links come only from `data/resources.json`.

## 7. The screen's components

```mermaid
flowchart TB
    M["main.jsx<br/>starts React, loads fonts and CSS"] --> App["App.jsx<br/>remembers the screen and the student,<br/>loads GET /options"]
    App --> Sh["Shell.jsx<br/>green rail, step dots, student name"]
    Sh --> P["ProfileScreen"]
    Sh --> Re["ResearchScreen"]
    Sh --> Te["TestScreen<br/>(also the practice round)"]
    Sh --> Rp["ReportScreen"]
    Sh --> Pl["PlanScreen"]
    Te --> Iv["Interviewer<br/>face and voice, practice only"]
    api["api.js<br/>backend address"] -.-> P
    api -.-> Re
    api -.-> Te
    api -.-> Rp
    api -.-> Pl
```

`App.jsx` passes the student and the `options` lists down as props, and each screen calls back (`onSaved`, `onNext`, `onDone`, `onPractice`, `onRestart`) to move to the next screen.

## 8. The API at a glance

| Endpoint | Does |
|---|---|
| `GET /health` | Is the backend alive |
| `GET /options` | Roles and skills for the profile screen |
| `POST /profile` | Save the student, returns `student_id` |
| `POST /research` | Job research. 202 while working, 200 with the result |
| `GET /test` | Create a test and return its questions |
| `POST /test/answer` | Save an answer, grading starts in the background |
| `GET /test/results` | Progress and results of a test |
| `GET /practice` | Create a practice test on the top gaps |
| `GET /report` | The gap report |
| `GET /plan` | The study plan |

Errors always look like `{"error": "short message"}`.

## 9. Known limits

| Limit | Why |
|---|---|
| Restarting the backend loses answers waiting to be marked | The waiting list is in memory only |
| A page refresh loses the current test | The test and student id live in browser memory |
| Marking is slow | One model call per rubric point, on a CPU |
| Research has no time limit | A stuck page read can hang |
| 8 skills have no questions | Content is still to be written |
| The report averages all attempts | "Latest attempt only" is not built |
