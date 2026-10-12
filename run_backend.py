#!/usr/bin/env python3
"""
NE-SHIELD: Real-Time Landslide Early Warning & Disaster Intelligence System
Backend Execution Launcher & Static Portal Runner
"""

import sys
import os
import time
import webbrowser
import threading

# UTF-8 encoding support for Windows PowerShell / CMD
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def open_browser(url: str, delay_seconds: float = 1.8):
    """Opens browser after server is ready."""
    def _open():
        time.sleep(delay_seconds)
        print(f"\n[NE-SHIELD] Opening web browser: {url} ...")
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"[Warning] Could not auto-launch browser: {e}")
    t = threading.Thread(target=_open, daemon=True)
    t.start()

def print_banner():
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    print(f"\n{CYAN}{BOLD}" + "=" * 80)
    print("  NE-SHIELD: AI LANDSLIDE EARLY WARNING & REAL-TIME DISASTER MONITORING")
    print("  North Eastern Region Operational Command Center (GSI / IMD / ISRO Bhuvan)")
    print("=" * 80 + f"{RESET}\n")

    print(f"{GREEN}{BOLD}✓ Backend FastAPI & Telemetry Schedulers Starting...{RESET}")
    print(f"  • Static GIS Command Center:  {CYAN}{BOLD}http://localhost:8000/static/index.html{RESET}")
    print(f"  • Root Portal:                {CYAN}{BOLD}http://localhost:8000/{RESET}")
    print(f"  • Swagger API Documentation:  {YELLOW}http://localhost:8000/docs{RESET}")
    print(f"  • React Modern GIS Frontend:  {YELLOW}http://localhost:5173/{RESET}")
    print("-" * 80 + "\n")

def main():
    print_banner()

    target_url = "http://localhost:8000/static/index.html"
    open_browser(target_url, delay_seconds=2.0)

    try:
        import uvicorn
        uvicorn.run(
            "backend.app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n[NE-SHIELD] Server stopped by user.")
    except Exception as e:
        print(f"\n[Error] Failed to start backend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
