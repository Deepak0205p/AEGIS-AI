"""
Database and Conversation History Manager for Air-Gapped Local AI.
Implements SQLite persistence, 10-message windowing, cached summaries for older turns,
and context trimming to respect NUM_CTX limits.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from backend.config import DB_PATH, NUM_CTX, logger


def get_db_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite database with row factory."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite schema if not exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            mode TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_id ON messages (chat_id)")
    
    # 2. Chat summary cache
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_summaries (
            chat_id TEXT PRIMARY KEY,
            summary TEXT NOT NULL,
            last_msg_id INTEGER NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. Generated files registry
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            file_id TEXT PRIMARY KEY,
            chat_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_chat_id ON files (chat_id)")
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")


def save_message(chat_id: str, role: str, content: str, mode: str = "chat") -> int:
    """Persists a message to SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (chat_id, role, content, mode) VALUES (?, ?, ?, ?)",
        (chat_id, role, content, mode)
    )
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id


def get_chat_history(chat_id: str) -> List[Dict[str, Any]]:
    """Returns all messages for a given chat_id ordered by id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, chat_id, role, content, mode, timestamp FROM messages WHERE chat_id = ? ORDER BY id ASC",
        (chat_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "chat_id": r["chat_id"],
            "role": r["role"],
            "content": r["content"],
            "mode": r["mode"],
            "timestamp": str(r["timestamp"]),
        }
        for r in rows
    ]


def get_cached_summary(chat_id: str) -> Optional[Tuple[str, int]]:
    """Returns (summary, last_msg_id) if cached."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT summary, last_msg_id FROM chat_summaries WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["summary"], row["last_msg_id"]
    return None


def save_cached_summary(chat_id: str, summary: str, last_msg_id: int):
    """Caches conversation summary."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO chat_summaries (chat_id, summary, last_msg_id, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(chat_id) DO UPDATE SET
            summary=excluded.summary,
            last_msg_id=excluded.last_msg_id,
            updated_at=CURRENT_TIMESTAMP
        """,
        (chat_id, summary, last_msg_id)
    )
    conn.commit()
    conn.close()


def save_file_record(file_id: str, chat_id: str, filename: str, file_type: str, file_path: str):
    """Registers a generated deliverable file in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO files (file_id, chat_id, filename, file_type, file_path)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(file_id) DO UPDATE SET
            filename=excluded.filename,
            file_type=excluded.file_type,
            file_path=excluded.file_path
        """,
        (file_id, chat_id, filename, file_type, str(file_path))
    )
    conn.commit()
    conn.close()


def get_file_record(file_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves file metadata by file_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, chat_id, filename, file_type, file_path, created_at FROM files WHERE file_id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def estimate_tokens(text: str) -> int:
    """Rough estimate of token count (avg 3.5 chars per token for code/english)."""
    return max(1, int(len(text) / 3.5))


async def build_context_messages(
    chat_id: str,
    system_prompt: str,
    current_user_message: str,
) -> List[Dict[str, str]]:
    """
    Constructs the exact message list for Ollama inference:
    1. Base system prompt
    2. If > 10 prior messages exist: prepends 3-sentence summary (cached)
    3. Last 10 conversation messages
    4. Current user prompt
    5. Trims history if necessary to fit within NUM_CTX (or 4096).
    """
    from backend.ollama_client import call_ollama
    
    all_history = get_chat_history(chat_id)
    
    summary_text = ""
    if len(all_history) > 10:
        older_messages = all_history[:-10]
        recent_history = all_history[-10:]
        last_older_id = older_messages[-1]["id"]
        
        cached = get_cached_summary(chat_id)
        if cached and cached[1] == last_older_id:
            summary_text = cached[0]
        else:
            # Generate a 3-sentence summary of older conversation
            history_text = "\n".join([f"{m['role']}: {m['content']}" for m in older_messages])
            summary_prompt = [
                {
                    "role": "system",
                    "content": (
                        "You are an air-gapped factual summarizer. "
                        "Summarize the key facts, inputs, and constraints in the following prior conversation "
                        "in EXACTLY 3 short, factual sentences. Do NOT invent details."
                    )
                },
                {
                    "role": "user",
                    "content": f"Prior Conversation:\n{history_text}\n\nProvide 3-sentence factual summary:"
                }
            ]
            try:
                summary_res = await call_ollama(summary_prompt, stream=False, temperature=0.1, max_tokens=150)
                if isinstance(summary_res, str) and summary_res.strip():
                    summary_text = summary_res.strip()
                    save_cached_summary(chat_id, summary_text, last_older_id)
            except Exception as e:
                logger.warning(f"Could not generate history summary: {e}")
                summary_text = ""
    else:
        recent_history = all_history

    # Assemble messages
    effective_system_prompt = system_prompt
    if summary_text:
        effective_system_prompt += f"\n\n[Earlier Conversation Context Summary]:\n{summary_text}"
        
    messages: List[Dict[str, str]] = [{"role": "system", "content": effective_system_prompt}]
    
    # Add recent messages
    for msg in recent_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    # Add current user prompt if not already the last item in history
    if not (len(messages) > 1 and messages[-1].get("role") == "user" and messages[-1].get("content") == current_user_message):
        messages.append({"role": "user", "content": current_user_message})
    
    # Context trimming safety: Ensure estimated tokens fit inside NUM_CTX
    # Reserve buffer for output tokens (e.g. 2048)
    max_input_tokens = max(1024, NUM_CTX - 2048)
    
    while len(messages) > 2:  # Keep at least system and current user message
        total_chars = sum(len(m["content"]) for m in messages)
        estimated = estimate_tokens("x" * total_chars)
        if estimated <= max_input_tokens:
            break
        # Drop the oldest historical message (messages[1])
        dropped = messages.pop(1)
        logger.info(f"[CONTEXT] Trimmed message to fit num_ctx: role={dropped.get('role')} remaining={len(messages)}")
        
    return messages
