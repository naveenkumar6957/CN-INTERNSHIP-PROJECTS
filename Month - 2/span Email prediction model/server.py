import os
import sys
import webbrowser
import threading
import time
import uvicorn

# Ensure the project root directory is always on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def open_browser(host: str, port: int):
    time.sleep(1.2)
    display_host = "127.0.0.1" if host in ("0.0.0.0", "127.0.0.1") else host
    url = f"http://{display_host}:{port}"
    print(f"\n[SpamGuard AI] Opening Web Application in your browser: {url}\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))

    print("=" * 65)
    print("       SPAMGUARD AI - EMAIL SPAM CLASSIFIER SERVER")
    print("=" * 65)
    print(f"  * Web Dashboard  : http://{host}:{port}")
    print(f"  * API Docs       : http://{host}:{port}/docs")
    print(f"  * Health Check   : http://{host}:{port}/api/health")
    print("=" * 65)

    # Launch browser only on local desktop systems (skip in headless cloud/container environments)
    if not any(k in os.environ for k in ("RENDER", "DYNO", "VERCEL", "CI")):
        threading.Thread(target=open_browser, args=(host, port), daemon=True).start()

    # Start FastAPI application with uvicorn
    uvicorn.run("api.index:app", host=host, port=port, reload=False, app_dir=BASE_DIR)

