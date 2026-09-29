"""
Database dialect layer for the Air-Gapped Sovereign AI Workbench.

Supports **PostgreSQL** (default) and **MySQL/MariaDB** (legacy XAMPP path)
behind one small interface, so `backend/db.py` can stay dialect-agnostic and
every other module keeps importing the same function names.

Why this exists: the schema and the query set were originally written for
MySQL. The constructs that are *not* portable are isolated here:

  | Concern            | MySQL                          | PostgreSQL                          |
  |--------------------|--------------------------------|-------------------------------------|
  | identity column    | INT AUTO_INCREMENT             | INT GENERATED ... AS IDENTITY       |
  | inserted id        | cursor.lastrowid               | INSERT ... RETURNING id             |
  | upsert             | ON DUPLICATE KEY UPDATE        | ON CONFLICT (...) DO UPDATE         |
  | insert-if-absent   | INSERT IGNORE                  | ON CONFLICT DO NOTHING              |
  | table options      | ENGINE=InnoDB DEFAULT CHARSET  | (none)                              |
  | inline indexes     | INDEX n (c) inside CREATE      | separate CREATE INDEX IF NOT EXISTS  |
  | unique key         | UNIQUE KEY n (c)               | UNIQUE (c)                          |
  | boolean column     | TINYINT(1)                     | BOOLEAN                             |
  | ordered CASE value | FIELD(a, 'x', 'y')             | CASE a WHEN 'x' THEN 0 ... END      |
  | epoch seconds      | UNIX_TIMESTAMP(t)              | EXTRACT(EPOCH FROM t)               |
  | substring          | SUBSTRING(s, 1, 50)            | SUBSTRING(s FROM 1 FOR 50)          |
  | case-insensitive   | LIKE (ci collation by default)| ILIKE                               |
  | current schema     | DATABASE()                    | current_schema()                    |
  | auto-touch column  | ON UPDATE CURRENT_TIMESTAMP    | explicit update in the statement    |

Everything else (VARCHAR/TEXT/INT/BOOLEAN, %s placeholders, COALESCE,
CURRENT_TIMESTAMP, `with conn.cursor()`, cursor.rowcount) behaves the same in
both and is written once.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple

from backend.config import (
    DB_CONNECT_TIMEOUT,
    DB_DRIVER,
    IS_POSTGRES,
    PG_DB,
    PG_HOST,
    PG_PASSWORD,
    PG_PORT,
    PG_USER,
    MYSQL_DB,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
    logger,
)


# ══════════════════════════════════════════════════════════════════════
# Driver loading
# ══════════════════════════════════════════════════════════════════════
if IS_POSTGRES:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:  # pragma: no cover - configuration error
        raise ImportError(
            "PostgreSQL is the active database but psycopg is not installed. "
            "Run: pip install \"psycopg[binary]\"  (or set AEGIS_DB_DRIVER=mysql)"
        ) from exc
else:
    import pymysql
    import pymysql.cursors


# ══════════════════════════════════════════════════════════════════════
# Connections
# ══════════════════════════════════════════════════════════════════════
def get_db_connection():
    """
    Returns a connection to the configured database.

    Both drivers are opened in autocommit mode, matching the original MySQL
    behaviour, so callers never need an explicit commit. `connect_timeout` is
    always set: without it a driver can block indefinitely when the host is
    unreachable-but-not-refusing, which stalls startup and every DB-backed
    request instead of failing fast.
    """
    if IS_POSTGRES:
        return psycopg.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname=PG_DB,
            autocommit=True,
            connect_timeout=DB_CONNECT_TIMEOUT,
            row_factory=dict_row,
        )
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        connect_timeout=DB_CONNECT_TIMEOUT,
    )


def ensure_database_exists() -> None:
    """
    Creates the application database if it is missing.

    Connects to the server's maintenance database (`postgres` on PostgreSQL,
    no schema selected on MySQL) because the target database may not exist yet.
    """
    if IS_POSTGRES:
        conn = psycopg.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname="postgres",
            autocommit=True,
            connect_timeout=DB_CONNECT_TIMEOUT,
        )
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (PG_DB,))
                if cur.fetchone() is None:
                    # Identifier cannot be parameterised; the name comes from
                    # config, and it is quoted to keep it a single identifier.
                    cur.execute(f'CREATE DATABASE "{PG_DB}"')
                    logger.info(f"[DB SCHEMA] Created PostgreSQL database '{PG_DB}'")
        finally:
            conn.close()
    else:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            charset="utf8mb4",
            autocommit=True,
            connect_timeout=DB_CONNECT_TIMEOUT,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                )
        finally:
            conn.close()


# ══════════════════════════════════════════════════════════════════════
# DDL rendering
# ══════════════════════════════════════════════════════════════════════
def _pg_identity(col: str) -> str:
    return f"{col} INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY"


def _mysql_identity(col: str) -> str:
    return f"{col} INT AUTO_INCREMENT PRIMARY KEY"


def _pg_text() -> str:
    return "TEXT"


def _timestamp() -> str:
    # MySQL DATETIME has no timezone; PostgreSQL TIMESTAMP is timezone-aware.
    # TIMESTAMPTZ would change what Python receives, so plain TIMESTAMP is used
    # to keep `str(row["created_at"])` output identical across drivers.
    return "TIMESTAMP"


class Column:
    """One column in the portable schema definition."""

    def __init__(
        self,
        name: str,
        pg_type: str,
        mysql_type: Optional[str] = None,
        identity: bool = False,
        not_null: bool = False,
        default: Optional[str] = None,
    ) -> None:
        self.name = name
        self.pg_type = pg_type
        self.mysql_type = mysql_type or pg_type
        self.identity = identity
        self.not_null = not_null
        self.default = default

    def render(self) -> str:
        if self.identity:
            return _pg_identity(self.name) if IS_POSTGRES else _mysql_identity(self.name)
        col_type = self.pg_type if IS_POSTGRES else self.mysql_type
        parts = [self.name, col_type]
        if self.not_null:
            parts.append("NOT NULL")
        if self.default is not None:
            parts.append(f"DEFAULT {self.default}")
        return " ".join(parts)


def create_table(cursor, table: str, columns: Sequence[Column],
                 uniques: Sequence[Sequence[str]] = (),
                 primary_key: Optional[Sequence[str]] = None) -> None:
    """
    Emits `CREATE TABLE IF NOT EXISTS` plus any key constraints.

    `primary_key` produces a real `PRIMARY KEY` table constraint. Passing the
    key through `uniques` instead yields only a UNIQUE constraint, which is what
    this previously did for `files`, `chat_summaries` and `chat_channels` -
    so those tables had no primary key at all (pg_constraint.contype = 'u'
    rather than 'p'). That blocks foreign keys from referencing them and makes
    the schema diverge from what Prisma introspects.

    Secondary indexes are created separately by `create_index` because
    PostgreSQL has no inline `INDEX name (col)` clause.
    """
    body = ",\n                ".join(c.render() for c in columns)
    constraints: List[str] = []
    if primary_key:
        constraints.append("PRIMARY KEY (" + ", ".join(primary_key) + ")")
    for cols in uniques:
        if list(cols) == list(primary_key or []):
            continue    # already expressed as the primary key
        constraints.append("UNIQUE (" + ", ".join(cols) + ")")
    if constraints:
        body += ",\n                " + ",\n                ".join(constraints)
    if IS_POSTGRES:
        cursor.execute(
            f'CREATE TABLE IF NOT EXISTS "{table}" (\n                {body}\n            )'
        )
    else:
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS `{table}` (\n                {body}\n"
            f"            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
        )


def create_index(cursor, table: str, index: str, columns: Sequence[str]) -> None:
    """Creates a secondary index if it does not already exist."""
    if IS_POSTGRES:
        cursor.execute(f'CREATE INDEX IF NOT EXISTS "{index}" ON "{table}" '
                       f'({", ".join(chr(34) + c + chr(34) for c in columns)})')
    else:
        try:
            cursor.execute(f"CREATE INDEX `{index}` ON `{table}` "
                           f"({', '.join('`' + c + '`' for c in columns)})")
        except Exception as exc:
            # 1061 is MySQL/MariaDB error code for duplicate key/index name
            if "1061" in str(exc) or "Duplicate key name" in str(exc):
                pass
            else:
                raise


def add_column(cursor, table: str, column: str, column_def: str) -> bool:
    """
    Idempotently adds a column to an existing table.

    Returns True when the column was added. A genuine failure (missing
    privileges, wrong schema) is logged rather than swallowed, because the
    original bare `except: pass` hid real breakage until it surfaced much later
    as an opaque "Unknown column" error on every query.
    """
    try:
        if IS_POSTGRES:
            cursor.execute(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = current_schema() AND table_name = %s "
                "AND column_name = %s",
                (table, column),
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) AS present FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s "
                "AND COLUMN_NAME = %s",
                (table, column),
            )
        row = cursor.fetchone()
        if IS_POSTGRES:
            missing = row is None
        else:
            missing = int((row or {}).get("present") or 0) == 0

        if missing:
            # The column NAME must be rendered here: `column_def` is only the
            # type/constraint fragment. The previous version interpolated the
            # definition alone, producing
            #     ALTER TABLE "files" ADD COLUMN IF NOT EXISTS BOOLEAN DEFAULT FALSE
            # which is a syntax error. It was invisible while this call sat
            # behind a bare `except: pass`, so `is_important`, `sha256_hash`,
            # `size_bytes` and `updated_at` were silently never added and every
            # deliverable write later failed on those columns.
            full_def = f"{column} {column_def}".strip()
            if IS_POSTGRES:
                cursor.execute(
                    f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS {full_def}'
                )
            else:
                cursor.execute(f"ALTER TABLE `{table}` ADD COLUMN {full_def}")
            logger.info(f"[DB SCHEMA] Added column {table}.{column}")
            return True
        return False
    except Exception as exc:
        logger.warning(f"[DB SCHEMA] Could not ensure column {table}.{column}: {exc}")
        return False


# ══════════════════════════════════════════════════════════════════════
# Write helpers
# ══════════════════════════════════════════════════════════════════════
def insert_returning_id(cursor, sql: str, params: Sequence[Any],
                        id_column: str = "id") -> int:
    """
    Runs an INSERT and returns the new primary key.

    psycopg3 has no `cursor.lastrowid`, so on PostgreSQL the id comes back via
    a RETURNING clause. On MySQL the original `lastrowid` path is preserved.
    """
    if IS_POSTGRES:
        cursor.execute(f"{sql.rstrip().rstrip(';')} RETURNING {id_column}", tuple(params))
        row = cursor.fetchone()
        return int(row[id_column]) if row else 0
    cursor.execute(sql, tuple(params))
    return int(cursor.lastrowid or 0)


def upsert(cursor, table: str, values: Dict[str, Any],
           conflict_columns: Sequence[str],
           update_columns: Optional[Sequence[str]] = None,
           coalesce_columns: Sequence[str] = (),
           raw_columns: Sequence[str] = ()) -> None:
    """
    Portable INSERT ... ON CONFLICT / ON DUPLICATE KEY UPDATE.

    * `update_columns`  - overwritten with the incoming value on conflict.
    * `coalesce_columns`- overwritten only when the incoming value is not NULL,
                         so a genuine hash/size is never clobbered by a NULL.
    * `raw_columns`     - the value is a SQL expression (e.g. CURRENT_TIMESTAMP)
                         and is inlined rather than bound as a parameter.
    """
    cols = list(values.keys())
    # A raw column is inlined as a SQL expression (CURRENT_TIMESTAMP) instead of
    # being sent as a bound parameter, so it must not occupy a placeholder.
    value_tokens: List[str] = []
    params: List[Any] = []
    for c in cols:
        if c in raw_columns:
            value_tokens.append(str(values[c]))
        else:
            value_tokens.append("%s")
            params.append(values[c])
    values_list = ", ".join(value_tokens)

    if IS_POSTGRES:
        assignments = []
        for c in update_columns:
            if c in raw_columns:
                assignments.append(f"{c} = {values[c]}")
            elif c in coalesce_columns:
                assignments.append(f"{c} = COALESCE(EXCLUDED.{c}, {table}.{c})")
            else:
                assignments.append(f"{c} = EXCLUDED.{c}")
        conflict = ", ".join(conflict_columns)
        col_list = ", ".join('"' + c + '"' for c in cols)
        sql = (
            f'INSERT INTO "{table}" ({col_list}) VALUES ({values_list}) '
            f"ON CONFLICT ({conflict}) DO UPDATE SET " + ", ".join(assignments)
        )
    else:
        assignments = []
        for c in update_columns:
            if c in raw_columns:
                assignments.append(f"{c}={values[c]}")
            elif c in coalesce_columns:
                assignments.append(f"{c}=COALESCE(VALUES({c}), {c})")
            else:
                assignments.append(f"{c}=VALUES({c})")
        col_list = ", ".join("`" + c + "`" for c in cols)
        sql = (
            f"INSERT INTO `{table}` ({col_list}) VALUES ({values_list}) "
            f"ON DUPLICATE KEY UPDATE " + ", ".join(assignments)
        )
    cursor.execute(sql, tuple(params))


def insert_ignore(cursor, table: str, values: Dict[str, Any],
                  conflict_columns: Sequence[str] = ()) -> None:
    """
    Portable "insert if absent".

    MySQL used `INSERT IGNORE`; PostgreSQL has no equivalent, so an explicit
    `ON CONFLICT DO NOTHING` is used. The target columns are required on
    PostgreSQL because `DO NOTHING` cannot be used without a conflict target
    when a partial/expression index might match.
    """
    cols = list(values.keys())
    placeholders = ", ".join(["%s"] * len(cols))
    if IS_POSTGRES:
        target = ", ".join(chr(34) + c + chr(34) for c in conflict_columns)
        sql = (
            f'INSERT INTO "{table}" ({", ".join(chr(34) + c + chr(34) for c in cols)}) '
            f"VALUES ({placeholders}) ON CONFLICT ({target}) DO NOTHING"
        )
    else:
        sql = (
            f"INSERT IGNORE INTO `{table}` "
            f"({', '.join('`' + c + '`' for c in cols)}) VALUES ({placeholders})"
        )
    cursor.execute(sql, tuple(values[c] for c in cols))


def case_insensitive_like(column: str) -> str:
    """
    Returns a case-insensitive LIKE expression.

    MySQL's default collation is case-insensitive, so `LIKE` there matched
    'Pump' and 'pump'. PostgreSQL's LIKE is always case-sensitive, which would
    silently change filter behaviour, so ILIKE is used there.
    """
    return f"ILIKE %s" if IS_POSTGRES else "LIKE %s"


def substring(column: str, start: int, length: int) -> str:
    """Portable SUBSTRING."""
    if IS_POSTGRES:
        return f"SUBSTRING({column} FROM {start} FOR {length})"
    return f"SUBSTRING({column}, {start}, {length})"


def epoch_seconds(column: str) -> str:
    """
    Portable epoch-seconds conversion for a timestamp column.

    PostgreSQL's `EXTRACT(EPOCH FROM ts)` yields a numeric/Decimal, so it is
    cast to bigint to match MySQL's `UNIX_TIMESTAMP()` integer.
    """
    if IS_POSTGRES:
        return f"CAST(EXTRACT(EPOCH FROM {column}) AS BIGINT)"
    return f"UNIX_TIMESTAMP({column})"


def bool_param(value: bool) -> Any:
    """
    Adapts a Python bool for a parameterised query.

    psycopg3 maps a real bool to a PostgreSQL boolean. Passing MySQL's 0/1
    integers to a BOOLEAN column works there, so the two paths differ.
    """
    if IS_POSTGRES:
        return bool(value)
    return 1 if value else 0


def describe() -> str:
    """Human-readable description of the active database target."""
    if IS_POSTGRES:
        return f"PostgreSQL {PG_DB} @ {PG_HOST}:{PG_PORT} (user {PG_USER})"
    return f"MySQL {MYSQL_DB} @ {MYSQL_HOST}:{MYSQL_PORT} (user {MYSQL_USER})"


__all__ = [
    "DB_CONNECT_TIMEOUT",
    "DB_DRIVER",
    "IS_POSTGRES",
    "Column",
    "add_column",
    "bool_param",
    "case_insensitive_like",
    "create_index",
    "create_table",
    "describe",
    "ensure_database_exists",
    "epoch_seconds",
    "get_db_connection",
    "insert_ignore",
    "insert_returning_id",
    "substring",
    "upsert",
]
