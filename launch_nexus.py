import subprocess
import os
import sys
import time
import webbrowser
from pathlib import Path

# Paths
ROOT = Path(r"C:\Users\rijan")
CLAUDE_DIR = ROOT / "Claude"
FRONTEND_DIR = ROOT / "frontend"
PYTHON_VENV = CLAUDE_DIR / ".venv312" / "Scripts" / "python.exe"

def launch():
    print("="*50)
    print(" NEXUS AI TERMINAL v3.0 - UNIFIED LAUNCHER")
    print("="*50)

    # 1. Start Backend
    print("[+] Starting Backend Engine (Port 8000)...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(CLAUDE_DIR)
    
    # Run the root server/main.py
    backend_proc = subprocess.Popen(
        [str(PYTHON_VENV), "server/main.py"],
        cwd=str(ROOT),
        env=env,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

    # 2. Start Frontend
    print("[+] Starting Frontend Grid (Port 5173)...")
    frontend_proc = subprocess.Popen(
        ["npm.cmd", "run", "dev"],
        cwd=str(FRONTEND_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

    # 3. Wait and Launch Browser
    print("[+] Syncing nodes...")
    time.sleep(8)
    
    print("[+] Launching Neural Interface...")
    # Using 127.0.0.1 for consistent browser routing
    url = "http://127.0.0.1:5173"
    
    # Try to open in App mode if Chrome is available
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if os.path.exists(chrome_path):
        subprocess.Popen([chrome_path, f"--app={url}"])
    else:
        webbrowser.open(url)

    print("\n[!] System ACTIVE. Keep this window open.")
    print("[!] To stop, close the spawned consoles or this window.")
    
    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print("[!] ALERT: Backend crashed. Restarting launcher recommended.")
                break
    except KeyboardInterrupt:
        print("[+] Shutting down...")
        backend_proc.terminate()
        frontend_proc.terminate()

if __name__ == "__main__":
    launch()
