"""Single-window launcher for SDGW 1914-1919.

Double-click target for the macOS .app bundle and Windows .bat shortcut.
Starts the Flask server on 127.0.0.1:5001 in a daemon thread, then opens
a native window pointing at it. Closing the window ends the process and
the daemon-thread server dies with it.
"""

import os
import socket
import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

os.environ.setdefault("FLASK_SECRET_KEY", os.urandom(32).hex())

HOST = "127.0.0.1"
PORT = 5001
URL = f"http://{HOST}:{PORT}"


def _port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def _run_server() -> None:
    from src.web_app import app

    app.run(host=HOST, port=PORT, debug=False, use_reloader=False, threaded=True)


def _wait_for_server(timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _port_open(HOST, PORT):
            return True
        time.sleep(0.1)
    return False


def main() -> int:
    if not _port_open(HOST, PORT):
        threading.Thread(target=_run_server, daemon=True).start()
        if not _wait_for_server():
            sys.stderr.write(f"SDGW server failed to start on {URL}\n")
            return 1

    import webview

    webview.create_window(
        "SDGW 1914-1919",
        URL,
        width=1280,
        height=860,
        min_size=(900, 600),
    )
    webview.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
