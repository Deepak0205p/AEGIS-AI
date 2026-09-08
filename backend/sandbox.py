"""
Sandbox execution engine for Python code verification.
Prioritizes fully isolated Docker container (--network none, memory/CPU bounds).
Gracefully falls back to local sandboxed subprocess if Docker is unavailable.
Supports generated file detection for downloadable outputs and interactive stdin inputs.
"""

import os
import sys
import uuid
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

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


# File extensions considered as generated output files
GENERATED_FILE_EXTENSIONS = {
    ".csv", ".json", ".xlsx", ".xls", ".png", ".jpg", ".jpeg",
    ".svg", ".html", ".txt", ".pdf", ".xml", ".parquet",
}


def _scan_generated_files(job_dir: Path, exclude_files: set) -> list:
    """Scans job directory for files created by the script execution."""
    generated = []
    try:
        for f in job_dir.iterdir():
            if f.is_file() and f.name not in exclude_files:
                ext = f.suffix.lower()
                if ext in GENERATED_FILE_EXTENSIONS:
                    generated.append({
                        "name": f.name,
                        "path": str(f),
                        "size_bytes": f.stat().st_size,
                        "extension": ext,
                    })
    except Exception as e:
        logger.warning(f"[SANDBOX] Error scanning generated files: {e}")
    return generated


def execute_python_sandbox(code: str, job_id: str = None, stdin_input: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes Python script in an isolated sandbox.
    Supports optional stdin_input for scripts requiring user input (e.g. input()).
    Returns:
    {
        "job_id": str,
        "stdout": str,
        "stderr": str,
        "exit_code": int,
        "isolated": bool,
        "execution_time_sec": float,
        "success": bool,
        "generated_files": list,
        "requires_input": bool
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
    
    # Standardize input stream data
    input_data = stdin_input if stdin_input is not None else ""
    if input_data and not input_data.endswith("\n"):
        input_data += "\n"

    if docker_active:
        abs_path = str(job_dir.resolve())
        docker_mount_path = abs_path.replace("\\", "/")
        if len(docker_mount_path) > 1 and docker_mount_path[1] == ":":
            drive = docker_mount_path[0].lower()
            docker_mount_path = f"/{drive}" + docker_mount_path[2:]
            
        cmd = [
            "docker", "run", "--rm", "-i",
            "--network", "none",
            "--memory", SANDBOX_MEMORY_LIMIT,
            "--cpus", "1",
            "--pids-limit", "128",
            "-u", "1000:1000",
            "-v", f"{abs_path}:/task",
            "python-sandbox",
            "python", "-u", "/task/main.py"
        ]
        
        try:
            res = subprocess.run(
                cmd,
                input=input_data,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15,
            )
            stdout = res.stdout
            stderr = res.stderr
            exit_code = res.returncode
            isolated = True
        except subprocess.TimeoutExpired:
            try:
                subprocess.run(["docker", "kill", f"sandbox_{job_id}"], timeout=3,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            stderr = "Execution timed out (exceeded 15 seconds limit).\nTip: Use the STDIN input box at the bottom to provide inputs."
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
                input=input_data,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15,
                env=restricted_env,
            )
            stdout = res.stdout
            stderr = res.stderr
            exit_code = res.returncode
            isolated = False
        except subprocess.TimeoutExpired as te:
            try:
                if hasattr(te, 'cmd'):
                    import signal
                    os.kill(res.pid, signal.SIGTERM) if hasattr(res, 'pid') else None
            except Exception:
                pass
            stderr = "Execution timed out (exceeded 15 seconds limit).\nTip: Use the STDIN input box below to supply input values."
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

    # Scan for generated output files
    generated_files = _scan_generated_files(job_dir, exclude_files={"main.py"})
    if generated_files:
        logger.info(f"[SANDBOX] Generated files detected: {[f['name'] for f in generated_files]}")

    return {
        "job_id": job_id,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "isolated": isolated,
        "execution_time_sec": elapsed,
        "success": success,
        "generated_files": generated_files
    }
