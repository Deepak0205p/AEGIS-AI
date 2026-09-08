"""
Configuration module for Air-Gapped Local AI Backend.
Enforces zero external internet calls and configures Ollama inference.
"""

import os
import sys
import logging
from pathlib import Path

# Enforce strict offline air-gapped environment
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["OLLAMA_NO_USAGE_STATS"] = "1"

# Directory Structure
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent if BACKEND_DIR.name == "backend" else BACKEND_DIR
LOGS_DIR = PROJECT_ROOT / "logs"
SANDBOX_JOBS_DIR = PROJECT_ROOT / "sandbox_jobs"
GENERATED_DIR = PROJECT_ROOT / "generated"

# XAMPP MySQL Database Configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "sih_sovereign_ai")

# Ensure runtime directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
SANDBOX_JOBS_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

# Model configuration: Exact model tag from `ollama list`
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-v4-pro:4b")
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "openbmb/minicpm-v2.6:latest")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
NUM_CTX = int(os.getenv("NUM_CTX", "8192"))
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "60.0"))
SANDBOX_MEMORY_LIMIT = os.getenv("SANDBOX_MEMORY_LIMIT", "512m")

# Adaptive Thinking & RAG Configuration
THINK_ON_COMPLEX_CHAT = True
MIN_RAG_SCORE = float(os.getenv("MIN_RAG_SCORE", "0.3"))
RAG_CACHE_TTL_SECONDS = 600.0  # 10 minutes

# Universal equipment tag pattern (e.g. F-101, HEX-201, TK-1002, P-101A, MOV-104)
EQUIPMENT_TAG_REGEX = r"\b[A-Z]{1,4}[-]\d{2,5}[A-Z]?\b"

# Domain technical keywords that trigger RAG search
RAG_DOMAIN_KEYWORDS = [
    "sop", "manual", "procedure", "standard", "specification", "drawing",
    "pid", "inspection", "approval", "guideline", "policy", "shift",
    "in-charge", "asme", "oisd", "ibr", "as per", "according to",
    "kya procedure", "maintenance", "tmt", "operating limit", "setpoint",
    "loto", "ptw", "vibration", "interlock", "psv", "flare", "corrosion"
]

DETERMINISTIC_FALLBACK_TEXT = (
    "Operational parameters for this query are not indexed in active Master SOPs (OISD/API/MRPL). "
    "Manual entry or Shift In-Charge sign-off required."
)

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
def enforce_air_gap_guard():
    """
    Installs a socket-level check to block all outbound external connections.
    Only localhost/127.0.0.1 (e.g. Ollama and local backend) is permitted.
    """
    import socket
    _orig_connect = socket.socket.connect

    def _guarded_connect(self, address):
        host = address[0] if isinstance(address, tuple) and len(address) > 0 else str(address)
        allowed_hosts = ("127.0.0.1", "localhost", "::1", "0.0.0.0")
        
        # Resolve hostname safely
        if host not in allowed_hosts:
            if not (host.startswith("127.") or host == "localhost"):
                logger.critical(f"BLOCKED illegal outbound connection attempt to external host: {host}")
                raise PermissionError(
                    f"SOVEREIGNTY VIOLATION: Outbound network call to '{host}' is strictly forbidden in air-gapped mode."
                )
        return _orig_connect(self, address)

    socket.socket.connect = _guarded_connect
    logger.info("Air-gap network guard activated: External outbound network calls blocked.")

# Activate network guard
try:
    enforce_air_gap_guard()
except Exception as e:
    logger.warning(f"Could not install socket guard: {e}")
