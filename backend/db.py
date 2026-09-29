"""
Database and Conversation History Manager for Air-Gapped Local AI.

Persistence is dialect-agnostic: **PostgreSQL** is the default target and
**MySQL/MariaDB** (XAMPP) remains supported. All engine-specific SQL lives in
`backend/db_dialect.py`; this module holds the schema definition and the query
logic, both of which are written once.

Provides conversation history, rolling summaries, the 2-step human verification
workflow for deliverables, feedback reports, plant team collaboration channels,
and the security activity ledger.
"""

import json
import os
import re
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from backend.config import (
    DB_DRIVER,
    DB_LABEL,
    IS_POSTGRES,
    MYSQL_DB,
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_USER,
    NUM_CTX,
    PG_DB,
    PG_HOST,
    PG_PORT,
    PG_USER,
    logger,
)
from backend.db_dialect import (
    Column,
    add_column,
    bool_param,
    case_insensitive_like,
    create_index,
    create_table,
    ensure_database_exists,
    epoch_seconds,
    get_db_connection,
    insert_ignore,
    insert_returning_id,
    substring,
    upsert,
)


def _ensure_column(cursor, table: str, column: str, column_def: str) -> None:
    """Backwards-compatible wrapper around the dialect-aware column adder."""
    add_column(cursor, table, column, column_def)


def _ts() -> str:
    """
    Portable timestamp column type.

    MySQL DATETIME has no timezone; PostgreSQL TIMESTAMP is timezone-aware while
    TIMESTAMPTZ would change the Python objects returned to callers. Plain
    TIMESTAMP is used so `str(row["created_at"])` stays identical across drivers.
    """
    return "TIMESTAMP"


# Columns added after the initial `files` CREATE so older installs pick them up.
# `is_important` is a real BOOLEAN on PostgreSQL, not TINYINT(1).
_FILES_MIGRATION_COLUMNS = [
    ("is_important", "BOOLEAN DEFAULT FALSE" if IS_POSTGRES else "TINYINT(1) DEFAULT 0"),
    ("verification_status", "VARCHAR(32) DEFAULT 'PENDING_STAGE_1'"),
    ("stage_1_verifier", "VARCHAR(64) DEFAULT NULL"),
    ("stage_1_at", f"{_ts()} DEFAULT NULL"),
    ("stage_1_notes", "TEXT DEFAULT NULL"),
    ("stage_2_verifier", "VARCHAR(64) DEFAULT NULL"),
    ("stage_2_at", f"{_ts()} DEFAULT NULL"),
    ("stage_2_notes", "TEXT DEFAULT NULL"),
    ("rejected_by", "VARCHAR(64) DEFAULT NULL"),
    ("rejected_at", f"{_ts()} DEFAULT NULL"),
    ("reject_reason", "TEXT DEFAULT NULL"),
    ("sha256_hash", "VARCHAR(64) DEFAULT NULL"),
    ("size_bytes", "BIGINT DEFAULT NULL"),
    ("updated_at", f"{_ts()} DEFAULT NULL"),
]


