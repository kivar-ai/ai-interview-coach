import json
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend import db
from agent import gap, grader, planner, question_bank, research

import threading

from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

DATA = Path(__file__).resolve().parent.parent / "data"
ROLES = json.loads((DATA / "roles.json").read_text(encoding="utf-8"))["roles"]
_skills_def = json.loads((DATA / "skills.json").read_text(encoding="utf-8"))["skills"]
SKILLS = {s["id"] for s in _skills_def}
SKILL_NAMES = {s["id"]: s["name"] for s in _skills_def}
RESOURCES = json.loads((DATA / "resources.json").read_text(encoding="utf-8"))["resources"]
app = FastAPI(title="AI Interview Coach")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],      # only our own screen may call the backend
    allow_methods=["*"],
    allow_headers=["*"],
)
db.init_db()

RESEARCH_RUNNING = set()        # jobs running right now, like "data_scientist__wipro"
RESEARCH_FAILED = {}            # job key -> error message, shown once
RESEARCH_LOCK = threading.Lock()


def cache_key(student):
    return f"{student['target_role']}__{research.slug(student['company'])}"


def cache_file_of(student):
    return research.CACHE_DIR / f"{cache_key(student)}.json"


def run_research(key, role, company):
    """Runs in the background. research() saves its result in the cache file when it finishes."""
    try:
        research.research(role, company)
    except Exception as error:
        RESEARCH_FAILED[key] = str(error)
    finally:
        RESEARCH_RUNNING.discard(key)

# The contract says every error looks like {"error": "short message"}
@app.exception_handler(StarletteHTTPException)
async def http_error(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse(status_code=422, content={"error": "The request is not in the expected format."})


class ProfileIn(BaseModel):
    name: str
    target_role: str
    company: Optional[str] = None
    job_description: Optional[str] = None
    self_rating: dict[str, Literal["beginner", "intermediate", "advanced"]]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/profile")
def save_profile(profile: ProfileIn):
    if profile.target_role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Unknown role '{profile.target_role}'")
    unknown = [skill for skill in profile.self_rating if skill not in SKILLS]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown skill ids: {', '.join(unknown)}")
    student_id = db.create_student(profile.name, profile.target_role, profile.company,
                                   profile.job_description, profile.self_rating)
    return {"student_id": student_id}

@app.get("/test")
def get_test(student_id: str):
    student = db.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Unknown student")
    cache_file = cache_file_of(student)
    #cache_file = research.CACHE_DIR / f"{student['target_role']}__{research.slug(student['company'])}.json"
    if not cache_file.exists():
        raise HTTPException(status_code=409, detail="The job has not been researched yet.")
    research_result = json.loads(cache_file.read_text(encoding="utf-8"))

    questions = question_bank.pick_questions(research_result["skills"])
    tested = {q["skill"] for q in questions}
    skipped = [s["skill"] for s in research_result["skills"] if s["skill"] not in tested]

    test_id = db.create_test(student_id, questions)
    return {"test_id": test_id, "total": len(questions), "questions": questions, "skipped_skills": skipped}

class AnswerIn(BaseModel):
    student_id: str
    test_id: str
    question_id: str
    answer: str = Field(max_length=4000)


@app.post("/test/answer")
def submit_answer(body: AnswerIn):
    question = db.get_test_question(body.student_id, body.test_id, body.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="This question is not part of that student's test.")
    if db.has_answer(body.test_id, body.question_id):
        raise HTTPException(status_code=409, detail="This question was already answered.")
    try:
        result = grader.grade_answer(body.question_id, body.answer)
    except ValueError as error:                      # the grader could not read the model's reply
        raise HTTPException(status_code=502, detail=str(error))
    db.save_answer(body.test_id, body.question_id, body.answer, result)
    return result

class ResearchIn(BaseModel):
    student_id: str


@app.post("/research")
def start_research(body: ResearchIn, background: BackgroundTasks):
    student = db.get_student(body.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Unknown student")

    key, cache_file = cache_key(student), cache_file_of(student)
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    with RESEARCH_LOCK:                          # two requests at the same time must not start two jobs
        if key in RESEARCH_FAILED:
            raise HTTPException(status_code=500, detail="Research failed: " + RESEARCH_FAILED.pop(key))
        if key not in RESEARCH_RUNNING:
            RESEARCH_RUNNING.add(key)
            background.add_task(run_research, key, student["target_role"], student["company"])
    return JSONResponse(status_code=202, content={"status": "working"})

def report_for(student_id):
    """The gap report of a student. Shared by /report and /plan."""
    student = db.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Unknown student")
    cache_file = cache_file_of(student)
    if not cache_file.exists():
        raise HTTPException(status_code=409, detail="The job has not been researched yet.")
    research_result = json.loads(cache_file.read_text(encoding="utf-8"))
    return gap.build_report(research_result["skills"], student["self_rating"], db.get_answer_rows(student_id))


@app.get("/report")
def get_report(student_id: str):
    return report_for(student_id)

@app.get("/plan")
def get_plan(student_id: str):
    report = report_for(student_id)
    return planner.build_plan(report, db.get_missed_points(student_id), RESOURCES, SKILL_NAMES)

@app.get("/options")
def get_options():
    """The roles and skills the screen can offer, straight from our data files."""
    return {
        "roles": [{"id": role_id, "name": role["name"]} for role_id, role in ROLES.items()],
        "skills": [{"id": s["id"], "name": s["name"]} for s in _skills_def],
    }