# Changelog — PurgeKit
All notable changes to PurgeKit are documented here.
Format: `## [version] - date | highlights`

---

## [3.8.1] - 2026-10-04

### Added
- **Tray icon during silent runs** (Recycle Bin → *Run PurgeKit Cleaner*, `--silent`, scheduler). Tooltip shows `PurgeKit — cleaning 12/58` plus the current task. Menu: live status, **Open log**, **Stop after current task**. The icon is removed when the run ends (also if it crashes). Windows may place it under the **^** overflow arrow. If the tray is unavailable the run carries on with notifications only.
- **Live log for silent runs** — the log file is rewritten after every task, so *Open log* shows progress while it runs. The finish notification has an **Open log** button.
- **Install folder choice** — the installer now always shows *Select Destination Location*.

### Fixed
- **Junk Scan → Clean Selected could run during a Tasks purge** (and vice-versa). Scan, Clean Selected, Start Purge and the 3rd Party tab now share one lock: a second purge is refused with a message. Junk Scan clean also locks the settings, logs per-item start/finish times, and always unlocks — even if a delete fails (before, the button could stay on "Cleaning…").
- **Upgrading from v3.7 installed a second copy** (`Program Files` next to `Program Files (x86)`), so the taskbar shortcut kept opening v3.7. v3.8 had switched the installer to 64-bit mode, which Windows treats as a different install. The installer is back in the original mode, so it now upgrades the existing install in place. (The Recycle Bin entry is written to the 64-bit registry view explicitly.)
- After **Cancel**, the log said "PURGE COMPLETE ✅" and printed the cancel message twice; it now says "PURGE STOPPED" once.
- Silent-mode tray/log code paths never leave a half-written log (atomic write).

### Changed
- **Tab renamed: "Scan" → "Junk Scan"** (English and the 25 languages that use the English label; Hindi, Tamil and Telugu keep their own word for "Scan").
- `build.bat` adds `--hidden-import pystray._win32` so the tray works in the packaged exe.
- Version `3.8.1` in `PurgeKit.py`, `core/updater.py`, `installer.iss`, README badge.

### Upgrade note (one-time, if you installed the v3.8 Setup)
Uninstall the extra copy at `C:\Program Files\PurgeKit` from Settings → Apps **first**, then run the 3.8.1 Setup. It will update `C:\Program Files (x86)\PurgeKit` in place.

---

## [3.8.0] - 2026-10-04

### Fixed
- **Purge finished but the app stayed on "Running" with the Cancel button active** — an error at the end of the purge thread (a bad `write_log` call) killed the thread before the UI was reset. The UI reset now lives in a `finally` block, so it runs after a normal finish, a cancel, *or* a crash.
- **Log file in Downloads\PurgeKit\Logs was blank (header line only)** — the log header referenced an undefined variable, so the write failed after the file was opened. Fixed; the log is now saved *last*, so it contains every line including the final summary. A failed write no longer leaves a half-written file.
- **"Selected 1 task, everything purged"** — selections were saved to disk and restored on the next launch, so an old "all selected" state (and any rebuild of the Tasks tab) silently overrode what you ticked. Selection is now kept in memory only: **every launch starts from the built-in defaults** (System, User and Browser ticked; Developer, 3rd Party, Adobe, Games, Communication, Media, DevTools and Optional unticked — 58 of 142 tasks). Your choices still survive theme/language changes within a session. Switching tabs in Spacious mode no longer rebuilds (and resets) the Tasks tab.
- **Settings could be changed during a purge** — the earlier "lock" did nothing. Theme, language, compact mode, dry-run, auto-start, PIN, scheduler and Save are now genuinely locked (controls disabled *and* handlers refuse) until the purge ends.
- **3rd Party tab could run at the same time as a Tasks purge** — it now shares the same running/lock state.
- **Software Updater saved corrupt installers** (e.g. Notepad++, VLC) — downloads were accepted even if the connection dropped early or the server returned a web page. Downloads now go to a temp file and are only kept if: the byte count matches `Content-Length`, the server did not send HTML, and the file header is a real `.exe` / `.msi` / `.msix`. The real file name is taken from the server's `Content-Disposition` header or the signed-URL query string. A rejected download tells you why and saves nothing.
- **System Info error handler** could itself crash (`ex` used after its `except` block ended).
- **Per-task timing** — each task now logs `▶ started HH:MM:SS` and `⏱ finished HH:MM:SS — took N.Ns — freed X` (Tasks tab, 3rd Party tab, silent mode). Disk Cleanup warns when it hits its 5-minute limit.