def _init_schema(cursor) -> None:
    """
    Creates every table and index if absent.

    Written once against the portable `Column` spec; `db_dialect` renders the
    identity columns, table options and index statements per engine.
    """
    # ── messages ────────────────────────────────────────────────────────
    create_table(cursor, "messages", [
        Column("id", "INT", identity=True),
        Column("chat_id", "VARCHAR(128)", not_null=True),
        Column("role", "VARCHAR(32)", not_null=True),
        Column("content", "TEXT", "LONGTEXT", not_null=True),
        Column("mode", "VARCHAR(32)", not_null=True),
        Column("timestamp", _ts(), "DATETIME", default="CURRENT_TIMESTAMP"),
    ])
    create_index(cursor, "messages", "idx_chat_id", ["chat_id"])

    # ── chat_summaries ──────────────────────────────────────────────────
    create_table(cursor, "chat_summaries", [
        Column("chat_id", "VARCHAR(128)", not_null=True),
        Column("summary", "TEXT", not_null=True),
        Column("last_msg_id", "INT", not_null=True),
        Column("updated_at", _ts(), "DATETIME", default="CURRENT_TIMESTAMP"),
    ], primary_key=["chat_id"])
    if not IS_POSTGRES:
        # Preserve the legacy MySQL auto-touch semantics for existing installs.
        # PostgreSQL has no ON UPDATE CURRENT_TIMESTAMP, so `updated_at` is
        # stamped explicitly in save_cached_summary() on both paths.
        try:
            cursor.execute(
                "ALTER TABLE `chat_summaries` MODIFY updated_at DATETIME "
                "DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
            )
        except Exception:
            pass

    # ── files (generated deliverables + verification state) ─────────────
    create_table(cursor, "files", [
        Column("file_id", "VARCHAR(64)", not_null=True),
        Column("chat_id", "VARCHAR(128)", not_null=True),
        Column("filename", "VARCHAR(255)", not_null=True),
        Column("file_type", "VARCHAR(32)", not_null=True),
        Column("file_path", "TEXT", not_null=True),
        Column("verification_status", "VARCHAR(32)", default="'PENDING_STAGE_1'"),
        Column("stage_1_verifier", "VARCHAR(64)"),
        Column("stage_1_at", _ts(), "DATETIME"),
        Column("stage_1_notes", "TEXT"),
        Column("stage_2_verifier", "VARCHAR(64)"),
        Column("stage_2_at", _ts(), "DATETIME"),
        Column("stage_2_notes", "TEXT"),
        Column("rejected_by", "VARCHAR(64)"),
        Column("rejected_at", _ts(), "DATETIME"),
        Column("reject_reason", "TEXT"),
        Column("created_at", _ts(), "DATETIME", default="CURRENT_TIMESTAMP"),
    ], primary_key=["file_id"])
    create_index(cursor, "files", "idx_files_chat_id", ["chat_id"])
    create_index(cursor, "files", "idx_files_status", ["verification_status"])
    for col_name, col_def in _FILES_MIGRATION_COLUMNS:
        add_column(cursor, "files", col_name, col_def)

    # ── feedback_reports ────────────────────────────────────────────────
    create_table(cursor, "feedback_reports", [
        Column("id", "INT", identity=True),
        Column("report_type", "VARCHAR(32)", not_null=True),
        Column("user_id", "VARCHAR(64)"),
        Column("username", "VARCHAR(64)", default="'operator'"),
        Column("chat_id", "VARCHAR(128)"),
        Column("message_id", "VARCHAR(64)"),
        Column("message_content", "TEXT", "LONGTEXT"),
        Column("category", "VARCHAR(64)", default="'GENERAL'"),
        Column("title", "VARCHAR(255)", not_null=True),
        Column("description", "TEXT", "LONGTEXT", not_null=True),
        Column("suggested_fix", "TEXT", "LONGTEXT"),
        Column("status", "VARCHAR(32)", default="'OPEN'"),
        Column("admin_notes", "TEXT", "LONGTEXT"),
        Column("admin_response", "TEXT", "LONGTEXT"),
        Column("resolved_by", "VARCHAR(64)"),
        Column("resolved_at", _ts(), "DATETIME"),
        Column("created_at", _ts(), "DATETIME", default="CURRENT_TIMESTAMP"),
        Column("updated_at", _ts(), "DATETIME", default="CURRENT_TIMESTAMP"),
    ])
    create_index(cursor, "feedback_reports", "idx_fb_type", ["report_type"])
    create_index(cursor, "feedback_reports", "idx_fb_status", ["status"])
    create_index(cursor, "feedback_reports", "idx_fb_created", ["created_at"])

    # ── chat_channels ───────────────────────────────────────────────────
    create_table(cursor, "chat_channels", [
        Column("id", "VARCHAR(64)", not_null=True),
        Column("name", "VARCHAR(128)", not_null=True),
        Column("channel_type", "VARCHAR(32)", default="'CHANNEL'"),
        Column("description", "TEXT"),
        Column("department", "VARCHAR(64)", default="'ALL'"),
        Column("created_by", "VARCHAR(64)", default="'system'"),
        Column("created_at", _ts(), "DATETIME", default="CURRENT_TIMESTAMP"),
    ], primary_key=["id"])

    # ── channel_members ─────────────────────────────────────────────────
    create_table(cursor, "channel_members", [
        Column("id", "INT", identity=True),
        Column("channel_id", "VARCHAR(64)", not_null=True),
        Column("username", "VARCHAR(64)", not_null=True),
        Column("role", "VARCHAR(64)", default="'OPERATOR'"),
        Column("joined_at", _ts(), "DATETIME", default="CURRENT_TIMESTAMP"),
    ], uniques=[["channel_id", "username"]])
    create_index(cursor, "channel_members", "idx_mem_chan", ["channel_id"])
    create_index(cursor, "channel_members", "idx_mem_user", ["username"])

    # ── channel_messages ────────────────────────────────────────────────
    create_table(cursor, "channel_messages", [
        Column("id", "INT", identity=True),
        Column("channel_id", "VARCHAR(64)", not_null=True),
        Column("sender_username", "VARCHAR(64)", not_null=True),
        Column("sender_role", "VARCHAR(64)", default="'OPERATOR'"),
        Column("content", "TEXT", "LONGTEXT", not_null=True),
        Column("message_type", "VARCHAR(32)", default="'TEXT'"),
        Column("file_id", "VARCHAR(64)"),
        Column("file_name", "VARCHAR(255)"),
        Column("file_type", "VARCHAR(64)"),
        Column("file_size", "INT"),
        Column("file_url", "TEXT"),
        Column("created_at", _ts(), "DATETIME", default="CURRENT_TIMESTAMP"),
    ])
    create_index(cursor, "channel_messages", "idx_cmsg_chan", ["channel_id"])
    create_index(cursor, "channel_messages", "idx_cmsg_created", ["created_at"])

    # ── user_activity_logs (security audit ledger) ──────────────────────
    create_table(cursor, "user_activity_logs", [
        Column("id", "INT", identity=True),
        Column("username", "VARCHAR(64)", not_null=True),
        Column("role", "VARCHAR(64)", default="'OPERATOR'"),
        Column("activity_type", "VARCHAR(64)", not_null=True),
        Column("channel_or_chat_id", "VARCHAR(128)"),
        Column("query_text", "TEXT", "LONGTEXT"),
        Column("details", "TEXT", "LONGTEXT"),
        Column("file_meta", "TEXT", "LONGTEXT"),
        Column("ip_address", "VARCHAR(64)", default="'127.0.0.1'"),
        Column("risk_level", "VARCHAR(32)", default="'NORMAL'"),
        Column("created_at", _ts(), "DATETIME", default="CURRENT_TIMESTAMP"),
    ])
    create_index(cursor, "user_activity_logs", "idx_act_user", ["username"])
    create_index(cursor, "user_activity_logs", "idx_act_type", ["activity_type"])
    create_index(cursor, "user_activity_logs", "idx_act_risk", ["risk_level"])
    create_index(cursor, "user_activity_logs", "idx_act_created", ["created_at"])


