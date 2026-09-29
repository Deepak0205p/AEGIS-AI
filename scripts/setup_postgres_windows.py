r"""
One-time setup for the local PostgreSQL server on Windows.

Downloads the official PostgreSQL binaries (no installer, no admin rights, no
Docker required), creates a data cluster under `.runtime\pgdata`, starts the
server on 127.0.0.1:5432, and creates the application role and database.

Use this when Docker is unavailable. If you have Docker, prefer:

    docker compose up -d

Usage:
    python scripts/setup_postgres_windows.py
    python scripts/setup_postgres_windows.py --version 17.11-1
    python scripts/setup_postgres_windows.py --recreate-cluster
"""
import argparse
import os
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / ".runtime"
BIN = RUNTIME / "pgsql" / "pgsql" / "bin"
DATA = RUNTIME / "pgdata"
DOWNLOADS = RUNTIME / "downloads"
LOG = RUNTIME / "pg.log"

PG_VERSION = "17.11-1"
PG_MAJOR = "17"
BASE_URL = "https://get.enterprisedb.com/postgresql"

APP_ROLE = "aegis"
APP_PASSWORD = "aegis"
APP_DB = "sih_sovereign_ai"
SANDBOX_DB = "sih_sql_sandbox"
PORT = 5432


def step(msg):
    print(f"\n=== {msg} ===")


def bin_path(name):
    return str(BIN / f"{name}.exe")


