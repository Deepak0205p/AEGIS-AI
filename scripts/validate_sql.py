"""
Offline SQL validation for the dialect layer.

Renders every statement `backend/db.py` and `backend/db_dialect.py` produce, for
BOTH dialects, and parses the result:
  * PostgreSQL SQL -> pglast (the real PostgreSQL grammar)
  * MySQL SQL      -> sqlglot (mysql dialect)

This catches syntax errors without needing a live database server.

Usage:  python scripts/validate_sql.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pglast  # noqa: E402
import sqlglot  # noqa: E402


class FakeCursor:
    """Records executed SQL instead of sending it to a server."""

    def __init__(self, sink):
        self.sink = sink
        self.rowcount = 1
        self.lastrowid = 1
        self._returning = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        if sql.strip().upper().endswith("RETURNING ID"):
            self._returning = {"id": 1}
        else:
            self._returning = None
        self.sink.append((sql, params))

    def fetchone(self):
        return self._returning or {"present": 0}

    def fetchall(self):
        return []


class FakeConnection:
    def __init__(self, sink):
        self.sink = sink
        self.closed = False

    def cursor(self):
        return FakeCursor(self.sink)

    def close(self):
        self.closed = True


def render(dialect):
    """Re-imports the stack with AEGIS_DB_DRIVER=dialect and exercises every path."""
    os.environ["AEGIS_DB_DRIVER"] = dialect
    for mod in [m for m in sys.modules if m.startswith("backend")]:
        del sys.modules[mod]

    import backend.db_dialect as dd
    import backend.db as db

    stmts = []
    fake = FakeConnection(stmts)
    dd.get_db_connection = lambda: fake
    dd.ensure_database_exists = lambda: None
    db.get_db_connection = lambda: fake
    db.ensure_database_exists = lambda: None

    # 1. Full schema
    db._init_schema(FakeCursor(stmts))

    # 2. Runtime write/read paths
    db.save_message("c1", "user", "hi", "chat")
    db.save_cached_summary("c1", "summary", 7)
    db.save_file_record("f1", "c1", "a.docx", "docx", "x.docx", "PENDING_STAGE_1", True)
    db.get_pending_verifications("SUPER_ADMIN")
    db.get_pending_verifications("FIELD_OPERATOR")
    db.get_all_deliverable_files()
    db.create_feedback_report("ERROR", "t", "d")
    db.get_all_feedback_reports("ERROR", "OPEN", "Pump")
    db.update_feedback_report(1, "RESOLVED", "n", "r", "admin")
    db.get_all_user_activity_logs("operator", "CHAT_QUERY", "NORMAL", "pump", 50)
    db.list_all_chat_sessions()
    db.seed_default_collaboration_channels()
    db.get_or_create_dm_channel("alice", "bob")
    db.create_new_channel("ops", "d", "ops", "alice")
    db.save_channel_message("chan_x", "alice", "OPERATOR", "hi")
    db.get_channel_messages("chan_x", 50)
    db.log_user_activity("operator", "CHAT_QUERY", "q", "c", "d", {"k": 1})
    db.delete_chat_session_data("c1")

    # 3. DDL helper units
    cur = FakeCursor(stmts)
    dd.create_index(cur, "t", "i", ["a", "b"])
    dd.add_column(cur, "t", "c", "VARCHAR(8) DEFAULT NULL")

    return stmts


def _substitute(sql, params):
    """
    Replaces %s placeholders with literal values.

    Both parsers reject driver placeholders (they parse SQL text, not a
    parameterised query), so the values are inlined for validation only. Types
    are chosen to match what the driver actually sends: bools for PostgreSQL,
    ints for MySQL's TINYINT.
    """
    if not params:
        return sql
    vals = list(params)
    out = sql
    for v in vals:
        if isinstance(v, bool):
            lit = "TRUE" if v else "FALSE"
        elif isinstance(v, (int, float)):
            lit = str(v)
        elif v is None:
            lit = "NULL"
        else:
            lit = "'" + str(v).replace("'", "''") + "'"
        out = out.replace("%s", lit, 1)
    return out


def validate(stmts, dialect):
    bad = 0
    for sql, params in stmts:
        rendered = _substitute(sql, params)
        one = " ".join(rendered.split())
        try:
            if dialect == "postgres":
                pglast.parse_sql(rendered)
            else:
                sqlglot.parse_one(rendered, dialect="mysql")
        except Exception as exc:
            bad += 1
            print(f"\n  SYNTAX ERROR ({dialect})")
            print(f"    {one[:320]}")
            print(f"    -> {type(exc).__name__}: {str(exc)[:200]}")
    return bad


total_bad = 0
for dialect in ("postgres", "mysql"):
    stmts = render(dialect)
    target = "PostgreSQL" if dialect == "postgres" else "MySQL"
    bad = validate(stmts, dialect)
    total_bad += bad
    print(f"{target}: {len(stmts) - bad}/{len(stmts)} statements valid")

print()
print("ALL SQL VALID" if total_bad == 0 else f"{total_bad} INVALID STATEMENTS")
sys.exit(1 if total_bad else 0)
