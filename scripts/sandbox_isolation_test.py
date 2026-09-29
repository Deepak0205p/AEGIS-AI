"""
Live verification of the no-Docker sandbox isolation controls.

Proves the containment that `backend/sandbox.py` claims when Docker is
unavailable. Each case asserts a real kernel-enforced effect, not just that a
return value looks right.

  Windows Job Object : memory cap, CPU-time cap, process-count cap, and
                       kill-the-whole-tree on handle close.
  Network guard      : injected into the child interpreter; loopback and
                       RFC 1918 allowed, external blocked.
  Static screen      : dangerous imports rejected before execution.

Usage:
    python scripts/sandbox_isolation_test.py
"""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import logger  # noqa: E402
from backend.sandbox import execute_python_sandbox  # noqa: E402
from backend.sandbox_isolation import ProcessJob  # noqa: E402

MB = 1024 * 1024
PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name:52} {detail}")


def run_in_job(code, mem_mb=200, max_procs=64, timeout=40):
    """Runs `code` inside a Job Object and returns (returncode, stdout, stderr)."""
    job = ProcessJob(memory_limit_bytes=mem_mb * MB,
                     cpu_seconds=5, max_processes=max_procs)
    p = subprocess.Popen([sys.executable, "-u", "-c", code],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if job.available:
        job.assign(p)
    try:
        out, err = p.communicate(timeout=timeout)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        job.terminate()
        p.kill()
        out, err, rc = "", "", "TIMEOUT"
    job.close()
    return rc, out, err


def main() -> int:
    print("AEGIS AI  |  sandbox isolation verification (no-Docker path)")
    print("=" * 72)

    job_available = ProcessJob().available
    print(f"  Windows Job Object available: {job_available}")
    print()

    if job_available:
        print("Job Object - memory cap")
        rc, out, err = run_in_job(
            "x=bytearray(900*1024*1024)\nprint('ALLOCATED', len(x)//1024//1024,'MB')\n",
            mem_mb=200)
        check("900MB allocation killed under a 200MB cap", rc != 0, f"exit={rc}")
        rc, out, err = run_in_job(
            "x=bytearray(50*1024*1024)\nprint('OK', len(x)//1024//1024,'MB')\n",
            mem_mb=200)
        check("50MB allocation allowed under a 200MB cap", rc == 0, out.strip())

        print("\nJob Object - CPU time cap")
        t0 = time.time()
        rc, out, err = run_in_job("while True: pass\n", mem_mb=400, timeout=30)
        dt = time.time() - t0
        check("infinite loop killed by the CPU-time cap", rc != 0, f"exit={rc} in {dt:.1f}s")

        print("\nJob Object - process count cap")
        rc, out, err = run_in_job(
            "import subprocess,sys\n"
            "ps=[subprocess.Popen([sys.executable,'-c','import time;time.sleep(5)']) "
            "for _ in range(40)]\nprint('SPAWNED',len(ps))\n",
            mem_mb=400, max_procs=8, timeout=30)
        check("40 children refused with max_processes=8", rc != 0, f"exit={rc}")

        print("\nJob Object - kill-on-close reaps descendants")
        job = ProcessJob(memory_limit_bytes=400 * MB, cpu_seconds=30)
        p = subprocess.Popen(
            [sys.executable, "-u", "-c",
             "import subprocess,sys,time\n"
             "subprocess.Popen([sys.executable,'-c','import time;time.sleep(300)'])\n"
             "print('grandchild spawned')\ntime.sleep(300)\n"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        job.assign(p)
        time.sleep(2.0)
        alive_before = p.poll() is None
        job.close()          # KILL_ON_JOB_CLOSE must reap the whole tree
        time.sleep(2.0)
        check("parent alive before handle close", alive_before, "")
        check("parent terminated after handle close", p.poll() is not None, "")
    else:
        print("Job Object NOT available on this platform - "
              "process/memory/CPU limits cannot be enforced.\n")

    print("\nNetwork guard (injected into the child interpreter)")
    # Exercised through the hardened local runner directly, bypassing the static
    # screen on purpose: the point being tested is the RUNTIME guard, i.e. the
    # case where static screening has been defeated and the second layer must
    # still hold. (Through execute_python_sandbox, `import socket` is rejected
    # by the screen before the guard is ever reached.)
    from backend.sandbox import _build_child_bootstrap, _run_hardened_local
    from backend.config import SANDBOX_JOBS_DIR
    from backend.sandbox_isolation import NETWORK_GUARD_SOURCE
    import uuid

    def guarded_run(code):
        jid = uuid.uuid4().hex[:8]
        jd = SANDBOX_JOBS_DIR / jid
        jd.mkdir(parents=True, exist_ok=True)
        (jd / "_sandbox_netguard.py").write_text(NETWORK_GUARD_SOURCE, encoding="utf-8")
        sp = jd / "main.py"
        sp.write_text(_build_child_bootstrap(jd) + code, encoding="utf-8")
        try:
            return _run_hardened_local(jd, sp, "")
        finally:
            try:
                (sp).unlink()
                (jd / "_sandbox_netguard.py").unlink()
                jd.rmdir()
            except Exception:
                pass

    # _run_hardened_local returns (stdout, stderr, exit_code, controls)
    out, err, rc, _ = guarded_run(
        "import socket\n"
        "try:\n"
        "    socket.create_connection(('1.1.1.1',80),timeout=6)\n"
        "    print('LEAK')\n"
        "except PermissionError:\n"
        "    print('BLOCKED')\n"
        "except Exception as e:\n"
        "    print('OTHER', type(e).__name__)\n"
    )
    check("external egress refused by the runtime guard", "BLOCKED" in out,
          (out or err).strip()[:70])

    out, err, rc, _ = guarded_run(
        "import socket\n"
        "s=socket.socket()\n"
        "s.bind(('127.0.0.1',0))\n"
        "s.listen(1)\n"
        "print('LOOPBACK OK')\n"
    )
    check("loopback still permitted", "LOOPBACK OK" in out, (out or err).strip()[:70])

    out, err, rc, _ = guarded_run(
        "import socket\n"
        "try:\n"
        "    socket.getaddrinfo('example.com',80)\n"
        "    print('DNS LEAK')\n"
        "except PermissionError:\n"
        "    print('DNS BLOCKED')\n"
    )
    check("external DNS resolution refused", "DNS BLOCKED" in out,
          (out or err).strip()[:70])

    print("\nStatic screen (pre-execution rejection)")
    for label, code in [
        ("import subprocess", "import subprocess\nprint('x')\n"),
        ("import socket", "import socket\nprint('x')\n"),
        ("import ctypes", "import ctypes\nprint('x')\n"),
        ("eval()", "eval('1+1')\n"),
        ("open() outside job dir", "open('C:/Windows/win.ini').read()\n"),
    ]:
        r = execute_python_sandbox(code)
        check(f"rejects {label}", r["exit_code"] == 2 and not r["success"],
              r["stderr"].strip()[:70])

    print("\nBenign engineering code must still run")
    r = execute_python_sandbox(
        "import math\n"
        "rho, mu = 998.0, 1.002e-3\n"
        "Q = 0.05\n"
        "d = (4*Q/(math.pi*rho*0.5**2))**(1/3)\n"
        "print('diameter_mm', round(d*1000, 2))\n"
    )
    check("hydraulic calc executes and prints",
          r["success"] and "diameter_mm" in r["stdout"],
          r["stdout"].strip()[:60] or r["stderr"].strip()[:60])
    check("isolation level reported", r.get("isolation_level") in
          ("hardened", "restricted", "container"),
          f"level={r.get('isolation_level')}")

    print()
    total = len(PASS) + len(FAIL)
    print(f"{len(PASS)}/{total} passed")
    if FAIL:
        print("FAILED:")
        for f in FAIL:
            print(f"  - {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
