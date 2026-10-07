"""
PurgeKit v3.1
MIT License — TeamExyKings
GitHub: https://github.com/yashwanthramsomireddy/PurgeKit
Built with love by Yashwanth Ram Somireddy, Chennai, India

Fixes in v3.1:
- Compact tab spacing fixed
- Spacious mode: sidebar navigation instead of missing tabs
- Theme applies on the fly (no restart needed)
- About tab: proper left-aligned two-column layout
- Startup tab: Enable/Disable per program, full path shown
- Scan tab: checkboxes + Clean Selected button
- Dry Run: visible topbar indicator, button text changes
- Taskbar/pinned icon uses PurgeKit icon correctly
"""

import sys
import os
import ctypes
import threading
import datetime
import platform
import tkinter as tk
from tkinter import messagebox, filedialog
import winreg
import tempfile

# ── Admin ─────────────────────────────────────────────────────
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def relaunch_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable,
        " ".join(f'"{a}"' for a in sys.argv), None, 1)
    sys.exit()

if platform.system() == "Windows" and not is_admin():
    relaunch_as_admin()

import customtkinter as ctk
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from core.config       import (load_config, save_config, load_history, save_history,
                                load_whitelist, save_whitelist, verify_pin,
                                set_pin, clear_pin)
from core.cleaner      import (TASKS, DISK_CLEANUP_CATS, get_drives,
                                fmt_size, run, ep, run_task, recreate, folder_size)
from core.scanner      import scan_all, total_junk, SCAN_PATHS
from core.lang_manager import LANGUAGES, load_lang, t
from core.updater      import (check_for_update, download_update,
                                apply_update, is_frozen, CURRENT_VERSION as UPDATER_VERSION)
from core.scheduler    import create_schedule, remove_schedule, get_next_run, schedule_exists
from core.startup_manager import get_startup_programs, disable_startup, enable_startup
from core.log_manager  import write_log
from core.software_updater import (is_winget_available, get_upgradeable_apps,
                                    download_installer, open_installer,
                                    open_in_folder)
from ui.themes         import get_theme

APP_VERSION  = "3.8.1"
GITHUB_URL   = "https://github.com/yashwanthramsomireddy/PurgeKit"
AUTHOR_NAME  = "Yashwanth Ram Somireddy"
AUTHOR_LOC   = "Chennai, India"
AUTHOR_BRAND = "TeamExyKings"
AUTOSTART_KEY = "PurgeKit"
AUTOSTART_REG = r"Software\Microsoft\Windows\CurrentVersion\Run"

# ── Icon ─────────────────────────────────────────────────────
def generate_icon(accent_color=(0, 230, 118)):
    size = 256
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r, g, b = accent_color
    draw.ellipse([4,4,252,252], fill=(10,10,10,255), outline=(r,g,b,255), width=6)
    draw.ellipse([20,20,236,236], outline=(r,g,b,80), width=2)
    draw.line([(128,60),(128,160)], fill=(r,g,b), width=10)
    for i, offset in enumerate([-40,-25,-10,5,20,35,50]):
        draw.line([(128,160),(88+offset,210)],
                  fill=(r,g,b,max(60,255-i*28)), width=5)
    draw.ellipse([118,50,138,70], fill=(r,g,b,255))
    return img

def save_icon_file(accent_color=(0,230,118)):
    """Save .ico to temp and return path — used for taskbar/pinned icon."""
    try:
        img      = generate_icon(accent_color)
        ico_path = os.path.join(tempfile.gettempdir(), "purgekit_app.ico")
        img.save(ico_path, format="ICO",
                 sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])
        return ico_path
    except Exception:
        return ""

# ── Auto-start ────────────────────────────────────────────────
def get_autostart():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, AUTOSTART_KEY)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

def set_autostart(enable):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG, 0, winreg.KEY_SET_VALUE)
        if enable:
            val = (f'"{sys.executable}"' if getattr(sys,"frozen",False)
                   else f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"')
            winreg.SetValueEx(key, AUTOSTART_KEY, 0, winreg.REG_SZ, val)
        else:
            try:
                winreg.DeleteValue(key, AUTOSTART_KEY)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

# ══════════════════════════════════════════════════════════════
#  PIN SCREEN
# ══════════════════════════════════════════════════════════════
class PinScreen(ctk.CTkToplevel):
    MAX_ATTEMPTS = 3
    LOCKOUT_SECS = 30

    def __init__(self, parent, cfg, on_success, T):
        super().__init__(parent)
        self.cfg        = cfg
        self.on_success = on_success
        self.T          = T
        self.attempts   = cfg.get("pin_attempts", 0)
        th = get_theme(cfg.get("theme","Green"))
        self.title("PurgeKit — Locked")
        self.geometry("340x360")
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))
        self.configure(fg_color=th["bg_darkest"])
        self._th = th
        self._build(th)

    def _build(self, th):
        try:
            acc = tuple(int(th["accent"].lstrip("#")[i:i+2],16) for i in (0,2,4))
            li  = generate_icon(acc)
            lc  = ctk.CTkImage(light_image=li, dark_image=li, size=(56,56))
            ctk.CTkLabel(self, image=lc, text="").pack(pady=(24,4))
        except Exception:
            pass
        ctk.CTkLabel(self, text="PurgeKit",
                     font=ctk.CTkFont("Segoe UI",20,"bold"),
                     text_color=th["accent"]).pack()
        ctk.CTkLabel(self, text=t(self.T,"pin_enter"),
                     font=ctk.CTkFont("Segoe UI",13),
                     text_color=th["text_gray"]).pack(pady=(4,16))
        self.pin_var   = tk.StringVar()
        self.pin_entry = ctk.CTkEntry(self, textvariable=self.pin_var,
                                       show="●", width=200, height=44,
                                       font=ctk.CTkFont("Segoe UI",18),
                                       fg_color=th["bg_card"],
                                       text_color=th["text_white"],
                                       border_color=th["accent_dark"],
                                       justify="center")
        self.pin_entry.pack(pady=(0,4))
        self.pin_entry.bind("<Return>", lambda e: self._check())
        self.pin_entry.focus()
        self.msg_lbl = ctk.CTkLabel(self, text="",
                                     font=ctk.CTkFont("Segoe UI",11),
                                     text_color=th["error"])
        self.msg_lbl.pack(pady=(0,12))
        ctk.CTkButton(self, text=t(self.T,"pin_unlock"),
                      font=ctk.CTkFont("Segoe UI",13,"bold"),
                      height=38, corner_radius=8,
                      fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                      text_color=th["accent"],
                      command=self._check).pack(padx=40, fill="x")

    def _check(self):
        pin = self.pin_var.get().strip()
        if verify_pin(pin, self.cfg.get("pin_hash","")):
            self.cfg["pin_attempts"] = 0
            save_config(self.cfg)
            self.destroy()
            self.on_success()
        else:
            self.attempts += 1
            self.cfg["pin_attempts"] = self.attempts
            save_config(self.cfg)
            self.pin_var.set("")
            remaining = self.MAX_ATTEMPTS - self.attempts
            if remaining <= 0:
                self.msg_lbl.configure(text=t(self.T,"pin_locked",seconds=self.LOCKOUT_SECS))
                self.pin_entry.configure(state="disabled")
                self.after(self.LOCKOUT_SECS*1000, self._reset_lockout)
            else:
                self.msg_lbl.configure(text=t(self.T,"pin_wrong",remaining=remaining))

    def _reset_lockout(self):
        self.attempts = 0
        self.cfg["pin_attempts"] = 0
        save_config(self.cfg)
        self.pin_entry.configure(state="normal")
        self.msg_lbl.configure(text="")
        self.pin_entry.focus()

# ══════════════════════════════════════════════════════════════
#  FIRST RUN WIZARD
# ══════════════════════════════════════════════════════════════
class FirstRunWizard(ctk.CTkToplevel):
    def __init__(self, parent, cfg, on_done):
        super().__init__(parent)
        self.cfg     = cfg
        self.on_done = on_done
        th = get_theme(cfg.get("theme","Green"))
        self.title("Welcome to PurgeKit")
        self.geometry("480x540")
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._finish)
        self.configure(fg_color=th["bg_darkest"])
        self._th = th
        self._build_step0()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _build_step0(self):
        self._clear()
        th = self._th
        try:
            acc = tuple(int(th["accent"].lstrip("#")[i:i+2],16) for i in (0,2,4))
            li  = generate_icon(acc)
            lc  = ctk.CTkImage(light_image=li, dark_image=li, size=(80,80))
            ctk.CTkLabel(self, image=lc, text="").pack(pady=(28,8))
        except Exception:
            pass
        ctk.CTkLabel(self, text="Welcome to PurgeKit",
                     font=ctk.CTkFont("Segoe UI",22,"bold"),
                     text_color=th["accent"]).pack()
        ctk.CTkLabel(self, text=f"v{APP_VERSION}  —  Windows Temp & Cache Cleaner",
                     font=ctk.CTkFont("Segoe UI",12),
                     text_color=th["text_gray"]).pack(pady=(2,12))
        ctk.CTkLabel(self,
                     text=(f"Built by {AUTHOR_NAME}\n"
                           f"{AUTHOR_LOC}  ({AUTHOR_BRAND})\n\n"
                           "Let's set up PurgeKit in 3 quick steps."),
                     font=ctk.CTkFont("Segoe UI",12),
                     text_color=th["text_white"], justify="center").pack(pady=(0,24))
        ctk.CTkButton(self, text="Next →",
                      font=ctk.CTkFont("Segoe UI",13,"bold"),
                      height=40, corner_radius=8,
                      fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                      text_color=th["accent"],
                      command=self._build_step1).pack(padx=60, fill="x")

    def _build_step1(self):
        self._clear()
        th = self._th
        ctk.CTkLabel(self, text="Step 1 of 3 — Choose Language",
                     font=ctk.CTkFont("Segoe UI",16,"bold"),
                     text_color=th["accent"]).pack(pady=(28,12))
        self._lang_var = tk.StringVar(value=self.cfg.get("language","en"))
        scroll = ctk.CTkScrollableFrame(self, fg_color=th["bg_card"], corner_radius=8, height=320)
        scroll.pack(fill="x", padx=24, pady=(0,12))
        for code, name in LANGUAGES.items():
            ctk.CTkRadioButton(scroll, text=name, variable=self._lang_var, value=code,
                               font=ctk.CTkFont("Segoe UI",11),
                               text_color=th["text_white"],
                               fg_color=th["accent_dark"], hover_color=th["accent_dark"],
                               border_color=th["text_dim"]).pack(anchor="w", padx=12, pady=4)
        ctk.CTkButton(self, text="Next →",
                      font=ctk.CTkFont("Segoe UI",13,"bold"),
                      height=40, corner_radius=8,
                      fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                      text_color=th["accent"],
                      command=self._save_step1).pack(padx=60, fill="x")

    def _save_step1(self):
        self.cfg["language"] = self._lang_var.get()
        self._build_step2()

    def _build_step2(self):
        self._clear()
        th = self._th
        ctk.CTkLabel(self, text="Step 2 of 3 — Choose Theme",
                     font=ctk.CTkFont("Segoe UI",16,"bold"),
                     text_color=th["accent"]).pack(pady=(28,16))
        self._theme_var = tk.StringVar(value=self.cfg.get("theme","Green"))
        for tname, color in [("Green","#00e676"),("Blue","#40c4ff"),("Purple","#ea80fc"),("White","#1a7a40")]:
            row = ctk.CTkFrame(self, fg_color=th["bg_card"], corner_radius=8)
            row.pack(fill="x", padx=24, pady=6)
            ctk.CTkRadioButton(row, text=tname, variable=self._theme_var, value=tname,
                               font=ctk.CTkFont("Segoe UI",13,"bold"),
                               text_color=color,
                               fg_color=th["accent_dark"], hover_color=th["accent_dark"],
                               border_color=th["text_dim"]).pack(side="left", padx=14, pady=14)
            ctk.CTkLabel(row, text="●"*10, font=ctk.CTkFont("Segoe UI",14),
                         text_color=color).pack(side="right", padx=14)
        ctk.CTkFrame(self, fg_color="transparent", height=16).pack()
        ctk.CTkButton(self, text="Next →",
                      font=ctk.CTkFont("Segoe UI",13,"bold"),
                      height=40, corner_radius=8,
                      fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                      text_color=th["accent"],
                      command=self._save_step2).pack(padx=60, fill="x")

    def _save_step2(self):
        self.cfg["theme"] = self._theme_var.get()
        self._build_step3()

    def _build_step3(self):
        self._clear()
        th = get_theme(self.cfg.get("theme","Green"))
        T  = load_lang(self.cfg.get("language","en"))
        self.configure(fg_color=th["bg_darkest"])
        ctk.CTkLabel(self, text="Step 3 of 3 — Quick Options",
                     font=ctk.CTkFont("Segoe UI",16,"bold"),
                     text_color=th["accent"]).pack(pady=(28,16))
        self._autostart_var = tk.BooleanVar(value=False)
        self._dryrun_var    = tk.BooleanVar(value=False)
        for var, label, note in [
            (self._autostart_var, t(T,"settings_autostart"), t(T,"settings_autostart_note")),
            (self._dryrun_var,    t(T,"settings_dry_run"),   "Preview what will be deleted before purging."),
        ]:
            row = ctk.CTkFrame(self, fg_color=th["bg_card"], corner_radius=8)
            row.pack(fill="x", padx=24, pady=6)
            ctk.CTkCheckBox(row, text=label, variable=var,
                            font=ctk.CTkFont("Segoe UI",12),
                            text_color=th["text_white"],
                            fg_color=th["accent_dark"], hover_color=th["accent_dark"],
                            checkmark_color=th["accent"],
                            border_color=th["text_dim"]).pack(anchor="w", padx=14, pady=(10,2))
            ctk.CTkLabel(row, text=f"  {note}",
                         font=ctk.CTkFont("Segoe UI",10),
                         text_color=th["text_gray"], anchor="w").pack(fill="x", padx=14, pady=(0,10))
        ctk.CTkFrame(self, fg_color="transparent", height=16).pack()
        ctk.CTkButton(self, text="✅  Finish Setup",
                      font=ctk.CTkFont("Segoe UI",13,"bold"),
                      height=40, corner_radius=8,
                      fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                      text_color=th["accent"],
                      command=self._finish).pack(padx=60, fill="x")

    def _finish(self):
        try:
            self.cfg["autostart"] = self._autostart_var.get()
            self.cfg["dry_run"]   = self._dryrun_var.get()
            if self._autostart_var.get():
                set_autostart(True)
        except Exception:
            pass
        self.cfg["first_run"] = False
        save_config(self.cfg)
        self.destroy()
        self.on_done()

