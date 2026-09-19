"""
AI Hiring Intelligence System - Application Runner
Launches the FastAPI backend server and automatically opens the dashboard in the default browser.
"""

import sys
import os
import time
import threading
import webbrowser
import uvicorn

def auto_open_browser():
    """Wait for server to bind port, then open default browser."""
    time.sleep(1.5)
    url = "http://127.0.0.1:8000"
    print(f"\n[*] Launching web browser at: {url}")
    try:
        webbrowser.open_new_tab(url)
    except Exception as exc:
        print(f"[!] Note: Automatic browser launch encountered: {exc}")
        print(f"[i] Please navigate manually to: {url}\n")

def main():
    print("=" * 70)
    print("  AI Hiring Intelligence & Bias Mitigation Dashboard")
    print("  Qualification-Based Assessment | Faithfulness (EFS) | Gap Analysis (BGI)")
    print("=" * 70)
    print("\n[*] Initializing FastAPI backend on http://127.0.0.1:8000 ...")
    print("[*] Your web browser will open automatically in 2 seconds.")
    print("[i] Press CTRL+C in this terminal window to stop the server.\n")

    # Start browser opener daemon
    threading.Thread(target=auto_open_browser, daemon=True).start()

    # Run Uvicorn server
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False, log_level="info")

if __name__ == "__main__":
    main()