### Added
- **Start Menu**: `PurgeKit` and `PurgeKit (Run Cleaner Now)`.
- **Recycle Bin right-click → "Run PurgeKit Cleaner"** (installer option, on by default). Runs the default selections silently (no window) and shows a toast when it starts and finishes. Honours your whitelist.
- Cancel is also honoured before Disk Cleanup and Activity History steps.

### Changed
- `--silent` (Recycle Bin, scheduler) now runs the **built-in default selection** instead of "last used", and respects the whitelist.
- Installer is 64-bit (needed so the Recycle Bin entry is written where Explorer reads it).
- Corrected task count: **142** tasks (earlier notes said 104+/160+).
- `APP_VERSION`, `CURRENT_VERSION`, `installer.iss` → `3.8`.

---

## [3.7.1] - 2026-09-24

### Fixed
- **`subfolder` variable error in U38/U40/U42** — broken UWP handler code was accidentally nested inside the U38 elif block from a previous edit, causing `cannot access local variable 'subfolder'` errors on those tasks even after successful completion. Completely removed and replaced with a clean handler.
- **A6 Adobe Photoshop Temp removed** — was incorrectly pointing to `%TEMP%` (same path as U1), causing a duplicate reboot-pending schedule. Removed entirely.
- **Log header version hardcoded as v3.0** — `write_log()` now accepts a `version` parameter; PurgeKit passes `APP_VERSION` dynamically. Log header now shows the correct version.
- **Log auto-saves after purge completes** — no more need to manually click Save Log after every run.
- **Windows Store popup on U12** — replaced `wsreset.exe` call (which opens the Store window as a side effect) with direct deletion of `Packages\Microsoft.WindowsStore_8wekyb3d8bbwe\LocalCache`. No window opens.
- **U37 Power BI Desktop Cache removed** — was hanging silently with no log output due to locked Power BI process handles.
- **U39 TeamViewer Logs removed** — was hanging silently after U38.
- **Task timeout wrapper added** — every task now runs with a 120-second timeout via a threading wrapper. If any task hangs, the log shows `⏱ TIMEOUT (120s) — skipping` and purge moves to the next task automatically. App can never freeze indefinitely again.

---

## [3.7.0] - 2026-09-23

### Added
- **U35** Teams Meeting Addin MSIs (`%LOCALAPPDATA%\Microsoft\TeamsMeetingAddinMsis`)
- **U36** Teams Meeting Addin Cache (`%LOCALAPPDATA%\Microsoft\TeamsMeetingAddin`)
- **U38** CEF Browser Cache (`%LOCALAPPDATA%\CEF`) — Chromium Embedded Framework
- **U40** ConnectedDevices Platform Cache (`%LOCALAPPDATA%\ConnectedDevicesPlatform`) — 266 MB on average
- **U41** VS Code Workspace Storage (`%APPDATA%\Code\User\workspaceStorage`) — unchecked by default
- **U42** VS Code Logs (`%APPDATA%\Code\logs`)
- **U43** UWP App LocalCache — wildcard scan of all `Packages\*\LocalCache` folders
- **U44** UWP App TempState — wildcard scan of all `Packages\*\TempState` folders
- **U45** UWP App INetCache — wildcard scan of all `Packages\*\AC\INetCache` folders
- **Cancel button** (⏹) next to Start Purge — enabled during purge, stops cleanly after current task finishes
- **UI locked during purge** — theme toggle, compact toggle, dry run switch all disabled while purge is running; unlock on finish or cancel
- **Per-task start time + elapsed time in log** — every task now logs `⏱ TaskName: X.Xs — freed Y MB`
- **Scroll FPS boost** — `_boost_scroll()` method applies 4× mouse wheel speed to all CTkScrollableFrame instances across all tabs; eliminates scroll lag