def init_db():
    """Creates the database (if absent) and applies the full schema."""
    ensure_database_exists()

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            _init_schema(cursor)
    finally:
        conn.close()

    logger.info(f"Database initialized: {DB_LABEL}")


def save_message(chat_id: str, role: str, content: str, mode: str = "chat") -> int:
    """Persists a message to the configured database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            msg_id = insert_returning_id(
                cursor,
                "INSERT INTO messages (chat_id, role, content, mode) "
                "VALUES (%s, %s, %s, %s)",
                (chat_id, role, content, mode),
            )
    finally:
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
    """Caches the rolling conversation summary for a chat."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            upsert(
                cursor,
                "chat_summaries",
                {
                    "chat_id": chat_id,
                    "summary": summary,
                    "last_msg_id": last_msg_id,
                    # Stamped explicitly: PostgreSQL has no ON UPDATE
                    # CURRENT_TIMESTAMP, so relying on the column default here
                    # would leave updated_at stale on an update.
                    "updated_at": "CURRENT_TIMESTAMP",
                },
                conflict_columns=["chat_id"],
                update_columns=["summary", "last_msg_id", "updated_at"],
                raw_columns=["updated_at"],
            )
    finally:
        conn.close()


def file_integrity(file_path: Any) -> Tuple[Optional[str], Optional[int]]:
    """Returns (sha256_hash, size_bytes) for a deliverable on disk, or (None, None)."""
    import hashlib

    try:
        path = Path(str(file_path))
        if not path.exists() or not path.is_file():
            return None, None
        raw = path.read_bytes()
        return hashlib.sha256(raw).hexdigest(), len(raw)
    except Exception:
        return None, None


