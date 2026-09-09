"""
Database and Conversation History Manager for Air-Gapped Local AI.
Implements XAMPP MySQL (MariaDB) persistence, 10-message windowing,
cached summaries for older turns, and context trimming to respect NUM_CTX limits.
"""

import json
import os
import re
import time
import uuid
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

        # Generated deliverable files registry with 2-step human verification columns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                file_id VARCHAR(64) PRIMARY KEY,
                chat_id VARCHAR(128) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                file_type VARCHAR(32) NOT NULL,
                file_path TEXT NOT NULL,
                verification_status VARCHAR(32) DEFAULT 'PENDING_STAGE_1',
                stage_1_verifier VARCHAR(64) DEFAULT NULL,
                stage_1_at DATETIME DEFAULT NULL,
                stage_1_notes TEXT DEFAULT NULL,
                stage_2_verifier VARCHAR(64) DEFAULT NULL,
                stage_2_at DATETIME DEFAULT NULL,
                stage_2_notes TEXT DEFAULT NULL,
                rejected_by VARCHAR(64) DEFAULT NULL,
                rejected_at DATETIME DEFAULT NULL,
                reject_reason TEXT DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_files_chat_id (chat_id),
                INDEX idx_files_status (verification_status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Feedback & Error Reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_reports (
                id INT AUTO_INCREMENT PRIMARY KEY,
                report_type VARCHAR(32) NOT NULL, -- 'ERROR' | 'SUGGESTION'
                user_id VARCHAR(64) DEFAULT NULL,
                username VARCHAR(64) DEFAULT 'operator',
                chat_id VARCHAR(128) DEFAULT NULL,
                message_id VARCHAR(64) DEFAULT NULL,
                message_content LONGTEXT DEFAULT NULL,
                category VARCHAR(64) DEFAULT 'GENERAL',
                title VARCHAR(255) NOT NULL,
                description LONGTEXT NOT NULL,
                suggested_fix LONGTEXT DEFAULT NULL,
                status VARCHAR(32) DEFAULT 'OPEN', -- 'OPEN', 'IN_REVIEW', 'RESOLVED', 'REJECTED'
                admin_notes LONGTEXT DEFAULT NULL,
                admin_response LONGTEXT DEFAULT NULL,
                resolved_by VARCHAR(64) DEFAULT NULL,
                resolved_at DATETIME DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_fb_type (report_type),
                INDEX idx_fb_status (status),
                INDEX idx_fb_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Collaboration Channels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_channels (
                id VARCHAR(64) PRIMARY KEY,
                name VARCHAR(128) NOT NULL,
                channel_type VARCHAR(32) DEFAULT 'CHANNEL', -- 'CHANNEL' or 'DM'
                description TEXT DEFAULT NULL,
                department VARCHAR(64) DEFAULT 'ALL',
                created_by VARCHAR(64) DEFAULT 'system',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Channel Members table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channel_members (
                id INT AUTO_INCREMENT PRIMARY KEY,
                channel_id VARCHAR(64) NOT NULL,
                username VARCHAR(64) NOT NULL,
                role VARCHAR(64) DEFAULT 'OPERATOR',
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_chan_user (channel_id, username),
                INDEX idx_mem_chan (channel_id),
                INDEX idx_mem_user (username)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Channel Messages table (supports text, file attachments, and AI @aegis responses)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channel_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                channel_id VARCHAR(64) NOT NULL,
                sender_username VARCHAR(64) NOT NULL,
                sender_role VARCHAR(64) DEFAULT 'OPERATOR',
                content LONGTEXT NOT NULL,
                message_type VARCHAR(32) DEFAULT 'TEXT', -- 'TEXT', 'FILE', 'AI_RESPONSE', 'SYSTEM'
                file_id VARCHAR(64) DEFAULT NULL,
                file_name VARCHAR(255) DEFAULT NULL,
                file_type VARCHAR(64) DEFAULT NULL,
                file_size INT DEFAULT NULL,
                file_url TEXT DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_cmsg_chan (channel_id),
                INDEX idx_cmsg_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # User Activity & Security Monitoring Table (tracks searches, chat, file uploads, anomalous activities)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(64) NOT NULL,
                role VARCHAR(64) DEFAULT 'OPERATOR',
                activity_type VARCHAR(64) NOT NULL, -- 'CHAT_QUERY', 'SEARCH_RAG', 'FILE_UPLOAD', 'FILE_DOWNLOAD', 'CHANNEL_MSG', 'LOGIN', 'SECURITY_TRIGGER'
                channel_or_chat_id VARCHAR(128) DEFAULT NULL,
                query_text LONGTEXT DEFAULT NULL,
                details LONGTEXT DEFAULT NULL,
                file_meta LONGTEXT DEFAULT NULL,
                ip_address VARCHAR(64) DEFAULT '127.0.0.1',
                risk_level VARCHAR(32) DEFAULT 'NORMAL', -- 'NORMAL', 'SUSPICIOUS', 'CRITICAL'
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_act_user (username),
                INDEX idx_act_type (activity_type),
                INDEX idx_act_risk (risk_level),
                INDEX idx_act_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)



        # Run safe migrations for existing tables if columns are missing
        columns_to_add = [
            ("is_important", "TINYINT(1) DEFAULT 0"),
            ("verification_status", "VARCHAR(32) DEFAULT 'PENDING_STAGE_1'"),
            ("stage_1_verifier", "VARCHAR(64) DEFAULT NULL"),
            ("stage_1_at", "DATETIME DEFAULT NULL"),
            ("stage_1_notes", "TEXT DEFAULT NULL"),
            ("stage_2_verifier", "VARCHAR(64) DEFAULT NULL"),
            ("stage_2_at", "DATETIME DEFAULT NULL"),
            ("stage_2_notes", "TEXT DEFAULT NULL"),
            ("rejected_by", "VARCHAR(64) DEFAULT NULL"),
            ("rejected_at", "DATETIME DEFAULT NULL"),
            ("reject_reason", "TEXT DEFAULT NULL"),
        ]
        for col_name, col_def in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE files ADD COLUMN {col_name} {col_def};")
            except Exception:
                pass  # Column already exists
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


def save_file_record(
    file_id: str,
    chat_id: str,
    filename: str,
    file_type: str,
    file_path: str,
    verification_status: str = "PENDING_STAGE_1",
    is_important: bool = True
):
    """Registers a generated deliverable file in XAMPP MySQL."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO files (file_id, chat_id, filename, file_type, file_path, verification_status, is_important)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                filename=VALUES(filename),
                file_type=VALUES(file_type),
                file_path=VALUES(file_path),
                verification_status=VALUES(verification_status),
                is_important=VALUES(is_important)
            """,
            (file_id, chat_id, filename, file_type, str(file_path), verification_status, 1 if is_important else 0)
        )
    conn.close()


def get_file_record(file_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves file metadata by file_id from XAMPP MySQL."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM files WHERE file_id = %s", (file_id,))
        row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_all_deliverable_files(chat_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all files with complete verification audit trail."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        if chat_id:
            cursor.execute("SELECT * FROM files WHERE chat_id = %s ORDER BY created_at DESC", (chat_id,))
        else:
            cursor.execute("SELECT * FROM files ORDER BY created_at DESC")
        rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pending_verifications(user_role: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns ONLY important documents pending human verification according to strict hierarchy:
    - Only files marked as is_important = 1 are routed to human verification pipeline.
    - Step 1 (Lower Post: PROCESS_LEAD, MAINTENANCE_ENG, FIELD_OPERATOR):
        Strictly items in 'PENDING_STAGE_1'
    - Step 2 (Higher Post: SUPER_ADMIN / Executive Compliance Chief):
        Items in 'PENDING_STAGE_2' (and review pipeline overview)
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        if user_role == "SUPER_ADMIN":
            cursor.execute("SELECT * FROM files WHERE is_important = 1 AND verification_status IN ('PENDING_STAGE_2', 'PENDING_STAGE_1') ORDER BY FIELD(verification_status, 'PENDING_STAGE_2', 'PENDING_STAGE_1'), created_at DESC")
        elif user_role in ("PROCESS_LEAD", "MAINTENANCE_ENG", "FIELD_OPERATOR"):
            cursor.execute("SELECT * FROM files WHERE is_important = 1 AND verification_status = 'PENDING_STAGE_1' ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM files WHERE is_important = 1 AND verification_status IN ('PENDING_STAGE_1', 'PENDING_STAGE_2') ORDER BY created_at DESC")
        rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def verify_file_stage_1(file_id: str, verifier: str, notes: str = "") -> bool:
    """Stage 1 approval: Transitions file from PENDING_STAGE_1 to PENDING_STAGE_2."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE files 
            SET verification_status = 'PENDING_STAGE_2',
                stage_1_verifier = %s,
                stage_1_at = CURRENT_TIMESTAMP,
                stage_1_notes = %s
            WHERE file_id = %s
            """,
            (verifier, notes, file_id)
        )
    conn.close()
    return True


def verify_file_stage_2(file_id: str, verifier: str, notes: str = "") -> bool:
    """Stage 2 approval: Final sign-off transition from PENDING_STAGE_2 to VERIFIED."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE files 
            SET verification_status = 'VERIFIED',
                stage_2_verifier = %s,
                stage_2_at = CURRENT_TIMESTAMP,
                stage_2_notes = %s
            WHERE file_id = %s
            """,
            (verifier, notes, file_id)
        )
    conn.close()
    return True


def reject_file(file_id: str, rejected_by: str, reason: str = "") -> bool:
    """Rejects deliverable file with reason."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE files 
            SET verification_status = 'REJECTED',
                rejected_by = %s,
                rejected_at = CURRENT_TIMESTAMP,
                reject_reason = %s
            WHERE file_id = %s
            """,
            (rejected_by, reason, file_id)
        )
    conn.close()
    return True


def rename_file_record(file_id: str, new_filename: str) -> bool:
    """Updates filename and optionally renames physical file on storage."""
    record = get_file_record(file_id)
    if not record:
        return False
    
    old_path = Path(record["file_path"])
    new_path = old_path
    
    # Clean new filename
    clean_name = new_filename.strip()
    if clean_name:
        # Preserve original extension if user omitted it
        old_ext = old_path.suffix
        if not any(clean_name.lower().endswith(ext) for ext in [".docx", ".xlsx", ".pptx", ".py", ".pdf", ".csv", ".json"]):
            clean_name += old_ext
        
        # Rename physical file on disk if exists
        try:
            if old_path.exists():
                candidate_path = old_path.parent / clean_name
                old_path.rename(candidate_path)
                new_path = candidate_path
        except Exception:
            pass

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE files SET filename = %s, file_path = %s WHERE file_id = %s",
            (clean_name, str(new_path), file_id)
        )
    conn.close()
    return True


