"""
Database and Conversation History Manager for Air-Gapped Local AI.
Implements XAMPP MySQL (MariaDB) persistence, 10-message windowing,
cached summaries for older turns, and context trimming to respect NUM_CTX limits.
"""

import json
import os
import pymysql
import pymysql.cursors
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from backend.config import (
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_DB,
    NUM_CTX,
    logger,
)


def get_db_connection() -> pymysql.Connection:
    """Returns a connection to the XAMPP MySQL database with DictCursor."""
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )


def init_db():
    """Initializes XAMPP MySQL database schema and migrates existing SQLite data if present."""
    # 1. Ensure database exists
    root_conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        charset="utf8mb4",
        autocommit=True
    )
    with root_conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    root_conn.close()

    # 2. Initialize schema tables
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id VARCHAR(128) NOT NULL,
                role VARCHAR(32) NOT NULL,
                content LONGTEXT NOT NULL,
                mode VARCHAR(32) NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_chat_id (chat_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Chat summary cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_summaries (
                chat_id VARCHAR(128) PRIMARY KEY,
                summary TEXT NOT NULL,
                last_msg_id INT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Generated deliverable files registry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                file_id VARCHAR(64) PRIMARY KEY,
                chat_id VARCHAR(128) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                file_type VARCHAR(32) NOT NULL,
                file_path TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_files_chat_id (chat_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
    conn.close()
    logger.info(f"XAMPP MySQL database '{MYSQL_DB}' initialized on {MYSQL_HOST}:{MYSQL_PORT}")


def save_message(chat_id: str, role: str, content: str, mode: str = "chat") -> int:
    """Persists a message to XAMPP MySQL."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO messages (chat_id, role, content, mode) VALUES (%s, %s, %s, %s)",
            (chat_id, role, content, mode)
        )
        msg_id = cursor.lastrowid
    conn.close()
    return msg_id


def get_chat_history(chat_id: str) -> List[Dict[str, Any]]:
    """Returns all messages for a given chat_id ordered by id, with attached deliverable files."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id, chat_id, role, content, mode, timestamp FROM messages WHERE chat_id = %s ORDER BY id ASC",
            (chat_id,)
        )
        rows = cursor.fetchall()

        # Query all files associated with this chat_id
        cursor.execute(
            "SELECT file_id, chat_id, filename, file_type, file_path, created_at FROM files WHERE chat_id = %s ORDER BY created_at ASC",
            (chat_id,)
        )
        file_rows = cursor.fetchall()
    conn.close()

    files_list = [dict(f) for f in file_rows]

    result = []
    for r in rows:
        msg_content = r["content"] or ""
        matched_deliv_ids = []

        # 1. Match files whose file_id or filename appears in msg_content
        for f in files_list:
            fid = f["file_id"]
            fname = f["filename"]
            if fid in msg_content or fname in msg_content or f"/api/files/{fid}" in msg_content or f"/api/files/download/{fid}" in msg_content:
                if fid not in matched_deliv_ids:
                    matched_deliv_ids.append(fid)

        # 2. Extract any /api/files/... links from msg_content directly
        import re
        extracted = re.findall(r'/api/files/(?:download/)?([a-zA-Z0-9_\-\.]+)', msg_content)
        for ext_id in extracted:
            clean = ext_id.strip()
            if clean and clean not in matched_deliv_ids:
                matched_deliv_ids.append(clean)

        result.append({
            "id": r["id"],
            "chat_id": r["chat_id"],
            "role": r["role"],
            "content": r["content"],
            "mode": r["mode"],
            "timestamp": str(r["timestamp"]),
            "deliverable_ids": matched_deliv_ids,
        })
    return result


def get_cached_summary(chat_id: str) -> Optional[Tuple[str, int]]:
    """Returns (summary, last_msg_id) if cached."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT summary, last_msg_id FROM chat_summaries WHERE chat_id = %s", (chat_id,))
        row = cursor.fetchone()
    conn.close()
    if row:
        return row["summary"], row["last_msg_id"]
    return None


def save_cached_summary(chat_id: str, summary: str, last_msg_id: int):
    """Caches conversation summary in XAMPP MySQL."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO chat_summaries (chat_id, summary, last_msg_id, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE
                summary=VALUES(summary),
                last_msg_id=VALUES(last_msg_id),
                updated_at=CURRENT_TIMESTAMP
            """,
            (chat_id, summary, last_msg_id)
        )
    conn.close()


def save_file_record(file_id: str, chat_id: str, filename: str, file_type: str, file_path: str):
    """Registers a generated deliverable file in XAMPP MySQL."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO files (file_id, chat_id, filename, file_type, file_path)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                filename=VALUES(filename),
                file_type=VALUES(file_type),
                file_path=VALUES(file_path)
            """,
            (file_id, chat_id, filename, file_type, str(file_path))
        )
    conn.close()


def get_file_record(file_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves file metadata by file_id from XAMPP MySQL."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT file_id, chat_id, filename, file_type, file_path, created_at FROM files WHERE file_id = %s", (file_id,))
        row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def estimate_tokens(text: str) -> int:
    """Rough estimate of token count (avg 3.5 chars per token for code/english)."""
    return max(1, int(len(text) / 3.5))


def list_all_chat_sessions() -> List[Dict[str, Any]]:
    """Returns list of distinct chat sessions from XAMPP MySQL."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                chat_id as id,
                UNIX_TIMESTAMP(MIN(timestamp)) as created_at,
                COALESCE(
                    MAX(CASE WHEN role = 'user' THEN SUBSTRING(content, 1, 50) END),
                    'Chat'
                ) as title,
                COUNT(*) as count
            FROM messages
            GROUP BY chat_id
            ORDER BY MAX(timestamp) DESC
        """)
        rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "title": (r["title"] or "Chat")[:50],
            "created_at": int(r["created_at"] or datetime.now().timestamp()),
            "count": int(r["count"])
        }
        for r in rows
    ]


def delete_chat_session_data(chat_id: str) -> bool:
    """Deletes all messages, summaries, and file metadata for a chat session from XAMPP MySQL."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM messages WHERE chat_id = %s", (chat_id,))
        cursor.execute("DELETE FROM chat_summaries WHERE chat_id = %s", (chat_id,))
        cursor.execute("DELETE FROM files WHERE chat_id = %s", (chat_id,))
    conn.close()
    return True


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

    # Inject authoritative live system date and time
    try:
        from backend.custom_agents import get_system_temporal_context_block
        temporal_block = get_system_temporal_context_block()
        effective_system_prompt = f"{temporal_block}\n\n{effective_system_prompt}"
    except Exception as temp_err:
        logger.warning(f"[CONTEXT] Temporal context injection warning: {temp_err}")

    # Check for temporary cross-model handoff context buffer
    try:
        from backend.context_handoff import context_handoff
        handoff_block = context_handoff.format_handoff_prompt_block(chat_id)
        if handoff_block:
            effective_system_prompt += f"\n\n{handoff_block}"
            logger.info(f"[CONTEXT] Injected cross-model handoff context into system prompt for chat_id={chat_id}")
    except Exception as handoff_err:
        logger.warning(f"[CONTEXT] Handoff context injection error: {handoff_err}")
        
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