def save_file_record(
    file_id: str,
    chat_id: str,
    filename: str,
    file_type: str,
    file_path: str,
    verification_status: str = "PENDING_STAGE_1",
    is_important: bool = True
):
    """Registers a generated deliverable file."""
    sha256_hash, size_bytes = file_integrity(file_path)

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            upsert(
                cursor,
                "files",
                {
                    "file_id": file_id,
                    "chat_id": chat_id,
                    "filename": filename,
                    "file_type": file_type,
                    "file_path": str(file_path),
                    "verification_status": verification_status,
                    "is_important": bool_param(is_important),
                    "sha256_hash": sha256_hash,
                    "size_bytes": size_bytes,
                    "updated_at": "CURRENT_TIMESTAMP",
                },
                conflict_columns=["file_id"],
                update_columns=[
                    "filename", "file_type", "file_path", "verification_status",
                    "is_important", "sha256_hash", "size_bytes", "updated_at",
                ],
                # A genuine hash/size must never be replaced by a NULL that
                # results from the file being temporarily unreadable.
                coalesce_columns=["sha256_hash", "size_bytes"],
                raw_columns=["updated_at"],
            )
    finally:
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
    try:
        with conn.cursor() as cursor:
            if user_role == "SUPER_ADMIN":
                # MySQL's FIELD(x,'a','b') has no PostgreSQL equivalent, so the
                # ordering is expressed as a portable CASE. Stage 2 first.
                if IS_POSTGRES:
                    order = ("CASE verification_status "
                             "WHEN 'PENDING_STAGE_2' THEN 0 "
                             "WHEN 'PENDING_STAGE_1' THEN 1 ELSE 2 END")
                else:
                    order = "FIELD(verification_status, 'PENDING_STAGE_2', 'PENDING_STAGE_1')"
                cursor.execute(
                    "SELECT * FROM files WHERE is_important = %s "
                    "AND verification_status IN ('PENDING_STAGE_2', 'PENDING_STAGE_1') "
                    f"ORDER BY {order}, created_at DESC",
                    (bool_param(True),),
                )
            elif user_role in ("PROCESS_LEAD", "MAINTENANCE_ENG", "FIELD_OPERATOR"):
                cursor.execute(
                    "SELECT * FROM files WHERE is_important = %s "
                    "AND verification_status = 'PENDING_STAGE_1' ORDER BY created_at DESC",
                    (bool_param(True),),
                )
            else:
                cursor.execute(
                    "SELECT * FROM files WHERE is_important = %s "
                    "AND verification_status IN ('PENDING_STAGE_1', 'PENDING_STAGE_2') "
                    "ORDER BY created_at DESC",
                    (bool_param(True),),
                )
            rows = cursor.fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def verify_file_stage_1(file_id: str, verifier: str, notes: str = "") -> bool:
    """Stage 1 approval: Transitions file from PENDING_STAGE_1 to PENDING_STAGE_2.

    The status guard is part of the WHERE clause and rowcount is checked, so a
    caller cannot skip Stage 1 (or approve a nonexistent file) and still be
    told the transition succeeded.
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE files 
            SET verification_status = 'PENDING_STAGE_2',
                stage_1_verifier = %s,
                stage_1_at = CURRENT_TIMESTAMP,
                stage_1_notes = %s
            WHERE file_id = %s AND verification_status = 'PENDING_STAGE_1'
            """,
            (verifier, notes, file_id)
        )
        updated = cursor.rowcount
    conn.close()
    return updated > 0


def verify_file_stage_2(file_id: str, verifier: str, notes: str = "") -> bool:
    """Stage 2 approval: Final sign-off transition from PENDING_STAGE_2 to VERIFIED.

    Only a file that actually reached PENDING_STAGE_2 can be signed off, so the
    Lower-Post -> Higher-Post hierarchy cannot be short-circuited.
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE files 
            SET verification_status = 'VERIFIED',
                stage_2_verifier = %s,
                stage_2_at = CURRENT_TIMESTAMP,
                stage_2_notes = %s
            WHERE file_id = %s AND verification_status = 'PENDING_STAGE_2'
            """,
            (verifier, notes, file_id)
        )
        updated = cursor.rowcount
    conn.close()
    return updated > 0


