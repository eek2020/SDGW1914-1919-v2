"""Self-update for the SDGW Windows installer.

On launch the frozen Windows .exe asks GitHub for the latest release.
If a newer version exists it downloads the new SDGW-Setup.exe and
spawns it with Inno Setup's /SILENT flag — the installer overwrites
the install in place and relaunches the app. The end user sees a
small "Updating SDGW…" splash window during this and nothing else.

Designed to fail invisibly: any network error, timeout, parse error,
download failure or unexpected response makes the updater return
quietly so the app opens normally with the existing version. Better
to skip an update than to strand a non-technical user on a broken
launch.

Only runs on Windows inside a PyInstaller frozen bundle. No-ops on
macOS, Linux, and developer runs from the repo.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from version import __version__, __repo__

# Use the OS trust store for SSL on the frozen Windows build. Without this,
# the bundled Python can't verify the cert chain on GitHub's release-download
# CDN (the 302 target for /releases/download/...), and the silent updater
# fails at the download step with CERTIFICATE_VERIFY_FAILED.
if sys.platform == "win32" and getattr(sys, "frozen", False):
    try:
        import truststore
        truststore.inject_into_ssl()
    except Exception:
        pass

CHECK_INTERVAL_SECONDS = 24 * 3600
NETWORK_TIMEOUT_SECONDS = 5
DOWNLOAD_TIMEOUT_SECONDS = 600
INSTALLER_ASSET_NAME = "SDGW-Setup.exe"

DETACHED_PROCESS = 0x00000008
CREATE_NO_WINDOW = 0x08000000


def _state_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "SDGW"
    return Path.home() / ".config" / "sdgw"


def _log_file() -> Path:
    return _state_dir() / "updater.log"


def _log(msg: str) -> None:
    """Append a timestamped line to updater.log. Never raises."""
    try:
        _state_dir().mkdir(parents=True, exist_ok=True)
        with open(_log_file(), "a", encoding="utf-8") as f:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{ts} [{__version__}] {msg}\n")
    except Exception:
        pass


def _log_exc(msg: str) -> None:
    """Append a message plus traceback. Never raises."""
    _log(msg + "\n" + traceback.format_exc())


def _last_check_file() -> Path:
    return _state_dir() / "last_update_check"


def _should_check() -> bool:
    f = _last_check_file()
    if not f.exists():
        return True
    try:
        last = float(f.read_text().strip())
    except (ValueError, OSError):
        return True
    return (time.time() - last) > CHECK_INTERVAL_SECONDS


def _mark_checked() -> None:
    try:
        _state_dir().mkdir(parents=True, exist_ok=True)
        _last_check_file().write_text(str(time.time()))
    except OSError:
        pass


def _parse_version(v: str) -> tuple:
    """Parse 'v1.2.3' / '1.2.3' / '0.0.0-abc1234' into (major, minor, patch).

    Non-tagged builds carry a dev suffix and parse to (0, 0, 0) so any
    real tagged release is considered newer.
    """
    v = v.lstrip("v")
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:[-.+]|$)", v)
    if not m:
        return (0, 0, 0)
    return tuple(int(x) for x in m.groups())


def _is_newer(latest: str, current: str) -> bool:
    return _parse_version(latest) > _parse_version(current)


def check_for_update() -> Optional[dict]:
    """Return {'tag', 'url', 'size'} if a newer release exists, else None."""
    if not _should_check():
        _log("skip: throttled by last_update_check timestamp")
        return None

    api_url = f"https://api.github.com/repos/{__repo__}/releases/latest"
    _log(f"checking {api_url}")
    try:
        req = urllib.request.Request(
            api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"sdgw-updater/{__version__}",
            },
        )
        with urllib.request.urlopen(req, timeout=NETWORK_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _log(f"check failed: {type(e).__name__}: {e}")
        return None

    _mark_checked()

    latest_tag = data.get("tag_name", "")
    _log(f"github says latest={latest_tag!r}, current={__version__!r}")
    if not latest_tag:
        _log("skip: no tag_name in response")
        return None
    if not _is_newer(latest_tag, __version__):
        _log(f"skip: parsed {_parse_version(latest_tag)} not newer than {_parse_version(__version__)}")
        return None

    for asset in data.get("assets", []):
        if asset.get("name") == INSTALLER_ASSET_NAME:
            _log(f"found asset {INSTALLER_ASSET_NAME}, size={asset.get('size', 0)}")
            return {
                "tag": latest_tag,
                "url": asset["browser_download_url"],
                "size": asset.get("size", 0),
            }
    _log(f"skip: no asset named {INSTALLER_ASSET_NAME} in release")
    return None


def _download(url: str, target: Path) -> None:
    _log(f"downloading {url} -> {target}")
    with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_SECONDS) as resp, open(target, "wb") as out:
        while True:
            chunk = resp.read(64 * 1024)
            if not chunk:
                break
            out.write(chunk)
    _log(f"download complete, {target.stat().st_size} bytes")


def _spawn_installer(installer: Path) -> None:
    """Launch Inno Setup installer detached with silent + close + restart flags."""
    flags = DETACHED_PROCESS | CREATE_NO_WINDOW
    cmd = [str(installer), "/SILENT", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS", "/NORESTART"]
    _log(f"spawning: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, creationflags=flags, close_fds=True)
    _log(f"installer pid={proc.pid}")


def _show_splash_and_install(release: dict) -> bool:
    _log(f"showing splash for {release['tag']}")
    """Display a small pywebview splash while downloading + spawning installer.

    Returns True if the installer was spawned successfully (caller should
    exit immediately so Inno Setup can replace files), False otherwise.
    """
    import webview

    result = {"spawned": False}

    def worker():
        try:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".exe", prefix="SDGW-Setup-")
            tmp.close()
            target = Path(tmp.name)
            _download(release["url"], target)
            _spawn_installer(target)
            result["spawned"] = True
            _log("worker complete, will destroy splash window")
        except Exception as e:
            _log_exc(f"worker failed: {type(e).__name__}: {e}")
        finally:
            for w in list(webview.windows):
                try:
                    w.destroy()
                except Exception:
                    pass

    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>Updating SDGW</title></head>"
        "<body style=\"font-family:'Segoe UI',sans-serif;text-align:center;"
        "padding:3em 2em;background:#f8f9fa;color:#1a1a1a;margin:0;\">"
        "<h2 style=\"margin:0 0 0.8em 0;font-weight:600;\">Updating SDGW…</h2>"
        f"<p style=\"color:#4a4a4a;margin:0 0 0.4em 0;\">Installing version {release['tag']}.</p>"
        "<p style=\"color:#6a6a6a;margin:0;font-size:0.9em;\">This may take a minute. "
        "The app will reopen automatically when finished.</p>"
        "</body></html>"
    )

    webview.create_window(
        "Updating SDGW",
        html=html,
        width=480,
        height=240,
        resizable=False,
    )
    webview.start(worker)
    return result["spawned"]


def try_update() -> bool:
    """Entry point. Returns True if an update was kicked off and the caller
    should exit so the installer can replace this process's files."""
    if sys.platform != "win32":
        return False
    if not getattr(sys, "frozen", False):
        _log("skip: not frozen (dev mode)")
        return False

    _log(f"try_update() starting, current={__version__}")
    try:
        release = check_for_update()
    except Exception as e:
        _log_exc(f"check_for_update raised: {type(e).__name__}: {e}")
        return False
    if release is None:
        _log("no update to apply")
        return False

    try:
        spawned = _show_splash_and_install(release)
        _log(f"splash returned spawned={spawned}")
        return spawned
    except Exception as e:
        _log_exc(f"splash failed: {type(e).__name__}: {e}")
        return False
