[Setup]
AppName=qManager
AppVersion=1.2.0
AppPublisher=factiosi
AppDescription=Приложение для автоматизации работы с PDF-документами в логистике
DefaultDirName={pf}\qManager
DefaultGroupName=qManager
UninstallDisplayIcon={app}\resources\Icon.ico
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
Source: "dist\start.dist\start.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\start.dist\start.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Настройки и конфигурация
Source: "dist\start.dist\start.dist\settings.json"; DestDir: "{app}"; Flags: ignoreversion

; Ресурсы приложения
Source: "dist\start.dist\start.dist\src\resources\*"; DestDir: "{app}\src\resources"; Flags: ignoreversion recursesubdirs createallsubdirs

; Внешние зависимости (теперь копируются отдельные подпапки)
Source: "dist\start.dist\start.dist\vendor\poppler\bin\*"; DestDir: "{app}\vendor\poppler\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\start.dist\start.dist\vendor\Tesseract-OCR\*"; DestDir: "{app}\vendor\Tesseract-OCR"; Flags: ignoreversion recursesubdirs createallsubdirs

; Python библиотеки
Source: "dist\start.dist\start.dist\PySide6\*"; DestDir: "{app}\PySide6"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\start.dist\start.dist\pandas\*"; DestDir: "{app}\pandas"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\start.dist\start.dist\numpy\*"; DestDir: "{app}\numpy"; Flags: ignoreversion recursesubdirs createallsubdirs

; Дополнительные файлы
Source: "dist\start.dist\start.dist\*.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\start.dist\start.dist\*.pyd"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\qManager"; Filename: "{app}\start.exe"; IconFilename: "{app}\resources\Icon.ico"
Name: "{userdesktop}\qManager"; Filename: "{app}\start.exe"; IconFilename: "{app}\resources\Icon.ico"

[Run]
Filename: "{app}\start.exe"; Description: "Запустить qManager"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\qManager"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
