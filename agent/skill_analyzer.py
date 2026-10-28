
import sys
import json
from pathlib import Path
from servicer.llm_service import analyze_job
import re
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

SKILL_ALIASES = {
    "ms excel": "excel",
    "microsoft excel": "excel",
    "excel spreadsheet": "excel",
    "power bi": "power bi",
    "powerbi": "power bi",
    "machine-learning": "machine learning",
    "ml": "machine learning",
    "js": "javascript",
    "postgres": "postgresql",
    "rest api": "rest apis",
    "restful api": "rest apis",
}


def normalize_skill(skill):
    skill = str(skill).strip().lower()
    skill = re.sub(r"[^a-z0-9+#.\s]", " ", skill)
    return " ".join(skill.split())


def expand_skills(skills):
    expanded = set()

    for skill in skills or []:
        normalized = normalize_skill(skill)
        if not normalized:
            continue

        expanded.add(normalized)

        # Split compound skills into smaller concepts.
        parts = re.split(
            r"\s+(?:and|or|including|such as)\s+|[,;/]+",
            normalized
        )

        for part in parts:
            part = normalize_skill(part)
            if part:
                expanded.add(part)

    return expanded



def analyze_skills(required_skills, user_skills):
    required = list(dict.fromkeys(
        normalize_skill(s)
        for s in (required_skills or [])
        if s and normalize_skill(s)
    ))

    user = set(
        normalize_skill(s)
        for s in (user_skills or [])
        if s and normalize_skill(s)
    )

    aliases = {
        "accounting principles and financial reporting": {
            "accounting",
            "financial reporting",
        },
        "bank reconciliation and bookkeeping": {
            "bank reconciliation",
            "bookkeeping",
        },
        "attention to detail and analytical thinking": {
            "attention to detail",
            "analytical thinking",
        },
    }

    matched = []
    missing = []

    for skill in required:
        accepted = {skill} | aliases.get(skill, set())

        if any(
            user_skill == candidate
            or candidate in user_skill
            or user_skill in candidate
            for user_skill in user
            for candidate in accepted
        ):
            matched.append(skill)
        else:
            missing.append(skill)

    percentage = (
        len(matched) / len(required) * 100
        if required else 0
    )

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "match_percentage": round(percentage, 2),
        "required_count": len(required),
        "matched_count": len(matched),
    }




if __name__ == "__main__":
    description = """
    We need a Python developer with Django,
    SQL, REST APIs, and Git.
    """

    job_data = analyze_job(description)

    if isinstance(job_data, str):
        job_data = json.loads(job_data)

    required_skills = job_data.get("required_skills", [])

    user_skills = ["Python", "SQL", "Git"]

    result = analyze_skills(required_skills, user_skills)

    print("Job title:", job_data.get("job_title", "Unknown"))
    print("Required skills:", required_skills)
    print("Skill analysis:", result)
