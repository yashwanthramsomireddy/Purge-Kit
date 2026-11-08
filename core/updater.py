"""
PurgeKit v3.2 — Auto Update Checker + Downloader
MIT License — TeamExyKings
"""

import urllib.request
import urllib.error
import json
import os
import sys
import subprocess
import tempfile
import threading

GITHUB_API      = "https://api.github.com/repos/yashwanthramsomireddy/PurgeKit/releases/latest"
GITHUB_RELEASES = "https://github.com/yashwanthramsomireddy/PurgeKit/releases"
CURRENT_VERSION = "3.8.1"
EXE_ASSET_NAME  = "PurgeKit.exe"

def check_for_update(timeout=8):
    """
    Returns (is_available, latest_version, download_url, release_url)
    is_available: True = newer exists, False = up to date, None = check failed
    """
    try:
        req = urllib.request.Request(
            GITHUB_API,
            headers={"User-Agent": f"PurgeKit-Updater/{CURRENT_VERSION}"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())

        tag         = data.get("tag_name", "").lstrip("v")
        release_url = data.get("html_url", GITHUB_RELEASES)
        assets      = data.get("assets", [])

        # Find the exe download URL
        download_url = ""
        for asset in assets:
            if asset.get("name","").lower() == EXE_ASSET_NAME.lower():
                download_url = asset.get("browser_download_url","")
                break

        if tag and _version_gt(tag, CURRENT_VERSION):
            return True, tag, download_url, release_url
        return False, CURRENT_VERSION, "", release_url

    except Exception:
        return None, CURRENT_VERSION, "", GITHUB_RELEASES


def _version_gt(a, b):
    """Return True if version string a > b."""
    try:
        av = [int(x) for x in a.split(".")]
        bv = [int(x) for x in b.split(".")]
        return av > bv
    except Exception:
        return False


def is_frozen():
    """Returns True if running as compiled .exe via PyInstaller."""
    return getattr(sys, "frozen", False)


def get_current_exe():
    """Returns the path of the currently running exe."""
    if is_frozen():
        return sys.executable
    return None


def download_update(download_url, progress_fn=None):
    """
    Downloads the new exe to a temp file.
    progress_fn(pct, downloaded_mb, total_mb) called during download.
    Returns path to downloaded file, or None on failure.
    """
    try:
        tmp_dir  = tempfile.gettempdir()
        tmp_path = os.path.join(tmp_dir, "PurgeKit_update.exe")

        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": f"PurgeKit-Updater/{CURRENT_VERSION}"}
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 65536  # 64 KB chunks

            with open(tmp_path, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_fn and total > 0:
                        pct  = downloaded / total
                        dl_mb = downloaded / (1<<20)
                        tot_mb = total / (1<<20)
                        progress_fn(pct, dl_mb, tot_mb)

        return tmp_path

    except Exception as e:
        return None


def apply_update(new_exe_path):
    """
    Writes a temp batch script that:
    1. Waits for current process to exit
    2. Replaces PurgeKit.exe with the downloaded one
    3. Launches the new exe
    4. Deletes itself
    Then launches the batch script and exits current app.
    """
    current_exe = get_current_exe()
    if not current_exe:
        return False

    bat_path = os.path.join(tempfile.gettempdir(), "purgekit_update.bat")
    pid      = os.getpid()

    bat_content = f"""@echo off
:: PurgeKit Auto-Updater
:: Waits for old process to exit, replaces exe, launches new version

echo Waiting for PurgeKit to close...
:WAIT
tasklist /FI "PID eq {pid}" 2>NUL | find /I "{pid}" >NUL
if not errorlevel 1 (
    timeout /t 1 /nobreak >NUL
    goto WAIT
)

echo Applying update...
timeout /t 1 /nobreak >NUL

:: Replace exe
copy /Y "{new_exe_path}" "{current_exe}" >NUL
if errorlevel 1 (
    echo Update failed - could not replace exe.
    pause
    goto CLEANUP
)

echo Update successful! Launching PurgeKit...
start "" "{current_exe}"

:CLEANUP
:: Delete downloaded update file
del /f /q "{new_exe_path}" >NUL 2>&1
:: Delete this batch file
del /f /q "%~f0" >NUL 2>&1
"""

    try:
        with open(bat_path, "w") as f:
            f.write(bat_content)

        # Launch batch script minimized, independent of current process
        subprocess.Popen(
            ["cmd.exe", "/c", bat_path],
            creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS,
            close_fds=True
        )
        return True
    except Exception:
        return False
