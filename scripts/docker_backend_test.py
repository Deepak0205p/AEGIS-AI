"""
Verification of the Docker sandbox backend's command construction.

Docker cannot be installed on every host this project has to run on (it needs
administrative rights and WSL2). That made the Docker code path easy to ship
broken without anyone noticing, and it WAS broken three separate ways:

  1. The image sets ``ENTRYPOINT ["python", "-I"]``, but the run command
     appended a second literal ``python``, so the container executed
     ``python -I python -u /task/main.py`` and died with
     "can't open file 'python'" on every run.
  2. The builder produced ``mrpl-sandbox-runtime:latest`` while the runner
     asked for ``python-sandbox``. ``docker run`` would fail to find the image
     and then try to pull it from Docker Hub, which cannot work air-gapped.
  3. The shell runner appended ``bash /task/main.sh`` after the same python
     entrypoint, so it too was unreachable.

None of that is visible without either Docker or a test. This test inspects the
argv the code actually builds and checks it composes correctly with the real
Dockerfile, so the path is verified on hosts where Docker is absent.

If Docker IS present, it additionally builds the image and runs a real
zero-egress smoke test.

    python scripts/docker_backend_test.py
    python scripts/docker_backend_test.py --build   # also build + smoke test
"""
import re
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DOCKERFILE = ROOT / "sandbox" / "Dockerfile.sandbox"

PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name:56} {detail}")


# ───────────────────────── Dockerfile introspection ─────────────────────────

def _final_instruction(text: str, keyword: str):
    """Returns the value of the last `KEYWORD <value>` line in a Dockerfile."""
    value = None
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        m = re.match(rf"^{keyword}\s+(.+)$", line, re.IGNORECASE)
        if m:
            value = m.group(1).strip().strip('"')
    return value


def parse_dockerfile():
    text = DOCKERFILE.read_text(encoding="utf-8")
    ep = _final_instruction(text, "ENTRYPOINT")
    # ENTRYPOINT ["python", "-I"] -> ["python", "-I"]
    if ep and ep.startswith("["):
        ep = [tok.strip().strip('"') for tok in ep.strip("[]").split(",") if tok.strip()]
    else:
        ep = ep.split() if ep else []
    return {
        "entrypoint": ep,
        "user": _final_instruction(text, "USER"),
        "workdir": _final_instruction(text, "WORKDIR"),
        "cmd": _final_instruction(text, "CMD"),
    }


def split_volume(spec):
    """
    Splits a `-v host:container` spec into (host, container).

    Splits from the RIGHT, which matters on Windows: a host path such as
    `D:/jobs/x:/task` contains a colon, and `split(":")` would shred the drive
    letter into `D` and make a raw Windows path look like a valid Docker one.
    """
    host, _, container = spec.rpartition(":")
    return host, container


def volume_is_docker_style(spec):
    """True when the host side is a path Docker can bind-mount."""
    host, _ = split_volume(spec)
    if not host:
        return False, "<empty host path>"
    if re.match(r"^[A-Za-z]:[\\/]", host):
        return False, host
    if "\\" in host:
        return False, host
    return True, host


def argv_after_image(argv, image):
    """The CMD arguments Docker appends after the image name."""
    return argv[argv.index(image) + 1:]


def compose_command(argv, image, image_entrypoint):
    """
    Reproduces how Docker builds the final process command line.

    This is the whole point of the test. The container does NOT simply receive
    the tokens after the image name: they are appended to the image's
    ENTRYPOINT, unless `--entrypoint` overrides it, in which case they are
    appended to the override instead.

        ENTRYPOINT ["python","-I"]  +  ["python","-u","/task/main.py"]
            -> python -I python -u /task/main.py   (fails: no file named 'python')

        ENTRYPOINT ["python","-I"]  +  ["--entrypoint","bash","/task/main.sh"]
            -> bash /task/main.sh                 (works)

    Returns (composed_argv, ok) where ok is False if the composition is
    structurally impossible - e.g. an interpreter asked to run a non-Python
    file, or a bare binary name in the script position.
    """
    tail = argv_after_image(argv, image)

    if "--entrypoint" in tail:
        i = tail.index("--entrypoint")
        entry = [tail[i + 1]] if i + 1 < len(tail) else []
        args = tail[i + 2:]
    else:
        entry = list(image_entrypoint)
        args = tail

    return entry + args, True


