; Inno Setup script for SDGW 1914-1919.
;
; Compile from repo root after PyInstaller has produced dist/SDGW/
; and after data/sd_2011.db is in place:
;     iscc /DAppVersion=1.0.0 packaging/installer.iss
;
; Output: build/SDGW-Setup.exe (single self-extracting installer ~310 MB)
;
; Design notes:
;   - PrivilegesRequired=lowest installs to %LOCALAPPDATA% with no UAC prompt.
;     This is the friction-saver for the elderly end user: SmartScreen
;     fires once on first run of the unsigned installer, but no second
;     "do you want to allow this app to make changes" dialog after that.
;   - The /SILENT flag is honoured by the auto-updater so future updates
;     happen without showing the wizard. The first install is interactive.
;   - Compression is lzma2/ultra — slow to compile, smallest to download.

#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif

[Setup]
AppId={{B7F4C3F2-1E2E-4F2A-9C58-9A7E1D3D5B11}}
AppName=Soldiers Died in the Great War 1914-1919
AppVersion={#AppVersion}
AppVerName=SDGW 1914-1919 {#AppVersion}
AppPublisher=eek2020
; AppMutex must match the named mutex created in launcher.py on Windows.
; Without it, /CLOSEAPPLICATIONS passed by the silent auto-updater has no
; way to identify the running SDGW.exe, so the running process holds file
; locks and the installer cannot overwrite them — the "update" produces no
; version change. With AppMutex set, Inno Setup detects the running app
; and gracefully closes + restarts it.
AppMutex=SDGW1914-1919-AppMutex
AppPublisherURL=https://github.com/eek2020/SDGW1914-1919-v2
AppSupportURL=https://github.com/eek2020/SDGW1914-1919-v2/issues
DefaultDirName={localappdata}\SDGW
DefaultGroupName=SDGW 1914-1919
DisableDirPage=auto
DisableProgramGroupPage=yes
DisableWelcomePage=no
PrivilegesRequired=lowest
OutputBaseFilename=SDGW-Setup
OutputDir=..\build
SetupIconFile=..\src\static\SDGW1419.ico
WizardStyle=modern
Compression=lzma2/ultra
SolidCompression=yes
UninstallDisplayIcon={app}\SDGW.exe
UninstallDisplayName=Soldiers Died in the Great War 1914-1919
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
Source: "..\dist\SDGW\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\data\sd_2011.db"; DestDir: "{app}\data"; Flags: ignoreversion

[Icons]
Name: "{group}\Soldiers Died in the Great War"; Filename: "{app}\SDGW.exe"; IconFilename: "{app}\SDGW.exe"
Name: "{group}\Uninstall SDGW"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Soldiers Died in the Great War"; Filename: "{app}\SDGW.exe"; IconFilename: "{app}\SDGW.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SDGW.exe"; Description: "Launch SDGW now"; Flags: nowait postinstall skipifsilent