# ─── Feedback & Error Reports CRUD ──────────────────────────────────────────

def create_feedback_report(
    report_type: str,
    title: str,
    description: str,
    user_id: Optional[str] = None,
    username: str = "operator",
    chat_id: Optional[str] = None,
    message_id: Optional[str] = None,
    message_content: Optional[str] = None,
    category: str = "GENERAL",
    suggested_fix: Optional[str] = None,
) -> int:
    """Inserts a new error or suggestion report into XAMPP MySQL."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO feedback_reports (
                report_type, user_id, username, chat_id, message_id,
                message_content, category, title, description, suggested_fix, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'OPEN')
            """,
            (
                report_type.upper(),
                user_id,
                username,
                chat_id,
                message_id,
                message_content,
                category.upper(),
                title,
                description,
                suggested_fix,
            )
        )
        report_id = cursor.lastrowid
    conn.close()
    return report_id


def get_all_feedback_reports(
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetches all feedback/error reports from XAMPP MySQL with optional filtering."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        query = "SELECT * FROM feedback_reports WHERE 1=1"
        params: List[Any] = []

        if report_type and report_type.upper() != "ALL":
            query += " AND report_type = %s"
            params.append(report_type.upper())

        if status and status.upper() != "ALL":
            query += " AND status = %s"
            params.append(status.upper())

        if search and search.strip():
            query += " AND (title LIKE %s OR description LIKE %s OR username LIKE %s OR category LIKE %s)"
            pattern = f"%{search.strip()}%"
            params.extend([pattern, pattern, pattern, pattern])

        query += " ORDER BY created_at DESC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_feedback_report_by_id(report_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single feedback report by ID."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM feedback_reports WHERE id = %s", (report_id,))
        row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_feedback_report(
    report_id: int,
    status: str,
    admin_notes: Optional[str] = None,
    admin_response: Optional[str] = None,
    resolved_by: Optional[str] = None,
) -> bool:
    """Updates status, admin notes/correction, and resolution info for a report."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        is_resolving = status.upper() in ("RESOLVED", "REJECTED")
        cursor.execute(
            """
            UPDATE feedback_reports
            SET status = %s,
                admin_notes = COALESCE(%s, admin_notes),
                admin_response = COALESCE(%s, admin_response),
                resolved_by = CASE WHEN %s THEN %s ELSE resolved_by END,
                resolved_at = CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE resolved_at END
            WHERE id = %s
            """,
            (
                status.upper(),
                admin_notes,
                admin_response,
                is_resolving,
                resolved_by,
                is_resolving,
                report_id,
            )
        )
    conn.close()
    return True


def delete_feedback_report(report_id: int) -> bool:
    """Deletes a feedback report from XAMPP MySQL."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM feedback_reports WHERE id = %s", (report_id,))
    conn.close()
    return True


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


