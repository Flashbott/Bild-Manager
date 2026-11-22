#define MyAppName "Pokémon-Manager"
#ifndef MyAppVersion
  #define MyAppVersion "0.3.1"
#endif
#define MyAppPublisher "Julian"

[Setup]
AppId={{D2BB7F9A-6E4E-4FC4-8B9A-0E5E0F2E67A9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\PokemonManager
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\Release
OutputBaseFilename=Pokemon-Manager-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName}

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Files]
Source: "..\Release\dist\Pokemon-Manager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}\Anleitung"; DestName: "README.md"; Flags: ignoreversion
Source: "..\Gebrauchsanweisung_Pokemon-Auswahl.html"; DestDir: "{app}\Anleitung"; Flags: ignoreversion
Source: "..\Gebrauchsanweisung_Pokemon-Auswahl.md"; DestDir: "{app}\Anleitung"; Flags: ignoreversion
Source: "..\docs\*"; DestDir: "{app}\Anleitung\Projekt"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\VERSION.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\Pokemon-Manager.exe"
Name: "{autoprograms}\{#MyAppName}\Anleitung"; Filename: "{app}\Anleitung\Gebrauchsanweisung_Pokemon-Auswahl.html"
Name: "{autoprograms}\{#MyAppName}\README"; Filename: "{app}\Anleitung\README.md"
Name: "{autoprograms}\{#MyAppName}\Projektdokumentation"; Filename: "{app}\Anleitung\Projekt\PROJEKTDOKUMENTATION.md"

[Run]
Filename: "{app}\Pokemon-Manager.exe"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: postinstall nowait skipifsilent