### Fixed
- **Windows Defender Scan History (U19) — removed entirely** — cleaning this path takes 10-20 minutes due to 100,000+ tiny locked files; MpCmdRun.exe approach did not reliably fix the hang. Removed from task list. Users can clear via Windows Security if needed.
- **Duplicate task definitions** — U19, U35, U36, U43-U45 were appearing twice in TASKS list due to multiple insertion attempts; deduplicated to single entries.
- **Scroll row flicker** — Tasks, Scan, 3rd Party, Updater tabs were rendering rows one-by-one causing visible flicker. Fixed with `update_idletasks()` batching and canvas state management.

### Changed
- `APP_VERSION` → `3.7`, `CURRENT_VERSION` → `3.7`, `installer.iss` → `3.7`

---

## [3.6.0] - 2026-09-22

### Added
- **3rd Party Apps tab** — separate tab with 6 categories, all unchecked by default:
  - 🎮 Games & Launchers: Steam, Epic Games, GOG Galaxy, Riot, Battle.net, Overwolf, Origin, Ubisoft
  - 💬 Communication: Telegram, Signal, Outlook offline cache
  - 📦 Other 3rd Party: Slack, Postman, NVIDIA, AMD, Brave, Opera, Vivaldi, Chrome Canary, Figma, WebEx, Dropbox, Google Drive, Spotify UWP, CrashRpt
  - 🎨 Adobe: All 12 Adobe apps
  - 🎬 Media: OBS Studio, DaVinci Resolve, HandBrake, VLC
  - 🔧 Dev Tools: JetBrains IDEs, Visual Studio, Electron Builder
  - Per-category ✔/✘ buttons on each section header
  - Own progress bar and Purge button per tab
- **Per-category Select All / Deselect All in Tasks tab** — ✔/✘ buttons on every phase header
- **Donate tab — location-aware** — detects country via ipapi.co; India: Razorpay (₹) primary + PayPal secondary; International: PayPal ($) primary + Razorpay secondary
- **Razorpay Payment Page** — updated to `rzp.io/rzp/TEVSyhk` (replaces old profile link; no phone number shown)
- **New cleaning tasks**: Games (G1-G12), Communication (C1-C4), Media (M1-M6), DevTools (V1-V5)

### Fixed
- **Updater scroll bg on dynamic theme change** — force-sets `_parent_canvas` bg on each panel build; white background on dark themes fixed without re-scan
- **Activity History radio buttons** — larger (18×18), bold text, accent-colored border, descriptive subtitle under each option; reordered to Skip → Delete → Disable
- **Disk Cleanup section label** — added clear description: "Only removes temp files, system logs, update backups and recycle bin — never your personal files or apps"

### Changed
- `APP_VERSION` → `3.6`, `CURRENT_VERSION` → `3.6`
- 29 lang files updated with `tab_thirdparty` key

---

## [3.5.3] - 2026-09-18

### Added
- **104+ cleaning tasks** across 9 phases
- **3rd Party phase (T1-T19)**: Slack, Postman, Skype, Google Drive, Dropbox, Figma, WebEx, Brave, Vivaldi, Opera, Chrome Canary, NVIDIA DXCache/GLCache/Temp, AMD DxCache, Teams Meeting Add-in, Spotify UWP, CrashRpt
- **Adobe phase (A1-A13)**: Media Cache, Acrobat DC, Premiere Pro, After Effects, Illustrator, InDesign, XD, Lightroom, Bridge, Creative Cloud Logs, CoreSync Cache
- **Developer phase expanded (D6-D11)**: NuGet HTTP Cache, NuGet Packages Store, Yarn, pnpm, Cargo Registry, Android Studio

---

## [3.5.2] - 2026-09-15

### Added
- U21 Downloaded Installations Cache
- U22 SquirrelTemp
- U23 iTunes Cache