# ─── Multi-User Collaboration & Plant Channels CRUD ─────────────────────────

DEFAULT_CHANNELS = [
    {
        "id": "chan_refinery_ops",
        "name": "refinery-operations",
        "channel_type": "CHANNEL",
        "department": "OPERATIONS",
        "description": "MRPL / ONGC CDU, VDU, HCU & PFCCU Unit Operations, Shift Handover & Log Coordination",
    },
    {
        "id": "chan_hse_safety",
        "name": "hse-safety-permits",
        "channel_type": "CHANNEL",
        "department": "HSE",
        "description": "OISD-105 Safety Protocols, Work Permits (PTW), LOTO, Gas Leak & Emergency Response",
    },
    {
        "id": "chan_mechanical_maint",
        "name": "mechanical-maintenance",
        "channel_type": "CHANNEL",
        "department": "MAINTENANCE",
        "description": "Pumps, Compressors, Turbines, Vibration Diagnostics & Overhaul Coordination",
    },
    {
        "id": "chan_drilling_ep",
        "name": "upstream-drilling-ep",
        "channel_type": "CHANNEL",
        "department": "DRILLING",
        "description": "ONGC Rigs, Mud Rheology, Hydrostatic Calculations & Well Engineering",
    },
    {
        "id": "chan_general_plant",
        "name": "general-plant-broadcast",
        "channel_type": "CHANNEL",
        "department": "ALL",
        "description": "Plant-wide announcements, Shift schedules, and cross-department collaboration with @aegis AI",
    },
]

