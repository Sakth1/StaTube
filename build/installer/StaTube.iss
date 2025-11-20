; Inno Setup script template — values set by /D defines passed to ISCC
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


[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"


[Files]
; SourceDir will be passed by the workflow as a /DSourceDir define
Source: "{#emit("SourceDir")}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs


[Icons]
Name: "{group}\{#emit("MyAppName")}"; Filename: "{app}\{#emit("MyAppName")}.exe"


[Run]
Filename: "{app}\{#emit("MyAppName")}.exe"; Description: "Launch {#emit("MyAppName")}"; Flags: nowait postinstall skipifsilent
