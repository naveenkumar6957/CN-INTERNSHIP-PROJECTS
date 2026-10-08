import os
import sys
import webbrowser
import threading
import time
import uvicorn

def open_browser():
    time.sleep(1.5)
    url = "http://127.0.0.1:8000"
    print(f"\n[SpamGuard AI] Opening Web Application in your browser: {url}\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    print("=" * 65)
    print("       SPAMGUARD AI - EMAIL SPAM CLASSIFIER SERVER")
    print("=" * 65)
    print("  * Web Dashboard  : http://127.0.0.1:8000")
    print("  * API Docs       : http://127.0.0.1:8000/docs")
    print("  * Health Check   : http://127.0.0.1:8000/api/health")
    print("=" * 65)

    threading.Thread(target=open_browser, daemon=True).start()

    # Start FastAPI application with uvicorn
    uvicorn.run("api.index:app", host="127.0.0.1", port=8000, reload=False)