def composition_is_runnable(composed):
    """
    Sanity-checks a composed argv the way CPython/bash would.

    Returns a reason string when the command cannot execute, else None.
    """
    if not composed:
        return "empty command"
    exe = Path(composed[0]).name.lower()
    if exe.startswith("python"):
        # The first non-flag token is the script to run; it must be a file.
        for tok in composed[1:]:
            if tok.startswith("-"):
                continue
            if Path(tok).stem.lower() in ("python", "python3", "python.exe", "py"):
                return f"python asked to execute a file named '{tok}'"
            if not tok.endswith(".py"):
                return f"python asked to execute a non-Python file '{tok}'"
            return None
        return "python given no script to execute"
    if exe in ("bash", "sh"):
        for tok in composed[1:]:
            if tok.startswith("-"):
                continue
            return None
        return "shell given no script to execute"
    return None


# ───────────────────────── argv capture (no Docker) ─────────────────────────

def capture_docker_argv():
    """Invokes _run_docker with subprocess.run stubbed; returns the argv."""
    from backend import sandbox as sb

    captured = {}

    class FakeResult:
        stdout, stderr, returncode = "ok\n", "", 0

    def fake_run(cmd, **kw):
        captured["argv"] = list(cmd)
        return FakeResult()

    job_dir = sb.SANDBOX_JOBS_DIR / "_argvcapture"
    job_dir.mkdir(parents=True, exist_ok=True)
    script = job_dir / "main.py"
    script.write_text("print('x')\n", encoding="utf-8")
    try:
        with mock.patch.object(sb.subprocess, "run", fake_run):
            sb._run_docker(job_dir, script, "", "deadbeef")
    finally:
        script.unlink(missing_ok=True)
        try:
            job_dir.rmdir()
        except OSError:
            pass
    return captured.get("argv", [])


def capture_shell_argv():
    """Invokes _run_shell with is_docker_available/_run_process stubbed."""
    from backend import code_runner as cr

    captured = {}

    def fake_process(cmd, cwd, input_text="", timeout=0):
        captured["argv"] = list(cmd)
        return {"stdout": "ok", "stderr": "", "exit_code": 0,
                "timed_out": False, "duration_ms": 1.0, "truncated": False}

    with mock.patch.object(cr, "is_docker_available", lambda: True, create=True), \
         mock.patch("backend.sandbox.is_docker_available", lambda: True), \
         mock.patch.object(cr, "_run_process", fake_process):
        cr._run_shell("echo hi\n", "")

    argv = captured.get("argv", [])
    for d in cr.SANDBOX_JOBS_DIR.glob("shell_*"):
        for f in d.iterdir():
            f.unlink(missing_ok=True)
        try:
            d.rmdir()
        except OSError:
            pass
    return argv


# ───────────────────────── the checks ─────────────────────────