def reject_file(file_id: str, rejected_by: str, reason: str = "") -> bool:
    """Rejects deliverable file with reason.

    An already-VERIFIED file is not silently downgraded: a rejection only
    applies to a file that is still awaiting sign-off. Returns False when the
    file does not exist or is not in a rejectable state.
    """
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
              AND verification_status IN ('PENDING_STAGE_1', 'PENDING_STAGE_2')
            """,
            (rejected_by, reason, file_id)
        )
        updated = cursor.rowcount
    conn.close()
    return updated > 0


def rename_file_record(file_id: str, new_filename: str) -> bool:
    """Updates filename and optionally renames physical file on storage."""
    record = get_file_record(file_id)
    if not record:
        return False
    
    old_path = Path(record["file_path"])
    new_path = old_path
    
    # Clean new filename. A blank/whitespace name must be rejected outright:
    # the previous guard fell through and wrote filename = '' with the file_path
    # unchanged, orphaning the record from the file on disk.
    clean_name = new_filename.strip()
    if not clean_name:
        logger.warning(f"[DB] Refusing to blank the filename for file_id={file_id}")
        return False

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
            "UPDATE files SET filename = %s, file_path = %s, updated_at = CURRENT_TIMESTAMP WHERE file_id = %s",
            (clean_name, str(new_path), file_id)
        )
    conn.close()
    return True


def backfill_file_metadata(file_id: str, sha256_hash: Optional[str] = None, size_bytes: Optional[int] = None) -> bool:
    """Fills in missing integrity metadata for legacy rows without overwriting real values."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE files
            SET sha256_hash = COALESCE(sha256_hash, %s),
                size_bytes = COALESCE(size_bytes, %s)
            WHERE file_id = %s
            """,
            (sha256_hash, size_bytes, file_id)
        )
    conn.close()
    return True


def mark_file_edited(
    file_id: str,
    sha256_hash: Optional[str] = None,
    size_bytes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Records a Canvas edit and re-opens the human verification gate.

    A deliverable that already reached PENDING_STAGE_2 / VERIFIED (or was
    REJECTED) is sent back to PENDING_STAGE_1: the approved bytes no longer
    match what is on disk, so it must pass the 2-step review again. Previously
    captured sign-off fields are cleared because they applied to other content;
    the edit itself is recorded in the user activity audit ledger by the caller.
    """
    record = get_file_record(file_id)
    if not record:
        return {}

    previous_status = record.get("verification_status") or "PENDING_STAGE_1"
    reverification_required = previous_status in ("PENDING_STAGE_2", "VERIFIED", "REJECTED")
    new_status = "PENDING_STAGE_1" if reverification_required else previous_status

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE files
            SET sha256_hash = COALESCE(%s, sha256_hash),
                size_bytes = COALESCE(%s, size_bytes),
                updated_at = CURRENT_TIMESTAMP,
                verification_status = %s,
                stage_1_verifier = NULL, stage_1_at = NULL, stage_1_notes = NULL,
                stage_2_verifier = NULL, stage_2_at = NULL, stage_2_notes = NULL,
                rejected_by = NULL, rejected_at = NULL, reject_reason = NULL
            WHERE file_id = %s
            """,
            (sha256_hash, size_bytes, new_status, file_id)
        )
    conn.close()

    return {
        "previous_status": previous_status,
        "verification_status": new_status,
        "reverification_required": reverification_required,
    }


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
    """Inserts a new error or suggestion report."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            report_id = insert_returning_id(
                cursor,
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
                ),
            )
    finally:
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
            # MySQL's default collation made LIKE case-insensitive; PostgreSQL
            # LIKE is always case-sensitive, so ILIKE is used there to keep
            # search behaviour identical across the two drivers.
            like = case_insensitive_like("%s")
            query += (
                f" AND (title {like} OR description {like} "
                f"OR username {like} OR category {like})"
            )
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
    try:
        with conn.cursor() as cursor:
            is_resolving = status.upper() in ("RESOLVED", "REJECTED")
            cursor.execute(
                """
                UPDATE feedback_reports
                SET status = %s,
                    admin_notes = COALESCE(%s, admin_notes),
                    admin_response = COALESCE(%s, admin_response),
                    resolved_by = CASE WHEN %s THEN %s ELSE resolved_by END,
                    resolved_at = CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE resolved_at END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    status.upper(),
                    admin_notes,
                    admin_response,
                    # psycopg3 requires a real boolean; MySQL's TINYINT accepts 0/1.
                    bool_param(is_resolving),
                    resolved_by,
                    bool_param(is_resolving),
                    report_id,
                )
            )
    finally:
        conn.close()
    return True


def delete_feedback_report(report_id: int) -> bool:
    """Deletes a feedback report."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM feedback_reports WHERE id = %s", (report_id,))
    finally:
        conn.close()
    return True


def estimate_tokens(text: str) -> int:
    """Rough estimate of token count (avg 3.5 chars per token for code/english)."""
    return max(1, int(len(text) / 3.5))