# ══════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════
class PurgeKitApp(ctk.CTk):

    COMPACT_W,  COMPACT_H  = 780, 740
    SPACIOUS_W, SPACIOUS_H = 1120, 860

    # Sidebar nav items: (key, icon, builder_method)
    NAV_ITEMS = [
        ("tab_tasks",     "🧹", "_panel_tasks"),
        ("tab_log",       "📄", "_panel_log"),
        ("tab_scan",      "🔍", "_panel_scan"),
        ("tab_thirdparty","📦", "_panel_thirdparty"),
        ("tab_sysinfo",   "💻", "_panel_sysinfo"),
        ("tab_updater",   "🔄", "_panel_updater"),
        ("tab_settings",  "⚙",  "_panel_settings"),
        ("tab_about",     "ℹ",  "_panel_about"),
    ]

    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        if self.cfg.get("theme","Green") == "White":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.cfg       = load_config()
        self.history   = load_history()
        self.whitelist = load_whitelist()
        self.T         = load_lang(self.cfg.get("language","en"))
        self.th        = get_theme(self.cfg.get("theme","Green"))

        self.compact_mode  = tk.BooleanVar(value=self.cfg.get("compact_mode",True))
        self.task_vars     = {}
        self._session_tasks = {}
        self.cfg.pop("last_tasks", None)   # old versions saved this to disk -> stale selections
        self.drive_vars    = {}
        self.activity_var  = tk.StringVar(value=self.cfg.get("activity_choice","skip"))
        self.dry_run_var   = tk.BooleanVar(value=self.cfg.get("dry_run",False))
        self.autostart_var = tk.BooleanVar(value=get_autostart())
        self.running       = False
        self._cancel_flag  = False
        self.reboot_needed = [False]
        self.log_lines     = []
        self._active_nav   = t(self.T,"tab_tasks")
        self._nav_btns     = {}
        self._scan_results = []
        self._scan_check_vars = {}

        self.title(f"PurgeKit v{APP_VERSION}  —  {AUTHOR_BRAND}")
        self.configure(fg_color=self.th["bg_darkest"])
        self.resizable(True, True)
        self.minsize(720, 580)

        # ── Taskbar/pinned icon ───────────────────────────────
        self._apply_icon()

        self._set_window_size()
        self._center_window()

        if self.cfg.get("first_run", True):
            self.withdraw()
            self.after(100, self._show_wizard)
        elif self.cfg.get("pin_enabled", False):
            self.withdraw()
            self.after(100, self._show_pin)
        else:
            self._init_ui()
            self._check_update()

    def _apply_icon(self):
        """Apply icon to window AND register with Windows for taskbar pinning."""
        try:
            th  = self.th
            acc = tuple(int(th["accent"].lstrip("#")[i:i+2],16) for i in (0,2,4))

            # Save icon to AppData so it persists for taskbar pinning
            app_dir  = os.path.join(os.environ.get("APPDATA",""), "PurgeKit")
            os.makedirs(app_dir, exist_ok=True)
            ico_path = os.path.join(app_dir, "purgekit.ico")

            img = generate_icon(acc)
            img.save(ico_path, format="ICO",
                     sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])

            if os.path.exists(ico_path):
                self.iconbitmap(default=ico_path)

            # Register App User Model ID so Windows taskbar uses our icon
            app_id = "TeamExyKings.PurgeKit"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass

    def _set_window_size(self):
        w = self.COMPACT_W  if self.compact_mode.get() else self.SPACIOUS_W
        h = self.COMPACT_H  if self.compact_mode.get() else self.SPACIOUS_H
        self.geometry(f"{w}x{h}")

    def _center_window(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w  = self.COMPACT_W if self.compact_mode.get() else self.SPACIOUS_W
        h  = self.COMPACT_H if self.compact_mode.get() else self.SPACIOUS_H
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def _show_wizard(self):
        FirstRunWizard(self, self.cfg, self._after_wizard).lift()

    def _after_wizard(self):
        self.cfg = load_config()
        self._reload_theme_lang()
        self.deiconify()
        self._init_ui()
        self._check_update()

    def _show_pin(self):
        PinScreen(self, self.cfg, self._after_pin, self.T)

    def _after_pin(self):
        self.deiconify()
        self._init_ui()
        self._check_update()

    def _reload_theme_lang(self):
        """Apply new theme/lang without restarting — rebuilds entire UI."""
        self.cfg = load_config()
        self.T   = load_lang(self.cfg.get("language","en"))
        self.th  = get_theme(self.cfg.get("theme","Green"))
        # Switch appearance mode for White theme
        if self.cfg.get("theme","Green") == "White":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")
        self.configure(fg_color=self.th["bg_darkest"])
        self._apply_icon()
        self._active_nav = t(self.T,"tab_tasks")
        self._init_ui()

    def _init_ui(self):
        for w in self.winfo_children():
            w.destroy()
        self._build_topbar()
        self.main_frame = ctk.CTkFrame(self, fg_color=self.th["bg_darkest"], corner_radius=0)
        self.main_frame.pack(fill="both", expand=True)
        self._build_content()

    # ── Top bar ──────────────────────────────────────────────
    def _build_topbar(self):
        th  = self.th
        top = ctk.CTkFrame(self, fg_color=th["bg_dark"], height=54, corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)

        lf = ctk.CTkFrame(top, fg_color="transparent")
        lf.pack(side="left", padx=14, pady=8)
        try:
            acc = tuple(int(th["accent"].lstrip("#")[i:i+2],16) for i in (0,2,4))
            li  = generate_icon(acc)
            lc  = ctk.CTkImage(light_image=li, dark_image=li, size=(30,30))
            ctk.CTkLabel(lf, image=lc, text="").pack(side="left", padx=(0,8))
        except Exception:
            pass
        ctk.CTkLabel(lf, text="PurgeKit",
                     font=ctk.CTkFont("Segoe UI",20,"bold"),
                     text_color=th["accent"]).pack(side="left")
        ctk.CTkLabel(lf, text=f" v{APP_VERSION}",
                     font=ctk.CTkFont("Segoe UI",12),
                     text_color=th["text_gray"]).pack(side="left")

        rf = ctk.CTkFrame(top, fg_color="transparent")
        rf.pack(side="right", padx=14, pady=8)

        # Dry run indicator
        self.dryrun_lbl = ctk.CTkLabel(rf,
                                        text="🔍 DRY RUN ON" if self.dry_run_var.get() else "",
                                        font=ctk.CTkFont("Segoe UI",10,"bold"),
                                        text_color=th["warn"])
        self.dryrun_lbl.pack(side="left", padx=(0,8))

        ctk.CTkLabel(rf, text="Dry Run",
                     font=ctk.CTkFont("Segoe UI",10),
                     text_color=th["text_gray"]).pack(side="left", padx=(0,2))
        ctk.CTkSwitch(rf, text="", variable=self.dry_run_var,
                      command=self._on_dryrun_toggle,
                      width=40, height=20,
                      button_color=th["warn"], button_hover_color=th["warn"],
                      progress_color="#3a2000").pack(side="left", padx=(0,14))

        ctk.CTkLabel(rf, text=t(self.T,"compact_mode"),
                     font=ctk.CTkFont("Segoe UI",11),
                     text_color=th["text_gray"]).pack(side="left", padx=(0,4))
        ctk.CTkSwitch(rf, text="", variable=self.compact_mode,
                      command=self._toggle_compact,
                      width=44, height=22,
                      button_color=th["accent"], button_hover_color=th["accent_dim"],
                      progress_color=th["accent_dark"]).pack(side="left")

    def _on_dryrun_toggle(self):
        if self._locked_guard(lambda: self.dry_run_var.set(not self.dry_run_var.get())):
            return
        on = self.dry_run_var.get()
        try:
            self.dryrun_lbl.configure(text="🔍 DRY RUN ON" if on else "")
            if hasattr(self, "start_btn"):
                T  = self.T
                th = self.th
                if on:
                    self.start_btn.configure(text=t(T,"dry_run"),
                                              fg_color="#3a2000",
                                              text_color=th["warn"])
                else:
                    self.start_btn.configure(text=t(T,"start_purge"),
                                              fg_color=th["accent_dark"],
                                              text_color=th["accent"])
        except Exception:
            pass
        # Refresh sizes — dry run doesn't change sizes but updates total label color
        self.after(100, self._refresh_task_sizes)

    # ── Layout ───────────────────────────────────────────────
    def _build_content(self):
        # Remember checkbox state IN MEMORY so a theme/language/mode rebuild keeps
        # the user's selection. Never written to disk (a fresh launch = defaults).
        if getattr(self, 'task_vars', None):
            self._session_tasks = {tid: v.get() for tid, v in self.task_vars.items()}
        self._spacious_panel_cache = {}  # clear on theme/lang rebuild
        for w in self.main_frame.winfo_children():
            w.destroy()
        if self.compact_mode.get():
            self._build_compact()
        else:
            self._build_spacious()

    # ── SPACIOUS: Sidebar + content area ─────────────────────
    def _build_spacious(self):
        th = self.th

        # Sidebar
        sidebar = ctk.CTkFrame(self.main_frame, fg_color=th["bg_dark"],
                               width=180, corner_radius=0)
        sidebar.pack(side="left", fill="y", padx=(0,1))
        sidebar.pack_propagate(False)

        ctk.CTkFrame(sidebar, fg_color="transparent", height=12).pack()

        self._nav_btns = {}
        for key, icon, method in self.NAV_ITEMS:
            label = f"  {icon}  {t(self.T, key)}"
            is_active = t(self.T, key) == self._active_nav
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                font=ctk.CTkFont("Segoe UI", 12, "bold" if is_active else "normal"),
                height=40,
                corner_radius=8,
                anchor="w",
                fg_color=th["accent_dark"] if is_active else "transparent",
                hover_color=th["bg_hover"],
                text_color=th["accent"] if is_active else th["text_gray"],
                command=lambda k=key, m=method: self._nav_click_spacious(k, m)
            )
            btn.pack(fill="x", padx=8, pady=3)
            self._nav_btns[key] = btn

        # Content area
        self.content_area = ctk.CTkFrame(self.main_frame,
                                          fg_color=th["bg_darkest"], corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        # Right log panel (always visible in spacious)
        right = ctk.CTkFrame(self.main_frame, fg_color=th["bg_dark"],
                              corner_radius=10, width=300)
        right.pack(side="right", fill="both", padx=(0,8), pady=8)
        right.pack_propagate(False)
        self._build_log_panel(right)

        self._show_spacious_panel(self._active_nav)

    def _nav_click_spacious(self, key, method):
        th = self.th
        self._active_nav = t(self.T, key)
        # Update button styles
        for k, btn in self._nav_btns.items():
            is_active = k == key
            btn.configure(
                fg_color=th["accent_dark"] if is_active else "transparent",
                text_color=th["accent"] if is_active else th["text_gray"],
                font=ctk.CTkFont("Segoe UI", 12, "bold" if is_active else "normal")
            )
        self._show_spacious_panel(t(self.T, key))

    def _show_spacious_panel(self, nav_label):
        # Cache panels so tab switching never rebuilds _panel_tasks
        # This preserves checkbox state when user navigates away and back
        if not hasattr(self, "_spacious_panel_cache"):
            self._spacious_panel_cache = {}
        mapping = {
            t(self.T, "tab_tasks"):      self._panel_tasks,
            t(self.T, "tab_scan"):       self._panel_scan,
            t(self.T, "tab_thirdparty"): self._panel_thirdparty,
            t(self.T, "tab_sysinfo"):    self._panel_sysinfo,
            t(self.T, "tab_updater"):    self._panel_updater,
            t(self.T, "tab_settings"):   self._panel_settings,
            t(self.T, "tab_about"):      self._panel_about,
        }
        # Hide all cached panels
        for frame in self._spacious_panel_cache.values():
            try: frame.pack_forget()
            except Exception: pass
        # Show or build the requested panel
        if nav_label in self._spacious_panel_cache:
            try:
                frame = self._spacious_panel_cache[nav_label]
                frame.pack(fill="both", expand=True)
                return
            except Exception:
                pass
        builder = mapping.get(nav_label)
        if builder:
            panel_frame = ctk.CTkFrame(self.content_area,
                                       fg_color=self.th["bg_darkest"],
                                       corner_radius=0)
            panel_frame.pack(fill="both", expand=True)
            builder(panel_frame)
            self._spacious_panel_cache[nav_label] = panel_frame

    # ── COMPACT: CTkTabview with proper spacing ───────────────
    def _build_compact(self):
        th = self.th
        T  = self.T

        tabs = ctk.CTkTabview(
            self.main_frame,
            fg_color=th["bg_dark"],
            segmented_button_fg_color=th["bg_card"],
            segmented_button_selected_color=th["accent_dark"],
            segmented_button_selected_hover_color=th["accent_hover"],
            segmented_button_unselected_color=th["bg_card"],
            segmented_button_unselected_hover_color=th["bg_hover"],
            text_color=th["text_white"],
            text_color_disabled=th["text_dim"],
            border_color=th["text_dim"],
            border_width=1,
        )
        try:
            tabs._segmented_button.configure(font=ctk.CTkFont("Segoe UI", 11))
        except Exception:
            pass
        tabs.pack(fill="both", expand=True, padx=8, pady=8)

        tab_defs = [
            (t(T,"tab_tasks"),      self._panel_tasks),
            (t(T,"tab_log"),        self._panel_log),
            (t(T,"tab_scan"),       self._panel_scan),
            (t(T,"tab_thirdparty"), self._panel_thirdparty),
            (t(T,"tab_sysinfo"),    self._panel_sysinfo),
            (t(T,"tab_updater"),    self._panel_updater),
            (t(T,"tab_settings"),   self._panel_settings),
            (t(T,"tab_about"),      self._panel_about),
        ]
        for name, builder in tab_defs:
            tabs.add(name)

        for name, builder in tab_defs:
            tab = tabs.tab(name)
            # Add consistent inner padding
            inner = ctk.CTkFrame(tab, fg_color=th["bg_darkest"], corner_radius=0)
            inner.pack(fill="both", expand=True, padx=4, pady=4)
            builder(inner)

    # ══════════════════════════════════════════════════════════
    #  PANEL BUILDERS
    # ══════════════════════════════════════════════════════════

    # ── Background size scanner ──────────────────────────────
    def _compute_task_sizes(self, task_vars, callback):
        """Background scan of ALL task paths. Updates sizes live.
        total only counts checked tasks so dry run + select all shows correct total."""
        def _scan():
            sizes = {}
            total = 0
            for task in TASKS:
                tid    = task[0]
                path   = task[3]
                do_exp = task[4]
                rp     = ep(path) if do_exp else path
                sz     = 0
                try:
                    if os.path.exists(rp):
                        sz = folder_size(rp)
                except Exception:
                    pass
                sizes[tid] = sz
                # Only add to total if task is checked
                try:
                    if task_vars.get(tid) and task_vars[tid].get():
                        total += sz
                except Exception:
                    pass
                try:
                    self.after(0, lambda s=dict(sizes), tot=total: callback(s, tot, False))
                except Exception:
                    pass
            try:
                self.after(0, lambda: callback(dict(sizes), total, True))
            except Exception:
                pass
        threading.Thread(target=_scan, daemon=True).start()

    def _refresh_task_sizes(self):
        """Re-trigger size scan — call after select all / deselect all / dry run toggle."""
        try:
            th = self.th
            def _size_callback(sizes, total, done):
                try:
                    self.total_size_lbl.configure(
                        text=f"  💾  Total selected size: {fmt_size(total)}",
                        text_color=th["accent"] if done else th["text_gray"])
                    self.size_scan_lbl.configure(text="✅" if done else "⏳")
                    for tid, lbl in self._row_size_labels.items():
                        sz = sizes.get(tid, None)
                        if sz is not None:
                            var = self.task_vars.get(tid)
                            checked = var.get() if var else False
                            lbl.configure(
                                text=fmt_size(sz) if sz > 0 else "—",
                                text_color=th["accent"] if (sz > 0 and checked) else th["text_dim"])
                except Exception:
                    pass
            self.total_size_lbl.configure(
                text="  💾  Total selected size: scanning...",
                text_color=th["text_gray"])
            self._compute_task_sizes(self.task_vars, _size_callback)
        except Exception:
            pass

    # ── Tasks Panel ──────────────────────────────────────────
    def _panel_tasks(self, parent):
        th = self.th
        T  = self.T

        br = ctk.CTkFrame(parent, fg_color="transparent")
        br.pack(fill="x", pady=(4,6), padx=4)
        ctk.CTkButton(br, text=t(T,"select_all"), width=130, height=30,
                      fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                      text_color=th["accent"],
                      font=ctk.CTkFont("Segoe UI",12), corner_radius=6,
                      command=self._select_all).pack(side="left", padx=(0,8))
        ctk.CTkButton(br, text=t(T,"deselect_all"), width=130, height=30,
                      fg_color=th["bg_card"], hover_color=th["bg_hover"],
                      text_color=th["text_gray"],
                      font=ctk.CTkFont("Segoe UI",12), corner_radius=6,
                      command=self._deselect_all).pack(side="left")

        # Total size row
        size_row = ctk.CTkFrame(parent, fg_color=th["bg_card"], corner_radius=6)
        size_row.pack(fill="x", padx=4, pady=(0,6))
        self.total_size_lbl = ctk.CTkLabel(size_row,
                                            text="  💾  Total selected size: scanning...",
                                            font=ctk.CTkFont("Segoe UI",11),
                                            text_color=th["text_gray"], anchor="w")
        self.total_size_lbl.pack(side="left", padx=8, pady=6)
        self.size_scan_lbl = ctk.CTkLabel(size_row, text="",
                                           font=ctk.CTkFont("Segoe UI",10),
                                           text_color=th["text_dim"])
        self.size_scan_lbl.pack(side="right", padx=8)
        self._row_size_labels = {}

        scroll = ctk.CTkScrollableFrame(parent, fg_color=th["bg_darkest"], corner_radius=8,
                                        scrollbar_button_color=th["accent_dark"],
                                        scrollbar_button_hover_color=th["accent"])
        scroll.pack(fill="both", expand=True, padx=2)
        self.update_idletasks()  # suppress flicker

        # In-memory only. None -> task's built-in default (System/User/Browser on).
        last_tasks = getattr(self, "_session_tasks", {})

        # Suppress redraws during build
        self.update_idletasks()
        # Freeze redraws during bulk row creation
        try:
            scroll._parent_canvas.configure(state="disabled")
        except Exception:
            pass
        phase_meta = {
            "System":     (th["phase_system"],  "⚙",   th["accent"], t(T,"phase_system")),
            "User":       (th["phase_user"],    "👤",  th["accent"], t(T,"phase_user")),
            "Browser":    (th["phase_browser"], "🌐",  th["accent"], t(T,"phase_browser")),
            "Developer":  (th["phase_dev"],     "💻",  th["accent"], t(T,"phase_developer")),
            "ThirdParty": ("#0a1520",           "📦",  th["accent"], "📦  3rd Party Apps  (unchecked by default)"),
            "Adobe":      ("#1a0a1a",           "🎨",  "#ea80fc",    "🎨  Adobe Apps  (unchecked by default)"),
            "Optional":   (th["phase_opt"],     "⚠",   th["warn"],   t(T,"phase_optional")),
        }
        phases = {}
        for task in TASKS:
            phases.setdefault(task[1], []).append(task)

        for phase, tasks in phases.items():
            bg, icon, hdr_c, title = phase_meta.get(phase,(th["bg_card"],"•",th["accent"],phase))
            ph_f = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=8)
            ph_f.pack(fill="x", pady=(8,2), padx=2)
            hdr_row = ctk.CTkFrame(ph_f, fg_color="transparent")
            hdr_row.pack(fill="x", padx=8, pady=(4,2))
            ctk.CTkLabel(hdr_row, text=f"  {icon}  {title}",
                         font=ctk.CTkFont("Segoe UI",12,"bold"),
                         text_color=hdr_c, anchor="w").pack(side="left")
            # Per-category select/deselect — capture phase in closure
            def _make_phase_sel(ph_tasks, val):
                def _do():
                    for t_ in ph_tasks:
                        if t_[0] in self.task_vars:
                            self.task_vars[t_[0]].set(val)
                    self.after(50, self._refresh_task_sizes)
                return _do
            ctk.CTkButton(hdr_row, text="✔", width=28, height=22,
                          font=ctk.CTkFont("Segoe UI",10), corner_radius=4,
                          fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                          text_color=th["accent"],
                          command=_make_phase_sel(tasks, True)
                          ).pack(side="right", padx=(0,2))
            ctk.CTkButton(hdr_row, text="✘", width=28, height=22,
                          font=ctk.CTkFont("Segoe UI",10), corner_radius=4,
                          fg_color=th["bg_card"], hover_color=th["bg_hover"],
                          text_color=th["text_gray"],
                          command=_make_phase_sel(tasks, False)
                          ).pack(side="right", padx=(0,4))

            for task in tasks:
                tid, ph, label, path, expand, default, warning = task
                # In-session memory (survives theme/language rebuilds); else default
                saved = last_tasks.get(tid)
                is_wl   = any(path in w or (expand and ep(path) in w) for w in self.whitelist)
                checked = (saved if saved is not None else default) and not is_wl
                var = tk.BooleanVar(value=checked)
                self.task_vars[tid] = var

                row = ctk.CTkFrame(scroll, fg_color=th["bg_card"], corner_radius=6)
                row.pack(fill="x", pady=2, padx=2)
                ctk.CTkCheckBox(row, text=label, variable=var,
                                font=ctk.CTkFont("Segoe UI",12),
                                text_color=th["text_dim"] if is_wl else th["text_white"],
                                fg_color=th["accent_dark"], hover_color=th["accent_dark"],
                                checkmark_color=th["accent"], border_color=th["text_dim"],
                                width=20, height=20).pack(side="left", padx=(10,6), pady=6)
                if is_wl:
                    ctk.CTkLabel(row, text="🚫",
                                 font=ctk.CTkFont("Segoe UI",10),
                                 text_color=th["text_dim"]).pack(side="left")
                if warning:
                    ctk.CTkLabel(row, text="⚠",
                                 font=ctk.CTkFont("Segoe UI",12),
                                 text_color=th["warn"]).pack(side="left", padx=(0,4))
                # Size label per row (updated after background scan)
                size_lbl = ctk.CTkLabel(row, text="—",
                                        font=ctk.CTkFont("Segoe UI",10,"bold"),
                                        text_color=th["accent"])
                size_lbl.pack(side="right", padx=(0,6))
                self._row_size_labels[tid] = size_lbl

                ctk.CTkLabel(row, text=path,
                             font=ctk.CTkFont("Segoe UI",10),
                             text_color=th["text_gray"]).pack(side="right", padx=(0,6))
                if warning:
                    wr = ctk.CTkFrame(scroll, fg_color="#110a00", corner_radius=4)
                    wr.pack(fill="x", padx=12, pady=(0,2))
                    ctk.CTkLabel(wr, text=f"  {warning}",
                                 font=ctk.CTkFont("Segoe UI",10),
                                 text_color=th["warn"], anchor="w").pack(fill="x", padx=8, pady=3)

        # Disk cleanup
        dc_f = ctk.CTkFrame(scroll, fg_color=th["phase_dc"], corner_radius=8)
        dc_f.pack(fill="x", pady=(10,2), padx=2)
        ctk.CTkLabel(dc_f, text=f"  🗑  {t(T,'phase_disk')}",
                     font=ctk.CTkFont("Segoe UI",12,"bold"),
                     text_color=th["accent"], anchor="w").pack(fill="x", padx=12, pady=(8,2))
        ctk.CTkLabel(dc_f,
                     text="  Runs Windows Disk Cleanup tool on selected drives. Only removes temp files, "
                          "system logs, update backups, and recycle bin — never your personal files or apps.",
                     font=ctk.CTkFont("Segoe UI",10),
                     text_color=th["text_gray"],
                     wraplength=620, anchor="w", justify="left"
                     ).pack(fill="x", padx=12, pady=(0,6))
        last_drives = self.cfg.get("last_drives",[])
        self.drive_vars = {}
        for drive_path, label, free, total in get_drives():
            var = tk.BooleanVar(value=(drive_path in last_drives) if last_drives else True)
            self.drive_vars[drive_path] = var
            row = ctk.CTkFrame(dc_f, fg_color=th["bg_card"], corner_radius=6)
            row.pack(fill="x", pady=2, padx=8)
            name = f"{drive_path}  {label}" if label else drive_path
            sz   = f"{fmt_size(free)} free / {fmt_size(total)}" if total>0 else ""
            ctk.CTkCheckBox(row, text=name, variable=var,
                            font=ctk.CTkFont("Segoe UI",12), text_color=th["text_white"],
                            fg_color=th["accent_dark"], hover_color=th["accent_dark"],
                            checkmark_color=th["accent"], border_color=th["text_dim"],
                            width=20, height=20).pack(side="left", padx=(10,6), pady=6)
            if sz:
                ctk.CTkLabel(row, text=sz, font=ctk.CTkFont("Segoe UI",10),
                             text_color=th["text_gray"]).pack(side="right", padx=(0,10))
        ctk.CTkFrame(dc_f, fg_color="transparent", height=6).pack()

        # Activity History
        ah_f = ctk.CTkFrame(scroll, fg_color=th["bg_card"], corner_radius=8)
        ah_f.pack(fill="x", pady=(10,2), padx=2)
        ctk.CTkLabel(ah_f, text=t(T,"activity_history"),
                     font=ctk.CTkFont("Segoe UI",12,"bold"),
                     text_color=th["warn"], anchor="w").pack(fill="x", padx=12, pady=(8,2))
        ctk.CTkLabel(ah_f, text=f"  {t(T,'activity_desc')}",
                     font=ctk.CTkFont("Segoe UI",10),
                     text_color=th["text_gray"], anchor="w").pack(fill="x", padx=12, pady=(0,6))
        for val, key, desc in [
            ("skip",    "activity_skip",    "Do not clean activity history"),
            ("delete",  "activity_delete",  "Delete ActivitiesCache.db (one-time clean)"),
            ("disable", "activity_disable", "Delete + Disable Activity History permanently"),
        ]:
            rb = ctk.CTkRadioButton(ah_f, text=t(T,key),
                               variable=self.activity_var, value=val,
                               font=ctk.CTkFont("Segoe UI",11,"bold"),
                               text_color=th["text_white"],
                               fg_color=th["accent"],
                               hover_color=th["accent_dim"],
                               border_color=th["accent"],
                               border_width_unchecked=2,
                               border_width_checked=6,
                               radiobutton_width=18,
                               radiobutton_height=18)
            rb.pack(anchor="w", padx=20, pady=4)
            ctk.CTkLabel(ah_f, text=f"     {desc}",
                         font=ctk.CTkFont("Segoe UI",9),
                         text_color=th["text_dim"], anchor="w").pack(fill="x", padx=20, pady=(0,2))
        ctk.CTkFrame(ah_f, fg_color="transparent", height=8).pack()

        # Unfreeze after all rows built
        try:
            scroll._parent_canvas.configure(state="normal")
            scroll.update_idletasks()
        except Exception:
            pass

        # Bottom bar
        bot = ctk.CTkFrame(parent, fg_color=th["bg_darkest"], corner_radius=0)
        bot.pack(fill="x", pady=(8,0), padx=4)
        self.progress_label = ctk.CTkLabel(bot, text=t(T,"ready"),
                                           font=ctk.CTkFont("Segoe UI",11),
                                           text_color=th["text_gray"], anchor="w")
        self.progress_label.pack(fill="x", pady=(0,4))
        self.progress_bar = ctk.CTkProgressBar(bot, height=10, fg_color=th["bg_card"],
                                               progress_color=th["accent"], corner_radius=5)
        self.progress_bar.pack(fill="x", pady=(0,8))
        self.progress_bar.set(0)

        # Trigger background size scan — slight delay so all widgets are ready
        def _size_callback(sizes, total, done):
            try:
                self.total_size_lbl.configure(
                    text=f"  💾  Total selected size: {fmt_size(total)}",
                    text_color=th["accent"] if done else th["text_gray"])
                self.size_scan_lbl.configure(text="✅" if done else "⏳")
                for tid, lbl in self._row_size_labels.items():
                    sz = sizes.get(tid, None)
                    if sz is not None:
                        var     = self.task_vars.get(tid)
                        checked = var.get() if var else False
                        lbl.configure(
                            text=fmt_size(sz) if sz > 0 else "—",
                            text_color=th["accent"] if (sz > 0 and checked) else th["text_dim"])
            except Exception:
                pass

        def _start_size_scan():
            self.total_size_lbl.configure(
                text="  💾  Total selected size: scanning...",
                text_color=th["text_gray"])
            self.size_scan_lbl.configure(text="⏳")
            self._compute_task_sizes(self.task_vars, _size_callback)

        self.after(300, _start_size_scan)

        btn_r = ctk.CTkFrame(bot, fg_color="transparent")
        btn_r.pack(fill="x")
        dry = self.dry_run_var.get()
        self.start_btn = ctk.CTkButton(
            btn_r,
            text=t(T,"dry_run") if dry else t(T,"start_purge"),
            font=ctk.CTkFont("Segoe UI",14,"bold"),
            height=42, corner_radius=8,
            fg_color="#3a2000" if dry else th["accent_dark"],
            hover_color=th["accent_hover"],
            text_color=th["warn"] if dry else th["accent"],
            command=self._start_purge)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0,6))
        self.cancel_btn = ctk.CTkButton(btn_r, text="⏹ Cancel", height=42, width=90,
                      corner_radius=8, fg_color="#3a0000",
                      hover_color="#5a0000", text_color=th["error"],
                      font=ctk.CTkFont("Segoe UI",12,"bold"),
                      state="disabled",
                      command=self._cancel_purge)
        self.cancel_btn.pack(side="left", padx=(0,6))
        ctk.CTkButton(btn_r, text=t(T,"save_log"), height=42, width=80,
                      corner_radius=8, fg_color=th["bg_card"],
                      hover_color=th["bg_hover"], text_color=th["text_gray"],
                      font=ctk.CTkFont("Segoe UI",12),
                      command=self._save_log_manual).pack(side="left")

    # ── Log Panel ────────────────────────────────────────────
    def _panel_log(self, parent):
        self._build_log_panel(parent)

    def _build_log_panel(self, parent):
        th = self.th
        T  = self.T
        ctk.CTkLabel(parent, text=t(T,"tab_log"),
                     font=ctk.CTkFont("Segoe UI",13,"bold"),
                     text_color=th["accent"], anchor="w").pack(fill="x", padx=12, pady=(10,4))
        self.log_box = ctk.CTkTextbox(
            parent, fg_color=th["bg_darkest"], text_color=th["text_white"],
            font=ctk.CTkFont("Consolas",11), corner_radius=6,
            scrollbar_button_color=th["accent_dark"],
            scrollbar_button_hover_color=th["accent"],
            wrap="word", state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=8, pady=(0,8))
        for tag, color in [("success",th["success"]),("warn",th["warn"]),
                           ("error",th["error"]),("dim",th["text_gray"]),
                           ("accent",th["accent"]),("white",th["text_white"])]:
            self.log_box.tag_config(tag, foreground=color)
        self._log(f"PurgeKit v{APP_VERSION} ready.", "accent")
        self._log(t(T,"select_tasks"), "dim")

    # ── Scan Panel ───────────────────────────────────────────
    def _panel_scan(self, parent):
        th = self.th
        T  = self.T
        ctk.CTkLabel(parent, text=t(T,"scan_title"),
                     font=ctk.CTkFont("Segoe UI",14,"bold"),
                     text_color=th["accent"]).pack(pady=(12,2), padx=12, anchor="w")
        ctk.CTkLabel(parent, text=t(T,"scan_desc"),
                     font=ctk.CTkFont("Segoe UI",11),
                     text_color=th["text_gray"]).pack(padx=12, anchor="w", pady=(0,6))

        self.scan_progress_lbl = ctk.CTkLabel(parent, text="",
                                               font=ctk.CTkFont("Segoe UI",10),
                                               text_color=th["text_gray"])
        self.scan_progress_lbl.pack(padx=12, anchor="w")
        self.scan_progress_bar = ctk.CTkProgressBar(parent, height=8,
                                                     fg_color=th["bg_card"],
                                                     progress_color=th["accent"])
        self.scan_progress_bar.pack(fill="x", padx=12, pady=(2,6))
        self.scan_progress_bar.set(0)

        # Scan results scroll
        self.scan_scroll = ctk.CTkScrollableFrame(parent, fg_color=th["bg_darkest"],
                                                   corner_radius=8,
                                                   scrollbar_button_color=th["accent_dark"],
                                                   scrollbar_button_hover_color=th["accent"])
        self.scan_scroll.pack(fill="both", expand=True, padx=8, pady=(0,4))
        self.after(100, lambda f=self.scan_scroll: self._boost_scroll(f))

        # Bottom button row
        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(4,4))
        ctk.CTkButton(btn_row, text=t(T,"scan_start"),
                      font=ctk.CTkFont("Segoe UI",13,"bold"),
                      height=38, corner_radius=8,
                      fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                      text_color=th["accent"],
                      command=self._run_scan).pack(side="left", padx=(0,8))
        self.scan_clean_btn = ctk.CTkButton(btn_row, text="🧹  Clean Selected",
                                             font=ctk.CTkFont("Segoe UI",13,"bold"),
                                             height=38, corner_radius=8,
                                             fg_color="#1a1200", hover_color="#2a1e00",
                                             text_color=th["warn"],
                                             state="disabled",
                                             command=self._clean_scan_selected)
        self.scan_clean_btn.pack(side="left")

        # Clean progress bar (hidden until clean starts)
        self.scan_clean_progress_lbl = ctk.CTkLabel(parent, text="",
                                                     font=ctk.CTkFont("Segoe UI",10),
                                                     text_color=th["text_gray"])
        self.scan_clean_progress_lbl.pack(padx=12, anchor="w")
        self.scan_clean_bar = ctk.CTkProgressBar(parent, height=8,
                                                  fg_color=th["bg_card"],
                                                  progress_color=th["warn"],
                                                  corner_radius=5)
        self.scan_clean_bar.pack(fill="x", padx=12, pady=(2,8))
        self.scan_clean_bar.set(0)

    def _run_scan(self):
        if self._busy_guard():
            return
        th = self.th
        # Clear old results completely
        for w in self.scan_scroll.winfo_children():
            w.destroy()
        self._scan_check_vars = {}
        self._scan_results    = []
        self.scan_clean_btn.configure(state="disabled", text="🧹  Clean Selected")
        try:
            self.scan_clean_bar.set(0)
            self.scan_clean_progress_lbl.configure(text="")
        except Exception:
            pass

        def progress(pct, msg):
            try:
                self.after(0, lambda: (
                    self.scan_progress_bar.set(pct),
                    self.scan_progress_lbl.configure(text=msg)
                ))
            except Exception:
                pass

        def do_scan():
            results = scan_all(progress)
            self._scan_results = results
            total   = total_junk(results)

            def render():
                for w in self.scan_scroll.winfo_children():
                    w.destroy()

                # Total header
                hdr = ctk.CTkFrame(self.scan_scroll, fg_color=th["phase_dc"], corner_radius=8)
                hdr.pack(fill="x", pady=(0,6), padx=2)
                ctk.CTkLabel(hdr,
                             text=f"  Total junk found: {fmt_size(total)}  —  {len(results)} folders",
                             font=ctk.CTkFont("Segoe UI",13,"bold"),
                             text_color=th["accent"]).pack(side="left", padx=12, pady=8)

                # Select all / deselect for scan
                sr = ctk.CTkFrame(self.scan_scroll, fg_color="transparent")
                sr.pack(fill="x", padx=2, pady=(0,4))
                ctk.CTkButton(sr, text="✔ Select All", width=110, height=26,
                              fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                              text_color=th["accent"],
                              font=ctk.CTkFont("Segoe UI",11), corner_radius=6,
                              command=lambda: [v.set(True) for v in self._scan_check_vars.values()]
                              ).pack(side="left", padx=(0,6))
                ctk.CTkButton(sr, text="✘ Deselect All", width=110, height=26,
                              fg_color=th["bg_card"], hover_color=th["bg_hover"],
                              text_color=th["text_gray"],
                              font=ctk.CTkFont("Segoe UI",11), corner_radius=6,
                              command=lambda: [v.set(False) for v in self._scan_check_vars.values()]
                              ).pack(side="left")

                for i, (label, path, size) in enumerate(results):
                    var = tk.BooleanVar(value=True)
                    self._scan_check_vars[path] = var

                    row = ctk.CTkFrame(self.scan_scroll, fg_color=th["bg_card"], corner_radius=6)
                    row.pack(fill="x", pady=2, padx=2)

                    ctk.CTkCheckBox(row, text="", variable=var,
                                    fg_color=th["accent_dark"], hover_color=th["accent_dark"],
                                    checkmark_color=th["accent"], border_color=th["text_dim"],
                                    width=20, height=20).pack(side="left", padx=(8,4), pady=8)

                    info = ctk.CTkFrame(row, fg_color="transparent")
                    info.pack(side="left", fill="x", expand=True, padx=(0,8), pady=6)
                    ctk.CTkLabel(info, text=f"#{i+1}  {label}",
                                 font=ctk.CTkFont("Segoe UI",12,"bold"),
                                 text_color=th["text_white"], anchor="w").pack(fill="x")
                    ctk.CTkLabel(info, text=path,
                                 font=ctk.CTkFont("Segoe UI",9),
                                 text_color=th["text_dim"], anchor="w").pack(fill="x")

                    ctk.CTkLabel(row, text=fmt_size(size),
                                 font=ctk.CTkFont("Segoe UI",12,"bold"),
                                 text_color=th["accent"]).pack(side="right", padx=12)

                self.scan_clean_btn.configure(state="normal")
            self.after(0, render)

        threading.Thread(target=do_scan, daemon=True).start()

    def _clean_scan_selected(self):
        if self._busy_guard():
            return
        selected_paths = [p for p, v in self._scan_check_vars.items() if v.get()]
        if not selected_paths:
            messagebox.showwarning("Nothing Selected", "Select at least one item to clean.")
            return
        confirm = messagebox.askyesno(
            "Confirm Clean",
            f"Delete {len(selected_paths)} selected folder(s) from scan results?\n\nThis cannot be undone."
        )
        if not confirm:
            return
        # From here on this counts as a purge: same running flag + settings lock
        self.running = True
        self._cancel_flag = False
        self._set_ui_locked(True)
        reboot = [False]
        total_count = len(selected_paths)

        def set_scan_clean_progress(pct, msg):
            try:
                self.after(0, lambda: (
                    self.scan_clean_bar.set(pct),
                    self.scan_clean_progress_lbl.configure(text=msg)
                ))
            except Exception:
                pass

        def do_clean():
            total_freed = 0
            try:
                from core.cleaner import force_delete
                self.after(0, lambda: self.scan_clean_btn.configure(
                    state="disabled", text="⏳  Cleaning..."))
                for i, path in enumerate(selected_paths):
                    pct = i / max(total_count, 1)
                    set_scan_clean_progress(pct, f"[{i+1}/{total_count}] Cleaning: {os.path.basename(path)}...")
                    t0 = self._log_task_start("Junk Scan", path)
                    freed = 0
                    if os.path.exists(path):
                        freed = folder_size(path)
                        force_delete(path, self._log, reboot, self.dry_run_var.get())
                        recreate(path)
                        total_freed += freed
                    self._log_task_end("Junk Scan", t0, freed)
                set_scan_clean_progress(1.0, f"✅ Done — freed {fmt_size(total_freed)}")
                self._log(f"\n✅ Junk scan clean complete. Freed: {fmt_size(total_freed)}", "success")
            except Exception as e:
                self._log(f"  ❌ Junk scan clean stopped by an unexpected error: {e}", "error")
            finally:
                def _done():
                    try:
                        self.scan_clean_btn.configure(state="normal", text="🧹  Clean Selected")
                    except Exception:
                        pass
                    self._set_ui_locked(False)
                    self.running = False
                self.after(0, _done)
        threading.Thread(target=do_clean, daemon=True).start()

    # ── History Panel ────────────────────────────────────────
    def _panel_history(self, parent):
        th = self.th
        T  = self.T
        ctk.CTkLabel(parent, text=t(T,"history_title"),
                     font=ctk.CTkFont("Segoe UI",14,"bold"),
                     text_color=th["accent"]).pack(pady=(12,8), padx=12, anchor="w")

        if not self.history:
            ctk.CTkLabel(parent, text=t(T,"history_no_data"),
                         font=ctk.CTkFont("Segoe UI",12),
                         text_color=th["text_gray"]).pack(pady=40)
            return

        total_freed = sum(r.get("freed_bytes",0) for r in self.history)
        summary = ctk.CTkFrame(parent, fg_color=th["bg_card"], corner_radius=8)
        summary.pack(fill="x", padx=12, pady=(0,8))
        for lbl, val in [(t(T,"history_runs"), str(len(self.history))),
                         (t(T,"history_total"), fmt_size(total_freed))]:
            r = ctk.CTkFrame(summary, fg_color="transparent")
            r.pack(side="left", expand=True, pady=10)
            ctk.CTkLabel(r, text=val, font=ctk.CTkFont("Segoe UI",18,"bold"),
                         text_color=th["accent"]).pack()
            ctk.CTkLabel(r, text=lbl, font=ctk.CTkFont("Segoe UI",10),
                         text_color=th["text_gray"]).pack()

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            recent = self.history[-12:]
            labels = [r.get("date","")[-5:] for r in recent]
            values = [r.get("freed_bytes",0)/(1<<20) for r in recent]
            fig, ax = plt.subplots(figsize=(5,2.2))
            fig.patch.set_facecolor(th["bg_darkest"])
            ax.set_facecolor(th["bg_card"])
            ax.bar(labels, values, color=th["accent"], width=0.6)
            ax.tick_params(colors=th["text_gray"], labelsize=7)
            ax.spines[:].set_color(th["text_dim"])
            ax.set_ylabel("MB freed", color=th["text_gray"], fontsize=8)
            plt.xticks(rotation=30, ha="right")
            plt.tight_layout(pad=0.4)
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", padx=12, pady=(0,6))
            plt.close(fig)
        except Exception:
            pass

        scroll = ctk.CTkScrollableFrame(parent, fg_color=th["bg_darkest"], corner_radius=8,
                                         scrollbar_button_color=th["accent_dark"],
                                         scrollbar_button_hover_color=th["accent"])
        scroll.pack(fill="both", expand=True, padx=8, pady=(0,8))
        for run_data in reversed(self.history[-20:]):
            row = ctk.CTkFrame(scroll, fg_color=th["bg_card"], corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)
            ctk.CTkLabel(row, text=run_data.get("date",""),
                         font=ctk.CTkFont("Segoe UI",11),
                         text_color=th["text_white"]).pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(row, text=run_data.get("elapsed",""),
                         font=ctk.CTkFont("Segoe UI",10),
                         text_color=th["text_gray"]).pack(side="left", padx=6)
            ctk.CTkLabel(row, text=fmt_size(run_data.get("freed_bytes",0)),
                         font=ctk.CTkFont("Segoe UI",11,"bold"),
                         text_color=th["accent"]).pack(side="right", padx=10)

    # ── Startup Panel ────────────────────────────────────────
    def _panel_startup(self, parent):
        th = self.th
        T  = self.T
        ctk.CTkLabel(parent, text=t(T,"startup_title"),
                     font=ctk.CTkFont("Segoe UI",14,"bold"),
                     text_color=th["accent"]).pack(pady=(12,2), padx=12, anchor="w")
        ctk.CTkLabel(parent, text=t(T,"startup_desc"),
                     font=ctk.CTkFont("Segoe UI",11),
                     text_color=th["text_gray"]).pack(padx=12, anchor="w", pady=(0,6))

        self.startup_scroll = ctk.CTkScrollableFrame(parent, fg_color=th["bg_darkest"],
                                                      corner_radius=8,
                                                      scrollbar_button_color=th["accent_dark"],
                                                      scrollbar_button_hover_color=th["accent"])
        self.startup_scroll.pack(fill="both", expand=True, padx=8, pady=(0,4))
        ctk.CTkButton(parent, text=t(T,"startup_refresh"),
                      font=ctk.CTkFont("Segoe UI",12),
                      height=34, corner_radius=8,
                      fg_color=th["bg_card"], hover_color=th["bg_hover"],
                      text_color=th["text_gray"],
                      command=self._refresh_startup).pack(fill="x", padx=12, pady=(4,8))
        self._refresh_startup()

    def _refresh_startup(self):
        th = self.th
        for w in self.startup_scroll.winfo_children():
            w.destroy()
        try:
            programs = get_startup_programs()
            if not programs:
                ctk.CTkLabel(self.startup_scroll, text="No startup programs found.",
                             font=ctk.CTkFont("Segoe UI",11),
                             text_color=th["text_gray"]).pack(pady=20)
                return

            for prog in programs:
                # Card per program
                card = ctk.CTkFrame(self.startup_scroll, fg_color=th["bg_card"], corner_radius=8)
                card.pack(fill="x", pady=3, padx=2)

                top_row = ctk.CTkFrame(card, fg_color="transparent")
                top_row.pack(fill="x", padx=12, pady=(8,2))

                # Name + registry hive
                name_frame = ctk.CTkFrame(top_row, fg_color="transparent")
                name_frame.pack(side="left", fill="x", expand=True)
                ctk.CTkLabel(name_frame,
                             text=prog["name"],
                             font=ctk.CTkFont("Segoe UI",12,"bold"),
                             text_color=th["text_white"], anchor="w").pack(anchor="w")
                ctk.CTkLabel(name_frame,
                             text=f"Registry: {prog['label']}",
                             font=ctk.CTkFont("Segoe UI",9),
                             text_color=th["text_dim"], anchor="w").pack(anchor="w")

                # Enable / Disable button
                is_en = prog.get("enabled", True)
                btn_text  = "⏸ Disable" if is_en else "▶ Enable"
                btn_color = "#3a0000" if is_en else th["accent_dark"]
                btn_tc    = th["error"] if is_en else th["accent"]

                def make_toggle(p=prog, enabled=is_en):
                    def toggle():
                        try:
                            if enabled:
                                ok = disable_startup(p["name"], p["hive"], p["key"])
                            else:
                                ok = enable_startup(p["name"])
                            if ok:
                                # Small delay before refresh to let registry settle
                                self.after(400, self._refresh_startup)
                            else:
                                messagebox.showerror(
                                    "Error",
                                    f"Could not toggle '{p['name']}'.\n\n"
                                    "Some programs require elevated permissions to disable.")
                        except Exception as ex:
                            messagebox.showerror("Error", str(ex))
                    return toggle

                ctk.CTkButton(top_row,
                              text=btn_text, width=100, height=28,
                              fg_color=btn_color, hover_color=th["bg_hover"],
                              text_color=btn_tc,
                              font=ctk.CTkFont("Segoe UI",11), corner_radius=6,
                              command=make_toggle()).pack(side="right", padx=(8,0))

                # Full path — wrapping label
                ctk.CTkLabel(card,
                             text=prog["path"],
                             font=ctk.CTkFont("Segoe UI",9),
                             text_color=th["text_gray"],
                             anchor="w", wraplength=600, justify="left"
                             ).pack(fill="x", padx=12, pady=(2,8))

        except Exception as e:
            ctk.CTkLabel(self.startup_scroll,
                         text=f"Could not load startup programs:\n{e}",
                         font=ctk.CTkFont("Segoe UI",10),
                         text_color=th["error"]).pack(pady=20, padx=12)

    # ── 3rd Party Apps Panel ─────────────────────────────────
    def _panel_thirdparty(self, parent):
        th = self.th
        T  = self.T

        self._tp_task_vars = {}

        ctk.CTkLabel(parent, text="📦  3rd Party Apps",
                     font=ctk.CTkFont("Segoe UI",14,"bold"),
                     text_color=th["accent"]).pack(pady=(10,2), padx=12, anchor="w")
        ctk.CTkLabel(parent,
                     text="Clean caches from games, communication, media, creative and dev tools. All unchecked by default.",
                     font=ctk.CTkFont("Segoe UI",10),
                     text_color=th["text_gray"]).pack(padx=12, anchor="w", pady=(0,4))

        # Total size + select all row
        top_row = ctk.CTkFrame(parent, fg_color=th["bg_card"], corner_radius=6)
        top_row.pack(fill="x", padx=12, pady=(0,4))
        self.tp_total_lbl = ctk.CTkLabel(top_row,
                                          text="  💾  Total selected size: —",
                                          font=ctk.CTkFont("Segoe UI",11),
                                          text_color=th["text_gray"])
        self.tp_total_lbl.pack(side="left", padx=8, pady=5)
        ctk.CTkButton(top_row, text="✔ All", width=60, height=24,
                      font=ctk.CTkFont("Segoe UI",10), corner_radius=4,
                      fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                      text_color=th["accent"],
                      command=lambda: [v.set(True) for v in self._tp_task_vars.values()] or self._tp_refresh_total()
                      ).pack(side="right", padx=(0,4), pady=4)
        ctk.CTkButton(top_row, text="✘ None", width=60, height=24,
                      font=ctk.CTkFont("Segoe UI",10), corner_radius=4,
                      fg_color=th["bg_card"], hover_color=th["bg_hover"],
                      text_color=th["text_gray"],
                      command=lambda: [v.set(False) for v in self._tp_task_vars.values()] or self._tp_refresh_total()
                      ).pack(side="right", padx=(0,4), pady=4)

        scroll = ctk.CTkScrollableFrame(parent, fg_color=th["bg_darkest"],
                                        corner_radius=8,
                                        scrollbar_button_color=th["accent_dark"],
                                        scrollbar_button_hover_color=th["accent"])
        scroll.pack(fill="both", expand=True, padx=8, pady=(0,4))
        self.after(100, lambda f=scroll: self._boost_scroll(f))

        # Freeze redraws during bulk row creation
        try:
            scroll._parent_canvas.configure(state="disabled")
        except Exception:
            pass

        # Phase definitions: (phase_id, icon, title, bg_color, header_color)
        tp_phases = [
            ("Games",         "🎮", "Games & Launchers",
             "#0a1520", th["accent"]),
            ("Communication", "💬", "Communication Apps",
             "#0d1a10", th["accent"]),
            ("ThirdParty",    "📦", "Other 3rd Party Apps",
             "#0a0a1a", th["accent"]),
            ("Adobe",         "🎨", "Adobe Apps",
             "#1a0a1a", "#ea80fc"),
            ("Media",         "🎬", "Media & Creative",
             "#1a0f0a", "#ffab40"),
            ("DevTools",      "🔧", "Developer Tools",
             "#0a1a0a", th["accent"]),
        ]

        from core.cleaner import TASKS, ep, folder_size
        last_tasks = {}

        # Suppress redraws during build
        self.update_idletasks()
        for phase_id, icon, title, bg_col, hdr_col in tp_phases:
            phase_tasks = [t for t in TASKS if t[1] == phase_id]
            if not phase_tasks:
                continue

            # Phase header
            ph_f = ctk.CTkFrame(scroll, fg_color=bg_col, corner_radius=8)
            ph_f.pack(fill="x", pady=(8,2), padx=2)
            hdr_row = ctk.CTkFrame(ph_f, fg_color="transparent")
            hdr_row.pack(fill="x", padx=8, pady=(4,2))
            ctk.CTkLabel(hdr_row,
                         text=f"  {icon}  {title}  ({len(phase_tasks)} items)",
                         font=ctk.CTkFont("Segoe UI",12,"bold"),
                         text_color=hdr_col, anchor="w").pack(side="left")

            # Per-category ✔ ✘
            def _make_cat_sel(ptasks, val):
                def _do():
                    for t_ in ptasks:
                        if t_[0] in self._tp_task_vars:
                            self._tp_task_vars[t_[0]].set(val)
                    self._tp_refresh_total()
                return _do

            ctk.CTkButton(hdr_row, text="✔", width=28, height=22,
                          font=ctk.CTkFont("Segoe UI",10), corner_radius=4,
                          fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                          text_color=th["accent"],
                          command=_make_cat_sel(phase_tasks, True)
                          ).pack(side="right", padx=(0,2))
            ctk.CTkButton(hdr_row, text="✘", width=28, height=22,
                          font=ctk.CTkFont("Segoe UI",10), corner_radius=4,
                          fg_color=th["bg_card"], hover_color=th["bg_hover"],
                          text_color=th["text_gray"],
                          command=_make_cat_sel(phase_tasks, False)
                          ).pack(side="right", padx=(0,4))

            for task in phase_tasks:
                tid, ph, label, path, expand, default, warning = task
                var = tk.BooleanVar(value=False)  # Always unchecked by default
                self._tp_task_vars[tid] = var

                row = ctk.CTkFrame(scroll, fg_color=th["bg_card"], corner_radius=5)
                row.pack(fill="x", pady=1, padx=2)

                ctk.CTkCheckBox(row, text="", variable=var,
                                fg_color=th["accent_dark"], hover_color=th["accent_dark"],
                                checkmark_color=th["accent"], border_color=th["text_dim"],
                                width=16, height=16,
                                command=self._tp_refresh_total
                                ).pack(side="left", padx=(8,4), pady=5)

                ctk.CTkLabel(row, text=label,
                             font=ctk.CTkFont("Segoe UI",11,"bold"),
                             text_color=th["text_white"],
                             anchor="w").pack(side="left", padx=(2,4), pady=5)

                rp = ep(path) if expand else path
                ctk.CTkLabel(row, text=rp,
                             font=ctk.CTkFont("Segoe UI",9),
                             text_color=th["text_dim"],
                             anchor="e").pack(side="right", padx=(0,8))

                if warning:
                    wr = ctk.CTkFrame(scroll, fg_color="#110a00", corner_radius=3)
                    wr.pack(fill="x", padx=12, pady=(0,1))
                    ctk.CTkLabel(wr, text=f"  ⚠  {warning}",
                                 font=ctk.CTkFont("Segoe UI",9),
                                 text_color=th["warn"], anchor="w"
                                 ).pack(fill="x", padx=6, pady=2)

        # Unfreeze — show all rows at once
        try:
            scroll._parent_canvas.configure(state="normal")
            scroll.update_idletasks()
        except Exception:
            pass

        # Unfreeze scroll
        try:
            scroll._parent_canvas.configure(state="normal")
            scroll.update_idletasks()
        except Exception:
            pass
        # Bottom — purge button
        bot = ctk.CTkFrame(parent, fg_color=th["bg_darkest"])
        bot.pack(fill="x", padx=12, pady=(4,8))
        self.tp_progress_lbl = ctk.CTkLabel(bot, text="",
                                             font=ctk.CTkFont("Segoe UI",10),
                                             text_color=th["text_gray"])
        self.tp_progress_lbl.pack(anchor="w", pady=(0,2))
        self.tp_progress_bar = ctk.CTkProgressBar(bot, height=7,
                                                   fg_color=th["bg_card"],
                                                   progress_color=th["accent"],
                                                   corner_radius=3)
        self.tp_progress_bar.pack(fill="x", pady=(0,6))
        self.tp_progress_bar.set(0)

        dry = self.dry_run_var.get()
        self.tp_start_btn = ctk.CTkButton(bot,
                                          text="🧹  Purge Selected 3rd Party Caches",
                                          font=ctk.CTkFont("Segoe UI",13,"bold"),
                                          height=40, corner_radius=8,
                                          fg_color="#3a2000" if dry else th["accent_dark"],
                                          hover_color=th["accent_hover"],
                                          text_color=th["warn"] if dry else th["accent"],
                                          command=self._tp_start_purge)
        self.tp_start_btn.pack(fill="x")

        # Kick off size scan
        self.after(400, self._tp_refresh_total)

    def _tp_refresh_total(self):
        """Background scan total size of checked 3rd party tasks."""
        from core.cleaner import TASKS, ep, folder_size
        th = self.th
        def _scan():
            total = 0
            for task in TASKS:
                tid = task[0]
                var = self._tp_task_vars.get(tid)
                if not var or not var.get():
                    continue
                rp = ep(task[3]) if task[4] else task[3]
                try:
                    if os.path.exists(rp):
                        total += folder_size(rp)
                except Exception:
                    pass
            try:
                self.after(0, lambda: self.tp_total_lbl.configure(
                    text=f"  💾  Total selected size: {fmt_size(total)}",
                    text_color=th["accent"] if total > 0 else th["text_gray"]))
            except Exception:
                pass
        threading.Thread(target=_scan, daemon=True).start()

    def _tp_start_purge(self):
        from core.cleaner import TASKS, run_task, fmt_size
        th = self.th
        selected = [t for t in TASKS
                    if t[0] in self._tp_task_vars and self._tp_task_vars[t[0]].get()]
        if not selected:
            from tkinter import messagebox
            messagebox.showwarning("Nothing Selected", "Select at least one item to clean.")
            return

        dry = self.dry_run_var.get()
        if self.running:
            from tkinter import messagebox
            messagebox.showwarning("Purge running",
                                   "Another purge is already running. Please wait for it to finish.")
            return
        self.running = True
        self._cancel_flag = False
        self._set_ui_locked(True)
        self.tp_start_btn.configure(state="disabled", text="⏳  Running...")
        reboot = [False]
        total_freed = [0]
        done_count  = [0]

        def _progress(msg):
            try:
                self.after(0, lambda: self.tp_progress_lbl.configure(text=msg))
            except Exception:
                pass

        def _run_inner():
            for i, task in enumerate(selected):
                pct = i / max(len(selected), 1)
                try:
                    self.after(0, lambda p=pct: self.tp_progress_bar.set(p))
                except Exception:
                    pass
                _progress(f"[{i+1}/{len(selected)}] {task[2]}...")
                t0 = self._log_task_start(task[0], task[2])
                freed = run_task(task[0], self._log, reboot, dry)
                total_freed[0] += freed
                self._log_task_end(task[0], t0, freed)
                done_count[0]  += 1

            try:
                self.after(0, lambda: (
                    self.tp_progress_bar.set(1.0),
                    self.tp_progress_lbl.configure(
                        text=f"✅ Done — freed {fmt_size(total_freed[0])}"),
                    self.tp_start_btn.configure(
                        state="normal",
                        text="🧹  Purge Selected 3rd Party Caches")
                ))
            except Exception:
                pass
            self._log(f"\n✅ 3rd Party purge done. Freed: {fmt_size(total_freed[0])}", "success")

        def _run():
            try:
                _run_inner()
            except Exception as e:
                self._log(f"  ❌ 3rd Party purge stopped by an unexpected error: {e}", "error")
            finally:
                def _done():
                    try:
                        self.tp_start_btn.configure(
                            state="normal", text="🧹  Purge Selected 3rd Party Caches")
                    except Exception:
                        pass
                    self._set_ui_locked(False)
                    self.running = False
                self.after(0, _done)

        threading.Thread(target=_run, daemon=True).start()

    # ── System Info Panel ────────────────────────────────────
    def _panel_sysinfo(self, parent):
        th = self.th
        ctk.CTkLabel(parent, text="💻  System Info",
                     font=ctk.CTkFont("Segoe UI",14,"bold"),
                     text_color=th["accent"]).pack(pady=(12,8), padx=12, anchor="w")
        scroll = ctk.CTkScrollableFrame(parent, fg_color=th["bg_darkest"],
                                        corner_radius=8,
                                        scrollbar_button_color=th["accent_dark"],
                                        scrollbar_button_hover_color=th["accent"])
        scroll.pack(fill="both", expand=True, padx=8, pady=(0,4))
        self.after(100, lambda f=scroll: self._boost_scroll(f))
        ctk.CTkButton(parent, text="🔄  Refresh",
                      font=ctk.CTkFont("Segoe UI",12),
                      height=32, corner_radius=8,
                      fg_color=th["bg_card"], hover_color=th["bg_hover"],
                      text_color=th["text_gray"],
                      command=lambda: self._load_sysinfo(scroll)
                      ).pack(fill="x", padx=12, pady=(4,8))
        self._load_sysinfo(scroll)

    def _load_sysinfo(self, parent):
        th = self.th
        for w in parent.winfo_children():
            w.destroy()

        loading = ctk.CTkLabel(parent, text="Loading system info...",
                               font=ctk.CTkFont("Segoe UI",11),
                               text_color=th["text_gray"])
        loading.pack(pady=20)

        def _fetch():
            import platform, ctypes as _ct
            info = {}
            info["OS"]           = platform.platform()
            info["Machine"]      = platform.node()
            info["Architecture"] = platform.machine()
            info["Processor"]    = platform.processor() or "Unknown"

            # RAM
            try:
                class MEMSTATUS(_ct.Structure):
                    _fields_ = [
                        ("dwLength",                _ct.c_ulong),
                        ("dwMemoryLoad",            _ct.c_ulong),
                        ("ullTotalPhys",            _ct.c_ulonglong),
                        ("ullAvailPhys",            _ct.c_ulonglong),
                        ("ullTotalPageFile",        _ct.c_ulonglong),
                        ("ullAvailPageFile",        _ct.c_ulonglong),
                        ("ullTotalVirtual",         _ct.c_ulonglong),
                        ("ullAvailVirtual",         _ct.c_ulonglong),
                        ("ullAvailExtendedVirtual", _ct.c_ulonglong),
                    ]
                ms = MEMSTATUS()
                ms.dwLength = _ct.sizeof(ms)
                _ct.windll.kernel32.GlobalMemoryStatusEx(_ct.byref(ms))
                total_ram = ms.ullTotalPhys
                avail_ram = ms.ullAvailPhys
                used_ram  = total_ram - avail_ram
                ram_pct   = (used_ram / total_ram) if total_ram else 0
                info["RAM Total"]     = fmt_size(total_ram)
                info["RAM Available"] = fmt_size(avail_ram)
                info["RAM Used"]      = f"{fmt_size(used_ram)}  ({int(ram_pct*100)}%)"
                info["_ram_pct"]      = ram_pct
            except Exception:
                info["RAM Total"]  = "Unavailable"
                info["_ram_pct"]   = 0

            # Windows version
            try:
                import winreg as _wr
                key     = _wr.OpenKey(_wr.HKEY_LOCAL_MACHINE,
                                       r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                product = _wr.QueryValueEx(key, "ProductName")[0]
                build   = _wr.QueryValueEx(key, "CurrentBuildNumber")[0]
                info["Windows"] = f"{product}  (Build {build})"
                _wr.CloseKey(key)
            except Exception:
                info["Windows"] = platform.version()

            # Uptime
            try:
                ms_up = _ct.windll.kernel32.GetTickCount64()
                secs  = ms_up // 1000
                h, m  = divmod(secs // 60, 60)
                d, h  = divmod(h, 24)
                info["Uptime"] = f"{d}d {h}h {m}m"
            except Exception:
                info["Uptime"] = "Unavailable"

            # Drives
            info["_drives"] = {}
            for drv, label, free, total in get_drives():
                if total > 0:
                    used = total - free
                    pct  = used / total
                    name = f"{drv}  {label}" if label else drv
                    info["_drives"][name] = (free, total, used, pct)

            return info

        def _render(info):
            try:
                loading.destroy()
            except Exception:
                pass

            def section(title):
                ctk.CTkLabel(parent, text=title,
                             font=ctk.CTkFont("Segoe UI",12,"bold"),
                             text_color=th["accent"], anchor="w"
                             ).pack(fill="x", padx=4, pady=(10,3))

            def info_row(label, value):
                row = ctk.CTkFrame(parent, fg_color=th["bg_card"], corner_radius=6)
                row.pack(fill="x", pady=2, padx=2)
                ctk.CTkLabel(row, text=label,
                             font=ctk.CTkFont("Segoe UI",11),
                             text_color=th["text_gray"],
                             width=140, anchor="w").pack(side="left", padx=12, pady=7)
                ctk.CTkLabel(row, text=value,
                             font=ctk.CTkFont("Segoe UI",11,"bold"),
                             text_color=th["text_white"],
                             anchor="w").pack(side="left", padx=(0,12))

            def bar_row(label, value_str, pct):
                card = ctk.CTkFrame(parent, fg_color=th["bg_card"], corner_radius=6)
                card.pack(fill="x", pady=2, padx=2)
                top  = ctk.CTkFrame(card, fg_color="transparent")
                top.pack(fill="x", padx=12, pady=(7,2))
                ctk.CTkLabel(top, text=label,
                             font=ctk.CTkFont("Segoe UI",11),
                             text_color=th["text_gray"],
                             width=140, anchor="w").pack(side="left")
                ctk.CTkLabel(top, text=value_str,
                             font=ctk.CTkFont("Segoe UI",11,"bold"),
                             text_color=th["text_white"],
                             anchor="w").pack(side="left")
                bar_color = (th["error"] if pct > 0.85 else
                             th["warn"]  if pct > 0.65 else th["accent"])
                bar = ctk.CTkProgressBar(card, height=8,
                                         fg_color=th["bg_darkest"],
                                         progress_color=bar_color,
                                         corner_radius=4)
                bar.pack(fill="x", padx=12, pady=(2,8))
                bar.set(pct)

            section("🖥  System")
            info_row("Windows",       info.get("Windows",""))
            info_row("Machine",       info.get("Machine",""))
            info_row("Architecture",  info.get("Architecture",""))
            info_row("Uptime",        info.get("Uptime",""))

            section("🧠  Memory (RAM)")
            bar_row("RAM Used", info.get("RAM Used",""), info.get("_ram_pct",0))
            info_row("RAM Total",     info.get("RAM Total",""))
            info_row("RAM Available", info.get("RAM Available",""))

            section("💾  Disk Usage")
            for drv_name, (free, total, used, pct) in info.get("_drives",{}).items():
                bar_row(drv_name,
                        f"{fmt_size(used)} used / {fmt_size(total)}  ({int(pct*100)}% used)",
                        pct)

            section("⚡  Processor")
            proc = info.get("Processor","")
            if proc and proc != "Unknown":
                row = ctk.CTkFrame(parent, fg_color=th["bg_card"], corner_radius=6)
                row.pack(fill="x", pady=2, padx=2)
                ctk.CTkLabel(row, text=proc,
                             font=ctk.CTkFont("Segoe UI",10),
                             text_color=th["text_white"],
                             wraplength=500, anchor="w",
                             justify="left").pack(padx=12, pady=8, fill="x")

        def _worker():
            try:
                data = _fetch()
                self.after(0, lambda: _render(data))
            except Exception as ex:
                err = str(ex)          # 'ex' is deleted when this block ends
                self.after(0, lambda: ctk.CTkLabel(
                    parent, text=f"Error loading system info:\n{err}",
                    font=ctk.CTkFont("Segoe UI",10),
                    text_color=th["error"]).pack(pady=20))

        threading.Thread(target=_worker, daemon=True).start()

    # ── Software Updater Panel ───────────────────────────────
    # ── Software Updater Panel ───────────────────────────────
    # ── Software Updater Panel ───────────────────────────────
    def _panel_updater(self, parent):
        th = self.th
        self._updater_apps          = []
        self._updater_check_vars    = {}
        self._updater_status_labels = {}
        self._updater_dl_btns       = {}
        self._updater_busy          = False
        self._updater_queue         = []

        ctk.CTkLabel(parent, text="🔄  Software Updater",
                     font=ctk.CTkFont("Segoe UI",14,"bold"),
                     text_color=th["accent"]).pack(pady=(10,2), padx=12, anchor="w")
        ctk.CTkLabel(parent,
                     text="Downloads official installers via winget — you install them. One at a time, no silent execution.",
                     font=ctk.CTkFont("Segoe UI",10),
                     text_color=th["text_gray"]).pack(padx=12, anchor="w", pady=(0,6))

        if not is_winget_available():
            wf = ctk.CTkFrame(parent, fg_color="#1a0a00", corner_radius=8)
            wf.pack(fill="x", padx=12, pady=(0,8))
            ctk.CTkLabel(wf,
                         text="⚠  winget not found. Install Windows Package Manager to use this feature.",
                         font=ctk.CTkFont("Segoe UI",11),
                         text_color=th["warn"], wraplength=620, justify="left"
                         ).pack(padx=14, pady=(10,4), anchor="w")
            ctk.CTkButton(wf, text="🌐  Get winget",
                          font=ctk.CTkFont("Segoe UI",11), height=28,
                          corner_radius=6, fg_color=th["bg_card"],
                          hover_color=th["bg_hover"], text_color=th["text_white"],
                          command=lambda: __import__("webbrowser").open("https://aka.ms/getwinget")
                          ).pack(padx=14, pady=(0,10), anchor="w")
            return

        # Progress
        self.upd_progress_lbl = ctk.CTkLabel(parent, text="Press Scan to check for updates.",
                                              font=ctk.CTkFont("Segoe UI",10),
                                              text_color=th["text_gray"])
        self.upd_progress_lbl.pack(padx=12, anchor="w")
        self.upd_progress_bar = ctk.CTkProgressBar(parent, height=6,
                                                    fg_color=th["bg_card"],
                                                    progress_color=th["accent"],
                                                    corner_radius=3)
        self.upd_progress_bar.pack(fill="x", padx=12, pady=(2,4))
        self.upd_progress_bar.set(0)

        # Stats row
        stats = ctk.CTkFrame(parent, fg_color=th["bg_card"], corner_radius=6)
        stats.pack(fill="x", padx=12, pady=(0,4))
        self.upd_total_lbl = ctk.CTkLabel(stats, text="Updates found: —",
                                           font=ctk.CTkFont("Segoe UI",11),
                                           text_color=th["text_gray"])
        self.upd_total_lbl.pack(side="left", padx=12, pady=5)
        self.upd_sel_lbl = ctk.CTkLabel(stats, text="",
                                         font=ctk.CTkFont("Segoe UI",10),
                                         text_color=th["text_dim"])
        self.upd_sel_lbl.pack(side="right", padx=12)

        # Column header
        hdr = ctk.CTkFrame(parent, fg_color=th["accent_dark"], corner_radius=6)
        hdr.pack(fill="x", padx=12, pady=(0,2))
        hdr.grid_columnconfigure(1, weight=1)
        for col, (txt, w) in enumerate([
            ("", 28), ("Application", 0), ("Current", 90),
            ("Latest", 90), ("Source", 70), ("Status", 140)
        ]):
            ctk.CTkLabel(hdr, text=txt if txt else "☑",
                         font=ctk.CTkFont("Segoe UI",10,"bold"),
                         text_color=th["accent"],
                         width=w, anchor="w"
                         ).grid(row=0, column=col,
                                padx=(8 if col==0 else 4, 4),
                                pady=4,
                                sticky="w" if col <= 1 else "")

        # Scroll
        self.upd_scroll = ctk.CTkScrollableFrame(parent, fg_color=th["bg_darkest"],
                                                  corner_radius=6,
                                                  scrollbar_button_color=th["accent_dark"],
                                                  scrollbar_button_hover_color=th["accent"])
        self.upd_scroll.pack(fill="both", expand=True, padx=12, pady=(0,4))
        self.after(100, lambda f=self.upd_scroll: self._boost_scroll(f))
        # Force correct bg — needed when theme changes dynamically
        try:
            self.upd_scroll.configure(fg_color=th["bg_darkest"])
            self.upd_scroll._parent_canvas.configure(bg=th["bg_darkest"])
        except Exception:
            pass

        self.upd_empty_lbl = ctk.CTkLabel(self.upd_scroll,
                                           text="Press Scan to check for available updates.",
                                           font=ctk.CTkFont("Segoe UI",11),
                                           text_color=th["text_dim"])
        self.upd_empty_lbl.pack(pady=30)

        # Bottom buttons
        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0,8))

        ctk.CTkButton(btn_row, text="🔍  Scan",
                      font=ctk.CTkFont("Segoe UI",12,"bold"),
                      height=36, width=110, corner_radius=8,
                      fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                      text_color=th["accent"],
                      command=self._updater_scan).pack(side="left", padx=(0,6))

        self.upd_dl_all_btn = ctk.CTkButton(btn_row, text="⬇  Download Selected",
                                             font=ctk.CTkFont("Segoe UI",12,"bold"),
                                             height=36, width=170, corner_radius=8,
                                             fg_color="#1a1200", hover_color="#2a1e00",
                                             text_color=th["warn"],
                                             state="disabled",
                                             command=self._updater_download_all)
        self.upd_dl_all_btn.pack(side="left", padx=(0,6))

        ctk.CTkButton(btn_row, text="✔ All",
                      font=ctk.CTkFont("Segoe UI",11),
                      height=36, width=70, corner_radius=8,
                      fg_color=th["bg_card"], hover_color=th["bg_hover"],
                      text_color=th["text_gray"],
                      command=self._updater_select_all).pack(side="left", padx=(0,4))

        ctk.CTkButton(btn_row, text="✘ None",
                      font=ctk.CTkFont("Segoe UI",11),
                      height=36, width=70, corner_radius=8,
                      fg_color=th["bg_card"], hover_color=th["bg_hover"],
                      text_color=th["text_gray"],
                      command=self._updater_deselect_all).pack(side="left")

        # Downloads folder note
        dl_path = os.path.join(os.path.expanduser("~"), "Downloads", "PurgeKit", "Installers")
        ctk.CTkLabel(btn_row,
                     text=f"📁 {dl_path}",
                     font=ctk.CTkFont("Segoe UI",9),
                     text_color=th["text_dim"]).pack(side="right")

    # ── Scan ─────────────────────────────────────────────────
    def _updater_scan(self):
        th = self.th
        for w in self.upd_scroll.winfo_children():
            w.destroy()
        self._updater_apps          = []
        self._updater_check_vars    = {}
        self._updater_status_labels = {}
        self._updater_dl_btns       = {}
        self._updater_queue         = []
        self._updater_busy          = False
        self.upd_total_lbl.configure(text="Updates found: scanning...")
        self.upd_sel_lbl.configure(text="")
        try:
            self.upd_dl_all_btn.configure(state="disabled")
        except Exception:
            pass

        loading = ctk.CTkLabel(self.upd_scroll, text="⏳  Scanning installed apps...",
                               font=ctk.CTkFont("Segoe UI",11),
                               text_color=th["text_gray"])
        loading.pack(pady=30)

        def progress(pct, msg):
            try:
                self.after(0, lambda: (
                    self.upd_progress_bar.set(pct),
                    self.upd_progress_lbl.configure(text=msg)
                ))
            except Exception:
                pass

        def do_scan():
            apps = get_upgradeable_apps(progress)
            self._updater_apps = apps

            def render():
                try:
                    loading.destroy()
                except Exception:
                    pass

                if not apps:
                    ctk.CTkLabel(self.upd_scroll,
                                 text="✅  All your apps are up to date!",
                                 font=ctk.CTkFont("Segoe UI",12,"bold"),
                                 text_color=th["accent"]).pack(pady=30)
                    self.upd_total_lbl.configure(text="Updates found: 0")
                    return

                self.upd_total_lbl.configure(text=f"Updates found: {len(apps)}")
                try:
                    self.upd_dl_all_btn.configure(state="normal")
                except Exception:
                    pass

                # Freeze redraws during bulk row creation — eliminates flicker
                self.upd_scroll.pack_propagate(False)
                try:
                    self.upd_scroll._parent_canvas.configure(state="disabled")
                except Exception:
                    pass

                # Build all rows then render at once — no flicker
                self.upd_scroll.configure(fg_color=th["bg_darkest"])
                for app in apps:
                    app_id = app["id"]
                    var    = tk.BooleanVar(value=True)
                    self._updater_check_vars[app_id] = var

                    row = ctk.CTkFrame(self.upd_scroll, fg_color=th["bg_card"] if th["bg_card"] != "#f0f4f0" else th["bg_card"], corner_radius=5)
                    row.pack(fill="x", pady=1, padx=2)
                    row.grid_columnconfigure(1, weight=1)

                    # Checkbox
                    ctk.CTkCheckBox(row, text="", variable=var,
                                    fg_color=th["accent_dark"], hover_color=th["accent_dark"],
                                    checkmark_color=th["accent"], border_color=th["text_dim"],
                                    width=16, height=16,
                                    command=self._updater_count_selected
                                    ).grid(row=0, column=0, padx=(8,4), pady=4, sticky="w")

                    # Name + id in one compact cell
                    name_f = ctk.CTkFrame(row, fg_color="transparent")
                    name_f.grid(row=0, column=1, padx=(2,4), pady=3, sticky="w")
                    ctk.CTkLabel(name_f,
                                 text=app["name"][:44] + ("…" if len(app["name"])>44 else ""),
                                 font=ctk.CTkFont("Segoe UI",11,"bold"),
                                 text_color=th["text_white"],
                                 anchor="w").pack(anchor="w")
                    ctk.CTkLabel(name_f,
                                 text=app_id[:52],
                                 font=ctk.CTkFont("Consolas",8),
                                 text_color=th["text_dim"],
                                 anchor="w").pack(anchor="w")

                    # Current
                    ctk.CTkLabel(row,
                                 text=app["version"][:12] if app["version"] else "—",
                                 font=ctk.CTkFont("Consolas",10),
                                 text_color=th["text_gray"],
                                 width=90, anchor="w"
                                 ).grid(row=0, column=2, padx=4, pady=4)

                    # Latest
                    ctk.CTkLabel(row,
                                 text=app["available"][:12] if app["available"] else "—",
                                 font=ctk.CTkFont("Consolas",10,"bold"),
                                 text_color=th["accent"],
                                 width=90, anchor="w"
                                 ).grid(row=0, column=3, padx=4, pady=4)

                    # Source
                    ctk.CTkLabel(row,
                                 text=app["source"][:10] if app["source"] else "—",
                                 font=ctk.CTkFont("Segoe UI",9),
                                 text_color=th["text_dim"],
                                 width=70, anchor="w"
                                 ).grid(row=0, column=4, padx=4, pady=4)

                    # Status label (shows pending / downloading / ✅ / ❌)
                    status_lbl = ctk.CTkLabel(row, text="—",
                                              font=ctk.CTkFont("Segoe UI",10),
                                              text_color=th["text_dim"],
                                              width=130, anchor="w")
                    status_lbl.grid(row=0, column=5, padx=(4,8), pady=4)
                    self._updater_status_labels[app_id] = status_lbl

                # Unfreeze — show all rows at once
                try:
                    self.upd_scroll._parent_canvas.configure(state="normal")
                except Exception:
                    pass
                self.upd_scroll.pack_propagate(True)
                self.upd_scroll.update_idletasks()

                self.upd_scroll.update_idletasks()
                self._updater_count_selected()
                self.upd_scroll.update_idletasks()

            self.after(0, render)

        threading.Thread(target=do_scan, daemon=True).start()

    def _updater_count_selected(self):
        try:
            count = sum(1 for v in self._updater_check_vars.values() if v.get())
            self.upd_sel_lbl.configure(text=f"Selected: {count}")
        except Exception:
            pass

    def _updater_select_all(self):
        try:
            for v in self._updater_check_vars.values():
                v.set(True)
            self._updater_count_selected()
        except Exception:
            pass

    def _updater_deselect_all(self):
        try:
            for v in self._updater_check_vars.values():
                v.set(False)
            self._updater_count_selected()
        except Exception:
            pass

    def _updater_download_all(self):
        """Queue all selected apps for sequential download."""
        selected = [
            app for app in self._updater_apps
            if self._updater_check_vars.get(app["id"], tk.BooleanVar()).get()
        ]
        if not selected:
            from tkinter import messagebox
            messagebox.showwarning("Nothing Selected", "Select at least one app to download.")
            return

        # Build queue and start
        self._updater_queue = list(selected)
        self._updater_busy  = False

        # Mark all selected as queued
        for app in selected:
            lbl = self._updater_status_labels.get(app["id"])
            if lbl:
                lbl.configure(text="⏳ Queued", text_color=self.th["text_dim"])

        try:
            self.upd_dl_all_btn.configure(state="disabled", text="⬇  Downloading...")
        except Exception:
            pass

        self._updater_next_in_queue()

    def _updater_next_in_queue(self):
        """Start the next download in the queue."""
        if not self._updater_queue:
            # All done
            try:
                self.upd_dl_all_btn.configure(state="normal", text="⬇  Download Selected")
                self.upd_progress_lbl.configure(text="✅ All downloads complete!")
            except Exception:
                pass
            self._log("  ✅ All queued downloads complete.", "success")
            return

        app = self._updater_queue.pop(0)
        self._updater_busy = True
        app_id = app["id"]
        name   = app["name"]

        lbl = self._updater_status_labels.get(app_id)
        if lbl:
            lbl.configure(text="⬇ Downloading...", text_color=self.th["warn"])

        remaining = len(self._updater_queue)
        total_sel = sum(1 for v in self._updater_check_vars.values() if v.get()) + remaining + 1

        def progress(pct, msg):
            try:
                self.after(0, lambda: (
                    self.upd_progress_bar.set(pct),
                    self.upd_progress_lbl.configure(text=f"[{name[:30]}]  {msg}")
                ))
            except Exception:
                pass

        def done(success, message, file_path):
            self._updater_busy = False

            def _ui():
                th = self.th
                if success and file_path and os.path.exists(file_path):
                    fname   = os.path.basename(file_path)
                    sz_mb   = os.path.getsize(file_path) / (1 << 20)
                    if lbl:
                        # Small tick + filename, no open button
                        lbl.configure(
                            text=f"✅ {fname[:22]}… ({sz_mb:.0f}MB)" if len(fname)>22 else f"✅ {fname} ({sz_mb:.0f}MB)",
                            text_color=th["success"])
                    self._log(f"  ✅ {name}: {file_path}", "success")
                    open_in_folder(file_path)
                else:
                    if lbl:
                        lbl.configure(text=f"❌ Failed", text_color=th["error"])
                    self._log(f"  ❌ {name}: {message[:60]}", "error")

                # Start next in queue
                self.after(500, self._updater_next_in_queue)

            self.after(0, _ui)

        download_installer(app_id, name, progress_fn=progress, done_fn=done)

    def _panel_settings(self, parent):
        th = self.th
        T  = self.T

        scroll = ctk.CTkScrollableFrame(parent, fg_color=th["bg_darkest"], corner_radius=0,
                                        scrollbar_button_color=th["accent_dark"],
                                        scrollbar_button_hover_color=th["accent"])
        scroll.pack(fill="both", expand=True, padx=4, pady=4)
        self.after(100, lambda f=scroll: self._boost_scroll(f))

        def section(title, color=None):
            ctk.CTkLabel(scroll, text=title,
                         font=ctk.CTkFont("Segoe UI",13,"bold"),
                         text_color=color or th["accent"],
                         anchor="w").pack(fill="x", padx=4, pady=(14,4))

        def card():
            f = ctk.CTkFrame(scroll, fg_color=th["bg_card"], corner_radius=8)
            f.pack(fill="x", pady=3, padx=2)
            return f

        def row_in(parent, pady=10):
            r = ctk.CTkFrame(parent, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=pady)
            return r

        # Language
        section(f"🌐  {t(T,'settings_language')}")
        lf = card()
        r  = row_in(lf)
        ctk.CTkLabel(r, text=t(T,"settings_language"),
                     font=ctk.CTkFont("Segoe UI",12),
                     text_color=th["text_white"], width=140, anchor="w").pack(side="left")
        cur_lang_name = LANGUAGES.get(self.cfg.get("language","en"),"English")
        self._lang_var_s = tk.StringVar(value=cur_lang_name)
        ctk.CTkOptionMenu(r,
                          values=list(LANGUAGES.values()),
                          variable=self._lang_var_s,
                          fg_color=th["bg_card"],
                          button_color=th["accent_dark"],
                          button_hover_color=th["accent_hover"],
                          text_color=th["text_white"],
                          font=ctk.CTkFont("Segoe UI",11),
                          command=self._on_lang_change,
                          width=220).pack(side="right")

        # Theme
        section(f"🎨  {t(T,'settings_theme')}")
        tf = card()
        r  = row_in(tf)
        ctk.CTkLabel(r, text=t(T,"settings_theme"),
                     font=ctk.CTkFont("Segoe UI",12),
                     text_color=th["text_white"], width=140, anchor="w").pack(side="left")
        self._theme_var_s = tk.StringVar(value=self.cfg.get("theme","Green"))
        ctk.CTkSegmentedButton(r, values=["Green","Blue","Purple","White"],
                               variable=self._theme_var_s,
                               fg_color=th["bg_darkest"],
                               selected_color=th["accent_dark"],
                               selected_hover_color=th["accent_hover"],
                               unselected_color=th["bg_hover"],
                               unselected_hover_color=th["bg_card"],
                               text_color=th["text_white"],
                               font=ctk.CTkFont("Segoe UI",12),
                               command=self._on_theme_change).pack(side="right")

        # Dry Run
        section("🔍  Dry Run Mode")
        dr = card()
        r  = row_in(dr)
        ctk.CTkLabel(r, text=t(T,"settings_dry_run"),
                     font=ctk.CTkFont("Segoe UI",12),
                     text_color=th["text_white"],
                     wraplength=380, justify="left").pack(side="left", fill="x", expand=True)
        ctk.CTkSwitch(r, text="", variable=self.dry_run_var,
                      command=self._on_dryrun_toggle,
                      width=44, height=22,
                      button_color=th["warn"], button_hover_color=th["warn"],
                      progress_color="#3a2000").pack(side="right")

        # Auto-start
        section(f"🚀  {t(T,'settings_autostart')}")
        asf = card()
        r   = row_in(asf)
        ctk.CTkLabel(r, text=t(T,"settings_autostart"),
                     font=ctk.CTkFont("Segoe UI",12),
                     text_color=th["text_white"]).pack(side="left", fill="x", expand=True)
        ctk.CTkSwitch(r, text="", variable=self.autostart_var,
                      command=self._toggle_autostart,
                      width=44, height=22,
                      button_color=th["accent"], button_hover_color=th["accent_dim"],
                      progress_color=th["accent_dark"]).pack(side="right")
        ctk.CTkLabel(asf, text=f"  {t(T,'settings_autostart_note')}",
                     font=ctk.CTkFont("Segoe UI",10),
                     text_color=th["text_gray"], anchor="w").pack(fill="x", padx=14, pady=(0,10))

        # PIN Lock
        section(f"🔐  {t(T,'settings_pin')}", color=th["warn"])
        pf = card()
        r  = row_in(pf)
        pin_enabled = self.cfg.get("pin_enabled", False)
        self._pin_sw_var = tk.BooleanVar(value=pin_enabled)
        ctk.CTkLabel(r, text=t(T,"settings_pin_enable"),
                     font=ctk.CTkFont("Segoe UI",12),
                     text_color=th["text_white"]).pack(side="left")
        ctk.CTkSwitch(r, text="", variable=self._pin_sw_var,
                      command=self._toggle_pin,
                      width=44, height=22,
                      button_color=th["warn"], button_hover_color=th["warn"],
                      progress_color="#3a2000").pack(side="right")
        r2 = row_in(pf, pady=4)
        ctk.CTkButton(r2, text=t(T,"settings_pin_set"), width=130, height=30,
                      fg_color=th["bg_darkest"], hover_color=th["bg_hover"],
                      text_color=th["warn"],
                      font=ctk.CTkFont("Segoe UI",12), corner_radius=6,
                      command=self._set_pin_dialog).pack(side="left", padx=(0,8))
        ctk.CTkButton(r2, text=t(T,"settings_pin_disable"), width=130, height=30,
                      fg_color=th["bg_darkest"], hover_color=th["bg_hover"],
                      text_color=th["text_gray"],
                      font=ctk.CTkFont("Segoe UI",12), corner_radius=6,
                      command=self._disable_pin).pack(side="left")

        # Scheduler
        section(f"🗓  {t(T,'settings_scheduler')}")
        sf = card()
        self._sched_var = tk.BooleanVar(value=schedule_exists())
        r  = row_in(sf)
        ctk.CTkLabel(r, text=t(T,"settings_scheduler_enable"),
                     font=ctk.CTkFont("Segoe UI",12),
                     text_color=th["text_white"]).pack(side="left")
        ctk.CTkSwitch(r, text="", variable=self._sched_var,
                      command=self._toggle_scheduler,
                      width=44, height=22,
                      button_color=th["accent"], button_hover_color=th["accent_dim"],
                      progress_color=th["accent_dark"]).pack(side="right")
        r2 = row_in(sf, pady=4)
        self._freq_var = tk.StringVar(value=self.cfg["scheduler"].get("frequency","weekly").capitalize())
        ctk.CTkLabel(r2, text=t(T,"settings_frequency"),
                     font=ctk.CTkFont("Segoe UI",11),
                     text_color=th["text_gray"]).pack(side="left", padx=(0,8))
        ctk.CTkSegmentedButton(r2,
                               values=[t(T,"settings_weekly"), t(T,"settings_monthly")],
                               variable=self._freq_var,
                               fg_color=th["bg_darkest"],
                               selected_color=th["accent_dark"],
                               unselected_color=th["bg_hover"],
                               text_color=th["text_white"],
                               font=ctk.CTkFont("Segoe UI",11),
                               width=200).pack(side="left")
        next_run = get_next_run()
        ctk.CTkLabel(sf, text=f"  Next run: {next_run}",
                     font=ctk.CTkFont("Segoe UI",10),
                     text_color=th["text_gray"], anchor="w").pack(fill="x", padx=14, pady=(0,10))

        # Whitelist
        section(f"🚫  {t(T,'settings_whitelist')}")
        wf = card()
        self.wl_box = ctk.CTkTextbox(wf, height=80,
                                      fg_color=th["bg_darkest"],
                                      text_color=th["text_white"],
                                      font=ctk.CTkFont("Consolas",11))
        self.wl_box.pack(fill="x", padx=10, pady=(10,4))
        self.wl_box.insert("end", "\n".join(self.whitelist))
        r2 = row_in(wf, pady=6)
        ctk.CTkButton(r2, text=t(T,"settings_add_path"), width=130, height=28,
                      fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                      text_color=th["accent"],
                      font=ctk.CTkFont("Segoe UI",11), corner_radius=6,
                      command=self._add_whitelist).pack(side="left", padx=(0,8))
        ctk.CTkButton(r2, text=t(T,"settings_remove_path"), width=140, height=28,
                      fg_color=th["bg_darkest"], hover_color=th["bg_hover"],
                      text_color=th["text_gray"],
                      font=ctk.CTkFont("Segoe UI",11), corner_radius=6,
                      command=self._clear_whitelist).pack(side="left")

        # Save
        ctk.CTkFrame(scroll, fg_color="transparent", height=8).pack()
        ctk.CTkButton(scroll, text=t(T,"settings_save"),
                      font=ctk.CTkFont("Segoe UI",13,"bold"),
                      height=40, corner_radius=8,
                      fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                      text_color=th["accent"],
                      command=self._save_settings).pack(fill="x", padx=4, pady=(0,8))

    # ── About Panel ──────────────────────────────────────────
    def _panel_about(self, parent):
        th = self.th
        T  = self.T

        scroll = ctk.CTkScrollableFrame(parent, fg_color=th["bg_darkest"], corner_radius=0,
                                        scrollbar_button_color=th["accent_dark"],
                                        scrollbar_button_hover_color=th["accent"])
        scroll.pack(fill="both", expand=True, padx=4, pady=4)
        self.after(100, lambda f=scroll: self._boost_scroll(f))

        try:
            acc = tuple(int(th["accent"].lstrip("#")[i:i+2],16) for i in (0,2,4))
            li  = generate_icon(acc)
            lc  = ctk.CTkImage(light_image=li, dark_image=li, size=(72,72))
            ctk.CTkLabel(scroll, image=lc, text="").pack(pady=(16,8))
        except Exception:
            pass

        ctk.CTkLabel(scroll, text="PurgeKit",
                     font=ctk.CTkFont("Segoe UI",26,"bold"),
                     text_color=th["accent"]).pack()
        ctk.CTkLabel(scroll, text=f"v{APP_VERSION}  —  {t(T,'app_subtitle')}",
                     font=ctk.CTkFont("Segoe UI",12),
                     text_color=th["text_gray"]).pack(pady=(2,16))

        # Info card — properly aligned two columns
        info_f = ctk.CTkFrame(scroll, fg_color=th["bg_card"], corner_radius=10)
        info_f.pack(fill="x", padx=16, pady=(0,12))

        rows = [
            (f"Built by",  AUTHOR_NAME),
            ("Location",             AUTHOR_LOC),
            ("Brand",                AUTHOR_BRAND),
            ("License",              "MIT — Free & Open Source"),
            ("Platform",             "Windows 10 / 11"),
            (t(T,"about_version"),   APP_VERSION),
        ]
        for lbl, val in rows:
            r = ctk.CTkFrame(info_f, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=5)
            # Fixed width left column — right aligned label
            ctk.CTkLabel(r, text=lbl,
                         font=ctk.CTkFont("Segoe UI",11),
                         text_color=th["text_gray"],
                         width=140, anchor="w").pack(side="left")
            ctk.CTkLabel(r, text=val,
                         font=ctk.CTkFont("Segoe UI",11,"bold"),
                         text_color=th["text_white"],
                         anchor="w").pack(side="left", padx=(8,0))

        # GitHub
        ctk.CTkLabel(scroll, text=t(T,"about_github"),
                     font=ctk.CTkFont("Segoe UI",11),
                     text_color=th["text_gray"]).pack(pady=(10,4))
        ctk.CTkButton(scroll, text=GITHUB_URL,
                      font=ctk.CTkFont("Segoe UI",11,"bold"),
                      fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                      text_color=th["accent"], height=34, corner_radius=8,
                      command=self._open_github).pack(padx=16, pady=(0,10), fill="x")

        # ── Update section ───────────────────────────────────
        upd_f = ctk.CTkFrame(scroll, fg_color=th["bg_card"], corner_radius=10)
        upd_f.pack(fill="x", padx=16, pady=(0,12))

        self.update_status_lbl = ctk.CTkLabel(upd_f,
                                               text=t(T,"update_check"),
                                               font=ctk.CTkFont("Segoe UI",11),
                                               text_color=th["text_gray"])
        self.update_status_lbl.pack(padx=14, pady=(10,4), anchor="w")

        self.update_progress_bar = ctk.CTkProgressBar(upd_f, height=8,
                                                       fg_color=th["bg_darkest"],
                                                       progress_color=th["accent"],
                                                       corner_radius=4)
        self.update_progress_bar.pack(fill="x", padx=14, pady=(0,4))
        self.update_progress_bar.set(0)
        self.update_progress_bar.pack_forget()  # hidden until download starts

        self.update_progress_lbl = ctk.CTkLabel(upd_f, text="",
                                                  font=ctk.CTkFont("Segoe UI",10),
                                                  text_color=th["text_gray"])
        self.update_progress_lbl.pack(padx=14, anchor="w")
        self.update_progress_lbl.pack_forget()

        self.update_btn = ctk.CTkButton(upd_f,
                                         text="",
                                         font=ctk.CTkFont("Segoe UI",12,"bold"),
                                         height=36, corner_radius=8,
                                         fg_color=th["accent_dark"],
                                         hover_color=th["accent_hover"],
                                         text_color=th["accent"],
                                         command=self._do_update)
        self.update_btn.pack(fill="x", padx=14, pady=(4,12))
        self.update_btn.pack_forget()  # hidden until update found

        self._update_download_url = ""
        self._update_version      = ""

        # ── Donate ────────────────────────────────────────────
        donate_f = ctk.CTkFrame(scroll, fg_color=th["bg_card"], corner_radius=10)
        donate_f.pack(fill="x", padx=16, pady=(0,12))

        ctk.CTkLabel(donate_f, text="☕  Support PurgeKit",
                     font=ctk.CTkFont("Segoe UI",12,"bold"),
                     text_color=th["text_white"]).pack(pady=(12,2))
        ctk.CTkLabel(donate_f,
                     text="PurgeKit is free forever. If it saved you time, consider buying me a coffee!",
                     font=ctk.CTkFont("Segoe UI",10),
                     text_color=th["text_gray"], justify="center").pack(padx=14, pady=(0,8))

        # Detect country via IP — show ₹ for India, $ for others
        def _build_donate_buttons(is_india):
            for w in donate_f.winfo_children():
                if hasattr(w, "_donate_btn"):
                    w.destroy()

            if is_india:
                # India: Razorpay primary + PayPal secondary
                ctk.CTkLabel(donate_f, text="🇮🇳  India — Pay in ₹",
                             font=ctk.CTkFont("Segoe UI",10,"bold"),
                             text_color=th["accent"]).pack()
                rz_btn = ctk.CTkButton(donate_f,
                                       text="💸  Donate via Razorpay (₹)",
                                       font=ctk.CTkFont("Segoe UI",12,"bold"),
                                       height=36, corner_radius=8,
                                       fg_color="#2d6a4f", hover_color="#1b4332",
                                       text_color="#ffffff",
                                       command=lambda: __import__("webbrowser").open(
                                           "https://rzp.io/rzp/TEVSyhk"))
                rz_btn._donate_btn = True
                rz_btn.pack(padx=14, pady=(4,4), fill="x")
                pp_btn = ctk.CTkButton(donate_f,
                                       text="💛  Donate via PayPal ($)",
                                       font=ctk.CTkFont("Segoe UI",11),
                                       height=32, corner_radius=8,
                                       fg_color="#003087", hover_color="#002060",
                                       text_color="#FFC439",
                                       command=lambda: __import__("webbrowser").open(
                                           "https://www.paypal.com/paypalme/yash92duster"))
                pp_btn._donate_btn = True
                pp_btn.pack(padx=14, pady=(0,12), fill="x")
            else:
                # International: PayPal primary + Razorpay secondary
                ctk.CTkLabel(donate_f, text="🌍  International — Pay in $",
                             font=ctk.CTkFont("Segoe UI",10,"bold"),
                             text_color=th["accent"]).pack()
                pp_btn = ctk.CTkButton(donate_f,
                                       text="💛  Donate via PayPal ($)",
                                       font=ctk.CTkFont("Segoe UI",12,"bold"),
                                       height=36, corner_radius=8,
                                       fg_color="#003087", hover_color="#002060",
                                       text_color="#FFC439",
                                       command=lambda: __import__("webbrowser").open(
                                           "https://www.paypal.com/paypalme/yash92duster"))
                pp_btn._donate_btn = True
                pp_btn.pack(padx=14, pady=(4,4), fill="x")
                rz_btn = ctk.CTkButton(donate_f,
                                       text="💸  Donate via Razorpay (₹)",
                                       font=ctk.CTkFont("Segoe UI",11),
                                       height=32, corner_radius=8,
                                       fg_color="#2d6a4f", hover_color="#1b4332",
                                       text_color="#ffffff",
                                       command=lambda: __import__("webbrowser").open(
                                           "https://rzp.io/rzp/TEVSyhk"))
                rz_btn._donate_btn = True
                rz_btn.pack(padx=14, pady=(0,12), fill="x")

        # Default — show both, detect in background
        _build_donate_buttons(False)

        def _detect_location():
            try:
                import urllib.request, json as _json
                with urllib.request.urlopen(
                    "https://ipapi.co/json/", timeout=5) as r:
                    data = _json.loads(r.read())
                country = data.get("country_code","")
                self.after(0, lambda: _build_donate_buttons(country == "IN"))
            except Exception:
                pass  # Keep default (PayPal primary)

        threading.Thread(target=_detect_location, daemon=True).start()

        ctk.CTkLabel(scroll, text=t(T,"about_desc"),
                     font=ctk.CTkFont("Segoe UI",10),
                     text_color=th["text_dim"], justify="center").pack(pady=(0,12))

    # ── Helpers ──────────────────────────────────────────────
    def _log(self, text, tag="white"):
        ts   = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {text}"
        self.log_lines.append(line)
        def _ins():
            try:
                self.log_box.configure(state="normal")
                self.log_box.insert("end", line + "\n", tag)
                self.log_box.see("end")
                self.log_box.configure(state="disabled")
            except Exception:
                pass
        try:
            self.after(0, _ins)
        except Exception:
            pass

    def _set_progress(self, value, label):
        try:
            self.after(0, lambda: (
                self.progress_bar.set(value),
                self.progress_label.configure(text=label)
            ))
        except Exception:
            pass

    def _select_all(self):
        for v in self.task_vars.values():  v.set(True)
        for v in self.drive_vars.values(): v.set(True)
        self.after(100, self._refresh_task_sizes)

    def _deselect_all(self):
        for v in self.task_vars.values():  v.set(False)
        for v in self.drive_vars.values(): v.set(False)
        self.after(100, self._refresh_task_sizes)

    def _toggle_compact(self):
        if self._locked_guard(lambda: self.compact_mode.set(not self.compact_mode.get())):
            return
        self.cfg["compact_mode"] = self.compact_mode.get()
        save_config(self.cfg)
        self._set_window_size()
        self._build_content()

    def _boost_scroll(self, frame):
        """Boost scroll speed on CTkScrollableFrame — fixes FPS lag."""
        try:
            canvas = frame._parent_canvas
            def _fast_scroll(event):
                # 4x faster than default
                canvas.yview_scroll(int(-4*(event.delta/120)), "units")
                return "break"
            # Bind to canvas and all children recursively
            canvas.bind("<MouseWheel>", _fast_scroll, add="+")
            frame.bind("<MouseWheel>", _fast_scroll, add="+")
        except Exception:
            pass

    def _toggle_autostart(self):
        if self._locked_guard(lambda: self.autostart_var.set(not self.autostart_var.get())):
            return
        ok = set_autostart(self.autostart_var.get())
        if not ok:
            messagebox.showerror("Error", "Could not update startup registry.")
            self.autostart_var.set(not self.autostart_var.get())
        else:
            self.cfg["autostart"] = self.autostart_var.get()
            save_config(self.cfg)

    def _toggle_pin(self):
        if self._locked_guard(lambda: self._pin_sw_var.set(not self._pin_sw_var.get())):
            return
        if self._pin_sw_var.get():
            self._set_pin_dialog()
        else:
            self._disable_pin()

    def _set_pin_dialog(self):
        th = self.th
        T  = self.T
        win = ctk.CTkToplevel(self)
        win.title(t(T,"pin_set_title"))
        win.geometry("320x300")
        win.configure(fg_color=th["bg_darkest"])
        win.resizable(False, False)
        win.grab_set()
        ctk.CTkLabel(win, text=t(T,"pin_set_title"),
                     font=ctk.CTkFont("Segoe UI",16,"bold"),
                     text_color=th["accent"]).pack(pady=(20,12))
        pin1 = tk.StringVar()
        pin2 = tk.StringVar()
        msg_v = tk.StringVar()
        for var, placeholder in [(pin1,t(T,"pin_enter_new")),(pin2,t(T,"pin_confirm"))]:
            ctk.CTkLabel(win, text=placeholder,
                         font=ctk.CTkFont("Segoe UI",11),
                         text_color=th["text_gray"]).pack(pady=(4,0))
            ctk.CTkEntry(win, textvariable=var, show="●",
                         width=200, height=36,
                         font=ctk.CTkFont("Segoe UI",16),
                         fg_color=th["bg_card"],
                         text_color=th["text_white"],
                         justify="center").pack(pady=(2,4))
        ctk.CTkLabel(win, textvariable=msg_v,
                     font=ctk.CTkFont("Segoe UI",11),
                     text_color=th["error"]).pack()
        def save_pin():
            p1 = pin1.get().strip()
            p2 = pin2.get().strip()
            if len(p1) != 6 or not p1.isdigit():
                msg_v.set(t(T,"pin_too_short")); return
            if p1 != p2:
                msg_v.set(t(T,"pin_mismatch")); return
            set_pin(self.cfg, p1)
            self._pin_sw_var.set(True)
            win.destroy()
            messagebox.showinfo("PIN", t(T,"pin_set_success"))
        ctk.CTkButton(win, text=t(T,"settings_pin_set"),
                      font=ctk.CTkFont("Segoe UI",12,"bold"),
                      height=36, corner_radius=8,
                      fg_color=th["accent_dark"], hover_color=th["accent_hover"],
                      text_color=th["accent"],
                      command=save_pin).pack(padx=40, fill="x", pady=(10,0))

    def _disable_pin(self):
        clear_pin(self.cfg)
        self._pin_sw_var.set(False)
        messagebox.showinfo("PIN", t(self.T,"pin_disabled"))

    def _toggle_scheduler(self):
        if self._locked_guard(lambda: self._sched_var.set(not self._sched_var.get())):
            return
        if self._sched_var.get():
            freq = "weekly" if "weekly" in self._freq_var.get().lower() else "monthly"
            create_schedule(frequency=freq)
            self.cfg["scheduler"]["enabled"]   = True
            self.cfg["scheduler"]["frequency"] = freq
        else:
            remove_schedule()
            self.cfg["scheduler"]["enabled"] = False
        save_config(self.cfg)

    def _add_whitelist(self):
        path = filedialog.askdirectory(title="Select folder to exclude")
        if path:
            self.whitelist.append(path)
            self.wl_box.insert("end", "\n" + path)

    def _clear_whitelist(self):
        self.whitelist = []
        self.wl_box.delete("1.0","end")

    def _on_lang_change(self, selection):
        if self._locked_guard(lambda: self._lang_var_s.set(
                LANGUAGES.get(self.cfg.get("language", "en"), "English"))):
            return
        code = next((c for c,n in LANGUAGES.items() if n==selection), "en")
        self.cfg["language"] = code
        save_config(self.cfg)
        self._reload_theme_lang()

    def _on_theme_change(self, selection):
        if self._locked_guard(lambda: self._theme_var_s.set(self.cfg.get("theme", "Green"))):
            return
        self.cfg["theme"] = selection
        save_config(self.cfg)
        self._reload_theme_lang()

    def _save_settings(self):
        if self._locked_guard():
            return
        wl_text = self.wl_box.get("1.0","end").strip()
        self.whitelist = [p.strip() for p in wl_text.splitlines() if p.strip()]
        save_whitelist(self.whitelist)
        self.cfg["dry_run"] = self.dry_run_var.get()
        save_config(self.cfg)
        messagebox.showinfo("Settings", "Settings saved successfully.")

    def _open_github(self):
        import webbrowser
        webbrowser.open(GITHUB_URL)

    def _save_log_manual(self):
        path = write_log(self.log_lines, version=APP_VERSION)
        if path:
            messagebox.showinfo(t(self.T,"log_saved"),
                                t(self.T,"log_saved_to", path=path))
        else:
            messagebox.showerror("Error", "Could not save log.")

    def _check_update(self):
        def _do():
            result, ver, dl_url, rel_url = check_for_update()
            def _show():
                try:
                    T  = self.T
                    th = self.th
                    if result is True:
                        # Update available
                        self._update_version      = ver
                        self._update_download_url = dl_url
                        self.update_status_lbl.configure(
                            text=f"  🟡  Update Available — v{ver} is ready to download!",
                            text_color=th["warn"])
                        # Show download button
                        if dl_url:
                            self.update_btn.configure(
                                text=f"⬇  Download & Install v{ver}",
                                fg_color=th["accent_dark"],
                                text_color=th["accent"])
                        else:
                            self.update_btn.configure(
                                text=f"🌐  View Release on GitHub",
                                fg_color=th["bg_card"],
                                text_color=th["text_white"],
                                command=lambda: __import__("webbrowser").open(rel_url))
                        self.update_btn.pack(fill="x", padx=14, pady=(4,12))
                    elif result is False:
                        self.update_status_lbl.configure(
                            text=f"  ✅  You are on the latest version (v{ver})",
                            text_color=th["text_gray"])
                    else:
                        self.update_status_lbl.configure(
                            text="  ⚠  Could not check for updates",
                            text_color=th["text_dim"])
                except Exception:
                    pass
            self.after(0, _show)
        threading.Thread(target=_do, daemon=True).start()

    def _do_update(self):
        """Handle Download & Install click."""
        th = self.th
        dl_url = self._update_download_url
        ver    = self._update_version

        if not dl_url:
            import webbrowser
            webbrowser.open("https://github.com/yashwanthramsomireddy/PurgeKit/releases")
            return

        if not is_frozen():
            import webbrowser
            from tkinter import messagebox
            messagebox.showinfo(
                "Update",
                f"Auto-install works only with the compiled .exe version.\n\n"
                f"Please download v{ver} manually from GitHub.")
            webbrowser.open("https://github.com/yashwanthramsomireddy/PurgeKit/releases")
            return

        # Confirm
        from tkinter import messagebox
        ok = messagebox.askyesno(
            "Update PurgeKit",
            f"Download and install PurgeKit v{ver}?\n\n"
            f"The app will close and relaunch automatically after updating.")
        if not ok:
            return

        # Show progress UI
        self.update_btn.pack_forget()
        self.update_progress_bar.pack(fill="x", padx=14, pady=(0,4))
        self.update_progress_bar.set(0)
        self.update_progress_lbl.pack(padx=14, anchor="w", pady=(0,8))
        self.update_status_lbl.configure(
            text=f"  ⬇  Downloading v{ver}...",
            text_color=th["accent"])

        def _download():
            def progress(pct, dl_mb, tot_mb):
                try:
                    self.after(0, lambda: (
                        self.update_progress_bar.set(pct),
                        self.update_progress_lbl.configure(
                            text=f"  {dl_mb:.1f} MB / {tot_mb:.1f} MB  ({int(pct*100)}%)")
                    ))
                except Exception:
                    pass

            new_exe = download_update(dl_url, progress)

            if not new_exe:
                def _fail():
                    self.update_status_lbl.configure(
                        text="  ❌  Download failed. Check your internet connection.",
                        text_color=th["error"])
                    self.update_progress_bar.pack_forget()
                    self.update_progress_lbl.pack_forget()
                    self.update_btn.configure(text=f"⬇  Retry Download & Install v{ver}")
                    self.update_btn.pack(fill="x", padx=14, pady=(4,12))
                self.after(0, _fail)
                return

            # Apply update
            self.after(0, lambda: self.update_status_lbl.configure(
                text="  ✅  Download complete! Relaunching...",
                text_color=th["success"]))
            self.after(0, lambda: self.update_progress_bar.set(1.0))

            # Short pause so user sees the success message
            import time
            time.sleep(1.5)

            ok = apply_update(new_exe)
            if ok:
                # Quit current app — updater batch will relaunch
                self.after(0, self.quit)
            else:
                def _apply_fail():
                    self.update_status_lbl.configure(
                        text="  ❌  Could not apply update. Please install manually.",
                        text_color=th["error"])
                    import webbrowser
                    webbrowser.open(
                        "https://github.com/yashwanthramsomireddy/PurgeKit/releases")
                self.after(0, _apply_fail)

        threading.Thread(target=_download, daemon=True).start()

    # ── Purge Engine ─────────────────────────────────────────
    def _set_ui_locked(self, locked):
        """Disable/enable every settings-type control while a purge runs."""
        state = "disabled" if locked else "normal"
        lockable = (ctk.CTkSwitch, ctk.CTkSegmentedButton,
                    ctk.CTkOptionMenu, ctk.CTkRadioButton)

        def walk(widget):
            try:
                kids = widget.winfo_children()
            except Exception:
                return
            for child in kids:
                if isinstance(child, lockable):
                    try:
                        child.configure(state=state)
                    except Exception:
                        pass
                walk(child)
        walk(self)

    def _locked_guard(self, revert=None):
        """True (after reverting the control) if a purge is running."""
        if not getattr(self, "running", False):
            return False
        if revert:
            try:
                revert()
            except Exception:
                pass
        try:
            self._log("  🔒 Settings are locked while a purge is running.", "warn")
        except Exception:
            pass
        return True

    def _busy_guard(self):
        """True (after telling the user) if any purge/clean is already running."""
        if not getattr(self, "running", False):
            return False
        try:
            messagebox.showwarning(
                "Purge running",
                "Another purge or clean is already running.\n"
                "Please wait for it to finish.")
        except Exception:
            pass
        return True

    def _log_task_start(self, tid, label):
        t0 = datetime.datetime.now()
        self._log(f"\n── {tid}: {label}   ▶ started {t0:%H:%M:%S}", "accent")
        return t0

    def _log_task_end(self, tid, t0, freed=None):
        t1  = datetime.datetime.now()
        msg = f"  ⏱ {tid} finished {t1:%H:%M:%S} — took {(t1 - t0).total_seconds():.1f}s"
        if freed is not None:
            msg += f" — freed {fmt_size(freed)}"
        self._log(msg, "dim")

    def _cancel_purge(self):
        """Signal the running purge to stop after current task."""
        self._cancel_flag = True
        try:
            self.cancel_btn.configure(state="disabled", text="Cancelling...")
        except Exception:
            pass
        self._log("  ⏹ Cancel requested — stopping after current task...", "warn")

    def _start_purge(self):
        if self._busy_guard():
            return
        selected   = [tid for tid,v in self.task_vars.items() if v.get()]
        sel_drives = [d   for d,  v in self.drive_vars.items() if v.get()]
        if not selected and not sel_drives and self.activity_var.get()=="skip":
            messagebox.showwarning(t(self.T,"nothing_selected"), t(self.T,"select_one"))
            return
        self.running = True
        self._cancel_flag = False
        dry = self.dry_run_var.get()
        self.start_btn.configure(text=t(self.T,"running"), state="disabled",
                                  fg_color="#002510", text_color=self.th["text_gray"])
        try:
            self.cancel_btn.configure(state="normal")
        except Exception:
            pass
        # Lock UI controls during purge
        self._set_ui_locked(True)
        self.reboot_needed = [False]
        threading.Thread(target=self._purge_thread,
                         args=(selected, sel_drives, dry), daemon=True).start()

    def _purge_thread(self, selected, sel_drives, dry_run):
        """Wrapper: whatever happens, the UI is ALWAYS reset afterwards."""
        try:
            self._purge_thread_body(selected, sel_drives, dry_run)
        except Exception as e:
            try:
                self._log(f"  ❌ Purge stopped by an unexpected error: {e}", "error")
                write_log(self.log_lines, "", version=APP_VERSION)
            except Exception:
                pass
        finally:
            self.after(0, self._finish_purge_ui)

    def _finish_purge_ui(self):
        """Runs when a purge ends for any reason: finished, cancelled or crashed."""
        try:
            dry = self.dry_run_var.get()
            self.start_btn.configure(
                text=t(self.T, "dry_run") if dry else t(self.T, "start_purge"),
                state="normal",
                fg_color="#3a2000" if dry else self.th["accent_dark"],
                text_color=self.th["warn"] if dry else self.th["accent"])
        except Exception:
            pass
        try:
            self.cancel_btn.configure(state="disabled", text="⏹ Cancel")
        except Exception:
            pass
        self._set_ui_locked(False)
        self._cancel_flag = False
        self.running = False

    def _purge_thread_body(self, selected, sel_drives, dry_run):
        T   = self.T
        th  = self.th
        act = self.activity_var.get()
        total       = len(selected) + len(sel_drives) + (0 if act=="skip" else 1)
        done        = 0
        total_freed = 0
        start_time  = datetime.datetime.now()

        self._log("", "dim")
        self._log("═"*50, "accent")
        self._log(f"  {t(T,'purge_started')}" + (" [DRY RUN]" if dry_run else ""), "accent")
        self._log("═"*50, "accent")

        cancel_logged = False
        for task in TASKS:
            if self._cancel_flag:
                self._log("  ⏹ Purge cancelled by user.", "warn")
                cancel_logged = True
                break
            tid = task[0]
            if tid not in selected:
                continue
            path   = task[3]
            do_exp = task[4]
            rp     = ep(path) if do_exp else path
            if any(wl in rp or rp in wl for wl in self.whitelist):
                self._log(t(T,"whitelist_skip",path=rp), "dim")
                continue
            done += 1
            self._set_progress(done/max(total,1), f"[{done}/{total}] {task[2]}...")
            t0 = self._log_task_start(tid, task[2])
            freed = run_task(tid, self._log, self.reboot_needed, dry_run)
            total_freed += freed
            self._log_task_end(tid, t0, freed)

        for drv in sel_drives:
            if self._cancel_flag:
                if not cancel_logged:
                    self._log("  ⏹ Purge cancelled by user.", "warn")
                    cancel_logged = True
                break
            done += 1
            self._set_progress(done/max(total,1), f"[{done}/{total}] Disk Cleanup {drv}...")
            t0 = self._log_task_start("Disk Cleanup", drv)
            if not dry_run:
                for cat in DISK_CLEANUP_CATS:
                    run(f'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VolumeCaches\\{cat}" '
                        f'/v StateFlags0099 /t REG_DWORD /d 2 /f')
                run(f"cleanmgr /sagerun:99 /d {drv[0]}", timeout=300)
            else:
                self._log(f"  [DRY RUN] Would run Disk Cleanup on {drv}", "warn")
            _el = (datetime.datetime.now() - t0).total_seconds()
            if not dry_run and _el >= 295:
                self._log(f"  ⚠ Disk Cleanup hit its 5-minute limit on {drv} and was stopped early", "warn")
            else:
                self._log(f"  ✅ Disk Cleanup done: {drv}", "success")
            self._log_task_end("Disk Cleanup", t0)

        if act != "skip" and not self._cancel_flag:
            done += 1
            self._set_progress(done/max(total,1), "Windows Activity History...")
            self._log("\n── Activity History", "accent")
            cdp = ep(r"%LOCALAPPDATA%\ConnectedDevicesPlatform")
            if not dry_run:
                run("taskkill /f /im explorer.exe")
            if os.path.exists(cdp):
                for profile in os.listdir(cdp):
                    db = os.path.join(cdp, profile, "ActivitiesCache.db")
                    if os.path.exists(db):
                        if dry_run:
                            sz = os.path.getsize(db)
                            self._log(f"  [DRY RUN] Would delete: {db} ({fmt_size(sz)})", "warn")
                            total_freed += sz
                        else:
                            try:
                                sz = os.path.getsize(db)
                                os.remove(db)
                                total_freed += sz
                                self._log(f"  ✅ Deleted: {db}", "success")
                            except Exception:
                                run(f'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager" '
                                    f'/v PendingFileRenameOperations /t REG_MULTI_SZ /d "\\??\\{db}\\0" /f')
                                self.reboot_needed[0] = True
            if not dry_run:
                run("start explorer.exe")
                if act == "disable":
                    for v in ["EnableActivityFeed","PublishUserActivities","UploadUserActivities"]:
                        run(f'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" '
                            f'/v {v} /t REG_DWORD /d 0 /f')
                    self._log("  ✅ Activity History disabled", "success")

        elapsed     = datetime.datetime.now() - start_time
        elapsed_str = str(elapsed).split(".")[0]
        freed_str   = fmt_size(total_freed)
        summary     = (f"{'='*60}\n"
                       f"  {t(T,'space_freed')}: {freed_str}\n"
                       f"  {t(T,'time_taken')}:  {elapsed_str}\n"
                       f"{'='*60}")

        if not dry_run:
            self.history.append({
                "date":        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "freed_bytes": total_freed,
                "elapsed":     elapsed_str,
                "dry_run":     False,
            })
            save_history(self.history)

        self._session_tasks        = {tid: v.get() for tid,v in self.task_vars.items()}
        self.cfg["last_drives"]    = [d for d,v in self.drive_vars.items() if v.get()]
        self.cfg["activity_choice"]= act
        save_config(self.cfg)

        if not dry_run:
            try:
                from winotify import Notification
                Notification(app_id="PurgeKit",
                             title=t(T,"notification_title"),
                             msg=t(T,"notification_body",
                                   size=freed_str, time=elapsed_str, files="—"),
                             duration="short").show()
            except Exception:
                pass

        self._set_progress(1.0, "⏹ Stopped" if self._cancel_flag else "✅ All done!")
        self._log("", "dim")
        self._log("═"*50, "accent")
        complete_key = "dry_run_complete" if dry_run else "purge_complete"
        if self._cancel_flag:
            self._log("  ⏹ PURGE STOPPED — cancelled by user (remaining tasks were not run).", "warn")
        else:
            self._log(f"  {t(T,complete_key)}", "success")
        self._log(f"  {t(T,'space_freed')}: {freed_str}", "success")
        self._log(f"  {t(T,'time_taken')}: {elapsed_str}", "dim")
        if self.reboot_needed[0]:
            self._log(f"  ⚠ {t(T,'reboot_required')}", "warn")
            self.after(0, lambda: messagebox.showwarning(
                t(T,"reboot_required"), t(T,"reboot_msg")))
        self._log("═"*50, "accent")

        # Save the log LAST so the file contains every line above.
        log_path = write_log(self.log_lines, summary, version=APP_VERSION)
        if log_path:
            self._log(f"  💾 Log saved: {log_path}", "dim")
        else:
            self._log("  ⚠ Could not save the log file (Downloads\\PurgeKit\\Logs)", "warn")


