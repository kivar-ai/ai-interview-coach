# Question file format (Contract 2)

Every question lives in a CSV file in the `data/` folder, with a name like `questions_sql.csv`.
You can write the questions in **Google Sheets or Excel** and download as CSV (UTF-8). You do not need a laptop setup for this.

## Columns (exactly these names, in this order)

| Column | What to write | Example |
|---|---|---|
| `id` | Unique id: `q_<skill>_<number>` | `q_sql_004` |
| `skill` | One skill id from `data/skills.json` | `sql` |
| `difficulty` | `easy`, `medium` or `hard` | `medium` |
| `question` | The question, as an interviewer would ask it | `What is a primary key?` |
| `ideal_answer` | A correct, clear answer, 2 to 5 sentences, in your own words | `A primary key uniquely identifies...` |
| `rubric` | At least 3 points a good answer should contain, separated by `|` | `Unique per row | Cannot be NULL | Example` |
| `source` | `original` if you wrote it yourself | `original` |

## Rules

1. **Write everything yourself.** Do not copy questions or answers from websites, books, paid courses or other people's notes. It is a copyright risk and it would make our content not ours.
2. **Correctness first.** The grader marks students against your ideal answer, so a wrong ideal answer means wrong marks. Anything you are not sure about, mark in the `source` column as `needs_review`. The AI core person will check it.
3. **Target:** about 5 to 8 questions for each of the 12 skills, with a mix of easy, medium and hard.
4. **One idea per question.** Prefer "What is the difference between X and Y?" and "When would you use X?" over very long questions.
5. Look at `data/questions_sample.csv` for 10 finished examples.

## Check your file

```
python tools/validate_data.py
```
It tells you which line has a problem (wrong skill id, missing rubric and so on). If you cannot run Python, send the file to the AI core person and they will run it.
