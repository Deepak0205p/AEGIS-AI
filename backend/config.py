"""
Configuration module for Air-Gapped Local AI Backend.
Enforces zero external internet calls and configures Ollama inference.
"""

import os
import sys
import logging
from pathlib import Path

# Directory Structure
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent if BACKEND_DIR.name == "backend" else BACKEND_DIR


def _load_dotenv_file() -> None:
    """
    Loads KEY=VALUE pairs from the repo-root `.env` into os.environ.

    This MUST run before any configuration below is read. It used to live in
    `main.py`, which imports this module first -- so every value here was
    resolved before `.env` was parsed and the file had no effect on database
    credentials, model names or ports. Values already present in the real
    environment always win, so an explicit env var still overrides the file.
    """
    env_path = PROJECT_ROOT / ".env"
    if not env_path.is_file():
        return
    try:
        with open(env_path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        # Configuration continues with the real environment / defaults.
        pass


_load_dotenv_file()

# Enforce strict offline air-gapped environment
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["OLLAMA_NO_USAGE_STATS"] = "1"

LOGS_DIR = PROJECT_ROOT / "logs"
SANDBOX_JOBS_DIR = PROJECT_ROOT / "sandbox_jobs"
GENERATED_DIR = PROJECT_ROOT / "generated"

# ── Database Configuration ────────────────────────────────────────────────
# PostgreSQL is the default target. Set AEGIS_DB_DRIVER=mysql to keep using
# XAMPP MySQL/MariaDB; both dialects are supported by backend/db_dialect.py.
DB_DRIVER = os.getenv("AEGIS_DB_DRIVER", "postgres").strip().lower()
if DB_DRIVER not in ("postgres", "postgresql", "mysql", "mariadb"):
    # `logger` is configured further down this module, so this early sanity
    # check reports through the stdlib root logger instead.
    logging.getLogger("airgap_backend").warning(
        f"Unknown AEGIS_DB_DRIVER={DB_DRIVER!r}; falling back to postgres."
    )
    DB_DRIVER = "postgres"
IS_POSTGRES = DB_DRIVER.startswith("postgres")

# PostgreSQL (default)
PG_HOST = os.getenv("PGHOST", os.getenv("PG_HOST", "127.0.0.1"))
PG_PORT = int(os.getenv("PGPORT", os.getenv("PG_PORT", "5432")))
PG_USER = os.getenv("PGUSER", os.getenv("PG_USER", "postgres"))
PG_PASSWORD = os.getenv("PGPASSWORD", os.getenv("PG_PASSWORD", "postgres"))
PG_DB = os.getenv("PGDATABASE", os.getenv("PG_DB", "sih_sovereign_ai"))

# XAMPP MySQL / MariaDB (legacy fallback)
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "sih_sovereign_ai")

# Active-database label used in log lines and health output.
if IS_POSTGRES:
    DB_NAME = PG_DB
    DB_LABEL = f"PostgreSQL '{PG_DB}' on {PG_HOST}:{PG_PORT}"
else:
    DB_NAME = MYSQL_DB
    DB_LABEL = f"MySQL '{MYSQL_DB}' on {MYSQL_HOST}:{MYSQL_PORT}"

# Connect timeout in seconds. Without this the driver waits indefinitely when
# the database host is unreachable-but-not-refusing, which hangs the FastAPI
# startup and every request that touches the database.
DB_CONNECT_TIMEOUT = int(os.getenv("AEGIS_DB_CONNECT_TIMEOUT", "5"))

# Ensure runtime directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
SANDBOX_JOBS_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

# Model configuration: Exact model tag from `ollama list`
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-v4-pro:4b")
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "qwen2.5vl:3b")
OCR_MODEL_NAME = os.getenv("OCR_MODEL_NAME", "unlimited-ocr:latest")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
NUM_CTX = int(os.getenv("NUM_CTX", "8192"))
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "60.0"))
SANDBOX_MEMORY_LIMIT = os.getenv("SANDBOX_MEMORY_LIMIT", "512m")

