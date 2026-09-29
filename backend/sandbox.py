"""
Sandboxed code execution engine.

Backends, in order of preference:

  1. **Docker** (`--network none`, memory/CPU/PID caps, non-root, read-only
     task volume) - the only true isolation boundary.
  2. **Hardened local process** (no Docker) - Windows Job Object for the whole
     process tree plus a network guard injected into the child interpreter plus
     a static AST screen. Real containment, but explicitly *not* a kernel
     firewall; see `backend.sandbox_isolation` for exactly what is and is not
     enforced.

The response always reports which controls were actually active so the UI never
claims isolation that was not applied.
"""

import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from backend.config import (
    SANDBOX_DOCKER_IMAGE,
    SANDBOX_JOBS_DIR,
    SANDBOX_MEMORY_LIMIT,
    logger,
)
from backend.sandbox_isolation import (
    NETWORK_GUARD_SOURCE,
    ProcessJob,
    parse_memory_limit,
    screen_python_ast,
)


# ══════════════════════════════════════════════════════════════════════
# Docker availability (cached)
# ══════════════════════════════════════════════════════════════════════
# `docker info` takes up to 3 s. It used to run on EVERY execution, adding that
# latency to every code run. The result is cached for a short TTL instead.
_DOCKER_CACHE: Dict[str, Any] = {"value": None, "checked_at": 0.0}
_DOCKER_TTL_SECONDS = 60.0


def is_docker_available(force_refresh: bool = False) -> bool:
    """
    Checks whether the Docker daemon is responsive.

    Cached for `_DOCKER_TTL_SECONDS` so a warm cache costs no subprocess at all.
    """
    now = time.time()
    if not force_refresh and _DOCKER_CACHE["value"] is not None:
        if now - _DOCKER_CACHE["checked_at"] < _DOCKER_TTL_SECONDS:
            return bool(_DOCKER_CACHE["value"])
    try:
        res = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        ok = res.returncode == 0
    except Exception:
        ok = False
    _DOCKER_CACHE["value"] = ok
    _DOCKER_CACHE["checked_at"] = now
    if not ok:
        logger.debug("[SANDBOX] Docker daemon not available; using the hardened "
                     "local process backend")
    return ok


# File extensions considered as generated output files
GENERATED_FILE_EXTENSIONS = {
    ".csv", ".json", ".xlsx", ".xls", ".png", ".jpg", ".jpeg",
    ".svg", ".html", ".txt", ".pdf", ".xml", ".parquet",
}

EXEC_TIMEOUT_SECONDS = 15.0
DOCKER_IMAGE = SANDBOX_DOCKER_IMAGE


def _scan_generated_files(job_dir: Path, exclude_files: set) -> list:
    """Scans the job directory for files created by the script execution."""
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


def _docker_mount_path(abs_path: str) -> str:
    """Converts a Windows host path to the form Docker expects for -v."""
    p = abs_path.replace("\\", "/")
    if len(p) > 1 and p[1] == ":":
        return "/" + p[0].lower() + p[2:]
    return p


