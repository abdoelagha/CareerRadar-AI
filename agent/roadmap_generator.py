
import json
import re
from pathlib import Path

from dotenv import dotenv_values
from groq import Groq


BASE_DIR = Path(__file__).resolve().parent.parent
env_data = dotenv_values(BASE_DIR / ".env")
api_key = env_data.get("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=api_key)
MODEL = "openai/gpt-oss-20b"


def extract_json(text):
    """Extract and validate a JSON object from the model response."""
    text = (text or "").strip()

    if not text:
        raise ValueError("Groq returned an empty response.")

    # Remove Markdown code fences.
    text = re.sub(
        r"^\s*```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\s*```\s*$", "", text)

    # Extract the outermost JSON object.
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end < start:
        raise ValueError("Groq did not return a JSON object.")

    json_text = text[start:end + 1]

    try:
        result = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid roadmap JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(result, dict):
        raise ValueError("The roadmap response must be a JSON object.")

    required = ("learning_steps", "projects", "estimated_duration")
    for field in required:
        if field not in result:
            raise ValueError(f"Missing field in roadmap: {field}")

    if not isinstance(result["learning_steps"], list):
        raise ValueError("'learning_steps' must be a list.")

    if not isinstance(result["projects"], list):
        raise ValueError("'projects' must be a list.")

    duration = result["estimated_duration"]
    if not isinstance(duration, (dict, str, int, float)):
        raise ValueError("Invalid 'estimated_duration' value.")

    for i, step in enumerate(result["learning_steps"]):
        if not isinstance(step, dict):
            raise ValueError(f"Learning step {i + 1} must be an object.")
        for field in ("step", "skill", "description", "duration"):
            if field not in step:
                raise ValueError(
                    f"Learning step {i + 1} is missing '{field}'."
                )

    for i, project in enumerate(result["projects"]):
        if not isinstance(project, dict):
            raise ValueError(f"Project {i + 1} must be an object.")
        for field in ("name", "description"):
            if field not in project:
                raise ValueError(
                    f"Project {i + 1} is missing '{field}'."
                )

    return result


def generate_roadmap(
    missing_skills,
    user_goal="Get job-ready",
):
    if isinstance(missing_skills, str):
        missing_skills = [
            skill.strip()
            for skill in missing_skills.split(",")
            if skill.strip()
        ]
    elif missing_skills is None:
        missing_skills = []
    else:
        missing_skills = list(missing_skills)

    if not missing_skills:
        missing_skills = [
            "Improve professional development skills"
        ]

    prompt = f"""
Create a personalized learning roadmap.

Missing skills:
{json.dumps(missing_skills, ensure_ascii=False)}

User goal:
{user_goal}

Return one valid JSON object with this exact structure:
{{
  "learning_steps": [
    {{
      "step": 1,
      "skill": "Skill name",
      "description": "What to learn",
      "duration": "2 weeks"
    }}
  ],
  "projects": [
    {{
      "name": "Project name",
      "description": "Project description"
    }}
  ],
  "estimated_duration": {{
    "total_months": 3,
    "total_days": 90
  }}
}}

Requirements:
- Focus on the missing skills.
- Adapt the roadmap to the user's goal.
- Order learning steps logically.
- Include practical projects.
- Use realistic learning durations.
- Do not invent the user's background.
- Return JSON only, without Markdown.
- Ensure every string is properly escaped.
- Do not include trailing commas.
"""

    last_error = None

    # Try twice in case the model returns malformed JSON.
    for attempt in range(2):
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI career and learning assistant. "
                    "Return a valid JSON object matching the requested "
                    "schema. Never add Markdown or comments."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        if last_error:
            messages.append({
                "role": "user",
                "content": (
                    "Your previous response was invalid. Fix this issue "
                    "and return a complete corrected JSON object. "
                    f"Validation error: {last_error}"
                ),
            })

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            roadmap = extract_json(content)

            duration = roadmap["estimated_duration"]

            if isinstance(duration, dict):
                months = duration.get("total_months")
                days = duration.get("total_days")

                if months is not None:
                    duration = f"{months} months"
                elif days is not None:
                    duration = f"{days} days"
                else:
                    duration = "Flexible"

            roadmap["estimated_duration"] = str(duration)
            return roadmap

        except Exception as exc:
            last_error = str(exc)

    raise RuntimeError(
        "Could not generate a valid learning roadmap after 2 attempts. "
        f"Last error: {last_error}"
    )


if __name__ == "__main__":
    skills = input(
        "Enter missing skills separated by commas: "
    )
    goal = input("What is your career goal? ")

    missing_skills = [
        skill.strip()
        for skill in skills.split(",")
        if skill.strip()
    ]

    try:
        result = generate_roadmap(missing_skills, goal)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as exc:
        print(f"Roadmap generation failed: {exc}")