# Sandbox container image. Single source of truth: `backend/sandbox.py` (python
# runner), `backend/code_runner.py` (shell runner) and
# `scripts/build_sandbox_image.py` (builder) all read this. They previously
# hardcoded two different names -- the runner asked for `python-sandbox` while
# the builder produced `mrpl-sandbox-runtime:latest` -- so `docker run` would
# fail with "Unable to find image" and then try to pull it from Docker Hub,
# which cannot succeed on an air-gapped host.
SANDBOX_DOCKER_IMAGE = os.getenv("SANDBOX_DOCKER_IMAGE", "mrpl-sandbox-runtime:latest")

# Adaptive Thinking & RAG Configuration
THINK_ON_COMPLEX_CHAT = True
MIN_RAG_SCORE = float(os.getenv("MIN_RAG_SCORE", "0.50"))
MAX_RAG_CHUNKS = int(os.getenv("MAX_RAG_CHUNKS", "3"))
RAG_CACHE_TTL_SECONDS = 600.0  # 10 minutes

# Agentic Multi-Step Loop Hard Limits
AGENT_MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "6"))
AGENT_MAX_TOOL_CALLS = int(os.getenv("AGENT_MAX_TOOL_CALLS", "8"))
TOOL_RETURN_MAX_CHARS = int(os.getenv("TOOL_RETURN_MAX_CHARS", "2000"))

# Final Answer Synthesis Quality & Length Contracts
FINAL_SYNTHESIS_TEMPERATURE = float(os.getenv("FINAL_SYNTHESIS_TEMPERATURE", "0.10"))
TASK_MAX_WORDS = {
    "approval_note": int(os.getenv("MAX_WORDS_APPROVAL_NOTE", "400")),
    "inspection_report": int(os.getenv("MAX_WORDS_INSPECTION_REPORT", "450")),
    "sop_summary": int(os.getenv("MAX_WORDS_SOP_SUMMARY", "350")),
    "code_findings": int(os.getenv("MAX_WORDS_CODE_FINDINGS", "300")),
    "general_deliverable": int(os.getenv("MAX_WORDS_GENERAL_DELIVERABLE", "500")),
}

# Domain Configuration (defaults for backward compatibility; overridden by active domain)
AEGIS_DOMAIN = os.getenv("AEGIS_DOMAIN", "refinery")

# Universal equipment tag pattern (e.g. F-101, HEX-201, TK-1002, P-101A, MOV-104)
# NOTE: Use get_active_equipment_regex() for domain-aware regex
EQUIPMENT_TAG_REGEX = r"\b[A-Z]{1,4}[-]\d{2,5}[A-Z]?\b"

# Domain technical keywords that trigger RAG search
# NOTE: Use get_active_rag_keywords() for domain-aware keywords
RAG_DOMAIN_KEYWORDS = [
    "sop", "manual", "procedure", "standard", "specification", "drawing",
    "pid", "inspection", "approval", "guideline", "policy", "shift",
    "in-charge", "asme", "oisd", "ibr", "as per", "according to",
    "kya procedure", "maintenance", "tmt", "operating limit", "setpoint",
    "loto", "ptw", "vibration", "interlock", "psv", "flare", "corrosion",
    "ultrasonic", "thickness", "gauging", "ndt"
]

DETERMINISTIC_FALLBACK_TEXT = (
    "Operational parameters for this query are not indexed in active Master SOPs (OISD/API/MRPL). "
    "Manual entry or Shift In-Charge sign-off required."
)


def get_active_equipment_regex() -> str:
    """Returns equipment tag regex for the active domain."""
    try:
        from backend.domains import get_equipment_tag_regex
        return get_equipment_tag_regex()
    except Exception:
        return EQUIPMENT_TAG_REGEX


def get_active_rag_keywords():
    """Returns RAG domain keywords for the active domain."""
    try:
        from backend.domains import get_rag_keywords
        return get_rag_keywords()
    except Exception:
        return RAG_DOMAIN_KEYWORDS


