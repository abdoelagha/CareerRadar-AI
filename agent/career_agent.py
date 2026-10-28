
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tool.job_search import search_jobs
from agent.job_analyzer import job_analyzer
from agent.skill_analyzer import analyze_skills
from agent.roadmap_generator import generate_roadmap


def run_career_analysis(description, user_skills, goal=""):
    if not description or not description.strip():
        raise ValueError("Please enter a job description.")

    if isinstance(user_skills, str):
        user_skills = [
            skill.strip()
            for skill in user_skills.replace("\n", ",").split(",")
            if skill.strip()
        ]

    if not user_skills:
        raise ValueError("Please enter your skills.")

    job_data = job_analyzer(description)

    if isinstance(job_data, str):
        job_data = json.loads(job_data)

    if not isinstance(job_data, dict):
        raise ValueError("Job Analyzer must return a dictionary.")

    required_skills = job_data.get("required_skills", [])

    if not isinstance(required_skills, list):
        raise ValueError("Job Analyzer must return required_skills as a list.")

    job_title = str(job_data.get("job_title") or "").strip()

    if not job_title:
        job_title = (goal or "").strip()

    jobs = []
    if job_title:
        try:
            jobs = search_jobs(job_title, limit=5) or []
        except Exception as error:
            print(f"Job search failed: {error}")
            jobs = []

    skill_result = analyze_skills(required_skills, user_skills)

    matched_skills = skill_result.get("matched_skills", [])
    missing_skills = skill_result.get("missing_skills", [])
    match_percentage = skill_result.get("match_percentage", 0)

    roadmap = None
    if missing_skills:
        roadmap = generate_roadmap(
            missing_skills,
            goal or "Get job-ready"
        )

    return {
        "job_title": job_title or "Unknown Job",
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "match_percentage": match_percentage,
        "roadmap": roadmap,
        "jobs": jobs
    }


if __name__ == "__main__":
    description = """
    We need a Python developer with Django,
    SQL, REST APIs, and Git.
    """
    user_skills = ["Python", "SQL", "Git"]
    goal = "Become a professional Python backend developer"

    result = run_career_analysis(description, user_skills, goal)
    print(json.dumps(result, indent=2, ensure_ascii=False))
