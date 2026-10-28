"""Study plan: an ordered list of steps from the biggest gaps. Plain code: no model, no invented links."""

MAX_STEPS = 4
TASKS_PER_STEP = 3


def build_plan(report, missed_points_by_skill, resources, skill_names):
    """report: the result of gap.build_report. missed_points_by_skill: {"sql": ["...", ...]}.
    resources: {"sql": [{"title": ..., "url": ...}]} from data/resources.json.
    Returns the format of GET /plan in docs/API_CONTRACT.md."""
    steps = []
    for order, skill in enumerate(report["top_gaps"][:MAX_STEPS], start=1):
        name = skill_names.get(skill, skill)
        tasks = [f"Revise: {point}" for point in missed_points_by_skill.get(skill, [])[:TASKS_PER_STEP]]
        tasks.append(f"Answer practice questions on {name} out loud, then check them against the key points.")
        steps.append({
            "order": order,
            "skill": skill,
            "title": f"Strengthen {name}",
            "tasks": tasks,
            "resources": resources.get(skill, []),
        })
    return {"steps": steps}