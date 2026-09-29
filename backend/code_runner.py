"""
Genuine multi-language execution runner for the AEGIS Canvas editors.

Design contract: every runner here either REALLY executes the submitted code or
returns an honest `UNSUPPORTED` / `ERROR` result. No path fabricates output,
rows, or exit codes. Each response carries the engine that actually ran (or the
reason it could not), so the UI can display the truth.

Engines used (auto-detected per host):

  python       backend.sandbox.execute_python_sandbox - Docker (`--network none`)
               when the daemon answers, otherwise a hardened local subprocess
               with an AST screen and a 15 s timeout.
  javascript   Local Node.js started with the permission model
               (`node --permission`), which denies fs / child_process / addon
               access unless the job directory is explicitly allowed. NOTE: the
               permission model does NOT restrict network access.
  typescript   Same Node runtime; Node >= 23 strips type annotations natively.
  sql          The configured database (PostgreSQL by default, MySQL/MariaDB
               otherwise) against a dedicated read-only sandbox schema, with a
               statement guard, row cap and server-side statement timeout.
  json         Server-side RFC 8259 parse + validation.
  shell        Docker (`--network none`) when available; otherwise a syntax-only
               check and an explicit "not executed" verdict.
  cpp / rust   Local toolchain when installed, otherwise UNSUPPORTED.
"""

import json
import os
import re
import shutil
import subprocess
import time
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.config import (
    DB_DRIVER,
    IS_POSTGRES,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
    PG_DB,
    PG_HOST,
    PG_PASSWORD,
    PG_PORT,
    PG_USER,
    SANDBOX_DOCKER_IMAGE,
    SANDBOX_JOBS_DIR,
    logger,
)

EXEC_TIMEOUT_SEC = 15.0
COMPILE_TIMEOUT_SEC = 30.0
MAX_OUTPUT_CHARS = 200_000
SQL_MAX_ROWS = 500
SQL_STATEMENT_TIMEOUT_MS = 5_000
SQL_SANDBOX_DB = "sih_sql_sandbox"

# Human label for the active engine. The SQL sandbox runs against whichever
# database the deployment is configured for.
_DB_LABEL = "PostgreSQL" if IS_POSTGRES else "XAMPP MySQL"


def _sql_connect(dbname: Optional[str] = None, connect_timeout: int = 5):
    """Opens a connection to the SQL sandbox schema on the active engine."""
    if IS_POSTGRES:
        import psycopg

        return psycopg.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname=dbname or PG_DB,
            autocommit=True,
            connect_timeout=connect_timeout,
        )
    import pymysql

    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=dbname,
        charset="utf8mb4",
        autocommit=True,
        connect_timeout=connect_timeout,
    )


def _sql_create_database(name: str) -> None:
    """Creates the sandbox database/schema if it does not exist."""
    if IS_POSTGRES:
        import psycopg

        conn = psycopg.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname="postgres",
            autocommit=True,
        )
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
                if cur.fetchone() is None:
                    cur.execute(f'CREATE DATABASE "{name}"')
        finally:
            conn.close()
        return
    import pymysql

    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{name}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        conn.close()

SUPPORTED_LANGUAGES = (
    "python", "javascript", "typescript", "sql", "json",
    "shell", "bash", "cpp", "rust", "html", "css", "yaml", "markdown",
)

_LANGUAGE_ALIASES = {
    "py": "python",
    "js": "javascript",
    "jsx": "javascript",
    "ts": "typescript",
    "tsx": "typescript",
    "node": "javascript",
    "sh": "shell",
    "bash": "shell",
    "c++": "cpp",
    "md": "markdown",
    "yml": "yaml",
    "htm": "html",
}


# ─────────────────────────────── helpers ───────────────────────────────

def _clip(text: Optional[str]) -> Tuple[str, bool]:
    if not text:
        return "", False
    if len(text) > MAX_OUTPUT_CHARS:
        return text[:MAX_OUTPUT_CHARS] + f"\n... [truncated at {MAX_OUTPUT_CHARS} characters]", True
    return text, False


def _which(name: str) -> Optional[str]:
    return shutil.which(name)


def _restricted_env() -> Dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "WINDIR": os.environ.get("WINDIR", ""),
        "TEMP": os.environ.get("TEMP", ""),
        "TMP": os.environ.get("TMP", ""),
        "HOME": os.environ.get("HOME", ""),
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "OLLAMA_NO_USAGE_STATS": "1",
    }


