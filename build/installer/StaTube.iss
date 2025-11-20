; Inno Setup Template for StaTube
[Setup]
AppName={#emit("MyAppName")}
AppVersion={#emit("MyAppVersion")}
AppPublisher={#emit("MyAppPublisher")}
AppPublisherURL=https://example.com
DefaultDirName={autopf}\{#emit("MyAppName")}
DefaultGroupName={#emit("MyAppName")}
OutputBaseFilename=StaTube-{#emit("MyAppVersion")}-setup
Compression=lzma2
SolidCompression=yes

[Files]
Source: "{#emit("SourceDir")}\\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\\{#emit("MyAppName")}"; Filename: "{app}\\{#emit("MyAppName")}.exe"

[Run]
Filename: "{app}\\{#emit("MyAppName")}.exe"; Flags: nowait postinstall skipifsilent
