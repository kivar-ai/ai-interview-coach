import json
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend import db
from agent import grader, question_bank, research

DATA = Path(__file__).resolve().parent.parent / "data"
ROLES = json.loads((DATA / "roles.json").read_text(encoding="utf-8"))["roles"]
SKILLS = {s["id"] for s in json.loads((DATA / "skills.json").read_text(encoding="utf-8"))["skills"]}

app = FastAPI(title="AI Interview Coach")
db.init_db()


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

    cache_file = research.CACHE_DIR / f"{student['target_role']}__{research.slug(student['company'])}.json"
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