def _run_process(
    cmd: List[str],
    cwd: str,
    input_text: str = "",
    timeout: float = EXEC_TIMEOUT_SEC,
) -> Dict[str, Any]:
    """Runs a subprocess with a hard timeout and returns stdout/stderr/exit code."""
    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            input=input_text or "",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            env=_restricted_env(),
        )
        stdout, clipped_out = _clip(proc.stdout)
        stderr, clipped_err = _clip(proc.stderr)
        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": proc.returncode,
            "timed_out": False,
            "duration_ms": round((time.time() - start) * 1000, 2),
            "truncated": clipped_out or clipped_err,
        }
    except subprocess.TimeoutExpired as exc:
        stdout, _ = _clip(exc.stdout.decode() if isinstance(exc.stdout, bytes) else exc.stdout)
        stderr, _ = _clip(exc.stderr.decode() if isinstance(exc.stderr, bytes) else exc.stderr)
        note = f"Execution timed out after {timeout:g}s and was terminated."
        return {
            "stdout": stdout,
            "stderr": ((stderr + "\n") if stderr else "") + note,
            "exit_code": 124,
            "timed_out": True,
            "duration_ms": round((time.time() - start) * 1000, 2),
            "truncated": False,
        }
    except FileNotFoundError as exc:
        return {
            "stdout": "",
            "stderr": f"Executable not found: {exc}",
            "exit_code": 127,
            "timed_out": False,
            "duration_ms": round((time.time() - start) * 1000, 2),
            "truncated": False,
        }
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "stdout": "",
            "stderr": f"Sandbox runner failure: {exc}",
            "exit_code": 1,
            "timed_out": False,
            "duration_ms": round((time.time() - start) * 1000, 2),
            "truncated": False,
        }