KNOWN_PLANT_USERS = [
    {"username": "operator", "full_name": "Shift Field Operator", "role": "FIELD_OPERATOR", "department": "Operations", "avatar_color": "#F97316"},
    {"username": "process_lead", "full_name": "Senior Process Lead", "role": "PROCESS_LEAD", "department": "Engineering", "avatar_color": "#3B82F6"},
    {"username": "maintenance_eng", "full_name": "Chief Maintenance Engineer", "role": "MAINTENANCE_ENG", "department": "Mechanical", "avatar_color": "#10B981"},
    {"username": "hse_officer", "full_name": "HSE Safety Officer", "role": "SAFETY_OFFICER", "department": "HSE & Fire", "avatar_color": "#EF4444"},
    {"username": "drilling_supervisor", "full_name": "ONGC Rig Superintendent", "role": "DRILLING_SUP", "department": "Upstream E&P", "avatar_color": "#8B5CF6"},
    {"username": "admin", "full_name": "Super Admin & Chief Auditor", "role": "SUPER_ADMIN", "department": "Plant Management", "avatar_color": "#EC4899"},
]


def seed_default_collaboration_channels():
    """Ensures default plant channels exist in database."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        for ch in DEFAULT_CHANNELS:
            cursor.execute(
                """
                INSERT INTO chat_channels (id, name, channel_type, description, department, created_by)
                VALUES (%s, %s, %s, %s, %s, 'system')
                ON DUPLICATE KEY UPDATE
                    name=VALUES(name),
                    description=VALUES(description),
                    department=VALUES(department)
                """,
                (ch["id"], ch["name"], ch["channel_type"], ch["description"], ch["department"])
            )
            # Add default known users as members to public channels
            for u in KNOWN_PLANT_USERS:
                cursor.execute(
                    """
                    INSERT IGNORE INTO channel_members (channel_id, username, role)
                    VALUES (%s, %s, %s)
                    """,
                    (ch["id"], u["username"], u["role"])
                )
    conn.close()


def get_all_collaboration_channels(username: str = "operator") -> List[Dict[str, Any]]:
    """Fetches all channels and DMs accessible to the user."""
    seed_default_collaboration_channels()
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.*, 
                   (SELECT COUNT(*) FROM channel_members cm WHERE cm.channel_id = c.id) AS member_count,
                   (SELECT content FROM channel_messages msg WHERE msg.channel_id = c.id ORDER BY created_at DESC LIMIT 1) AS last_message,
                   (SELECT created_at FROM channel_messages msg WHERE msg.channel_id = c.id ORDER BY created_at DESC LIMIT 1) AS last_message_at
            FROM chat_channels c
            ORDER BY c.created_at ASC
            """
        )
        rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "name": r["name"],
            "channel_type": r["channel_type"],
            "description": r["description"],
            "department": r["department"],
            "created_by": r["created_by"],
            "created_at": str(r["created_at"]),
            "member_count": r["member_count"] or 0,
            "last_message": r["last_message"] or "No messages yet",
            "last_message_at": str(r["last_message_at"]) if r.get("last_message_at") else None,
        })
    return result


