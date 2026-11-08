"""
PurgeKit v3.8.1 — Log Manager
MIT License — TeamExyKings
Saves logs to: Downloads/PurgeKit/Logs/PurgeKit_YYYYMMDD_HHMMSS.txt
"""

import os
import datetime
import platform

GITHUB_URL   = "https://github.com/yashwanthramsomireddy/PurgeKit"
AUTHOR_NAME  = "Yashwanth Ram Somireddy"
AUTHOR_LOC   = "Chennai, India"
AUTHOR_BRAND = "TeamExyKings"
# Fallback only: the app passes its own APP_VERSION into write_log(version=...)
APP_VERSION  = "3.8.1"

def get_log_dir():
    log_dir = os.path.join(os.path.expanduser("~"), "Downloads", "PurgeKit", "Logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def get_log_path():
    dt = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(get_log_dir(), f"PurgeKit_{dt}.txt")

def write_log(log_lines: list, extra_summary: str = "", version: str = None,
              path: str = None):
    """
    Write the log. Pass `path` to rewrite the SAME file repeatedly (used for the
    live log of a silent run). Written atomically (temp file + replace) so a
    reader such as Notepad never sees a half-written file.
    """
    path = path or get_log_path()
    tmp  = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(f"  PurgeKit v{version if version else APP_VERSION}  |  MIT License  |  {AUTHOR_BRAND}\n")
            f.write(f"  Built with love by {AUTHOR_NAME}, {AUTHOR_LOC}\n")
            f.write(f"  GitHub  : {GITHUB_URL}\n")
            f.write(f"  Saved   : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"  User    : {os.environ.get('USERNAME', 'Unknown')}\n")
            f.write(f"  PC      : {platform.node()}\n")
            f.write(f"  OS      : {platform.platform()}\n")
            f.write("=" * 60 + "\n\n")
            if extra_summary:
                f.write(extra_summary + "\n\n")
                f.write("-" * 60 + "\n\n")
            for line in log_lines:
                f.write(line + "\n")
        os.replace(tmp, path)
        return path
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        return None
