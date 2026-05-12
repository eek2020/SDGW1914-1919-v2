"""Single-window launcher for SDGW 1914-1919.

Entry point for both the development workflow (run from repo root) and
the PyInstaller-frozen Windows/macOS bundle. Starts the Flask server on
127.0.0.1:5001 in a daemon thread, then opens a native window pointing
at it. Closing the window ends the process and the daemon-thread server
dies with it.
"""

import os
import socket
import sys
import threading
import time
from pathlib import Path

FROZEN = getattr(sys, 'frozen', False)

if not FROZEN:
    REPO_ROOT = Path(__file__).resolve().parent
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(REPO_ROOT / "src"))

os.environ.setdefault("FLASK_SECRET_KEY", os.urandom(32).hex())


def _claim_app_mutex():
    """Hold a named Windows mutex so Inno Setup can detect this running app.

    The name must match AppMutex in packaging/installer.iss. The handle is
    returned and stored at module scope so it lives for the lifetime of the
    process — closing the handle releases the mutex and tells the installer
    the app is gone. Without this, /CLOSEAPPLICATIONS in the silent updater
    is a no-op and the install over a running .exe silently fails to replace
    locked files.
    """
    if not (FROZEN and sys.platform == "win32"):
        return None
    try:
        import ctypes
        return ctypes.windll.kernel32.CreateMutexW(None, False, "SDGW1914-1919-AppMutex")
    except Exception:
        return None


_APP_MUTEX = _claim_app_mutex()

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


def _show_error(message: str) -> None:
    """Show a native dialog so a non-technical user sees the problem clearly."""
    try:
        import webview
        webview.create_window("SDGW 1914-1919", html=f"<body style='font-family:Segoe UI,sans-serif;padding:2em;'><h2>SDGW 1914-1919</h2><p>{message}</p></body>", width=560, height=300)
        webview.start()
    except Exception:
        sys.stderr.write(message + "\n")


def main() -> int:
    # Check for self-update before doing anything else. No-ops on dev
    # builds, non-Windows, and when no update is available. If an update
    # was kicked off this returns True and we exit so the installer can
    # replace files; Inno Setup's /RESTARTAPPLICATIONS relaunches us.
    try:
        from src.updater import try_update
        if try_update():
            return 0
    except Exception:
        pass

    from src.web_app import DB_PATH

    if not DB_PATH.exists():
        _show_error(
            "The personnel database file could not be found.<br><br>"
            f"Expected at: <code>{DB_PATH}</code><br><br>"
            "Please reinstall the application, or contact whoever sent it to you."
        )
        return 1

    if not _port_open(HOST, PORT):
        threading.Thread(target=_run_server, daemon=True).start()
        if not _wait_for_server():
            _show_error(
                "The application failed to start its internal server.<br><br>"
                "This is usually caused by another program already using port 5001, "
                "or by antivirus software blocking the application. "
                "Please restart your PC and try again."
            )
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
