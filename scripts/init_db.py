"""
Creates the application schema in the configured database.

Safe to re-run: every statement is IF NOT EXISTS / idempotent, and column
additions are checked before being applied.

Usage:
    python scripts/init_db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import backend.config as cfg  # noqa: E402
from backend.db import init_db  # noqa: E402
from backend.db_dialect import get_db_connection  # noqa: E402


def main() -> int:
    print(f"Target : {cfg.DB_LABEL}")
    try:
        init_db()
    except Exception as exc:
        print(f"ERROR: schema creation failed: {type(exc).__name__}: {exc}")
        return 1

    # Report what actually exists now, rather than assuming success.
    expected = [
        "messages", "chat_summaries", "files", "feedback_reports",
        "chat_channels", "channel_members", "channel_messages",
        "user_activity_logs",
    ]
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if cfg.IS_POSTGRES:
                cur.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = current_schema() ORDER BY table_name"
                )
                present = {r["table_name"] for r in cur.fetchall()}
            else:
                cur.execute(
                    "SELECT TABLE_NAME AS table_name FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA = DATABASE()"
                )
                present = {(r.get("table_name") or r.get("TABLE_NAME")) for r in cur.fetchall()}
    finally:
        conn.close()

    print()
    print(f"Tables in {cfg.DB_NAME}:")
    missing = []
    for t in expected:
        ok = t in present
        if not ok:
            missing.append(t)
        print(f"  {'OK  ' if ok else 'MISS'}  {t}")
    if missing:
        print(f"\n{len(missing)} table(s) missing: {', '.join(missing)}")
        return 1
    print(f"\nAll {len(expected)} application tables present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
