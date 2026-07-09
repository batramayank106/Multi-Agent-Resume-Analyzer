#!/usr/bin/env python3
"""Convenience script to start / stop the CV Chacha platform."""

import sys
import subprocess
import json
import os
from pathlib import Path

ROOT = Path(__file__).parent
PID_FILE = ROOT / ".run_pids.json"
NEW_CONSOLE = subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0


def _save_pids(**kw):
    pids = {}
    if PID_FILE.exists():
        try:
            pids = json.loads(PID_FILE.read_text())
        except Exception:
            pass
    pids.update({k: v for k, v in kw.items() if v})
    PID_FILE.write_text(json.dumps(pids, indent=2))


def _load_pids():
    if not PID_FILE.exists():
        return {}
    try:
        return json.loads(PID_FILE.read_text())
    except Exception:
        return {}


def _clear_pids():
    PID_FILE.unlink(missing_ok=True)


def start_background(service: str):
    title = "CV Chacha Backend" if service == "backend" else "CV Chacha Frontend"
    print(f"Starting {title}...")
    if service == "backend":
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app",
             "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=ROOT, creationflags=NEW_CONSOLE,
        )
        _save_pids(backend=proc.pid)
    else:
        proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "frontend/app.py",
             "--server.port", "8501"],
            cwd=ROOT, creationflags=NEW_CONSOLE,
        )
        _save_pids(frontend=proc.pid)


def start_blocking(service: str):
    print(f"Starting CV Chacha {service.title()}...")
    if service == "backend":
        subprocess.run([
            sys.executable, "-m", "uvicorn", "backend.main:app",
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ], cwd=ROOT)
    else:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "frontend/app.py",
            "--server.port", "8501"
        ], cwd=ROOT)


def _kill_pid(pid):
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                           capture_output=True, timeout=10)
            return True
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 15)
            return True
        except (OSError, ProcessLookupError):
            return False


def _kill_port(port):
    if sys.platform == "win32":
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | "
                 f"Select-Object -ExpandProperty OwningProcess"],
                capture_output=True, text=True, timeout=10,
            )
            for line in r.stdout.strip().splitlines():
                line = line.strip()
                if line:
                    try:
                        _kill_pid(int(line))
                    except ValueError:
                        pass
        except Exception:
            pass


def kill_all():
    killed = 0
    pids = _load_pids()

    for name in ("backend", "frontend"):
        pid = pids.get(name)
        if pid and _kill_pid(pid):
            print(f"Stopped {name} (PID {pid})")
            killed += 1

    for port in (8000, 8501):
        _kill_port(port)

    _clear_pids()

    if killed:
        print("All services stopped.")
    else:
        print("No running CV Chacha processes found.")


def show_status():
    pids = _load_pids()
    running = []
    for name, port in [("backend", 8000), ("frontend", 8501)]:
        pid = pids.get(name)
        if pid:
            running.append(f"  {name}: PID {pid}, port {port}")
        else:
            running.append(f"  {name}: not started via this script")
    print("CV Chacha Status:")
    print("\n".join(running))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CV Chacha Launcher")
    parser.add_argument(
        "action",
        choices=["backend", "frontend", "all", "kill", "status"],
        help="start backend, frontend, all, kill running services, or show status",
    )
    args = parser.parse_args()

    if args.action == "kill":
        kill_all()
    elif args.action == "status":
        show_status()
    elif args.action == "all":
        start_background("backend")
        start_background("frontend")
        print("\nBoth services starting in separate windows.")
        print("Backend:  http://localhost:8000")
        print("Frontend: http://localhost:8501")
        print("Run 'python run.py kill' to stop.\n")
    else:
        start_blocking(args.action)