# ── CLI silent mode ───────────────────────────────────────────
class _SilentTray:
    """
    Tray icon that exists ONLY while a --silent run is active.
    Shows "PurgeKit — cleaning 12/58" in its tooltip, has "Open log" and
    "Stop after current task" in its menu, and is removed when the run ends.
    Entirely best-effort: if pystray/Pillow or the tray is unavailable the run
    simply carries on with toast notifications only.
    """

    def __init__(self, total, log_path, stop_event):
        self.total, self.done, self.label = total, 0, "starting…"
        self.log_path   = log_path
        self.stop_event = stop_event
        self._icon      = None
        self._thread    = None
        try:
            import pystray
            img  = generate_icon((0, 230, 118)).convert("RGBA").resize((64, 64))
            menu = pystray.Menu(
                pystray.MenuItem(lambda item: self._status(), None, enabled=False),
                pystray.MenuItem("Open log", self._open_log),
                pystray.MenuItem("Stop after current task", self._request_stop),
            )
            self._icon   = pystray.Icon("PurgeKit", img, self._tooltip(), menu)
            self._thread = threading.Thread(target=self._run_icon, daemon=True)
            self._thread.start()
        except Exception:
            self._icon = None

    def _run_icon(self):
        try:
            self._icon.run()          # blocks until close() calls icon.stop()
        except Exception:
            pass                      # no tray available -> carry on without it

    def _status(self):
        return f"Cleaning {self.done}/{self.total}"

    def _tooltip(self):
        return f"PurgeKit — cleaning {self.done}/{self.total}\n{self.label}"[:120]

    def update(self, done, label):
        self.done, self.label = done, label
        if self._icon is not None:
            try:
                self._icon.title = self._tooltip()
                self._icon.update_menu()
            except Exception:
                pass

    def _open_log(self, icon=None, item=None):
        try:
            os.startfile(self.log_path)
        except Exception:
            pass

    def _request_stop(self, icon=None, item=None):
        self.stop_event.set()
        self.update(self.done, "stopping after current task…")

    def close(self):
        """Remove the icon from the tray (no ghost icon left behind)."""
        icon, self._icon = self._icon, None
        if icon is not None:
            try:
                icon.stop()
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=3)