def _run_docker(
    job_dir: Path, script_path: Path, input_data: str, job_id: str
) -> Tuple[str, str, int, Dict[str, Any]]:
    """
    Executes inside a disposable container.

    The container is explicitly NAMED. The previous version called
    `docker kill sandbox_{job_id}` on timeout, but the run command never passed
    `--name`, so the kill always failed and a timed-out container kept running.
    """
    abs_path = str(job_dir.resolve())
    container_name = f"aegis-sandbox-{job_id}"
    cmd = [
        "docker", "run", "--rm", "-i",
        "--name", container_name,
        "--network", "none",
        "--memory", SANDBOX_MEMORY_LIMIT,
        "--cpus", "1",
        "--pids-limit", "128",
        # Must match the image's own user. sandbox/Dockerfile.sandbox creates
        # UID/GID 10001 and chowns /workspace to it; running as a different UID
        # left the container unable to write generated files into /task.
        "-u", "10001:10001",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
        "-v", f"{_docker_mount_path(abs_path)}:/task",
        "-w", "/task",
        DOCKER_IMAGE,
        # NOTE: the image sets ENTRYPOINT ["python", "-I"], so these are CMD
        # arguments appended to it. Passing another literal "python" here made
        # the container execute `python -I python -u /task/main.py`, which fails
        # with "can't open file 'python'" on every single run.
        "-u", "/task/main.py",
    ]
    controls = {
        "container": True, "job_object": False, "network_blocked": True,
        "filesystem_jailed": True, "static_screen": True,
    }
    try:
        res = subprocess.run(
            cmd,
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=EXEC_TIMEOUT_SECONDS,
        )
        return res.stdout, res.stderr, res.returncode, controls
    except subprocess.TimeoutExpired:
        # The container IS named now, so this actually terminates it.
        try:
            subprocess.run(
                ["docker", "kill", container_name],
                timeout=5,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                timeout=5,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as kill_err:
            logger.warning(f"[SANDBOX] Could not kill container {container_name}: {kill_err}")
        return (
            "",
            f"Execution timed out (exceeded {int(EXEC_TIMEOUT_SECONDS)}s limit). "
            f"The container was terminated.",
            124,
            controls,
        )


def _build_child_bootstrap(job_dir: Path) -> str:
    """
    Prepended to the user script.

    Imports the network guard from the job directory before any user code runs.
    The parent's own socket monkey-patch lives in the parent process and is not
    inherited by a new interpreter, which is exactly why unguarded child code
    could reach the internet.
    """
    return (
        "import sys as _sys\n"
        f"_sys.path.insert(0, {str(job_dir)!r})\n"
        "try:\n"
        "    import _sandbox_netguard as _ng\n"
        "    _ng.install()\n"
        "except Exception:\n"
        "    pass\n"
        "del _sys\n"
        "\n"
    )


def _run_hardened_local(
    job_dir: Path, script_path: Path, input_data: str
) -> Tuple[str, str, int, Dict[str, Any]]:
    """
    Executes as a local process inside a Windows Job Object.

    Applies, in order of how much they actually contain:
      * Job Object: hard memory cap, CPU-time cap, process-count cap, and
        kill-the-whole-tree on close (so a timeout cannot orphan a child).
      * A network guard installed inside the child interpreter.
      * A minimal environment: no inherited secrets.
    """
    memory_bytes = parse_memory_limit(SANDBOX_MEMORY_LIMIT)

    # Minimal environment. Deliberately does NOT inherit the parent's
    # environment, which holds AEGIS_JWT_SECRET and the database password.
    restricted_env = {
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "COMSPEC": os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe"),
        "TEMP": str(job_dir),
        "TMP": str(job_dir),
        "HOME": str(job_dir),
        "PYTHONUNBUFFERED": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONHASHSEED": "0",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "OLLAMA_NO_USAGE_STATS": "1",
        # Block any nested interpreter from re-enabling site customization.
        "PYTHONNOUSERSITE": "1",
    }

    job = ProcessJob(
        memory_limit_bytes=memory_bytes,
        cpu_seconds=int(EXEC_TIMEOUT_SECONDS * 2),
        max_processes=64,
    )
    controls = {
        "container": False,
        "job_object": job.available,
        "network_blocked": True,     # guard injected into the child
        "filesystem_jailed": False,   # honest: a Job Object cannot restrict paths
        "static_screen": True,
    }
    if job.error:
        logger.warning(f"[SANDBOX] Job Object unavailable: {job.error}")

    proc = None
    try:
        # CREATE_NEW_PROCESS_GROUP: lets us address the tree if the Job Object
        # could not be created.
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        proc = subprocess.Popen(
            [sys.executable, "-u", str(script_path)],
            cwd=str(job_dir),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=restricted_env,
            creationflags=creationflags,
        )
        if job.available:
            job.assign(proc)
        else:
            controls["job_object"] = False

        try:
            stdout, stderr = proc.communicate(input=input_data, timeout=EXEC_TIMEOUT_SECONDS)
            return stdout, stderr, proc.returncode, controls
        except subprocess.TimeoutExpired:
            # Terminate the JOB, not just the direct child. The previous code
            # referenced `res` (unbound on the first timeout) inside a bare
            # `except: pass`, so the timeout path never killed anything and
            # grandchildren survived.
            job.terminate(exit_code=124)
            try:
                proc.kill()
            except Exception:
                pass
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except Exception:
                stdout, stderr = "", ""
            return (
                stdout,
                (stderr or "")
                + f"\nExecution timed out (exceeded {int(EXEC_TIMEOUT_SECONDS)}s limit). "
                  f"The process tree was terminated.",
                124,
                controls,
            )
    except Exception as exc:
        return "", f"Local sandbox execution failure: {exc}", 1, controls
    finally:
        # Closing the handle reaps any surviving descendants.
        job.close()
        if proc is not None:
            try:
                if proc.stdin:
                    proc.stdin.close()
            except Exception:
                pass


def execute_python_sandbox(
    code: str, job_id: str = None, stdin_input: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes a Python script in the strongest sandbox available on this host.

    Returns a dict including `isolation`, which names the controls that were
    genuinely active, plus `isolation_level` for a single-word summary.
    """
    if not job_id:
        job_id = uuid.uuid4().hex[:8]

    job_dir = SANDBOX_JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # ── Static screen ──────────────────────────────────────────────────
    allowed, reason = screen_python_ast(code)
    if not allowed:
        logger.warning(f"[SANDBOX] job_id={job_id} rejected by static screen: {reason}")
        _log_tool_call(job_id, len(code), None, 0.0, False, reason, [])
        return {
            "job_id": job_id,
            "stdout": "",
            "stderr": reason + "\n\nThe script was not executed. Remove the "
                               "restricted construct(s) and try again.",
            "exit_code": 2,
            "isolated": False,
            "isolation_level": "rejected",
            "isolation": {
                "container": False, "job_object": False,
                "network_blocked": False, "filesystem_jailed": False,
                "static_screen": True, "executed": False,
            },
            "execution_time_sec": 0.0,
            "success": False,
            "generated_files": [],
        }

    # Inject the network guard, then the user code.
    (job_dir / "_sandbox_netguard.py").write_text(
        NETWORK_GUARD_SOURCE, encoding="utf-8"
    )
    script_path = job_dir / "main.py"
    script_path.write_text(_build_child_bootstrap(job_dir) + code, encoding="utf-8")

    input_data = stdin_input if stdin_input is not None else ""
    if input_data and not input_data.endswith("\n"):
        input_data += "\n"

    start_time = time.time()
    use_docker = is_docker_available()

    if use_docker:
        try:
            stdout, stderr, exit_code, controls = _run_docker(
                job_dir, script_path, input_data, job_id
            )
        except Exception as exc:
            logger.warning(f"[SANDBOX] Docker path failed ({exc}); "
                           f"falling back to the hardened local process.")
            use_docker = False
            stdout, stderr, exit_code, controls = _run_hardened_local(
                job_dir, script_path, input_data
            )
    else:
        stdout, stderr, exit_code, controls = _run_hardened_local(
            job_dir, script_path, input_data
        )

    elapsed = round(time.time() - start_time, 3)
    success = exit_code == 0

    if controls.get("container"):
        level = "container"
    elif controls.get("job_object"):
        level = "hardened"
    else:
        level = "restricted"
    controls["level"] = level
    controls["executed"] = True
    controls["backend"] = "docker" if use_docker else "local_process"

    logger.info(
        f"[SANDBOX] job_id={job_id} exit={exit_code} level={level} "
        f"elapsed={elapsed}s success={success}"
    )
    if stderr:
        logger.debug(f"[SANDBOX stderr] {stderr.strip()[:300]}")

    generated_files = _scan_generated_files(
        job_dir, exclude_files={"main.py", "_sandbox_netguard.py"}
    )
    if generated_files:
        logger.info(f"[SANDBOX] Generated files: {[f['name'] for f in generated_files]}")

    _log_tool_call(job_id, len(code), stderr, elapsed, success, stderr, generated_files)

    return {
        "job_id": job_id,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        # Retained for compatibility: True only when a real boundary exists.
        "isolated": bool(controls.get("container")),
        "isolation_level": level,
        "isolation": controls,
        "execution_time_sec": elapsed,
        "success": success,
        "generated_files": generated_files,
    }


def _log_tool_call(job_id, code_len, stderr, elapsed, success, err, generated):
    try:
        from backend.structured_logger import log_tool_call
        log_tool_call(
            tool_name="python_sandbox",
            arguments={"job_id": job_id, "code_len": code_len,
                       "has_stdin": True},
            return_value={"stderr": (stderr or "")[:200],
                          "generated_files": len(generated)},
            elapsed_ms=elapsed * 1000.0,
            success=success,
            error=(err or None) if not success else None,
        )
    except Exception:
        pass


def sandbox_capabilities() -> Dict[str, Any]:
    """Describes what this host can actually enforce. Used by /api/sandbox/status."""
    from backend.sandbox_isolation import screen_report

    docker = is_docker_available()
    job = ProcessJob()
    job_ok = job.available
    job_error = job.error
    job.close()

    return {
        "docker_available": docker,
        "job_object_available": job_ok,
        "job_object_error": job_error,
        "static_screen": screen_report(),
        "active_backend": "docker_container" if docker else (
            "hardened_local_process" if job_ok else "restricted_local_process"
        ),
        "isolation_levels": {
            "container": "Docker: kernel-level namespace + network isolation",
            "hardened": "Windows Job Object (process tree, memory, CPU) + "
                        "injected network guard + static screen",
            "restricted": "Injected network guard + static screen only "
                          "(no Job Object on this platform)",
        },
        "not_enforced_without_docker": [
            "filesystem path confinement (a Job Object constrains processes, not paths)",
            "kernel-level network filtering (the guard is in-process)",
            "user/namespace separation",
        ],
        "memory_limit": SANDBOX_MEMORY_LIMIT,
        "timeout_seconds": EXEC_TIMEOUT_SECONDS,
        "image": DOCKER_IMAGE,
    }