def get_active_fallback_text() -> str:
    """Returns deterministic fallback text for the active domain."""
    try:
        from backend.domains import get_fallback_text
        return get_fallback_text()
    except Exception:
        return DETERMINISTIC_FALLBACK_TEXT

# Generation defaults
DEFAULT_TOP_P = 0.9
DEFAULT_TOP_K = 40
DEFAULT_REPEAT_PENALTY = 1.1

# Logging Setup
logger = logging.getLogger("airgap_backend")
logger.setLevel(logging.INFO)

# Prevent duplicate handlers if reloaded
if not logger.handlers:
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setFormatter(formatter)
    c_handler.setLevel(logging.INFO)
    logger.addHandler(c_handler)
    
    # File Handler -> ./logs/backend.log
    f_handler = logging.FileHandler(LOGS_DIR / "backend.log", encoding="utf-8")
    f_handler.setFormatter(formatter)
    f_handler.setLevel(logging.INFO)
    logger.addHandler(f_handler)

# Air-Gapped Network Guard: Restrict outbound network calls
def _is_allowed_air_gap_host(host: str) -> bool:
    """
    Returns True for loopback and RFC 1918 private LAN addresses.

    Private LAN ranges are permitted on purpose: the distributed compute-node
    feature (`/api/v1/nodes/*`) registers RFC 1918 workers by design, and
    `backend.nodes.is_private_or_loopback_ip` enforces exactly that policy
    before a node is ever added. Blocking them here made LAN nodes impossible
    to reach while the API advertised them as supported.
    """
    import ipaddress
    if not host:
        return False
    h = host.strip().strip("[]").lower()
    if h in ("localhost", "0.0.0.0", "::", "::1"):
        return True
    try:
        ip = ipaddress.ip_address(h)
    except ValueError:
        # A hostname: not a literal private address, so treat it as external.
        return False
    return ip.is_loopback or ip.is_private or ip.is_unspecified


def enforce_air_gap_guard():
    """
    Installs a socket-level check that blocks outbound connections to anything
    outside loopback and RFC 1918 private LAN space.

    Guards `connect`, `connect_ex` and UDP `sendto`. The previous version only
    patched `connect`, so `connect_ex` and UDP egress were not covered.
    """
    import socket
    _orig_connect = socket.socket.connect
    _orig_connect_ex = socket.socket.connect_ex
    _orig_sendto = socket.socket.sendto

    def _check(address, what: str):
        host = address[0] if isinstance(address, tuple) and len(address) > 0 else str(address)
        if not _is_allowed_air_gap_host(host):
            logger.critical(f"BLOCKED illegal outbound {what} to external host: {host}")
            raise PermissionError(
                f"SOVEREIGNTY VIOLATION: Outbound network call to '{host}' is strictly forbidden in air-gapped mode."
            )

    def _guarded_connect(self, address):
        _check(address, "connection")
        return _orig_connect(self, address)

    def _guarded_connect_ex(self, address):
        _check(address, "connection")
        return _orig_connect_ex(self, address)

    def _guarded_sendto(self, data, *args):
        # sendto(data, address) or sendto(data, flags, address)
        address = args[-1] if args else None
        _check(address, "datagram")
        return _orig_sendto(self, data, *args)

    socket.socket.connect = _guarded_connect
    socket.socket.connect_ex = _guarded_connect_ex
    socket.socket.sendto = _guarded_sendto
    logger.info(
        "Air-gap network guard activated: outbound traffic limited to loopback "
        "and RFC 1918 private LAN."
    )

# Activate network guard. This fails CLOSED: if the guard cannot be installed the
# process must not continue while claiming to be air-gapped.
try:
    enforce_air_gap_guard()
except Exception as e:
    logger.critical(
        f"Could not install socket guard: {e}. Air-gap enforcement is NOT active."
    )
    raise
