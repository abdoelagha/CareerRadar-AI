
from pathlib import Path
from dotenv import dotenv_values
from groq import Groq

from database.db import (
    init_db,
    create_chat_session,
    save_chat_message,
    get_chat_messages,
)

BASE_DIR = Path(__file__).resolve().parent.parent
env_data = dotenv_values(BASE_DIR / ".env")

api_key = env_data.get("GROQ_API_KEY")

if not api_key:
    raise ValueError("Groq API key is missing")

client = Groq(api_key=api_key)

SYSTEM_MESSAGE = {
    "role": "system",
    "content": """
    You are CareerRadar AI, a helpful career assistant.
    Answer questions about careers, programming,
    job skills, and learning.
    Be clear, practical, and honest.
    """
}


def start_chat(analysis_id=None):
    """Create a new chat session and return its ID."""
    init_db()
    return create_chat_session(analysis_id=analysis_id)


def chat(user_message, session_id):
    """Save the user message, get an AI response, and save it."""
    if not user_message or not user_message.strip():
        return "Please enter a message."

    if session_id is None:
        raise ValueError("Create a chat session first.")

    save_chat_message(session_id, "user", user_message.strip())

    saved_messages = get_chat_messages(session_id)

    messages = [SYSTEM_MESSAGE]

    for item in saved_messages:
        messages.append({
            "role": item["role"],
            "content": item["content"],
        })

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        temperature=0.5,
    )

    answer = response.choices[0].message.content or ""

    save_chat_message(session_id, "assistant", answer)

    return answer


def load_chat(session_id):
    """Load a saved conversation from the database."""
    return get_chat_messages(session_id)


if __name__ == "__main__":
    init_db()
    session_id = start_chat()

    print("CareerRadar AI chat started.")
    print("Session ID:", session_id)
    print("Type 'exit' to quit.")

    while True:
        question = input("\nYour question: ")

        if question.lower() in ["exit", "quit"]:
            break

        try:
            print("\nCareerRadar AI:", chat(question, session_id))
        except Exception as error:
            print("Chat error:", error)
