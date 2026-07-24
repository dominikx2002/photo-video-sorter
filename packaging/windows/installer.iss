#ifndef MyAppVersion
#define MyAppVersion "1.0.0"
#endif

[Setup]
AppId={{B7E9F5B4-6B7E-4A6B-9C8A-1B2C3D4E5F60}
AppName=Photo & Video Sorter
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\Photo & Video Sorter
DefaultGroupName=Photo & Video Sorter
OutputBaseFilename=PhotoVideoSorter-Setup
OutputDir=..\..\installer_output
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes

[Files]
Source: "..\..\dist\PhotoVideoSorter\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\Photo & Video Sorter"; Filename: "{app}\PhotoVideoSorter.exe"
Name: "{commondesktop}\Photo & Video Sorter"; Filename: "{app}\PhotoVideoSorter.exe"

[Run]
Filename: "{app}\PhotoVideoSorter.exe"; Description: "Launch Photo & Video Sorter"; Flags: nowait postinstall skipifsilent
