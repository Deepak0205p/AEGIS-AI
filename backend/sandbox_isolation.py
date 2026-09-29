"""
Process isolation primitives for the no-Docker execution path.

Docker remains the preferred backend (it gives a true `--network none`
filesystem/namespace boundary). When the Docker daemon is unavailable, this
module provides the strongest containment that is achievable on the host
**without administrator rights or virtualization**:

  1. **Windows Job Objects** (via ctypes, no dependencies)
     - `KILL_ON_JOB_CLOSE`   - closing the job handle kills the process *and
                              every descendant*, so a timeout can never leave
                              an orphan child running, and a child cannot
                              outlive its parent.
     - `JOB_MEMORY`          - hard cap on total memory for the whole tree.
     - `ACTIVE_PROCESS`      - cap on the number of processes in the tree.
     - `PROCESS_TIME`        - cap on CPU time.
     - `DIE_ON_UNHANDLED_EXCEPTION` - crash the tree on an unhandled fault.

  2. **A network guard injected into the child interpreter**
     - Patches `socket.socket.connect/connect_ex/sendto` and
       `socket.getaddrinfo` inside the child so only loopback and RFC 1918
       destinations are reachable.
     - The parent's own air-gap guard is a monkey-patch in the parent process
       and is NOT inherited by a freshly spawned interpreter, which is why an
       unguarded child could reach the internet.

  3. **A real AST screen** for statically dangerous constructs.

Honest limits (reported at runtime, never hidden):
  * A Job Object constrains processes, not the filesystem. Code can still read
    files outside its job directory unless the AST screen blocks it.
  * The network guard is enforced inside the CPython process, so code that
    re-imports `socket`, reloads it from disk, or calls WinSock through
    `ctypes` can bypass it. It stops LLM-generated and accidental egress; it is
    not a kernel-level firewall.
  * True kernel-enforced isolation requires Docker/Podman or a Windows Sandbox.
"""

from __future__ import annotations

import ast
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from backend.config import logger


# ══════════════════════════════════════════════════════════════════════
# 1. Windows Job Objects
# ══════════════════════════════════════════════════════════════════════
_IS_WINDOWS = os.name == "nt"


class _JobLimits:
    """
    Job Object limit flags.

    The two time flags are NOT interchangeable: Windows rejects the mismatched
    pairing with ERROR_INVALID_PARAMETER (87). Verified empirically on this
    host:
        JOB_OBJECT_LIMIT_PROCESS_TIME (0x2) <-> BasicLimit.PerProcessUserTimeLimit
        JOB_OBJECT_LIMIT_JOB_TIME     (0x4) <-> BasicLimit.PerJobUserTimeLimit
    We cap total CPU time for the whole tree, so JOB_TIME + PerJob is correct.
    Using PROCESS_TIME with PerJobUserTimeLimit silently disables every limit in
    the structure, which is how a 900 MB allocation slipped past a 512 MB cap.
    """
    PROCESS_TIME = 0x00000002
    JOB_TIME = 0x00000004
    ACTIVE_PROCESS = 0x00000008
    JOB_MEMORY = 0x00000200
    DIE_ON_UNHANDLED_EXCEPTION = 0x00000400
    KILL_ON_JOB_CLOSE = 0x00002000


def _build_job_types():
    """Builds the ctypes structures for JOBOBJECT_EXTENDED_LIMIT_INFORMATION."""
    import ctypes
    from ctypes import wintypes

    class LUID(ctypes.Structure):
        _fields_ = [("LowPart", wintypes.DWORD),
                    ("HighPart", wintypes.LONG)]

    class LARGE_INTEGER(ctypes.Structure):
        _fields_ = [("QuadPart", ctypes.c_longlong)]

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", LARGE_INTEGER),
            ("PerJobUserTimeLimit", LARGE_INTEGER),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    return JOBOBJECT_EXTENDED_LIMIT_INFORMATION


