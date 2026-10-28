"""Gap report: what the job needs versus what the student showed. Plain code, no model."""

TARGET = {"high": 90, "medium": 70, "low": 50}     # the score we expect for each importance level
RANK = {"high": 0, "medium": 1, "low": 2}
TOP_GAPS = 3


def measured_scores(answer_rows):
    """answer_rows: [{"skill": "sql", "score": 5, "max_score": 10}, ...].
    Returns the average per skill, in percent: {"sql": 50, ...}. Halves round up."""
    percents = {}
    for row in answer_rows:
        percents.setdefault(row["skill"], []).append(100 * row["score"] / row["max_score"])
    return {skill: int(sum(values) / len(values) + 0.5) for skill, values in percents.items()}


def build_report(research_skills, self_rating, answer_rows):
    """Returns the format of GET /report in docs/API_CONTRACT.md."""
    measured = measured_scores(answer_rows)
    skills = []
    for item in research_skills:
        skill, importance = item["skill"], item["importance"]
        score = measured.get(skill)                                  # None if the skill was never tested
        gap = None if score is None else max(0, TARGET[importance] - score)
        skills.append({"skill": skill, "job_needs": importance, "self_rating": self_rating.get(skill),
                       "measured_score": score, "gap": gap})
    skills.sort(key=lambda s: (RANK[s["job_needs"]], s["skill"]))

    open_gaps = [s for s in skills if s["gap"]]                      # tested, and below the target
    open_gaps.sort(key=lambda s: (-s["gap"], s["skill"]))
    return {"skills": skills, "top_gaps": [s["skill"] for s in open_gaps[:TOP_GAPS]]}