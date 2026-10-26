# API contract (Contract 3)

This file is the single source of truth for what the **screen** sends and what the **AI core** returns.
The screen is built against these examples (using a fake API) before the real pipeline exists.
Change this file only through a pull request that all three of us approve.

- Base address while developing: `http://localhost:8000`
- All bodies are JSON. Errors always look like `{"error": "short message"}`.
- Ids used everywhere: skill ids come from `data/skills.json`, role ids from `data/roles.json`.
- Self-rating values: `beginner`, `intermediate`, `advanced`. Importance values: `high`, `medium`, `low`.
- Scores for one answer are whole numbers from 0 to 10. Skill scores in the report are 0 to 100.

---

## 1. Save the student profile
`POST /profile`

Request
```json
{
  "name": "Priya",
  "target_role": "data_scientist",
  "company": "Infosys",
  "job_description": null,
  "self_rating": {"python": "intermediate", "sql": "advanced", "statistics": "beginner"}
}
```
Response
```json
{"student_id": "s_001"}
```

## 2. Research the job (the agent)
`POST /research`

Request
```json
{"student_id": "s_001"}
```
Response
```json
{
  "role": "data_scientist",
  "company": "Infosys",
  "skills": [
    {"skill": "sql", "importance": "high", "sources": ["https://example.com/job-post"], "basis": "web"},
    {"skill": "statistics", "importance": "high", "sources": [], "basis": "base_profile"}
  ],
  "pages_read": [
    {"url": "https://example.com/job-post", "read": true},
    {"url": "https://blocked.example.com", "read": false}
  ],
  "cached": false,
  "warnings": [],
  "dropped_unverified": [],
  "seconds": 180
}
```
`basis` says where a skill came from: `web` = proven by a page we read (the `sources` hold the proof),
`base_profile` = taken from our own role profile because the pages did not mention it (`sources` is empty).
The screen can show the two differently, for example a small "from web" label. `warnings` holds messages to show
the student (for example "Only 1 page could be read"). `dropped_unverified` and `seconds` are for us, not for students.

## 3. Get the test questions
`GET /test?student_id=s_001`

Response
```json
{
  "test_id": "t_001",
  "total": 12,
  "questions": [
    {"question_id": "q_sql_001", "number": 1, "skill": "sql", "text": "What is the difference between INNER JOIN and LEFT JOIN?"}
  ]
}
```

## 4. Submit and grade one test answer
`POST /test/answer`

Request
```json
{"student_id": "s_001", "test_id": "t_001", "question_id": "q_sql_001", "answer": "INNER JOIN gives matching rows..."}
```
Response
```json
{
  "score": 4,
  "max_score": 10,
  "feedback": "You covered INNER JOIN but did not explain what LEFT JOIN keeps.",
  "missed_points": ["LEFT JOIN keeps all rows from the left table", "Unmatched right-side columns become NULL"]
}
```

## 5. The gap report
`GET /report?student_id=s_001`

Response
```json
{
  "skills": [
    {"skill": "sql", "job_needs": "high", "self_rating": "advanced", "measured_score": 40, "gap": 50}
  ],
  "top_gaps": ["sql", "statistics"]
}
```

## 6. The study plan
`GET /plan?student_id=s_001`

Response
```json
{
  "steps": [
    {
      "order": 1,
      "skill": "sql",
      "title": "Master joins and aggregation",
      "tasks": ["Practise INNER and LEFT JOIN on two small tables"],
      "resources": [{"title": "Example resource", "url": "https://example.com"}]
    }
  ]
}
```

## 7. Mock interview
`POST /interview/start`

Request
```json
{"student_id": "s_001", "focus_skills": ["sql", "statistics"], "num_questions": 5}
```
Response
```json
{"session_id": "m_001", "question": {"question_id": "q_sql_002", "number": 1, "skill": "sql", "text": "What is the difference between WHERE and HAVING?"}}
```

`POST /interview/answer`

Request
```json
{"session_id": "m_001", "answer": "WHERE filters rows, HAVING filters groups."}
```
Response
```json
{
  "score": 7,
  "max_score": 10,
  "feedback": "Good. Add that HAVING can use aggregates.",
  "missed_points": ["HAVING can use aggregate functions"],
  "next_question": {"question_id": "q_sql_003", "number": 2, "skill": "sql", "text": "..."},
  "finished": false
}
```
When `finished` is `true`, `next_question` is `null`.

## 8. Progress
`GET /progress?student_id=s_001`

Response
```json
{"history": [{"date": "2026-10-26", "skill": "sql", "score": 40}, {"date": "2026-10-30", "skill": "sql", "score": 65}]}
```

## 9. Ask a doubt (optional feature, build last)
`POST /doubt`

Request
```json
{"student_id": "s_001", "text": "Explain LEFT JOIN"}
```
Response
```json
{"found": true, "answer": "A LEFT JOIN keeps every row from the left table...", "source_question_ids": ["q_sql_001"]}
```
When nothing relevant is found: `{"found": false, "answer": "I don't have this yet."}`.