class ProcessJob:
    """
    A Windows Job Object that constrains and reaps a process tree.

    Used as a context manager around the child process. On exit the handle is
    closed, and because `KILL_ON_JOB_CLOSE` is set, Windows terminates every
    process still in the job - which is what makes the timeout path reliable
    even when the child spawned grandchildren.

    On non-Windows platforms every method is a no-op and `available` is False,
    so callers can degrade gracefully.
    """

    def __init__(
        self,
        memory_limit_bytes: Optional[int] = None,
        cpu_seconds: Optional[int] = None,
        max_processes: int = 64,
    ) -> None:
        self.memory_limit_bytes = memory_limit_bytes
        self.cpu_seconds = cpu_seconds
        self.max_processes = max_processes
        self.available = False
        self.error: Optional[str] = None
        self._handle = None
        self._k32 = None
        if _IS_WINDOWS:
            self._create()

    def _create(self) -> None:
        try:
            import ctypes
            from ctypes import wintypes

            k32 = ctypes.WinDLL("kernel32", use_last_error=True)
            k32.CreateJobObjectW.restype = wintypes.HANDLE
            k32.SetInformationJobObject.argtypes = [
                wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD
            ]
            k32.SetInformationJobObject.restype = wintypes.BOOL
            k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
            k32.AssignProcessToJobObject.restype = wintypes.BOOL
            k32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
            k32.TerminateJobObject.restype = wintypes.BOOL
            k32.CloseHandle.argtypes = [wintypes.HANDLE]
            k32.CloseHandle.restype = wintypes.BOOL

            handle = k32.CreateJobObjectW(None, None)
            if not handle:
                self.error = f"CreateJobObjectW failed (err {ctypes.get_last_error()})"
                return

            info = _build_job_types()()
            bl = info.BasicLimitInformation
            flags = (
                _JobLimits.KILL_ON_JOB_CLOSE
                | _JobLimits.DIE_ON_UNHANDLED_EXCEPTION
                | _JobLimits.ACTIVE_PROCESS
            )
            if self.memory_limit_bytes:
                flags |= _JobLimits.JOB_MEMORY
                info.JobMemoryLimit = self.memory_limit_bytes
            if self.cpu_seconds:
                # JOB_TIME pairs with PerJobUserTimeLimit (total CPU for the
                # tree), which is what we want.
                flags |= _JobLimits.JOB_TIME
                bl.PerJobUserTimeLimit.QuadPart = int(self.cpu_seconds) * 10_000_000
            bl.LimitFlags = flags
            bl.ActiveProcessLimit = self.max_processes

            # JobObjectExtendedLimitInformation == 9
            ok = k32.SetInformationJobObject(
                handle, 9, ctypes.byref(info), ctypes.sizeof(info)
            )
            if not ok:
                self.error = (
                    f"SetInformationJobObject failed (err {ctypes.get_last_error()})"
                )
                k32.CloseHandle(handle)
                return

            self._k32 = k32
            self._handle = handle
            self.available = True
        except Exception as exc:  # pragma: no cover - defensive
            self.error = f"{type(exc).__name__}: {exc}"
            self.available = False

    def assign(self, process) -> bool:
        """Puts an already-started Popen into this job."""
        if not self.available:
            return False
        try:
            import ctypes

            handle = ctypes.c_void_p(int(process._handle))  # noqa: SLF001
            ok = self._k32.AssignProcessToJobObject(self._handle, handle)
            if not ok:
                self.error = (
                    f"AssignProcessToJobObject failed (err {ctypes.get_last_error()})"
                )
            return bool(ok)
        except Exception as exc:
            self.error = f"{type(exc).__name__}: {exc}"
            return False

    def terminate(self, exit_code: int = 1) -> None:
        """Kills every process in the job."""
        if self.available and self._handle:
            try:
                self._k32.TerminateJobObject(self._handle, exit_code)
            except Exception:
                pass

    def close(self) -> None:
        """
        Closes the handle.

        With KILL_ON_JOB_CLOSE this reaps any surviving descendants, so it is
        called on both the success and timeout paths.
        """
        if self._handle is not None:
            try:
                self._k32.CloseHandle(self._handle)
            except Exception:
                pass
            self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def parse_memory_limit(text: str) -> Optional[int]:
    """Parses a Docker-style memory string ('512m', '1g') into bytes."""
    if not text:
        return None
    s = str(text).strip().lower()
    mult = 1
    if s.endswith("k"):
        mult, s = 1024, s[:-1]
    elif s.endswith("m"):
        mult, s = 1024 ** 2, s[:-1]
    elif s.endswith("g"):
        mult, s = 1024 ** 3, s[:-1]
    try:
        return int(float(s) * mult)
    except ValueError:
        return None