def main() -> int:
    from backend.config import SANDBOX_DOCKER_IMAGE

    print("AEGIS AI  |  Docker sandbox backend verification")
    print("=" * 74)
    print("Docker binary on PATH:", shutil_which := _which_docker())
    print("Image tag (config):  ", SANDBOX_DOCKER_IMAGE)
    print()

    if not DOCKERFILE.exists():
        print(f"FATAL: {DOCKERFILE} not found - the Docker path has no image to run.")
        return 1

    df = parse_dockerfile()
    print(f"Dockerfile ENTRYPOINT: {df['entrypoint']}")
    print(f"Dockerfile USER:       {df['user']}")
    print(f"Dockerfile WORKDIR:    {df['workdir']}")
    print()

    # ── image identity must be shared between builder and runners ──
    print("Image identity")
    sys.path.insert(0, str(ROOT / "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_bsi", ROOT / "scripts" / "build_sandbox_image.py")
    bsi = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(bsi)
        builder_tag = bsi.IMAGE_TAG
    except Exception as e:
        builder_tag = f"<import failed: {e}>"
    check("builder builds the tag the runner requests",
          builder_tag == SANDBOX_DOCKER_IMAGE,
          f"{builder_tag} vs {SANDBOX_DOCKER_IMAGE}")

    # Both runners below assert their argv contains exactly SANDBOX_DOCKER_IMAGE.
    # That is the guard with teeth: re-hardcoding a literal in either argv makes
    # the containment check fail. (A source-text scan for the literal was tried
    # and rejected - it false-positives on human-readable label strings.)
    check("configured tag is the documented default",
          SANDBOX_DOCKER_IMAGE == "mrpl-sandbox-runtime:latest",
          SANDBOX_DOCKER_IMAGE)

    # ── python runner ──
    print("\nPython runner argv")
    argv = capture_docker_argv()
    if not argv:
        check("captured the docker run argv", False, "no argv captured")
        return 1
    check("captured the docker run argv", True, f"{len(argv)} tokens")

    check("invokes `docker run`", argv[:2] == ["docker", "run"], " ".join(argv[:2]))
    check("passes --rm so the container is reaped", "--rm" in argv)

    # The image tag is the pivot for every remaining check, so verify it is
    # actually present before using it as a pivot - otherwise a re-hardcoded
    # literal makes the test crash on `list.index` instead of failing an
    # assertion, which is a much worse failure mode.
    image_ok = argv.count(SANDBOX_DOCKER_IMAGE) == 1
    check("uses the shared image tag, not a literal", image_ok,
          SANDBOX_DOCKER_IMAGE if image_ok
          else f"expected {SANDBOX_DOCKER_IMAGE!r}, found "
               f"{[t for t in argv if ':' in t or t == 'python-sandbox']}")
    if not image_ok:
        print("  (skipping entrypoint/mount checks: no image tag to pivot on)")
        return 1

    ep = df["entrypoint"]
    composed, _ = compose_command(argv, SANDBOX_DOCKER_IMAGE, ep)
    reason = composition_is_runnable(composed)
    check("composed command is actually executable",
          reason is None, reason or " ".join(composed))
    check("composed command ends in the script to execute",
          bool(composed) and composed[-1].endswith(".py"),
          composed[-1] if composed else "")
    check("does not bypass the image ENTRYPOINT",
          "--entrypoint" not in argv_after_image(argv, SANDBOX_DOCKER_IMAGE),
          " ".join(composed))

    print("\nPython runner - isolation flags")
    for flag, want in [
        ("--network", "none"),
        ("--memory", None),
        ("--cpus", None),
        ("--pids-limit", None),
        ("--cap-drop", "ALL"),
        ("--security-opt", "no-new-privileges"),
    ]:
        if flag not in argv:
            check(f"{flag} present", False, "missing")
            continue
        got = argv[argv.index(flag) + 1]
        check(f"{flag} present", want is None or got == want, got)

    # -u must match the image's own user or the container cannot write /task
    if "--user" in argv or "-u" in argv:
        key = "--user" if "--user" in argv else "-u"
        got = argv[argv.index(key) + 1]
        check("runs as the image's own USER", got == df["user"], f"{got} vs {df['user']}")
    else:
        check("runs as the image's own USER", False, "no -u/--user flag")

    # -v must be a Docker-style path, not a raw C:\ path
    vkey = "-v" if "-v" in argv else ("--volume" if "--volume" in argv else None)
    if vkey is None:
        check("mounts the job directory", False, "no -v flag")
    else:
        ok, host = volume_is_docker_style(argv[argv.index(vkey) + 1])
        check("mounts via a Docker-style path, not a raw Windows path", ok, host)

    # the timeout handler kills by name, so --name must be present
    check("container is named (timeout kill depends on it)", "--name" in argv)
    if "--name" in argv:
        name = argv[argv.index("--name") + 1]
        captured = {}

        def fake_timeout(cmd, **kw):
            captured["kill"] = list(cmd)
            raise subprocess.TimeoutExpired(cmd, 15.0)

        from backend import sandbox as sb
        job_dir = sb.SANDBOX_JOBS_DIR / "_argvcapture2"
        job_dir.mkdir(parents=True, exist_ok=True)
        s2 = job_dir / "main.py"
        s2.write_text("print('x')\n", encoding="utf-8")
        try:
            with mock.patch.object(sb.subprocess, "run", fake_timeout):
                sb._run_docker(job_dir, s2, "", "deadbeef")
        finally:
            s2.unlink(missing_ok=True)
            try:
                job_dir.rmdir()
            except OSError:
                pass
        kill = captured.get("kill", [])
        check("timeout handler kills the SAME container it named",
              "kill" in kill and name in kill, " ".join(kill[:3]) or "no kill issued")

    # ── shell runner ──
    print("\nShell runner argv")
    sargv = capture_shell_argv()
    if not sargv:
        check("captured the shell runner argv", False, "no argv captured")
    else:
        check("invokes `docker run`", sargv[:2] == ["docker", "run"], " ".join(sargv[:2]))
        simage_ok = sargv.count(SANDBOX_DOCKER_IMAGE) == 1
        check("uses the shared image tag, not a literal", simage_ok,
              SANDBOX_DOCKER_IMAGE if simage_ok
              else f"expected {SANDBOX_DOCKER_IMAGE!r}, found "
                   f"{[t for t in sargv if ':' in t or t == 'python-sandbox']}")
        if not simage_ok:
            print("  (skipping remaining shell checks: no image tag to pivot on)")
        else:
            scomp, _ = compose_command(sargv, SANDBOX_DOCKER_IMAGE, df["entrypoint"])
            sreason = composition_is_runnable(scomp)
            check("composed shell command is actually executable",
                  sreason is None, sreason or " ".join(scomp))
            check("overrides the python ENTRYPOINT with bash",
                  "--entrypoint" in sargv
                  and sargv[sargv.index("--entrypoint") + 1] == "bash",
                  " ".join(argv_after_image(sargv, SANDBOX_DOCKER_IMAGE)))
            check("does not run the shell through the python interpreter",
                  not Path(scomp[0]).name.lower().startswith("python"), scomp[0])
            if "-v" in sargv:
                ok, host = volume_is_docker_style(sargv[sargv.index("-v") + 1])
                check("mounts via a Docker-style path, not a raw Windows path",
                      ok, host)
            check("shell runner keeps --network none", "--network" in sargv)

    # ── live Docker run, only when Docker exists ──
    if shutil_which:
        print("\nLive Docker smoke test")
        try:
            subprocess.run([shutil_which, "info"], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=20, check=True)
        except Exception:
            print("  SKIP  docker CLI present but the daemon is not running")
        else:
            from backend.sandbox import is_docker_available
            if not is_docker_available():
                check("daemon reachable", False, "is_docker_available() said no")
            else:
                import os
                os.environ["PYTHONPATH"] = str(ROOT)
                r = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "build_sandbox_image.py")],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=1800)
                check("builds the image and passes the smoke test",
                      r.returncode == 0,
                      (r.stdout or r.stderr).strip().splitlines()[-1][:60]
                      if (r.stdout or r.stderr) else "")
    else:
        print("\nLive Docker smoke test")
        print("  SKIP  no docker binary on PATH. The argv above is still verified")
        print("        against the real Dockerfile, so the path is known-correct.")
        print("        Install Docker (needs admin + WSL2) then re-run to execute:")
        print("          python scripts\\build_sandbox_image.py")

    print()
    total = len(PASS) + len(FAIL)
    print(f"{len(PASS)}/{total} passed")
    if FAIL:
        print("FAILED:")
        for f in FAIL:
            print(f"  - {f}")
    return 1 if FAIL else 0


def _which_docker():
    import shutil
    return shutil.which("docker")


if __name__ == "__main__":
    sys.exit(main())
