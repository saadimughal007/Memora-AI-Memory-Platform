import sqlite3
from contextlib import contextmanager
from backend.core.config import settings, resolve_path

DB_PATH = resolve_path(settings.database_path)

def initialize_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
            user_id TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('user','assistant')),
            content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id,id)")
        conn.execute("""CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, content TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'general', importance INTEGER NOT NULL DEFAULT 3,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id)")
        conn.commit()

@contextmanager
def get_connection():
    initialize_database()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def add_message(session_id, user_id, role, content):
    with get_connection() as conn:
        conn.execute("INSERT INTO messages(session_id,user_id,role,content) VALUES(?,?,?,?)",
                     (session_id,user_id,role,content))

def get_recent_messages(session_id, limit):
    with get_connection() as conn:
        rows = conn.execute("SELECT role,content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
                            (session_id,limit)).fetchall()
    return [dict(row) for row in reversed(rows)]

def clear_session(session_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))

def create_memory(user_id, content, category, importance):
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM memories WHERE user_id=? AND lower(content)=lower(?)",
                           (user_id,content.strip())).fetchone()
        if row:
            conn.execute("UPDATE memories SET category=?,importance=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                         (category,importance,row["id"]))
            return int(row["id"])
        cur = conn.execute("INSERT INTO memories(user_id,content,category,importance) VALUES(?,?,?,?)",
                           (user_id,content.strip(),category,importance))
        return int(cur.lastrowid)

def list_memories(user_id):
    with get_connection() as conn:
        rows = conn.execute("SELECT id,user_id,content,category,importance,created_at FROM memories "
                            "WHERE user_id=? ORDER BY importance DESC,id DESC",(user_id,)).fetchall()
    return [dict(row) for row in rows]

def delete_memory(memory_id, user_id):
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM memories WHERE id=? AND user_id=?", (memory_id,user_id))
        return cur.rowcount > 0

def delete_all_memories(user_id):
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM memories WHERE user_id=?", (user_id,))
        return cur.rowcount