def run_silent():
    """
    --silent / Recycle Bin "Run PurgeKit Cleaner" / scheduled runs.
    Runs exactly the tasks that a fresh launch shows ticked in the Tasks tab
    (System + User + Browser defaults), honours the whitelist, shows a tray
    icon with progress while it works, and a Windows toast at start and finish.
    """
    from core.cleaner import TASKS, get_drives, DISK_CLEANUP_CATS, run_task, run, fmt_size
    from core.log_manager import write_log, get_log_path

    def toast(title, msg, open_path=None):
        try:
            from winotify import Notification
            n = Notification(app_id="PurgeKit", title=title, msg=msg, duration="short")
            if open_path:
                try:
                    n.add_actions(label="Open log", launch=open_path)
                except Exception:
                    pass
            n.show()
        except Exception:
            pass

    reboot    = [False]
    log       = []
    freed     = 0
    whitelist = load_whitelist()
    started   = datetime.datetime.now()
    stop      = threading.Event()

    def log_fn(msg, tag=""):
        log.append(f"[{datetime.datetime.now():%H:%M:%S}] {msg}")

    todo = []
    for task in TASKS:
        if not task[5]:                       # default-ON tasks only
            continue
        rp = ep(task[3]) if task[4] else task[3]
        if any(wl in rp or rp in wl for wl in whitelist):
            log_fn(f"[SKIP] whitelisted: {rp}")
            continue
        todo.append(task)
    drives   = list(get_drives())
    total    = len(todo) + len(drives)
    log_path = get_log_path()

    print(f"PurgeKit v{APP_VERSION} — Silent Mode")
    log_fn(f"PurgeKit v{APP_VERSION} silent run — default selections "
           f"({len(todo)} tasks + {len(drives)} drive cleanup)")
    toast("PurgeKit", f"Cleaning started — {len(todo)} tasks. Tray icon: right-click to stop.")
    tray    = _SilentTray(total, log_path, stop)
    done    = 0
    stopped = False

    try:
        for task in todo:
            if stop.is_set():
                stopped = True
                break
            done += 1
            tray.update(done, task[2])
            t0 = datetime.datetime.now()
            log_fn(f"\n── {task[0]}: {task[2]}   ▶ started {t0:%H:%M:%S}")
            print(f"  Cleaning: {task[2]}")
            f = run_task(task[0], log_fn, reboot, False)
            freed += f
            t1 = datetime.datetime.now()
            log_fn(f"  ⏱ {task[0]} finished {t1:%H:%M:%S} — took {(t1 - t0).total_seconds():.1f}s — freed {fmt_size(f)}")
            write_log(log, "Run in progress…", version=APP_VERSION, path=log_path)   # live log

        if not stopped:
            for drv, _, _, _ in drives:
                if stop.is_set():
                    stopped = True
                    break
                done += 1
                tray.update(done, f"Disk Cleanup {drv}")
                t0 = datetime.datetime.now()
                log_fn(f"\n── Disk Cleanup: {drv}   ▶ started {t0:%H:%M:%S}")
                for cat in DISK_CLEANUP_CATS:
                    run(f'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VolumeCaches\\{cat}" '
                        f'/v StateFlags0099 /t REG_DWORD /d 2 /f')
                run(f"cleanmgr /sagerun:99 /d {drv[0]}", timeout=300)
                t1 = datetime.datetime.now()
                log_fn(f"  ⏱ Disk Cleanup {drv} finished {t1:%H:%M:%S} — took {(t1 - t0).total_seconds():.1f}s")
                write_log(log, "Run in progress…", version=APP_VERSION, path=log_path)

        if stopped:
            log_fn("⏹ Stopped from the tray menu — remaining steps were not run.")
    except Exception as e:
        log_fn(f"❌ Silent run stopped by an unexpected error: {e}")
    finally:
        took    = str(datetime.datetime.now() - started).split(".")[0]
        summary = (f"Silent run {'STOPPED' if stopped else 'complete'} — "
                   f"freed {fmt_size(freed)} in {took}")
        log_fn("\n" + summary)
        if reboot[0]:
            log_fn("REBOOT REQUIRED to finish removing locked files.")
        path = write_log(log, summary, version=APP_VERSION, path=log_path)
        tray.close()                          # icon disappears when the run ends
        print(f"Done. Freed {fmt_size(freed)}. Log: {path}")
        toast("PurgeKit — stopped" if stopped else "PurgeKit — done",
              f"Freed {fmt_size(freed)} in {took}" +
              ("  (restart needed to finish)" if reboot[0] else ""),
              open_path=path)
        if reboot[0]:
            print("REBOOT REQUIRED.")


if __name__ == "__main__":
    if "--silent" in sys.argv:
        run_silent()
    else:
        app = PurgeKitApp()
        app.mainloop()