### Fixed
- Activity History radio selection visibility
- Windows Defender scan history changed to target `History\Store` only (was full `History` tree)
- Disk Cleanup section description added

---

## [3.5.1] - 2026-09-12

### Fixed
- GitHub release download redirect (GitHub → CDN) now followed correctly
- YAML manifest files auto-deleted after software download

---

## [3.5.0] - 2026-09-10

### Added
- White (light) theme
- Official vendor URL download via `winget show --id` with redirect following
- Real byte-level progress bar in Software Updater

---

## [3.4.2] - 2026-09-08

### Changed
- Software Updater now download-only — user opens installer manually; PurgeKit never executes anything silently

---

## [3.4.1] - 2026-09-07

### Fixed
- Software Updater row height (pack_propagate issue)
- Select All / Deselect All buttons added to Software Updater tab

---

## [3.4.0] - 2026-09-05

### Added
- Software Updater — powered by Microsoft winget; scans for outdated apps, downloads official installer from vendor URL
- Social Media Kit (HTML tool with cards, captions, YouTube thumbnails)
- Project documentation (MD + DOCX + XLSX)

---

## [3.3.1] - 2026-09-03

### Fixed
- Version consistency across all 4 locations (PurgeKit.py, updater.py, installer.iss, README.md)
- SysInfo tab renamed (was showing tab key instead of display name)
- Inno Setup installer elevation fix (runascurrentuser)

---

## [3.3.0] - 2026-09-01

### Added
- New cache paths: Zoom, Discord, WhatsApp, OneDrive, Defender, Teams 2.0, Maven, Gradle, Docker
- System Info tab (RAM bar, disk per-drive bar, OS version, uptime, processor)
- Donate button in About tab
- Inno Setup installer (.exe setup with Start Menu + Desktop shortcut + uninstall)

---

## [3.2.0] - 2026-08-30

### Added
- Auto-update — checks GitHub Releases API on launch, downloads + replaces exe + relaunches automatically
- Download progress bar in auto-update

---

## [3.1.x] - 2026-08-28

### Fixed
- Startup and History tabs removed (non-functional)
- Scan tab Clean Selected wired correctly
- Size labels per task working consistently
- Taskbar icon fix (AppUserModelID + save to %APPDATA%)
- Version consistency fixes

---

## [3.1.0] - 2026-08-27

### Added
- Spacious sidebar navigation mode
- Scan tab: Clean Selected with progress bar
- Size label per task row (scanned in background thread)

---

## [3.0.0] - 2026-08-25

### Added
- 29 languages (live switch in Settings)
- 3 themes: Green, Blue, Purple (White added in v3.5)
- First run wizard (Language, Theme, Options)
- PIN lock (6-digit, SHA-256, 3-attempt lockout, 30s cooldown)
- Dry Run mode (preview deletions without deleting)
- Junk Scanner tab (ranked by size, Clean Selected)
- Scheduler (weekly/monthly auto-purge via Windows Task Scheduler)
- Whitelist (exclude folders from all cleaning)
- CLI silent mode (`PurgeKit.exe --silent`)

---

## [2.2.0] - 2026-08-23

### Added
- Compact/Spacious mode toggle
- Drive detection for Disk Cleanup
- Service Worker cache (Chrome + Edge)
- npm and pip cache cleaning

---

## [2.1.0] - 2026-08-22

### Added
- Per-drive Disk Cleanup (auto-detects drives, runs cleanmgr)
- About tab with version info and donate

---

## [2.0.0] - 2026-08-20

### Added
- Python GUI (CustomTkinter dark theme)
- Progress bar during purge
- Log panel with color-coded output
- Save log to file

---

## [1.1.0] - 2026-08-18

### Added
- 3-technique force delete (robocopy → takeown → reboot pending)
- Activity history clear + disable
- DNS cache flush

---

## [1.0.0] - 2026-08-15

### Added
- Initial release — .bat script Windows temp/cache cleaner
- Y/N prompt per cleaning step

---

*PurgeKit — Built by Yashwanth Ram Somireddy, Chennai, India (TeamExyKings)*
*MIT License — Free to use, modify, and distribute*
