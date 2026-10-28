
from pathlib import Path
from dotenv import dotenv_values
from groq import Groq

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

env_data = dotenv_values(ENV_PATH)
api_key = env_data.get("GROQ_API_KEY")

if not api_key:
    raise ValueError("Groq API key is missing")

client = Groq(api_key=api_key)


def analyze_job(description):
    response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
        messages=[
            
            {
              "role": "system",
              "content": """
              Analyze the job description and return only valid JSON.

              Use this structure:
             {
               "required_skills": [],
               "tools_and_technologies": [],
               "experience_requirements": [],
               "job_title": ""
             }

             Rules:
             - Extract only information explicitly mentioned in the job description.
             - Do not invent skills, tools, or experience requirements.
             - If information is missing, return an empty list or empty string.
             - Return JSON only, without Markdown.
            """
            },

            {
                "role": "user",
                "content": description
            }
        ],
        temperature=0.2,
    reasoning_effort="low",
    max_completion_tokens=2000,
    response_format={"type": "json_object"},
)

    return response.choices[0].message.content or ""


if __name__ == "__main__":
    description = """
    We need a Python developer with Django,
    SQL, REST APIs, and Git.
    """
    print(analyze_job(description))