def list_all_chat_sessions() -> List[Dict[str, Any]]:
    """Returns the list of distinct chat sessions."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # MySQL's UNIX_TIMESTAMP() / SUBSTRING(s, a, b) have no direct
            # PostgreSQL spelling; both are rendered by the dialect layer.
            cursor.execute(f"""
                SELECT
                    chat_id as id,
                    {epoch_seconds("MIN(timestamp)")} as created_at,
                    COALESCE(
                        MAX(CASE WHEN role = 'user'
                                 THEN {substring("content", 1, 50)} END),
                        'Chat'
                    ) as title,
                    COUNT(*) as count
                FROM messages
                GROUP BY chat_id
                ORDER BY MAX(timestamp) DESC
            """)
            rows = cursor.fetchall()
    finally:
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
    """Ensures the default plant channels exist in the database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            for ch in DEFAULT_CHANNELS:
                upsert(
                    cursor,
                    "chat_channels",
                    {
                        "id": ch["id"],
                        "name": ch["name"],
                        "channel_type": ch["channel_type"],
                        "description": ch["description"],
                        "department": ch["department"],
                        "created_by": "system",
                    },
                    conflict_columns=["id"],
                    update_columns=["name", "description", "department"],
                )
                # Add default known users as members to public channels
                for u in KNOWN_PLANT_USERS:
                    insert_ignore(
                        cursor,
                        "channel_members",
                        {
                            "channel_id": ch["id"],
                            "username": u["username"],
                            "role": u["role"],
                        },
                        conflict_columns=["channel_id", "username"],
                    )
    finally:
        conn.close()


def get_all_collaboration_channels(username: str = "operator") -> List[Dict[str, Any]]:
    """Fetches all channels and DMs accessible to the user.

    Access is scoped by membership: a DM (or a department-scoped channel) is only
    returned when `username` is in `channel_members`. The previous version
    ignored its `username` argument entirely, so every caller received every
    channel including other users' private DMs and the full text of their most
    recent message.
    """
    seed_default_collaboration_channels()
    viewer = (username or "").strip().lower()
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.*, 
                   (SELECT COUNT(*) FROM channel_members cm WHERE cm.channel_id = c.id) AS member_count,
                   (SELECT content FROM channel_messages msg WHERE msg.channel_id = c.id ORDER BY created_at DESC LIMIT 1) AS last_message,
                   (SELECT created_at FROM channel_messages msg WHERE msg.channel_id = c.id ORDER BY created_at DESC LIMIT 1) AS last_message_at
            FROM chat_channels c
            WHERE c.department = 'ALL'
               OR EXISTS (
                    SELECT 1 FROM channel_members cm
                    WHERE cm.channel_id = c.id AND LOWER(cm.username) = %s
               )
            ORDER BY c.created_at ASC
            """,
            (viewer,)
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
    try:
        with conn.cursor() as cursor:
            upsert(
                cursor,
                "chat_channels",
                {
                    "id": dm_id,
                    "name": dm_name,
                    "channel_type": "DM",
                    "description": f"Direct conversation between {users_sorted[0]} and {users_sorted[1]}",
                    "department": "DIRECT",
                    "created_by": user1,
                },
                conflict_columns=["id"],
                update_columns=["name"],
            )
            for u in users_sorted:
                insert_ignore(
                    cursor,
                    "channel_members",
                    {"channel_id": dm_id, "username": u, "role": "MEMBER"},
                    conflict_columns=["channel_id", "username"],
                )
    finally:
        conn.close()
    return {"id": dm_id, "name": dm_name, "channel_type": "DM"}


def create_new_channel(name: str, description: str, department: str, created_by: str) -> str:
    """Creates a new collaboration channel."""
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '-', name.lower().strip())
    chan_id = f"chan_{clean_name}_{int(time.time())}"
    conn = get_db_connection()
    try:
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
                insert_ignore(
                    cursor,
                    "channel_members",
                    {"channel_id": chan_id, "username": u["username"], "role": u["role"]},
                    conflict_columns=["channel_id", "username"],
                )
    finally:
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
    try:
        with conn.cursor() as cursor:
            msg_id = insert_returning_id(
                cursor,
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
                ),
            )
    finally:
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
    try:
        with conn.cursor() as cursor:
            log_id = insert_returning_id(
                cursor,
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
                ),
            )
    finally:
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
            like = case_insensitive_like("%s")
            query += f" AND (query_text {like} OR details {like} OR username {like})"
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