# ══════════════════════════════════════════════════════════════════════
# 2. Network guard injected into the child interpreter
# ══════════════════════════════════════════════════════════════════════
# This module is written into the job directory and imported by the bootstrap
# prepended to the user's script. It applies the same loopback + RFC 1918
# policy as the parent process, which a child interpreter does not otherwise
# inherit.
NETWORK_GUARD_SOURCE = r'''
"""Loopback + RFC 1918 network guard for sandboxed child interpreters."""
import ipaddress
import socket as _socket

_ALLOWED_HOSTNAMES = {"localhost", ""}


def _is_allowed(host):
    if not host:
        return True
    h = str(host).strip().strip("[]").lower()
    if h in _ALLOWED_HOSTNAMES or h == "0.0.0.0":
        return True
    try:
        ip = ipaddress.ip_address(h)
    except ValueError:
        # A hostname that is not a literal private address is external.
        return False
    if ip.is_loopback:
        return True
    return (ip in ipaddress.ip_network("10.0.0.0/8")
            or ip in ipaddress.ip_network("172.16.0.0/12")
            or ip in ipaddress.ip_network("192.168.0.0/16"))


def _addr_host(address):
    if isinstance(address, tuple) and address:
        return address[0]
    return str(address)


def _deny(host, what):
    raise PermissionError(
        "SOVEREIGNTY VIOLATION: outbound %s to %r is forbidden in air-gapped "
        "sandbox mode." % (what, host)
    )


def install():
    _orig_connect = _socket.socket.connect
    _orig_connect_ex = _socket.socket.connect_ex
    _orig_sendto = _socket.socket.sendto
    _orig_getaddrinfo = _socket.getaddrinfo

    def _check(address, what):
        if not _is_allowed(_addr_host(address)):
            _deny(_addr_host(address), what)

    def connect(self, address):
        _check(address, "connection")
        return _orig_connect(self, address)

    def connect_ex(self, address):
        _check(address, "connection")
        return _orig_connect_ex(self, address)

    def sendto(self, data, *args):
        _check(args[-1] if args else None, "datagram")
        return _orig_sendto(self, data, *args)

    def getaddrinfo(host, port, *args, **kwargs):
        # DNS to an external resolver is egress too.
        if not _is_allowed(host):
            _deny(host, "DNS resolution")
        return _orig_getaddrinfo(host, port, *args, **kwargs)

    _socket.socket.connect = connect
    _socket.socket.connect_ex = connect_ex
    _socket.socket.sendto = sendto
    _socket.getaddrinfo = getaddrinfo
'''


# ══════════════════════════════════════════════════════════════════════
# 3. AST screen
# ══════════════════════════════════════════════════════════════════════
# Statically dangerous imports. Each entry is a module the *model* has no
# legitimate reason to use when computing a refinery number, and every one of
# them is a sandbox-escape or exfiltration primitive.
_FORBIDDEN_MODULES = {
    "ctypes", "cffi", "socket", "subprocess", "winreg", "multiprocessing",
    "pty", "pdb", "imp", "pickle", "marshal", "shelve", "dill", "joblib",
    "requests", "urllib", "urllib2", "urllib3", "http", "httplib", "ftplib",
    "telnetlib", "smtplib", "poplib", "imaplib", "socketserver", "xmlrpc",
    "asyncio", "ssl", "webbrowser", "pydoc", "code", "codeop", "runpy",
    "sysconfig", "site", "venv", "ensurepip", "pip", "setuptools",
    "sqlite3", "psycopg", "psycopg2", "pymysql", "MySQLdb", "sqlalchemy",
    "boto3", "paramiko", "fabric", "winreg", "ctypes", "mmap", "shutil",
    "pathlib", "tempfile", "glob", "fileinput", "netrc", "keyring",
    "importlib", "pkgutil", "zipfile", "tarfile", "gzip", "lzma", "bz2",
}

