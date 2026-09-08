"""
Project Air-Gap & Active Socket Guard Daemon.
Monitors all project-specific processes (Uvicorn, Next.js Admin/Chat, MySQL, Ollama, Python Sandbox)
and enforces 100% localhost & private LAN air-gap policy.

Features:
1. Filters psutil sockets to show ONLY project-relevant services (FastAPI :8000, Next.js :3000, Admin :3001, MySQL :3306, Ollama :11434).
2. Actively terminates/kills any rogue external socket or unauthorized process attempting to phone home (WAN breach).
3. Provides real-time metrics and audit logs to the Sovereignty Observatory.
"""

import os
import psutil
import socket
import ipaddress
import time
from typing import List, Dict, Any, Optional

PROJECT_PORTS = {8000, 3000, 3001, 3306, 11434, 5000, 8080}
PROJECT_PROCESS_KEYWORDS = [
    "python", "uvicorn", "node", "next", "mysqld", "ollama", "xampp", "cmd.exe", "powershell"
]

# Tracked project PIDs
_project_pids = set()

def register_project_pid(pid: int):
    """Registers a known project PID."""
    if pid:
        _project_pids.add(pid)

def is_project_socket(conn, current_pid: int) -> bool:
    """
    Returns True if connection belongs strictly to our project stack:
    - Port matches 8000 (Backend), 3000 (Chat UI), 3001 (Admin UI), 3306 (MySQL), 11434 (Ollama)
    - Or PID belongs to python/node/mysqld/ollama processes in our tree
    """
    lport = conn.laddr.port if conn.laddr else 0
    rport = conn.raddr.port if conn.raddr else 0
    
    if lport in PROJECT_PORTS or rport in PROJECT_PORTS:
        return True
        
    if conn.pid:
        if conn.pid == current_pid or conn.pid in _project_pids:
            return True
        try:
            proc = psutil.Process(conn.pid)
            pname = proc.name().lower()
            if any(k in pname for k in PROJECT_PROCESS_KEYWORDS):
                cmdline = " ".join(proc.cmdline()).lower()
                if any(k in cmdline for k in ["sih", "hackthon", "main.py", "uvicorn", "ollama", "mysql", "next"]):
                    _project_pids.add(conn.pid)
                    return True
        except Exception:
            pass
            
    return False

def get_friendly_service_name(conn, proc_name: str) -> str:
    """Returns clean human-readable service tag for our stack."""
    lport = conn.laddr.port if conn.laddr else 0
    rport = conn.raddr.port if conn.raddr else 0
    
    if lport == 8000 or rport == 8000:
        return "FastAPI Core Backend (:8000)"
    elif lport == 3000 or rport == 3000:
        return "Chat User Portal Next.js (:3000)"
    elif lport == 3001 or rport == 3001:
        return "Admin Sovereignty Workbench (:3001)"
    elif lport == 3306 or rport == 3306:
        return "XAMPP MySQL Sovereignty DB (:3306)"
    elif lport == 11434 or rport == 11434:
        return "Ollama Local LLM Daemon (:11434)"
    elif "python" in proc_name.lower():
        return "Python Sandbox / Backend Worker"
    elif "node" in proc_name.lower():
        return "Frontend Node.js Service"
    return f"Project Service ({proc_name})"

def is_ip_allowed(ip_str: Optional[str]) -> bool:
    """Allows only Localhost (127.0.0.1, ::1, 0.0.0.0) and RFC 1918 Private LAN subnets."""
    if not ip_str or ip_str == "—" or ip_str == "*":
        return True
    clean_ip = ip_str.split(":")[0].strip()
    if clean_ip in ("127.0.0.1", "localhost", "::1", "0.0.0.0"):
        return True
    try:
        ip_obj = ipaddress.ip_address(clean_ip)
        return ip_obj.is_private or ip_obj.is_loopback
    except ValueError:
        return False

def inspect_and_guard_project_sockets(current_pid: int) -> List[Dict[str, Any]]:
    """
    Scans active network connections via psutil:
    1. Filters ONLY project-specific sockets (FastAPI, Chat UI, Admin UI, MySQL, Ollama).
    2. Enforces Air-Gap Guard: If any project process attempts an external WAN connection,
       it flags it as BLOCKED_BREACH and forcibly terminates the socket/process.
    """
    inspected_sockets = []
    
    try:
        connections = psutil.net_connections(kind="inet")
    except Exception:
        connections = []

    for c in connections:
        # Check if socket belongs to our project
        if not is_project_socket(c, current_pid):
            continue

        laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "—"
        raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "—"
        
        proc_name = "system"
        if c.pid:
            try:
                proc = psutil.Process(c.pid)
                proc_name = proc.name()
            except Exception:
                proc_name = "unknown"

        friendly_service = get_friendly_service_name(c, proc_name)
        remote_ip = c.raddr.ip if c.raddr else None

        tier = "LOCALHOST"
        verdict = "PERMITTED"

        if remote_ip and not (remote_ip.startswith("127.") or remote_ip in ("localhost", "::1", "0.0.0.0")):
            if is_ip_allowed(remote_ip):
                tier = "LAN_HOTSPOT"
                verdict = "PERMITTED"
            else:
                tier = "EXTERNAL_WAN"
                verdict = "BLOCKED_BREACH"
                # Active air-gap enforcement: kill/terminate socket or process attempting external WAN
                try:
                    if c.pid and c.pid != current_pid and c.pid != os.getpid():
                        rogue_proc = psutil.Process(c.pid)
                        rogue_proc.terminate()
                except Exception:
                    pass

        inspected_sockets.append({
            "id": f"sock-{c.pid or 0}-{laddr}-{c.status}",
            "pid": c.pid or 0,
            "process_name": friendly_service,
            "local_address": laddr,
            "remote_address": raddr,
            "tier": tier,
            "status": c.status,
            "security_verdict": verdict,
        })

    return inspected_sockets
