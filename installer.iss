; ============================================================
;  PurgeKit v3.8.1 — Inno Setup Installer Script
;  MIT License — TeamExyKings
;  GitHub: https://github.com/yashwanthramsomireddy/PurgeKit
; ============================================================

#define MyAppName      "PurgeKit"
#define MyAppVersion   "3.8.1"
#define MyAppPublisher "TeamExyKings"
#define MyAppURL       "https://github.com/yashwanthramsomireddy/PurgeKit"
#define MyAppExeName   "PurgeKit.exe"
#define MyAppAuthor    "Yashwanth Ram Somireddy"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=Output
OutputBaseFilename=Setup_PurgeKit_v{#MyAppVersion}
SetupIconFile=assets\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
; ---- Install location --------------------------------------------------
; Always show the "Select Destination Location" page so the folder can be chosen.
DisableDirPage=no
; If PurgeKit is already installed, the page is pre-filled with that folder.
UsePreviousAppDir=yes
; IMPORTANT: do NOT add ArchitecturesInstallIn64BitMode here. v3.7 and earlier
; were installed in 32-bit mode ("Program Files (x86)"). Changing the install
; mode makes Windows treat the new Setup as a different program, so it installs
; side-by-side in a second folder and the old copy keeps being launched.
; Keeping the same mode makes Setup upgrade the existing install IN PLACE.
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Windows Temp and Cache Cleaner
VersionInfoCopyright=Copyright 2026 {#MyAppAuthor} ({#MyAppPublisher})

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
; No Flags => ticked by default. ("checked" is NOT a valid [Tasks] flag.)
Name: "recyclebin_ctx"; Description: "Add ""Run PurgeKit Cleaner"" to the Recycle Bin right-click menu"; GroupDescription: "Shell integration:"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE";              DestDir: "{app}"; Flags: ignoreversion
Source: "README.md";            DestDir: "{app}"; Flags: ignoreversion
Source: "CHANGELOG.md";         DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}";                  Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} (Run Cleaner Now)"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--silent"; Comment: "Run PurgeKit with the default selections, no window"
Name: "{group}\Uninstall {#MyAppName}";         Filename: "{uninstallexe}"
; Desktop (optional task)
Name: "{autodesktop}\{#MyAppName}";            Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Recycle Bin right-click -> "Run PurgeKit Cleaner" (runs the default selections).
; HKLM64 = the 64-bit registry view. Explorer is 64-bit and only reads that view,
; and this installer runs in 32-bit mode (see note above), so it must be explicit.
; {{ is Inno's escape for a literal { character.
Root: HKLM64; Subkey: "SOFTWARE\Classes\CLSID\{{645FF040-5081-101B-9F08-00AA002F954E}\shell\PurgeKit";         ValueType: string; ValueName: ""; ValueData: "Run PurgeKit Cleaner"; Flags: uninsdeletekey; Check: IsWin64; Tasks: recyclebin_ctx
Root: HKLM64; Subkey: "SOFTWARE\Classes\CLSID\{{645FF040-5081-101B-9F08-00AA002F954E}\shell\PurgeKit";         ValueType: string; ValueName: "Icon"; ValueData: """{app}\{#MyAppExeName}"",0"; Check: IsWin64; Tasks: recyclebin_ctx
Root: HKLM64; Subkey: "SOFTWARE\Classes\CLSID\{{645FF040-5081-101B-9F08-00AA002F954E}\shell\PurgeKit\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --silent"; Check: IsWin64; Tasks: recyclebin_ctx

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent runascurrentuser

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\PurgeKit"