# Modules that are allowed even though their names collide with a forbidden one.
_ALLOWED_MODULES = {
    "socket": None,  # handled specially: allowed via socket-free stdlib only
}

# Attribute chains used to reach the filesystem or shell without importing.
_FORBIDDEN_ATTRS = {
    ("system",), ("popen",), ("spawn",), ("spawnl",), ("spawnv",), ("execv",),
    ("execl",), ("execve",), ("fork",), ("forkpty",), ("kill",),
    ("setuid",), ("setgid",), ("chroot",), ("unshare",), ("setrlimit",),
    ("remove",), ("unlink",), ("rmdir"), ("rename",), ("chmod",), ("chown",),
    ("environ",), ("putenv",), ("unsetenv",),
}

# Absolute-path literals that reach outside a job directory.
_SENSITIVE_PREFIXES = (
    "c:/windows", "c:/program files", "c:/users", "c:/$recycle",
    "/etc", "/proc", "/sys", "/dev", "/root", "/var", "/boot",
    "d:/aegis",  # the repository itself
)


class SandboxViolation(Exception):
    """Raised when the static screen rejects a script."""


def screen_python_ast(code: str) -> Tuple[bool, str]:
    """
    Statically screens a Python script for sandbox-escape primitives.

    Returns (allowed, reason). This is a *defence in depth* layer: the Job
    Object and network guard are the real controls, and both can be bypassed by
    a determined native-code payload, so this must not be reported as the
    primary isolation guarantee.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"Syntax error: {exc}"

    violations: List[str] = []

    for node in ast.walk(tree):
        # --- imports ---
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _FORBIDDEN_MODULES:
                    violations.append(f"import {alias.name!r} (line {node.lineno})")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in _FORBIDDEN_MODULES:
                    violations.append(
                        f"from {node.module!r} import ... (line {node.lineno})"
                    )

        # --- dangerous attribute access ---
        elif isinstance(node, ast.Attribute):
            if node.attr in {a[0] for a in _FORBIDDEN_ATTRS}:
                # `os.remove` style calls are the risk; plain reads are not.
                if isinstance(getattr(node, "ctx", None), ast.Load):
                    violations.append(
                        f"attribute .{node.attr} (line {node.lineno})"
                    )

        # --- open() on a sensitive absolute path ---
        elif isinstance(node, ast.Call):
            fn = node.func
            fname = getattr(fn, "id", None) or getattr(fn, "attr", None)
            if fname == "open" and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    low = first.value.replace("\\", "/").lower()
                    if low.startswith(_SENSITIVE_PREFIXES):
                        violations.append(
                            f"open({first.value!r}) outside the job directory "
                            f"(line {node.lineno})"
                        )
            # eval / exec / compile are escape primitives.
            if fname in {"eval", "exec", "compile"}:
                violations.append(f"{fname}() (line {node.lineno})")

    if violations:
        seen, uniq = set(), []
        for v in violations:
            if v not in seen:
                seen.add(v)
                uniq.append(v)
        return False, "Static screen rejected: " + "; ".join(uniq[:6])

    return True, ""


def screen_report() -> Dict[str, Any]:
    """Describes the static screen for the status endpoint."""
    return {
        "enabled": True,
        "forbidden_module_prefixes": len(_FORBIDDEN_MODULES),
        "forbidden_attributes": len(_FORBIDDEN_ATTRS),
        "blocked_builtins": ["eval", "exec", "compile"],
        "basis": "ast_static_analysis",
    }
