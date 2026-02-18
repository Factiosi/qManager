[Setup]
AppName=qManager
AppVersion=1.9.3
AppPublisher=Factiosi
AppComments=Программа для автоматизации работы с АКФК (Актами Карантинного Фитосанитарного Контроля)
DefaultDirName={pf}\qManager
DefaultGroupName=qManager
UninstallDisplayIcon={app}\src\resources\Icon.ico
OutputDir=dist
OutputBaseFilename=qManagerSetup
SetupIconFile=src/resources/Icon.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
; Основной исполняемый файл
Source: "dist\start.dist\qManager.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\start.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\qManager"; Filename: "{app}\qManager.exe"; IconFilename: "{app}\src\resources\Icon.ico"
Name: "{userdesktop}\qManager"; Filename: "{app}\qManager.exe"; IconFilename: "{app}\src\resources\Icon.ico"

[Run]
Filename: "{app}\qManager.exe"; Description: "Запустить qManager"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\qManager"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