def _result(
    language: str,
    engine: str,
    *,
    status: str = "SUCCESS",
    stdout: str = "",
    stderr: str = "",
    exit_code: int = 0,
    duration_ms: float = 0.0,
    isolated: bool = False,
    truncated: bool = False,
    message: str = "",
    sql: Optional[Dict[str, Any]] = None,
    executed: Optional[bool] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload = {
        "status": status,
        "language": language,
        "engine": engine,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "isolated": isolated,
        "truncated": truncated,
        "message": message,
        # Did the engine actually run? UNSUPPORTED always means "nothing ran".
        "executed": (status != "UNSUPPORTED") if executed is None else bool(executed),
    }
    if sql is not None:
        payload["sql"] = sql
    if extra:
        payload.update(extra)
    return payload


def _unsupported(language: str, engine: str, reason: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return _result(
        language,
        engine,
        status="UNSUPPORTED",
        stderr=reason,
        exit_code=-1,
        message=reason,
        extra=extra,
    )


def _normalise_language(language: str) -> str:
    lang = (language or "").strip().lower()
    return _LANGUAGE_ALIASES.get(lang, lang)


# ─────────────────────────────── python ───────────────────────────────

def _run_python(code: str, stdin_input: Optional[str]) -> Dict[str, Any]:
    from backend.sandbox import execute_python_sandbox, is_docker_available

    result = execute_python_sandbox(code, stdin_input=stdin_input)
    stdout, clipped_out = _clip(result.get("stdout"))
    stderr, clipped_err = _clip(result.get("stderr"))
    # Describe the backend that actually ran, using the level the sandbox
    # reported. This used to be a hardcoded pair of strings, one of which
    # ("hardened local subprocess") no longer matched any real backend name.
    level = result.get("isolation_level") or "unknown"
    engine = f"python-sandbox ({level} isolation)"
    status = "SUCCESS" if result.get("success") else "ERROR"
    message = (
        f"Python executed in {result.get('execution_time_sec', 0)}s "
        f"(exit code {result.get('exit_code')})."
    )
    return _result(
        "python",
        f"{engine} - Docker available: {is_docker_available()}",
        status=status,
        stdout=stdout,
        stderr=stderr,
        exit_code=int(result.get("exit_code", -1)),
        duration_ms=round(float(result.get("execution_time_sec", 0.0)) * 1000, 2),
        isolated=bool(result.get("isolated")),
        truncated=clipped_out or clipped_err,
        message=message,
        extra={"generated_files": result.get("generated_files", [])},
    )


# ────────────────────── javascript / typescript ──────────────────────

def _scan_job_outputs(job_dir: Path, exclude: set) -> List[Dict[str, Any]]:
    """Lists files a script produced inside its own (write-allowed) job directory."""
    produced: List[Dict[str, Any]] = []
    try:
        for item in job_dir.iterdir():
            if item.is_file() and item.name not in exclude:
                produced.append({
                    "name": item.name,
                    "path": str(item),
                    "size_bytes": item.stat().st_size,
                })
    except Exception as exc:
        logger.debug(f"[CODE RUNNER] output scan failed: {exc}")
    return produced


def _node_permission_supported(node: str) -> bool:
    try:
        probe = subprocess.run(
            [node, "--permission", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        return probe.returncode == 0
    except Exception:
        return False


def _node_version(node: str) -> str:
    try:
        probe = subprocess.run([node, "--version"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10)
        return (probe.stdout or "").strip() or "unknown"
    except Exception:
        return "unknown"


def _run_node(code: str, language: str, stdin_input: Optional[str]) -> Dict[str, Any]:
    node = _which("node")
    if not node:
        return _unsupported(
            language,
            "Node.js not found on PATH",
            "JavaScript/TypeScript execution requires a local Node.js runtime, which is not installed on this host.",
        )

    job_id = uuid.uuid4().hex[:8]
    job_dir = SANDBOX_JOBS_DIR / f"code_{job_id}"
    job_dir.mkdir(parents=True, exist_ok=True)
    script_path = job_dir / ("main.ts" if language == "typescript" else "main.js")
    script_path.write_text(code, encoding="utf-8")

    permission_ok = _node_permission_supported(node)
    cmd = [node]
    if permission_ok:
        # Permission model: no fs / net / child_process unless explicitly allowed.
        # The job directory is allowed so scripts may read/write their own outputs.
        cmd += ["--allow-fs-read", str(job_dir), "--allow-fs-write", str(job_dir)]
        cmd.append("--permission")
    cmd.append(str(script_path))

    proc = _run_process(cmd, cwd=str(job_dir), input_text=(stdin_input or ""), timeout=EXEC_TIMEOUT_SEC)

    version = _node_version(node)
    if permission_ok:
        engine = f"Node.js {version} (permission sandbox: filesystem/network restricted to the job dir)"
    else:
        engine = f"Node.js {version} (NO permission sandbox available on this runtime - treat output as untrusted)"

    status = "SUCCESS" if proc["exit_code"] == 0 else ("UNSUPPORTED" if proc["exit_code"] == 127 else "ERROR")
    message = (
        f"{language} executed in {proc['duration_ms']:.0f} ms (exit code {proc['exit_code']})."
        if proc["exit_code"] != 127
        else proc["stderr"]
    )
    return _result(
        language,
        engine,
        status=status,
        stdout=proc["stdout"],
        stderr=proc["stderr"],
        exit_code=proc["exit_code"],
        duration_ms=proc["duration_ms"],
        isolated=permission_ok,
        truncated=proc["truncated"],
        message=message,
        extra={"generated_files": _scan_job_outputs(job_dir, exclude={script_path.name})},
    )


# ───────────────────────────────── sql ─────────────────────────────────

SQL_ALLOWED_START = {"SELECT", "WITH", "SHOW", "EXPLAIN", "DESCRIBE", "DESC"}
SQL_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|RENAME|GRANT|REVOKE|CALL|"
    r"SET|LOCK|UNLOCK|LOAD_FILE|OUTFILE|DUMPFILE|SLEEP|BENCHMARK|HANDLER|PREPARE|EXECUTE)\b",
    re.IGNORECASE,
)

_SQL_SANDBOX_SEED_UNITS = [
    ("Unit-001", "Atmospheric Distillation Unit (CDU-1)", "CDU", 365.20, 1.840, 310.50, True),
    ("Unit-002", "Vacuum Distillation Column (VDU-1)", "VDU", 410.00, 0.080, 145.20, True),
    ("Unit-003", "Fluidized Catalytic Cracker (FCCU-2)", "FCCU", 525.00, 2.450, 98.75, True),
    ("Unit-004", "Diesel Hydrotreating Unit (DHT-3)", "DHT", 340.50, 45.000, 122.00, True),
    ("Unit-005", "Hydrocracker Heavy Unit (HCU-1)", "HCU", 380.00, 142.000, 110.40, True),
    ("Unit-006", "Crude Distiller Train 2 (CDU-2) [DECOMMISSIONED]", "CDU", 0.00, 0.000, 0.00, False),
]

# `is_active` is a genuine BOOLEAN on PostgreSQL and TINYINT(1) on MySQL.
# Sending Python ints 0/1 to a PostgreSQL boolean fails with
# "column is of type boolean but expression is of type smallint", so the seed
# values are converted per engine at insert time.
_SQL_SANDBOX_SEED_UNITS_MYSQL = [
    tuple(1 if v is True else 0 if v is False else v for v in row)
    for row in _SQL_SANDBOX_SEED_UNITS
]

_SQL_SANDBOX_SEED_READINGS = [
    ("Unit-001", "2026-09-24 06:00:00", 0.00, 20.80, 0.0),
    ("Unit-002", "2026-09-24 06:00:00", 0.00, 20.90, 0.0),
    ("Unit-003", "2026-09-24 06:00:00", 0.00, 20.80, 0.0),
    ("Unit-004", "2026-09-24 06:00:00", 0.00, 20.80, 0.0),
    ("Unit-005", "2026-09-24 06:00:00", 0.00, 20.80, 0.0),
    ("Unit-006", "2026-09-24 06:00:00", 0.00, 20.80, 0.0),
]


def _strip_sql_noise(sql: str) -> str:
    """Removes comments and string literals so keyword screening is not fooled."""
    cleaned = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    cleaned = re.sub(r"--[^\n]*", " ", cleaned)
    cleaned = re.sub(r"#[^\n]*", " ", cleaned)
    cleaned = re.sub(r"'(?:''|[^'])*'", "''", cleaned)
    cleaned = re.sub(r'"(?:""|[^"])*"', '""', cleaned)
    return cleaned.strip()


def _screen_sql(sql: str) -> Tuple[bool, str]:
    normalised = _strip_sql_noise(sql)
    if not normalised:
        return False, "The statement is empty."
    without_trailing = normalised.rstrip().rstrip(";").rstrip()
    if ";" in without_trailing:
        return False, "Only a single statement may be executed per run (multi-statement input rejected)."
    first_token = re.match(r"[A-Za-z]+", without_trailing)
    first_word = (first_token.group(0).upper() if first_token else "")
    if first_word not in SQL_ALLOWED_START:
        return False, (
            f"Read-only sandbox: '{first_word or 'statement'}' is not permitted. "
            "Allowed statement types: SELECT, WITH, SHOW, EXPLAIN, DESCRIBE."
        )
    forbidden = SQL_FORBIDDEN.search(without_trailing)
    if forbidden:
        return False, f"Read-only sandbox: keyword '{forbidden.group(0).upper()}' is not permitted."
    return True, ""


def _ensure_sql_sandbox() -> None:
    """Creates the read-only sandbox schema on first use (idempotent)."""
    _sql_create_database(SQL_SANDBOX_DB)

    conn = _sql_connect(SQL_SANDBOX_DB)
    try:
        with conn.cursor() as cur:
            if IS_POSTGRES:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS refinery_process_units (
                        unit_id VARCHAR(16) PRIMARY KEY,
                        unit_name VARCHAR(128) NOT NULL,
                        unit_type VARCHAR(32) NOT NULL,
                        operating_temp_c DECIMAL(8,2) NULL,
                        pressure_bar DECIMAL(8,3) NULL,
                        throughput_kbpd DECIMAL(8,2) NULL,
                        is_active BOOLEAN NOT NULL DEFAULT TRUE
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS oisd_atmospheric_readings (
                        id INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                        unit_id VARCHAR(16) NOT NULL,
                        reading_ts TIMESTAMP NOT NULL,
                        combustible_lel_pct DECIMAL(6,2) NULL,
                        oxygen_vol_pct DECIMAL(6,2) NULL,
                        h2s_toxic_ppm DECIMAL(8,2) NULL,
                        UNIQUE (unit_id, reading_ts)
                    )
                """)
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_reading_unit "
                    "ON oisd_atmospheric_readings (unit_id)"
                )
                units_sql = (
                    "INSERT INTO refinery_process_units "
                    "(unit_id, unit_name, unit_type, operating_temp_c, "
                    "pressure_bar, throughput_kbpd, is_active) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s) "
                    "ON CONFLICT (unit_id) DO NOTHING"
                )
                readings_sql = (
                    "INSERT INTO oisd_atmospheric_readings "
                    "(unit_id, reading_ts, combustible_lel_pct, "
                    "oxygen_vol_pct, h2s_toxic_ppm) "
                    "VALUES (%s, %s, %s, %s, %s) "
                    "ON CONFLICT (unit_id, reading_ts) DO NOTHING"
                )
            else:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS refinery_process_units (
                        unit_id VARCHAR(16) PRIMARY KEY,
                        unit_name VARCHAR(128) NOT NULL,
                        unit_type VARCHAR(32) NOT NULL,
                        operating_temp_c DECIMAL(8,2) NULL,
                        pressure_bar DECIMAL(8,3) NULL,
                        throughput_kbpd DECIMAL(8,2) NULL,
                        is_active TINYINT(1) NOT NULL DEFAULT 1
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS oisd_atmospheric_readings (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        unit_id VARCHAR(16) NOT NULL,
                        reading_ts DATETIME NOT NULL,
                        combustible_lel_pct DECIMAL(6,2) NULL,
                        oxygen_vol_pct DECIMAL(6,2) NULL,
                        h2s_toxic_ppm DECIMAL(8,2) NULL,
                        UNIQUE KEY uq_reading (unit_id, reading_ts),
                        KEY idx_reading_unit (unit_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                units_sql = (
                    "INSERT IGNORE INTO refinery_process_units "
                    "(unit_id, unit_name, unit_type, operating_temp_c, "
                    "pressure_bar, throughput_kbpd, is_active) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                )
                readings_sql = (
                    "INSERT IGNORE INTO oisd_atmospheric_readings "
                    "(unit_id, reading_ts, combustible_lel_pct, "
                    "oxygen_vol_pct, h2s_toxic_ppm) "
                    "VALUES (%s, %s, %s, %s, %s)"
                )
            seed_units = (
                _SQL_SANDBOX_SEED_UNITS
                if IS_POSTGRES
                else _SQL_SANDBOX_SEED_UNITS_MYSQL
            )
            cur.executemany(units_sql, seed_units)
            cur.executemany(readings_sql, _SQL_SANDBOX_SEED_READINGS)
    finally:
        conn.close()


def _db_server_version() -> str:
    """Returns the active database server version, or 'unknown'."""
    try:
        conn = _sql_connect(SQL_SANDBOX_DB, connect_timeout=3)
        try:
            with conn.cursor() as cur:
                # MySQL/MariaDB use VERSION(); PostgreSQL uses version().
                cur.execute(
                    "SELECT version()" if IS_POSTGRES else "SELECT VERSION()"
                )
                row = cur.fetchone()
        finally:
            conn.close()
        if not row:
            return "unknown"
        value = row[0] if not isinstance(row, dict) else list(row.values())[0]
        return str(value).split("-")[0]
    except Exception:
        return "unknown"


# Retained for backwards compatibility with existing call sites.
_mysql_server_version = _db_server_version


def _json_safe(value: Any) -> Any:
    from datetime import date, datetime, time as dt_time

    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, (date, dt_time)):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return f"0x{bytes(value).hex()}"
    return value


def _run_sql(sql: str) -> Dict[str, Any]:
    allowed, reason = _screen_sql(sql)
    if not allowed:
        return _result(
            "sql",
            f"{_DB_LABEL} read-only sandbox (`{SQL_SANDBOX_DB}`)",
            status="ERROR",
            stderr=reason,
            exit_code=2,
            message=reason,
            executed=False,
        )

    try:
        _ensure_sql_sandbox()
    except Exception as exc:
        return _result(
            "sql",
            f"{_DB_LABEL} read-only sandbox (`{SQL_SANDBOX_DB}`)",
            status="ERROR",
            stderr=f"Could not prepare the SQL sandbox schema: {exc}",
            exit_code=1,
            message="SQL sandbox schema is unavailable.",
        )

    start = time.time()
    conn = None
    try:
        conn = _sql_connect(SQL_SANDBOX_DB)
        with conn.cursor() as cur:
            # Statement timeout is spelled differently per engine: PostgreSQL
            # uses statement_timeout, MySQL max_execution_time and MariaDB
            # max_statement_time.
            if IS_POSTGRES:
                timeout_stmts = ("SET SESSION statement_timeout = %s",)
            else:
                timeout_stmts = (
                    "SET SESSION max_execution_time = %s",
                    "SET SESSION max_statement_time = %s",
                )
            for timeout_stmt in timeout_stmts:
                try:
                    cur.execute(timeout_stmt, (SQL_STATEMENT_TIMEOUT_MS,))
                    break
                except Exception:
                    continue
            cur.execute(sql)
            columns = [d[0] for d in cur.description] if cur.description else []
            raw_rows = cur.fetchmany(SQL_MAX_ROWS + 1)

        truncated = len(raw_rows) > SQL_MAX_ROWS
        rows = [[_json_safe(cell) for cell in row] for row in raw_rows[:SQL_MAX_ROWS]]
        duration = round((time.time() - start) * 1000, 2)
        message = f"{len(rows)} row(s) returned in {duration:.1f} ms"
        if truncated:
            message += f" (capped at {SQL_MAX_ROWS} rows)"

        return _result(
            "sql",
            f"{_DB_LABEL} {_db_server_version()} - read-only sandbox schema `{SQL_SANDBOX_DB}`",
            status="SUCCESS",
            stdout=message,
            exit_code=0,
            duration_ms=duration,
            isolated=True,
            truncated=truncated,
            message=message,
            sql={
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "truncated": truncated,
                "sandbox_schema": SQL_SANDBOX_DB,
            },
        )
    except Exception as exc:
        duration = round((time.time() - start) * 1000, 2)
        return _result(
            "sql",
            f"{_DB_LABEL} {_db_server_version()} - read-only sandbox schema `{SQL_SANDBOX_DB}`",
            status="ERROR",
            stderr=str(exc),
            exit_code=1,
            duration_ms=duration,
            isolated=True,
            message=f"Query failed: {exc}",
        )
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


# ──────────────────────────────── json ────────────────────────────────

def _run_json(code: str) -> Dict[str, Any]:
    start = time.time()
    try:
        parsed = json.loads(code)
    except json.JSONDecodeError as exc:
        duration = round((time.time() - start) * 1000, 2)
        detail = f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        return _result(
            "json",
            "Server-side RFC 8259 parser (Python json)",
            status="ERROR",
            stderr=detail,
            exit_code=1,
            duration_ms=duration,
            isolated=True,
            message=detail,
        )

    duration = round((time.time() - start) * 1000, 2)
    if isinstance(parsed, dict):
        structure = f"object with {len(parsed)} top-level key(s)"
    elif isinstance(parsed, list):
        structure = f"array with {len(parsed)} item(s)"
    else:
        structure = type(parsed).__name__
    message = f"Valid JSON — {structure}."
    return _result(
        "json",
        "Server-side RFC 8259 parser (Python json)",
        status="SUCCESS",
        stdout=message,
        exit_code=0,
        duration_ms=duration,
        isolated=True,
        message=message,
    )


# ─────────────────────────────── shell ───────────────────────────────

def _run_shell(code: str, stdin_input: Optional[str]) -> Dict[str, Any]:
    from backend.sandbox import is_docker_available

    if is_docker_available():
        job_id = uuid.uuid4().hex[:8]
        job_dir = SANDBOX_JOBS_DIR / f"shell_{job_id}"
        job_dir.mkdir(parents=True, exist_ok=True)
        script_path = job_dir / "main.sh"
        script_path.write_text(code, encoding="utf-8")

        abs_path = str(job_dir.resolve())
        from backend.sandbox import _docker_mount_path
        mount_path = _docker_mount_path(abs_path)

        proc = _run_process(
            [
                "docker", "run", "--rm", "-i",
                "--network", "none",
                "--memory", "512m",
                "--cpus", "1",
                "--pids-limit", "128",
                "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges",
                # Use the Docker-style path. `abs_path` was passed here even
                # though the conversion to `mount_path` was computed two lines
                # above and then left unused.
                "-v", f"{mount_path}:/task",
                "-w", "/task",
                SANDBOX_DOCKER_IMAGE,
                # The image's ENTRYPOINT is ["python", "-I"], so a bare
                # "bash ..." was appended to it and the container tried to run
                # `python -I bash /task/main.sh`. --entrypoint REPLACES the
                # image entrypoint instead of extending it.
                "--entrypoint", "bash",
                "/task/main.sh",
            ],
            cwd=str(job_dir),
            input_text=(stdin_input or ""),
            timeout=EXEC_TIMEOUT_SEC,
        )
        return _result(
            "shell",
            "Docker bash sandbox (--network none, 512m, 1 cpu)",
            status="SUCCESS" if proc["exit_code"] == 0 else "ERROR",
            stdout=proc["stdout"],
            stderr=proc["stderr"],
            exit_code=proc["exit_code"],
            duration_ms=proc["duration_ms"],
            isolated=True,
            truncated=proc["truncated"],
            message=f"Shell executed in the Docker sandbox (exit code {proc['exit_code']}).",
        )

    # No Docker: a syntax check is honest, execution is not silently faked.
    shell = _which("bash") or _which("sh")
    if not shell:
        return _unsupported(
            "shell",
            "Docker sandbox unavailable; no POSIX shell on PATH",
            "Shell execution needs the Docker sandbox (not running) or a local bash/sh. Nothing was executed.",
        )

    job_id = uuid.uuid4().hex[:8]
    job_dir = SANDBOX_JOBS_DIR / f"shell_{job_id}"
    job_dir.mkdir(parents=True, exist_ok=True)
    script_path = job_dir / "main.sh"
    script_path.write_text(code, encoding="utf-8")

    check = _run_process([shell, "-n", str(script_path)], cwd=str(job_dir), timeout=10.0)
    syntax_ok = check["exit_code"] == 0
    detail = (
        "Syntax check passed (`bash -n`), but the script was NOT executed."
        if syntax_ok
        else f"Syntax check failed:\n{check['stderr'] or check['stdout']}"
    )
    return _result(
        "shell",
        f"Syntax check only ({Path(shell).name}) — Docker sandbox unavailable, so the script was not executed",
        status="UNSUPPORTED",
        stdout=detail,
        stderr="" if syntax_ok else check["stderr"],
        exit_code=0 if syntax_ok else 2,
        duration_ms=check["duration_ms"],
        isolated=False,
        message=detail,
        extra={"executed": False, "syntax_valid": syntax_ok},
    )


# ─────────────────────────── cpp / rust ───────────────────────────

def _run_compiled(code: str, language: str, stdin_input: Optional[str]) -> Dict[str, Any]:
    if language == "cpp":
        compiler = _which("g++") or _which("clang++")
        compiler_name = "g++" if _which("g++") else ("clang++" if _which("clang++") else None)
        source_name, compile_cmd_tpl = "main.cpp", None
    else:
        compiler = _which("rustc")
        compiler_name = "rustc"
        source_name = "main.rs"

    if not compiler:
        wanted = "g++/clang++" if language == "cpp" else "rustc"
        return _unsupported(
            language,
            f"No {wanted} toolchain on PATH",
            f"{language} execution needs a local {wanted} compiler, which is not installed on this host. Nothing was compiled or run.",
        )

    job_id = uuid.uuid4().hex[:8]
    job_dir = SANDBOX_JOBS_DIR / f"{language}_{job_id}"
    job_dir.mkdir(parents=True, exist_ok=True)
    source_path = job_dir / source_name
    source_path.write_text(code, encoding="utf-8")
    binary_path = job_dir / ("main.exe" if os.name == "nt" else "main")

    if language == "cpp":
        compile_cmd = [compiler, "-std=c++17", "-O1", str(source_path), "-o", str(binary_path)]
    else:
        compile_cmd = [compiler, "-O", "-o", str(binary_path), str(source_path)]

    compile_proc = _run_process(compile_cmd, cwd=str(job_dir), timeout=COMPILE_TIMEOUT_SEC)
    if compile_proc["exit_code"] != 0:
        return _result(
            language,
            f"{compiler_name} (local toolchain)",
            status="ERROR",
            stdout=compile_proc["stdout"],
            stderr=compile_proc["stderr"] or "Compilation failed without diagnostics.",
            exit_code=compile_proc["exit_code"],
            duration_ms=compile_proc["duration_ms"],
            isolated=False,
            message="Compilation failed — the program was not executed.",
        )

    run_proc = _run_process([str(binary_path)], cwd=str(job_dir), input_text=(stdin_input or ""), timeout=EXEC_TIMEOUT_SEC)
    return _result(
        language,
        f"{compiler_name} (local toolchain, no container isolation)",
        status="SUCCESS" if run_proc["exit_code"] == 0 else "ERROR",
        stdout=run_proc["stdout"],
        stderr=run_proc["stderr"],
        exit_code=run_proc["exit_code"],
        duration_ms=run_proc["duration_ms"],
        isolated=False,
        truncated=run_proc["truncated"],
        message=f"Compiled and executed in {run_proc['duration_ms']:.0f} ms (exit code {run_proc['exit_code']}).",
    )


# ─────────────────────────────── dispatch ───────────────────────────────

def run_code(
    language: str,
    code: str,
    stdin_input: Optional[str] = None,
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """Executes (or honestly refuses to execute) the submitted code."""
    lang = _normalise_language(language)

    if lang not in SUPPORTED_LANGUAGES:
        return _unsupported(
            lang or "unknown",
            "no runner",
            f"Language '{language}' has no runner on this system. Supported: {', '.join(SUPPORTED_LANGUAGES)}.",
        )

    if code is None or not str(code).strip():
        return _result(
            lang, "no runner", status="ERROR", stderr="Nothing to execute: the editor buffer is empty.",
            exit_code=2, message="Nothing to execute: the editor buffer is empty.", executed=False,
        )

    code = str(code)

    try:
        if lang == "python":
            return _run_python(code, stdin_input)
        if lang in ("javascript", "typescript"):
            return _run_node(code, lang, stdin_input)
        if lang == "sql":
            return _run_sql(code)
        if lang == "json":
            return _run_json(code)
        if lang == "shell":
            return _run_shell(code, stdin_input)
        if lang in ("cpp", "rust"):
            return _run_compiled(code, lang, stdin_input)
    except Exception as exc:  # pragma: no cover - defensive, never fabricate
        logger.error(f"[CODE RUNNER] unexpected failure for {lang}: {exc}")
        return _result(
            lang, "runner error", status="ERROR", stderr=f"Runner failure: {exc}",
            exit_code=1, message=f"Runner failure: {exc}",
        )

    return _unsupported(
        lang,
        f"no dedicated runner for {lang}",
        f"'{lang}' has no server-side runner (it is a markup, style or documentation format). Nothing was executed.",
    )


def runner_availability() -> Dict[str, Any]:
    """Reports which runners can actually execute on this host right now."""
    from backend.sandbox import is_docker_available

    docker_on = is_docker_available()
    node = _which("node")
    permission_ok = _node_permission_supported(node) if node else False
    try:
        probe = _sql_connect(SQL_SANDBOX_DB, connect_timeout=3)
        probe.close()
        sql_ok = True
    except Exception:
        sql_ok = False

    # What the python runner actually enforces on this host. A Job Object gives
    # real memory/CPU/process limits, so reporting `isolated: False` whenever
    # Docker is absent understated the controls that are genuinely active.
    from backend.sandbox import ProcessJob
    job = ProcessJob()
    job_ok = job.available
    job_err = job.error
    job.close()
    if docker_on:
        py_engine, py_isolated, py_level = "Docker sandbox (--network none)", True, "container"
    elif job_ok:
        py_engine = "hardened local process (Job Object + network guard + AST screen)"
        py_isolated, py_level = True, "hardened"
    else:
        py_engine = "restricted local process (network guard + AST screen)"
        py_isolated, py_level = False, "restricted"

    return {
        "python": {
            "supported": True,
            "engine": py_engine,
            "isolated": py_isolated,
            "isolation_level": py_level,
        },
        "javascript": {
            "supported": bool(node),
            "engine": f"Node.js {_node_version(node)}" if node else "Node.js not installed",
            "isolated": permission_ok,
        },
        "typescript": {
            "supported": bool(node),
            "engine": f"Node.js {_node_version(node)} (native type stripping)" if node else "Node.js not installed",
            "isolated": permission_ok,
        },
        "sql": {
            "supported": sql_ok,
            "engine": f"{_DB_LABEL} read-only sandbox (`{SQL_SANDBOX_DB}`)" if sql_ok else f"{_DB_LABEL} unreachable",
            "isolated": sql_ok,
        },
        "json": {"supported": True, "engine": "RFC 8259 parser", "isolated": True},
        "shell": {
            "supported": docker_on,
            "engine": "Docker bash sandbox" if docker_on else "syntax check only (Docker unavailable)",
            "isolated": docker_on,
        },
        "cpp": {
            "supported": bool(_which("g++") or _which("clang++")),
            "engine": "local g++/clang++" if (_which("g++") or _which("clang++")) else "no C++ compiler installed",
            "isolated": False,
        },
        "rust": {
            "supported": bool(_which("rustc")),
            "engine": "local rustc" if _which("rustc") else "no Rust toolchain installed",
            "isolated": False,
        },
        # Metadata lives under a reserved key so that every other value in this
        # map is a per-language record. A bare `docker_available: <bool>` used to
        # sit alongside the language dicts, which broke any client that iterated
        # the map expecting {supported, engine, isolated}.
        "_meta": {
            "docker_available": docker_on,
            "job_object_available": job_ok,
            "job_object_error": job_err,
        },
    }