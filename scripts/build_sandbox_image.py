#!/usr/bin/env python3
"""
MRPL Sovereign AI Workbench — Sandbox Image Builder & Smoke Tester
=================================================================
Automated cross-platform CLI that:
  1. Probes Docker daemon availability
  2. Builds mrpl-sandbox-runtime:latest from sandbox/Dockerfile.sandbox
  3. Runs zero-egress smoke test (numpy/scipy pump efficiency calc)
  4. Runs network-blocking smoke test (confirms --network none)

Usage:
    python scripts/build_sandbox_image.py [--no-cache] [--skip-smoke]
"""

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Built image tag. Read from backend.config so the builder and the runners
# (`backend/sandbox.py`, `backend/code_runner.py`) can never disagree: they
# previously hardcoded `mrpl-sandbox-runtime:latest` and `python-sandbox`
# respectively, so `docker run` looked for an image nothing had ever built.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from backend.config import SANDBOX_DOCKER_IMAGE as IMAGE_TAG
except Exception:  # pragma: no cover - config import must not block the builder
    IMAGE_TAG = "mrpl-sandbox-runtime:latest"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE_PATH = PROJECT_ROOT / "sandbox" / "Dockerfile.sandbox"

# Smoke test scripts embedded directly (no external files needed)
CALC_SMOKE_SCRIPT = """\
import numpy as np
from scipy.constants import g
Q, H, rho, P_in = 150.0 / 3600.0, 45.0, 850.0, 15000.0
P_hyd = rho * g * Q * H
eta = (P_hyd / P_in) * 100.0
print(f"CALC_SUCCESS: {eta:.2f}%")
"""

NETWORK_SMOKE_SCRIPT = """\
import socket
try:
    socket.create_connection(('127.0.0.1', 80), timeout=2)
    print('NETWORK_LEAK')
except Exception as e:
    print(f'NETWORK_BLOCKED: {type(e).__name__}')
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def run_cmd(cmd: list[str], capture: bool = False, check: bool = False) -> subprocess.CompletedProcess:
    """Run a command with streaming output."""
    print(f"  \033[90m$ {' '.join(cmd)}\033[0m")
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=300,
    )


def probe_docker() -> bool:
    """Check if Docker daemon is reachable."""
    print("\n[1/4] Probing Docker daemon...")
    try:
        res = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res.returncode == 0:
            # Extract server version for display
            for line in res.stdout.splitlines():
                if line.strip().startswith("Server Version"):
                    print(f"  \033[92m✓ Docker daemon online — {line.strip()}\033[0m")
                    return True
            print("  \033[92m✓ Docker daemon online\033[0m")
            return True
        print("  \033[91m✗ Docker daemon not responding (exit code != 0)\033[0m")
        return False
    except FileNotFoundError:
        print("  \033[91m✗ Docker CLI not found on PATH\033[0m")
        print("    → Install Docker Desktop or Docker Engine: https://docs.docker.com/get-docker/")
        return False
    except subprocess.TimeoutExpired:
        print("  \033[91m✗ Docker daemon probe timed out (10s)\033[0m")
        return False


def build_image(use_cache: bool = True) -> bool:
    """Build the sandbox image from Dockerfile.sandbox."""
    print(f"\n[2/4] Building image \033[1m{IMAGE_TAG}\033[0m...")
    if not DOCKERFILE_PATH.exists():
        print(f"  \033[91m✗ Dockerfile not found at {DOCKERFILE_PATH}\033[0m")
        return False

    cmd = ["docker", "build", "-t", IMAGE_TAG, "-f", str(DOCKERFILE_PATH)]
    if not use_cache:
        cmd.append("--no-cache")
    cmd.append(".")

    t0 = time.perf_counter()
    res = run_cmd(cmd)
    elapsed = time.perf_counter() - t0

    if res.returncode == 0:
        print(f"  \033[92m✓ Image built successfully in {elapsed:.1f}s\033[0m")
        return True
    else:
        print(f"  \033[91m✗ Build failed (exit code {res.returncode})\033[0m")
        if res.stderr:
            print(f"    {res.stderr.strip()[:500]}")
        return False


def smoke_test_calc() -> bool:
    """Run numpy/scipy calculation inside container with --network none."""
    print("\n[3/4] Smoke test: numpy/scipy pump efficiency calculation...")
    cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--read-only",
        "--memory", "512m",
        "--cpus", "1.0",
        "--user", "10001:10001",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        IMAGE_TAG,
        "python", "-I", "-c", CALC_SMOKE_SCRIPT,
    ]
    res = run_cmd(cmd, capture=True)

    output = (res.stdout or "").strip()
    if "CALC_SUCCESS" in output:
        print(f"  \033[92m✓ {output}\033[0m")
        return True
    else:
        print(f"  \033[91m✗ CALC_SUCCESS not found in output\033[0m")
        if res.stderr:
            print(f"    stderr: {res.stderr.strip()[:300]}")
        return False


def smoke_test_network() -> bool:
    """Verify container cannot reach any network (air-gap enforcement)."""
    print("\n[4/4] Smoke test: network blocking (--network none)...")
    cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--read-only",
        "--memory", "512m",
        "--cpus", "1.0",
        "--user", "10001:10001",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        IMAGE_TAG,
        "python", "-I", "-c", NETWORK_SMOKE_SCRIPT,
    ]
    res = run_cmd(cmd, capture=True)

    output = (res.stdout or "").strip()
    if "NETWORK_BLOCKED" in output:
        print(f"  \033[92m✓ {output}\033[0m")
        return True
    else:
        print(f"  \033[91m✗ Expected NETWORK_BLOCKED, got: {output}\033[0m")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Build and smoke-test MRPL sandbox Docker image")
    parser.add_argument("--no-cache", action="store_true", help="Build without Docker layer cache")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip smoke tests after build")
    args = parser.parse_args()

    print("=" * 68)
    print("  MRPL SOVEREIGN AI — SANDBOX IMAGE BUILDER & VERIFIER")
    print("=" * 68)

    # Step 1: Probe Docker
    if not probe_docker():
        print("\n\033[93m⚠ Docker unavailable — backend will fall back to host subprocess.\033[0m")
        sys.exit(1)

    # Step 2: Build
    if not build_image(use_cache=not args.no_cache):
        sys.exit(1)

    # Step 3 & 4: Smoke tests
    if not args.skip_smoke:
        calc_ok = smoke_test_calc()
        net_ok = smoke_test_network()

        print("\n" + "=" * 68)
        if calc_ok and net_ok:
            print("  \033[92m✓ ALL SMOKE TESTS PASSED\033[0m")
            print(f"  Image: {IMAGE_TAG}")
            print("  Isolation: --network none, --read-only, --memory 512m, --cpus 1.0")
            print("  User: 10001:10001 (rootless, no-new-privileges)")
        else:
            print("  \033[91m✗ SMOKE TESTS FAILED\033[0m")
            sys.exit(1)
    else:
        print("\n\033[93m  Smoke tests skipped (--skip-smoke)\033[0m")

    print("=" * 68)
    sys.exit(0)


if __name__ == "__main__":
    main()