def download(version):
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    zip_path = DOWNLOADS / f"pg{version}-binaries.zip"
    if zip_path.exists() and zip_path.stat().st_size > 100 * 1024 * 1024:
        print(f"  already downloaded: {zip_path.name} "
              f"({zip_path.stat().st_size / 1024 / 1024:.0f} MB)")
        return zip_path

    url = f"{BASE_URL}/postgresql-{version}-windows-x64-binaries.zip"
    print(f"  downloading {url}")
    print("  (this is ~325 MB)")
    t0 = time.time()
    with urllib.request.urlopen(url, timeout=300) as resp, open(zip_path, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                pct = 100.0 * done / total
                sys.stdout.write(f"\r  {done / 1e6:6.0f} MB  {pct:5.1f}%")
                sys.stdout.flush()
    sys.stdout.write("\n")
    print(f"  downloaded in {time.time() - t0:.1f}s")
    return zip_path


def extract(zip_path):
    print(f"  extracting to {BIN.parent}")
    t0 = time.time()
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(BIN.parent)
    print(f"  extracted in {time.time() - t0:.1f}s")


def init_cluster(recreate):
    if DATA.exists():
        if not recreate:
            print(f"  cluster already exists at {DATA}")
            return
        print(f"  --recreate-cluster: removing {DATA}")
        subprocess.run(["taskkill", "/F", "/IM", "postgres.exe"],
                       capture_output=True)
        time.sleep(3)
        import shutil
        shutil.rmtree(DATA, ignore_errors=True)
    DATA.mkdir(parents=True, exist_ok=True)

    pwfile = RUNTIME / "pwfile.tmp"
    pwfile.write_text("aegis", encoding="ascii")
    cmd = [
        bin_path("initdb"),
        "-D", str(DATA),
        "-U", "postgres",
        f"--pwfile={pwfile}",
        "--auth-local=trust",
        "--auth-host=scram-sha-256",
        "-E", "UTF8",
        "--locale=C",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    pwfile.unlink(missing_ok=True)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        raise SystemExit("initdb failed")
    print("  cluster initialised (UTF8, C locale, SCRAM auth on loopback)")


def start():
    if is_running():
        print("  already running")
        return
    # Detached launch with redirected output. A child that inherits this console
    # keeps the pipe open, so the caller appears to hang indefinitely.
    subprocess.Popen(
        [bin_path("pg_ctl"), "-D", str(DATA), "-l", str(LOG),
         "-o", f"-c listen_addresses=127.0.0.1 -c port={PORT}", "-w", "-t", "40", "start"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    for _ in range(40):
        if is_running():
            print("  server is accepting connections on 127.0.0.1:5432")
            return
        time.sleep(1)
    tail = LOG.read_text(encoding="utf-8", errors="ignore")[-1500:] if LOG.exists() else ""
    raise SystemExit(f"server did not start.\n{tail}")


def is_running():
    res = subprocess.run(
        [bin_path("pg_isready"), "-h", "127.0.0.1", "-p", str(PORT), "-q"],
        capture_output=True,
    )
    return res.returncode == 0


def psql(sql, db="postgres", user="postgres", quiet=False):
    env = dict(os.environ, PGPASSWORD="aegis")
    res = subprocess.run(
        [bin_path("psql"), "-h", "127.0.0.1", "-p", str(PORT), "-U", user,
         "-d", db, "-v", "ON_ERROR_STOP=1", "-tAc", sql],
        capture_output=True, text=True, env=env,
    )
    if res.returncode != 0 and not quiet:
        print(f"  psql error: {res.stderr.strip()[:300]}")
    return res.stdout.strip()


def provision():
    print(f"  role {APP_ROLE!r}: ", end="")
    out = psql(
        "SELECT CASE WHEN EXISTS(SELECT 1 FROM pg_roles WHERE rolname='aegis') "
        "THEN 'exists' ELSE 'created' END;"
    )
    if out != "exists":
        psql(f"CREATE ROLE {APP_ROLE} LOGIN PASSWORD '{APP_PASSWORD}';")
    print(out or "exists")

    for db in (APP_DB, SANDBOX_DB):
        exists = psql(f"SELECT 1 FROM pg_database WHERE datname='{db}';")
        if exists == "1":
            print(f"  database {db}: exists")
        else:
            psql(
                f"CREATE DATABASE {db} OWNER {APP_ROLE} ENCODING 'UTF8' "
                f"LC_COLLATE 'C' LC_CTYPE 'C' TEMPLATE template0;"
            )
            print(f"  database {db}: created")

    psql(f"GRANT ALL ON SCHEMA public TO {APP_ROLE};", db=APP_DB)
    print(f"  granted usage on {APP_DB} to {APP_ROLE}")

    ver = psql("SELECT version();")
    print(f"  {ver}")


def write_env():
    """
    Rewrites the database block in `.env`, replacing any previous one.

    Scans for an existing "# --- Database" section and drops everything from
    that marker up to the next blank-line-separated non-database section, so
    repeated runs cannot append duplicate keys.
    """
    env_path = ROOT / ".env"
    managed = {
        "AEGIS_DB_DRIVER", "PGHOST", "PGPORT", "PGUSER", "PGPASSWORD",
        "PGDATABASE", "AEGIS_DB_CONNECT_TIMEOUT", "DATABASE_URL",
    }
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []

    # ASCII-only section marker: a Unicode box-drawing marker is fragile across
    # Windows code pages when the file is re-read and rewritten.
    marker_prefix = "# --- DATABASE"
    kept: list[str] = []
    in_db_block = False
    for ln in lines:
        if ln.strip().upper().startswith(marker_prefix):
            in_db_block = True
            continue
        if in_db_block:
            key = ln.split("=", 1)[0].strip()
            if ln.strip() == "" or key in managed or ln.lstrip().startswith("#"):
                continue          # drop managed keys and their comments
            in_db_block = False    # reached the next unrelated section
        if ln.split("=", 1)[0].strip() in managed:
            continue              # drop stray duplicates elsewhere
        kept.append(ln)

    dsn = (f"postgresql://{APP_ROLE}:{APP_PASSWORD}@127.0.0.1:"
           f"{PORT}/{APP_DB}?schema=public")
    block = [
        "",
        "# --- DATABASE -------------------------------------------------------",
        "# PostgreSQL is the default. Set AEGIS_DB_DRIVER=mysql to use XAMPP.",
        "# Created by scripts/setup_postgres_windows.py (or: docker compose up -d).",
        "#",
        "# PG*          -> read by the Python backend (psycopg)",
        "# DATABASE_URL -> read by the Node tooling (prisma generate/studio/verify)",
        "AEGIS_DB_DRIVER=postgres",
        "PGHOST=127.0.0.1",
        f"PGPORT={PORT}",
        f"PGUSER={APP_ROLE}",
        f"PGPASSWORD={APP_PASSWORD}",
        f"PGDATABASE={APP_DB}",
        f"DATABASE_URL={dsn}",
        "",
        "# Fail fast instead of hanging when the database is unreachable.",
        "AEGIS_DB_CONNECT_TIMEOUT=5",
    ]
    env_path.write_text(
        "\n".join(kept).rstrip() + "\n" + "\n".join(block) + "\n", encoding="utf-8"
    )
    print(f"  updated {env_path.name} with the PostgreSQL block")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--version", default=f"{PG_VERSION}",
                    help=f"PostgreSQL binaries version (default {PG_VERSION})")
    ap.add_argument("--recreate-cluster", action="store_true",
                    help="delete and re-create the data cluster (DESTROYS DATA)")
    args = ap.parse_args()

    print("=" * 66)
    print("AEGIS AI  |  local PostgreSQL setup (no Docker, no admin required)")
    print("=" * 66)

    if not BIN.exists() or not (BIN / "postgres.exe").exists():
        step("1/5  Download PostgreSQL binaries")
        zp = download(args.version)
        step("2/5  Extract")
        extract(zp)
    else:
        print(f"\n  binaries already present at {BIN}")

    step("3/5  Initialise data cluster")
    init_cluster(args.recreate_cluster)

    step("4/5  Start server")
    start()

    step("5/5  Create role and databases")
    provision()
    write_env()

    print()
    print("=" * 66)
    print("Setup complete.")
    print()
    print("  Start the server :  start_postgres.bat")
    print("  Stop the server  :  stop_postgres.bat")
    print("  Create the schema:  python scripts\\init_db.py")
    print("  Verify           :  curl http://localhost:8000/api/health")
    print("                     (look for database.connected = true)")
    print()
    print("  If you have Docker instead, skip all of this and use:")
    print("      docker compose up -d")
    print("=" * 66)


if __name__ == "__main__":
    main()