def get_or_create_dm_channel(user1: str, user2: str) -> Dict[str, Any]:
    """Retrieves or creates a 1-on-1 Direct Message channel between two users."""
    users_sorted = sorted([user1.strip().lower(), user2.strip().lower()])
    dm_id = f"dm_{users_sorted[0]}_{users_sorted[1]}"
    dm_name = f"{users_sorted[0]} & {users_sorted[1]}"

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO chat_channels (id, name, channel_type, description, department, created_by)
            VALUES (%s, %s, 'DM', %s, 'DIRECT', %s)
            ON DUPLICATE KEY UPDATE name=VALUES(name)
            """,
            (dm_id, dm_name, f"Direct conversation between {users_sorted[0]} and {users_sorted[1]}", user1)
        )
        for u in users_sorted:
            cursor.execute(
                """
                INSERT IGNORE INTO channel_members (channel_id, username, role)
                VALUES (%s, %s, 'MEMBER')
                """,
                (dm_id, u)
            )
    conn.close()
    return {"id": dm_id, "name": dm_name, "channel_type": "DM"}


def create_new_channel(name: str, description: str, department: str, created_by: str) -> str:
    """Creates a new collaboration channel."""
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '-', name.lower().strip())
    chan_id = f"chan_{clean_name}_{int(time.time())}"
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO chat_channels (id, name, channel_type, description, department, created_by)
            VALUES (%s, %s, 'CHANNEL', %s, %s, %s)
            """,
            (chan_id, clean_name, description, department.upper(), created_by)
        )
        # Add creator and known users
        for u in KNOWN_PLANT_USERS:
            cursor.execute(
                """
                INSERT IGNORE INTO channel_members (channel_id, username, role)
                VALUES (%s, %s, %s)
                """,
                (chan_id, u["username"], u["role"])
            )
    conn.close()
    return chan_id


