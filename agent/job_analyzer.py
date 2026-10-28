def extract_json(text):
    text = text.strip()
    if not text:
        raise ValueError("LLM returned an empty response.")
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Not JSON: {text[:200]}")
    return json.loads(text[start:end + 1])
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from servicer.llm_service import analyze_job



def job_analyzer(description):
    result = analyze_job(description)
    print("LLM RAW:", repr(result))

    if isinstance(result, str):
        result = extract_json(result)

    required_fields = [
        "job_title",
        "required_skills",
        "tools_and_technologies",
        "experience_requirements"
    ]

    for field in required_fields:
        if field not in result:
            raise ValueError(f"Missing field: {field}")

    return result


if __name__ == "__main__":
    description = """
    We need a Python developer with Django,
    SQL, REST APIs, and Git.
    """

    result = job_analyzer(description)

    print(json.dumps(result, indent=2, ensure_ascii=False))
