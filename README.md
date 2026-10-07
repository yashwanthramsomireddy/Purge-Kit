<div align="center">

# 🧹 PurgeKit

**Free, open-source Windows temp & cache cleaner**

![Version](https://img.shields.io/badge/Version-3.8.1-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-yellow.svg)
![Built with](https://img.shields.io/badge/Built%20with-CustomTkinter-purple.svg)

[⬇ Download](#download) · [📋 Changelog](CHANGELOG.md) · [🐛 Report Bug](https://github.com/yashwanthramsomireddy/PurgeKit/issues) · [💛 Donate](#donate)

</div>

---

## What is PurgeKit?

PurgeKit is a free, open-source Windows system cleaner with a modern dark GUI. It removes temporary files, browser caches, app caches, system logs, 3rd party app caches, Adobe caches, and outdated installer files — all in one click, with full transparency and zero cost.

> **Free forever. No ads. No subscription. No bloat.**

---

## ✨ Features

- ✅ **140+ cleaning tasks** across 11 phases
- ✅ **3rd Party Apps tab** — Games, Communication, Adobe, Media, Dev Tools caches
- ✅ **Software Updater** — winget-based, downloads official installer, open to install
- ✅ **Per-category Select All / Deselect All** — in Tasks and 3rd Party tabs
- ✅ **Cancel button** — stop purge cleanly after current task at any time
- ✅ **Settings lock during purge** — theme, language, mode and other switches can't be changed mid-run
- ✅ **Start Menu + Recycle Bin shortcut** — right-click the Recycle Bin → *Run PurgeKit Cleaner* runs the default selections silently
- ✅ **Tray icon during silent runs** — shows live progress in its tooltip, has *Open log* and *Stop after current task*, and disappears when the run ends
- ✅ **Choose the install folder** — the installer always shows the destination page and upgrades an existing install in place
- ✅ **Task timeout** — no task can freeze the app; 120s max per task
- ✅ **Per-task start/finish time in log** — see when each task started, finished and how long it took
- ✅ **Verified installer downloads** — Software Updater rejects truncated files and web pages saved as .exe
- ✅ **29 Languages** — live switch in Settings
- ✅ **4 Themes** — Green / Blue / Purple / White (light mode)
- ✅ **Dry Run mode** — preview what will be deleted without deleting
- ✅ **Junk Scanner** — scan and rank folders by size, clean selected
- ✅ **System Info** — RAM, disk usage, OS version, uptime, processor
- ✅ **PIN Lock** — 6-digit PIN, SHA-256, 3-attempt lockout
- ✅ **Scheduler** — weekly/monthly auto-purge via Windows Task Scheduler
- ✅ **Whitelist** — exclude any folder from all cleaning
- ✅ **Auto-Update** — downloads and relaunches from GitHub releases
- ✅ **Donate — location-aware** — ₹ Razorpay for India / $ PayPal for International
- ✅ **Inno Setup installer** — Start Menu + Desktop shortcut + uninstall support

---

## 📋 What It Cleans

> **11 cleaning phases, 142 tasks total** (58 ticked by default: System, User, Browser)

### Phase 1 — System (S1-S11) ✅ On by default
Windows Temp, Prefetch, Windows Update Cache, Delivery Optimization, WER, CBS Logs, Crash Dumps, Font Cache, DataStore Logs, Installer Patch Cache, DNS Cache

### Phase 2 — User (U1-U45) ✅ On by default
User Temp, Thumbnails, Recent Files, WebCache, INetCache, DirectX Cache, Teams, VS Code, Office, Spotify, Icon Cache, Clipboard, Store Cache, Zoom, Discord, WhatsApp, OneDrive, Defender History, Update Logs, Downloaded Installations, SquirrelTemp, iTunes, DISM Logs, MeasuredBoot, Diagnostics, LocalService Temp, NetworkService Temp, Jump Lists, Temp Low, CrashRpt, Extension Storage, Teams Addin, CEF, VS Code Workspace, ConnectedDevices, UWP App Caches

### Phase 3 — Browser (B1-B3b) ✅ On by default
Chrome (Cache + Service Worker), Firefox (cache2 + startupCache), Edge (Cache + Service Worker)

### Phase 4 — Developer (D1-D11) ☐ Off by default
npm, pip, Maven, Gradle, Docker, NuGet HTTP, NuGet Packages, Yarn, pnpm, Cargo, Android Studio

### Phase 5 — 3rd Party (T1-T19) ☐ Off by default
Slack, Postman, Skype, Google Drive, Dropbox, Figma, WebEx, Brave, Vivaldi, Opera, Chrome Canary, NVIDIA DXCache/GLCache/Temp, AMD DxCache, Teams Meeting Add-in, Spotify UWP, CrashRpt

### Phase 6 — Adobe (A1-A12) ☐ Off by default
Media Cache, Acrobat DC, Premiere Pro, After Effects, Illustrator, InDesign, XD, Lightroom, Bridge, Creative Cloud Logs, CoreSync Cache

### Phase 7 — Optional (O1-O11) ☐ Off by default
Event Logs, Recycle Bin, Telemetry, Cortana, ARP, NetBIOS, Winsock, Search Index, Skype Full, Adobe Common Full

### 3rd Party Apps Tab — 4 Additional Phases ☐ Off by default
| Phase | Apps |
|---|---|
| 🎮 Games | Steam, Epic Games, GOG Galaxy, Riot, Battle.net, Overwolf, Origin, Ubisoft |
| 💬 Communication | Telegram, Signal, Outlook |
| 🎬 Media | OBS Studio, DaVinci Resolve, HandBrake, VLC |
| 🔧 Dev Tools | JetBrains IDEs, Visual Studio, Electron Builder |

---

## 🛡 Force Delete — 3 Techniques

| Technique | Method | When Used |
|---|---|---|
| T1 | `robocopy /MIR` empty folder mirror | First attempt — fastest |
| T2 | `takeown` + `icacls` + force delete | T1 fails — permissions issue |
| T3 | Register pending delete on next reboot | T2 fails — file locked by system |

---

## 🔄 Software Updater

- Powered by **Microsoft winget** (official, free, no 3rd-party DB)
- Scans all installed apps for available updates
- Downloads official installer directly from vendor URL
- Full HTTP redirect following (GitHub releases → CDN)
- Real byte-level progress bar
- User opens installer — PurgeKit never executes anything silently
- Saves to `Downloads\PurgeKit\Installers\<AppName>\`

---

## 🎨 Themes

| Theme | Mode | Accent |
|---|---|---|
| Green (default) | Dark | `#00e676` |
| Blue | Dark | `#40c4ff` |
| Purple | Dark | `#ea80fc` |
| White | Light | `#1a7a40` |

---

## 🌐 Languages

English, Tamil, Hindi, Telugu, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, Urdu, Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Turkish, Dutch, Polish, Vietnamese, Thai, Indonesian, Malay, Swahili

---

## ⬇ Download

| File | Description |
|---|---|
| `PurgeKit.exe` | Portable — just double-click and run |
| `Setup_PurgeKit_v3.8.1.exe` | Windows installer — Start Menu + Desktop shortcut + uninstall |

👉 **[Get latest release](https://github.com/yashwanthramsomireddy/PurgeKit/releases)**

> Requires **Windows 10 or 11** with administrator privileges.

---

## 🏗 Build from Source

```bash
# 1. Clone
git clone https://github.com/yashwanthramsomireddy/PurgeKit.git
cd PurgeKit

# 2. Install dependencies
pip install customtkinter Pillow pystray winotify matplotlib pyinstaller

# 3. Generate icon
python generate_icon.py

# 4. Build exe
build.bat

# 5. Build installer (optional)
# Open installer.iss in Inno Setup → Compile
```

### Version Consistency — always update all 4
1. `APP_VERSION` in `PurgeKit.py`
2. `CURRENT_VERSION` in `core/updater.py`
3. `MyAppVersion` in `installer.iss`
4. Version badge in `README.md`

---

## 📁 Project Structure

```
PurgeKit/
├── PurgeKit.py              ← Main app — all UI panels (3200+ lines)
├── generate_icon.py         ← Icon generator
├── build.bat                ← PyInstaller build script
├── installer.iss            ← Inno Setup installer config
├── requirements.txt
│
├── core/
│   ├── cleaner.py           ← 142 tasks, 11 phases, force delete engine
│   ├── config.py            ← Config, history, whitelist, PIN (SHA-256)
│   ├── lang_manager.py      ← 29-language loader
│   ├── log_manager.py       ← Log writer → Downloads\PurgeKit\Logs\
│   ├── scanner.py           ← Junk folder scanner ranked by size
│   ├── scheduler.py         ← Windows Task Scheduler integration
│   ├── software_updater.py  ← winget scan + official URL download
│   ├── startup_manager.py   ← Startup programs reader
│   └── updater.py           ← GitHub API auto-update checker
│
├── ui/
│   └── themes.py            ← Green / Blue / Purple / White themes
│
├── lang/
│   ├── en.json              ← English (base)
│   └── ... (29 total)
│
└── assets/
    └── icon.ico
```

---

## 🗺 Roadmap

- [x] v3.0 — 29 languages, wizard, PIN, scanner, scheduler
- [x] v3.2 — Auto-update from GitHub
- [x] v3.4 — Software Updater (winget)
- [x] v3.5 — White theme, official URL download
- [x] v3.5.3 — 104+ tasks, 3rd Party + Adobe phases
- [x] v3.6 — 3rd Party Apps tab, per-category Select All, location-aware donate
- [x] v3.7 — Cancel button, task timeout, UWP caches, scroll FPS boost
- [x] v3.7.1 — Bug fixes: subfolder error, A6 path, log version, Store popup
- [x] v3.8 — Real settings lock, UI always resets after purge, log file fixed, verified downloads, defaults on every launch, Start Menu + Recycle Bin shortcut
- [x] v3.8.1 — Tray icon for silent runs, Junk Scan tab locked during purges, installer folder choice + in-place upgrade
- [ ] v4.0 — Full background/tray mode, portable mode, multi-language installer
- [ ] v4.1 — Secure delete (DoD 3-pass), disk health check
- [ ] v4.2 — PDF report export, run history analytics
- [ ] Future — Pro version (Supabase + Razorpay + Brevo) — TBD

---

## 🤝 Contributing

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "Add: description"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 💛 Donate

PurgeKit is and will always remain **100% free**. If it saved you time or disk space, consider supporting:

| Platform | Link | Currency |
|---|---|---|
| 💛 PayPal | [paypal.me/yash92duster](https://www.paypal.com/paypalme/yash92duster) | $ / ₹ |
| 💸 Razorpay | [rzp.io/rzp/TEVSyhk](https://rzp.io/rzp/TEVSyhk) | ₹ (India) |

The app auto-detects your country and shows the right option first.

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

<div align="center">

**Built with ❤️ by [Yashwanth Ram Somireddy](https://linkedin.com/in/yashwanth-ram-somireddy-15121b215), Chennai, India**

**[TeamExyKings](https://teamexykings.in) · [GitHub](https://github.com/yashwanthramsomireddy/PurgeKit)**

</div>
