
import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone

# Store the database inside the project folder.
PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "database" / "career_radar.db"


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DB_PATH), timeout=10)
    connection.row_factory = sqlite3.Row

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT,
            job_description TEXT NOT NULL,
            user_skills TEXT NOT NULL,
            goal TEXT,
            required_skills TEXT NOT NULL,
            matched_skills TEXT NOT NULL,
            missing_skills TEXT NOT NULL,
            match_percentage REAL,
            roadmap TEXT,
            jobs TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (analysis_id)
                REFERENCES analyses(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id)
                REFERENCES chat_sessions(id) ON DELETE CASCADE
        );
        """)


def _json(value):
    return json.dumps(value, ensure_ascii=False)


def _now():
    return datetime.now(timezone.utc).isoformat()


def save_analysis(description, user_skills, goal, result):
    """Save one completed career analysis and return its database ID."""
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO analyses (
                job_title, job_description, user_skills, goal,
                required_skills, matched_skills, missing_skills,
                match_percentage, roadmap, jobs, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.get("job_title"),
            description,
            _json(user_skills),
            goal or "",
            _json(result.get("required_skills", [])),
            _json(result.get("matched_skills", [])),
            _json(result.get("missing_skills", [])),
            result.get("match_percentage", 0),
            _json(result.get("roadmap")),
            _json(result.get("jobs", [])),
            _now(),
        ))
        return cursor.lastrowid


def create_chat_session(analysis_id=None):
    """Create a chat session, optionally linked to an analysis."""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO chat_sessions (analysis_id, created_at) VALUES (?, ?)",
            (analysis_id, _now()),
        )
        return cursor.lastrowid


def save_chat_message(session_id, role, content):
    if role not in ("user", "assistant"):
        raise ValueError("role must be 'user' or 'assistant'")

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO chat_messages (session_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
        """, (session_id, role, content, _now()))


def get_recent_analyses(limit=20):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM analyses ORDER BY id DESC LIMIT ?",
            (max(1, min(int(limit), 100)),),
        ).fetchall()
        return [dict(row) for row in rows]


def get_chat_messages(session_id):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT role, content, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id
        """, (session_id,)).fetchall()
        return [dict(row) for row in rows]


def get_analysis(analysis_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ?",
            (analysis_id,),
        ).fetchone()
        return dict(row) if row else None


if __name__ == "__main__":
    init_db()
    print(f"Database initialized: {DB_PATH}")

def test_database():
    init_db()

    # Test saving and retrieving an analysis
    sample_result = {
        "job_title": "Test Job",
        "required_skills": ["Python", "SQL"],
        "matched_skills": ["Python"],
        "missing_skills": ["SQL"],
        "match_percentage": 50,
        "roadmap": [],
        "jobs": [],
    }

    analysis_id = save_analysis(
        description="Test job description",
        user_skills=["Python"],
        goal="Test career goal",
        result=sample_result,
    )

    analysis = get_analysis(analysis_id)
    assert analysis is not None
    assert analysis["job_title"] == "Test Job"

    # Test saving and retrieving a chat session
    session_id = create_chat_session(analysis_id)
    save_chat_message(session_id, "user", "Hello")
    save_chat_message(session_id, "assistant", "Hello! How can I help?")

    messages = get_chat_messages(session_id)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"

    print("Database tests passed successfully!")
    print("Analysis ID:", analysis_id)
    print("Chat Session ID:", session_id)


if __name__ == "__main__":
    test_database()