def get_channel_messages(channel_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetches message history for a specific channel or DM."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM channel_messages 
            WHERE channel_id = %s 
            ORDER BY created_at ASC 
            LIMIT %s
            """,
            (channel_id, limit)
        )
        rows = cursor.fetchall()
    conn.close()
    
    formatted = []
    for r in rows:
        formatted.append({
            "id": r["id"],
            "channel_id": r["channel_id"],
            "sender_username": r["sender_username"],
            "sender_role": r["sender_role"],
            "content": r["content"],
            "message_type": r["message_type"],
            "file_id": r.get("file_id"),
            "file_name": r.get("file_name"),
            "file_type": r.get("file_type"),
            "file_size": r.get("file_size"),
            "file_url": r.get("file_url"),
            "created_at": str(r["created_at"]),
        })
    return formatted


def save_channel_message(
    channel_id: str,
    sender_username: str,
    sender_role: str,
    content: str,
    message_type: str = "TEXT",
    file_id: Optional[str] = None,
    file_name: Optional[str] = None,
    file_type: Optional[str] = None,
    file_size: Optional[int] = None,
    file_url: Optional[str] = None,
) -> int:
    """Saves a new message (text, file, or AI response) into the channel history."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO channel_messages (
                channel_id, sender_username, sender_role, content,
                message_type, file_id, file_name, file_type, file_size, file_url
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                channel_id,
                sender_username,
                sender_role,
                content,
                message_type,
                file_id,
                file_name,
                file_type,
                file_size,
                file_url,
            )
        )
        msg_id = cursor.lastrowid
    conn.close()
    return msg_id


def get_plant_users_directory() -> List[Dict[str, Any]]:
    """Returns directory of plant users with department and roles."""
    return KNOWN_PLANT_USERS


# ─── User Activity & Security Monitoring Logging Engine ─────────────────────

SUSPICIOUS_KEYWORDS = [
    "hack", "bypass", "jailbreak", "override guardrail", "leak credentials",
    "sabotage", "shutdown without permit", "root password", "unauthorized dump",
    "weapon", "explosive formula", "exfiltrate", "bypass airgap", "disable loto"
]

def evaluate_activity_risk(text: str, activity_type: str = "CHAT_QUERY") -> str:
    """Evaluates whether user query or activity contains suspicious signals."""
    if not text:
        return "NORMAL"
    text_lower = text.lower()
    for kw in SUSPICIOUS_KEYWORDS:
        if kw in text_lower:
            return "SUSPICIOUS"
    return "NORMAL"


def log_user_activity(
    username: str,
    activity_type: str,
    query_text: Optional[str] = None,
    channel_or_chat_id: Optional[str] = None,
    details: Optional[str] = None,
    file_meta: Optional[Any] = None,
    role: str = "FIELD_OPERATOR",
    ip_address: str = "127.0.0.1",
    risk_level: Optional[str] = None
) -> int:
    """Persists user search, chat, or file share activity into audit ledger."""
    if not risk_level:
        risk_level = evaluate_activity_risk(f"{query_text or ''} {details or ''}", activity_type)

    file_meta_str = json.dumps(file_meta) if isinstance(file_meta, dict) else (str(file_meta) if file_meta else None)

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO user_activity_logs (
                username, role, activity_type, channel_or_chat_id,
                query_text, details, file_meta, ip_address, risk_level
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                username,
                role,
                activity_type,
                channel_or_chat_id,
                query_text,
                details,
                file_meta_str,
                ip_address,
                risk_level
            )
        )
        log_id = cursor.lastrowid
    conn.close()
    return log_id


def get_all_user_activity_logs(
    username: Optional[str] = None,
    activity_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 150
) -> List[Dict[str, Any]]:
    """Fetches user activity logs for security audit & monitor screen."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        query = "SELECT * FROM user_activity_logs WHERE 1=1"
        params: List[Any] = []

        if username and username.lower() != "all":
            query += " AND username = %s"
            params.append(username.strip().lower())

        if activity_type and activity_type.upper() != "ALL":
            query += " AND activity_type = %s"
            params.append(activity_type.upper())

        if risk_level and risk_level.upper() != "ALL":
            query += " AND risk_level = %s"
            params.append(risk_level.upper())

        if search and search.strip():
            query += " AND (query_text LIKE %s OR details LIKE %s OR username LIKE %s)"
            p = f"%{search.strip()}%"
            params.extend([p, p, p])

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "username": r["username"],
            "role": r["role"],
            "activity_type": r["activity_type"],
            "channel_or_chat_id": r["channel_or_chat_id"],
            "query_text": r["query_text"],
            "details": r["details"],
            "file_meta": r["file_meta"],
            "ip_address": r["ip_address"],
            "risk_level": r["risk_level"],
            "created_at": str(r["created_at"]),
        })
    return result


