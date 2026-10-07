@echo off
:: ============================================================
::  PurgeKit v3.8.1 — Build Script
::  Run from the PurgeKit folder in a normal CMD window
::  Do NOT run as Administrator
:: ============================================================

echo.
echo  ============================================================
echo    PurgeKit v3.8.1 — Build
echo    TeamExyKings
echo  ============================================================
echo.

echo  [1/3] Installing dependencies...
pip install customtkinter Pillow pystray winotify matplotlib pyinstaller --upgrade --quiet
echo  Done.
echo.

echo  [2/3] Generating icon...
python generate_icon.py
echo  Done.
echo.

echo  [3/3] Building PurgeKit.exe...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "PurgeKit" ^
    --uac-admin ^
    --icon "assets\icon.ico" ^
    --add-data "lang;lang" ^
    --hidden-import pystray._win32 ^
    PurgeKit.py

echo.
echo  ============================================================
echo    Build complete!
echo    Portable exe : dist\PurgeKit.exe
echo    Next step    : Open installer.iss in Inno Setup → Compile
echo  ============================================================
echo.
pause
