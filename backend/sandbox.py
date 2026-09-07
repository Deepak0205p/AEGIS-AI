"""
Sandbox execution engine for Python code verification.
Prioritizes fully isolated Docker container (--network none, memory/CPU bounds).
Gracefully falls back to local sandboxed subprocess if Docker is unavailable.
"""

import os
import sys
import uuid
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Tuple

from backend.config import SANDBOX_JOBS_DIR, SANDBOX_MEMORY_LIMIT, logger


def is_docker_available() -> bool:
    """Checks if Docker daemon is responsive."""
    try:
        res = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
        return res.returncode == 0
    except Exception:
        return False


def execute_python_sandbox(code: str, job_id: str = None) -> Dict[str, Any]:
    """
    Executes Python script in an isolated sandbox.
    Returns:
    {
        "job_id": str,
        "stdout": str,
        "stderr": str,
        "exit_code": int,
        "isolated": bool,
        "execution_time_sec": float,
        "success": bool
    }
    """
    if not job_id:
        job_id = uuid.uuid4().hex[:8]
        
    job_dir = SANDBOX_JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    script_path = job_dir / "main.py"
    script_path.write_text(code, encoding="utf-8")
    
    start_time = time.time()
    docker_active = is_docker_available()
    
    stdout = ""
    stderr = ""
    exit_code = -1
    isolated = False
    
    if docker_active:
        abs_path = str(job_dir.resolve())
        # Format Windows path for Docker volume mounting if running on Windows
        # e.g. C:\path -> //c/path or /c/path or normalized absolute path
        docker_mount_path = abs_path.replace("\\", "/")
        if len(docker_mount_path) > 1 and docker_mount_path[1] == ":":
            drive = docker_mount_path[0].lower()
            docker_mount_path = f"/{drive}" + docker_mount_path[2:]
            
        cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", SANDBOX_MEMORY_LIMIT,
            "--cpus", "1",
            "--pids-limit", "128",
            "-u", "1000:1000",
            "-v", f"{abs_path}:/task",
            "python-sandbox",
            "python", "/task/main.py"
        ]
        
        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20,
            )
            stdout = res.stdout
            stderr = res.stderr
            exit_code = res.returncode
            isolated = True
        except subprocess.TimeoutExpired:
            stderr = "Execution timed out (exceeded 20 seconds limit)."
            exit_code = 124
            isolated = True
        except Exception as e:
            logger.warning(f"Docker sandbox execution encountered error ({e}). Falling back to subprocess runner.")
            docker_active = False

    # Fallback to local subprocess runner if Docker is unavailable or errored
    if not docker_active:
        restricted_env = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "OLLAMA_NO_USAGE_STATS": "1",
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        
        try:
            res = subprocess.run(
                [sys.executable, "-u", str(script_path)],
                cwd=str(job_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20,
                env=restricted_env,
            )
            stdout = res.stdout
            stderr = res.stderr
            exit_code = res.returncode
            isolated = False
        except subprocess.TimeoutExpired:
            stderr = "Execution timed out (exceeded 20 seconds limit)."
            exit_code = 124
            isolated = False
        except Exception as e:
            stderr = f"Subprocess runner failure: {str(e)}"
            exit_code = 1
            isolated = False

    elapsed = round(time.time() - start_time, 3)
    success = (exit_code == 0)
    
    logger.info(
        f"[SANDBOX] job_id={job_id} exit_code={exit_code} isolated={isolated} "
        f"elapsed={elapsed}s success={success}"
    )
    if stderr:
        logger.debug(f"[SANDBOX stderr] {stderr.strip()[:300]}")

    return {
        "job_id": job_id,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "isolated": isolated,
        "execution_time_sec": elapsed,
        "success": success
    }
