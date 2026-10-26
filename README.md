# AI Interview Coach

An AI coach for students preparing for data and AI jobs.
A student picks a role, the coach researches what the job needs, tests what the student knows, shows the gaps, builds a study plan, then runs a mock interview and scores every answer.

> Working name. Demo project. Built with open-source tools.

## How it works

1. **Profile** - the student picks a role and rates their own skills.
2. **Research (agent)** - the coach searches the web, reads pages, and lists the skills the job needs, with sources.
3. **Test (RAG + LLM)** - questions come from our own question bank. Answers are graded against our ideal answers.
4. **Gap** - job needs minus measured score, per skill.
5. **Plan** - a study plan from the biggest gaps.
6. **Mock interview** - questions on the weak skills, with scores and feedback.

Agent = outside knowledge. RAG = our own knowledge. LLM = the engine that reads, grades and writes.

## Status

| Version | Goal | Status |
|---|---|---|
| 1 | Research a role and answer with sources | in progress |
| 2 | Skill form, test, gap report, study plan | not started |
| 3 | Mock interview and progress | not started |
| 4 | Verifier, quality tests, polish | not started |

## Quick start (Windows PowerShell)

```
git clone https://github.com/kivar-ai/ai-interview-coach.git
cd ai-interview-coach
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
Install the **Ollama** app from ollama.com, then:
```
ollama pull qwen3:8b
python experiments\real_agent.py
```
Only the AI core work needs Ollama.

## Learn more
- `CONTRIBUTING.md` - how we work together
- `docs/API_CONTRACT.md` - screen and backend formats
- `docs/QUESTION_FORMAT.md` - how to write questions
- `data/` - skills, roles and sample questions

## Licence
MIT
