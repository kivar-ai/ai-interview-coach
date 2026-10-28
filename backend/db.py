import json
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent.parent / "data" / "coach.db"


def connect():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row          # rows behave like dictionaries
    return conn


def init_db():
    """Create the tables if they do not exist yet. Safe to run every time the server starts."""
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_role TEXT NOT NULL,
                company TEXT,
                job_description TEXT,
                self_rating TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_questions (
                test_id INTEGER NOT NULL,
                number INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                skill TEXT NOT NULL,
                text TEXT NOT NULL,
                PRIMARY KEY (test_id, number)
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                answer TEXT NOT NULL,
                score INTEGER NOT NULL,
                max_score INTEGER NOT NULL,
                feedback TEXT,
                missed_points TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (test_id, question_id)
            )""")


def create_student(name, target_role, company, job_description, self_rating):
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO students (name, target_role, company, job_description, self_rating) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, target_role, company, job_description, json.dumps(self_rating)),
        )
    return f"s_{cursor.lastrowid:03d}"          # 1 becomes "s_001"


def get_student(student_id):
    try:
        number = int(student_id.removeprefix("s_"))
    except ValueError:
        return None
    with connect() as conn:
        row = conn.execute("SELECT * FROM students WHERE id = ?", (number,)).fetchone()
    if row is None:
        return None
    student = dict(row)
    student["self_rating"] = json.loads(student["self_rating"])
    return student

def create_test(student_id, questions):
    """Save a test and its questions together. Returns the test id, like "t_001"."""
    student_number = int(student_id.removeprefix("s_"))
    with connect() as conn:                      # one transaction: both inserts happen, or neither
        cursor = conn.execute("INSERT INTO tests (student_id) VALUES (?)", (student_number,))
        test_number = cursor.lastrowid
        conn.executemany(
            "INSERT INTO test_questions (test_id, number, question_id, skill, text) VALUES (?, ?, ?, ?, ?)",
            [(test_number, q["number"], q["question_id"], q["skill"], q["text"]) for q in questions],
        )
    return f"t_{test_number:03d}"

def _number(text, prefix):
    """"s_007" becomes 7. Returns None if the text is not in that format."""
    try:
        return int(text.removeprefix(prefix))
    except ValueError:
        return None


def get_test_question(student_id, test_id, question_id):
    """The question, only if it belongs to a test of THIS student."""
    student_number, test_number = _number(student_id, "s_"), _number(test_id, "t_")
    if student_number is None or test_number is None:
        return None
    with connect() as conn:
        row = conn.execute(
            "SELECT q.* FROM test_questions q JOIN tests t ON t.id = q.test_id "
            "WHERE t.student_id = ? AND q.test_id = ? AND q.question_id = ?",
            (student_number, test_number, question_id),
        ).fetchone()
    return dict(row) if row else None


def has_answer(test_id, question_id):
    with connect() as conn:
        row = conn.execute("SELECT 1 FROM answers WHERE test_id = ? AND question_id = ?",
                           (_number(test_id, "t_"), question_id)).fetchone()
    return row is not None


def save_answer(test_id, question_id, answer, result):
    with connect() as conn:
        conn.execute(
            "INSERT INTO answers (test_id, question_id, answer, score, max_score, feedback, missed_points) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (_number(test_id, "t_"), question_id, answer, result["score"], result["max_score"],
             result["feedback"], json.dumps(result["missed_points"])),
        )

def get_answer_rows(student_id):
    """Every answer of this student, with the skill of its question."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT q.skill AS skill, a.score AS score, a.max_score AS max_score "
            "FROM answers a "
            "JOIN test_questions q ON q.test_id = a.test_id AND q.question_id = a.question_id "
            "JOIN tests t ON t.id = a.test_id "
            "WHERE t.student_id = ?",
            (_number(student_id, "s_"),),
        ).fetchall()
    return [dict(row) for row in rows]