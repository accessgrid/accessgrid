#define SourceDir "C:\AccessGridBuild\AccessGrid\Release"
#define OutputDir "C:\AccessGridBuild\AccessGrid-Build"
#define AppName "Access Grid Toolkit"
#define AppVersionLong "2.0 beta 2"
#define AppVersionShort "2.0b2"

[_ISTool]
EnableISX=true
LogFile=C:\AccessGridBuild\AccessGrid-Build\installer.log
LogFileAppend=false

[_ISToolPreCompile]
; It would be a good idea to figure out how to pass the SourceDir as a
; parameter to prebuild. Ti and I have chatted about this, it's on the
; to do list :-)
Name: python; Parameters: C:\AccessGridBuild\AccessGrid\packaging\makeServicePackages.py C:\AccessGridBuild\AccessGrid\AccessGrid\services; Flags: abortonerror
Name: C:\AccessGridBuild\AccessGrid\packaging\windows\Prebuild.cmd; Parameters: C:\AccessGridBuild\AccessGrid; Flags: abortonerror

; This section sets the standard variables needed for the installer

[Setup]
; Name with version information
AppVerName={#AppName} {#AppVersionLong}
; Version information
AppVersion={#AppVersionShort}
; What to build the installer from
SourceDir={#SourceDir}
; Where to put the built installer
OutputDir={#OutputDir}
; Name with version information
OutputBaseFilename=agtk-{#AppVersionShort}

AppName={#AppName}
AppCopyright=Copyright © 2003 University of Chicago. All Rights Reserved.
AppPublisher=Futures Laboratory / Argonne National Laboratory
AppPublisherURL=http://www.mcs.anl.gov/fl
AppSupportURL=http://bugzilla.mcs.anl.gov/accessgrid
AppUpdatesURL=http://www.mcs.anl.gov/fl/research/accessgrid
AppID={#AppName}
Compression=zip/9
MinVersion=0,5.00.2195
LicenseFile=..\COPYING.txt
DisableDirPage=false
DefaultGroupName={#AppName}
DefaultDirName={pf}\{#AppName}
UsePreviousAppDir=false
UserInfoPage=false
WindowVisible=false
UninstallDisplayIcon={app}\VenueClient.py
UninstallDisplayName={#AppName}
DisableStartupPrompt=false
WindowResizable=false
AlwaysShowComponentsList=true
ShowComponentSizes=true
FlatComponentsList=true
AllowNoIcons=false
DirExistsWarning=auto
DisableFinishedPage=false
DisableReadyMemo=true
UsePreviousUserInfo=false
WindowStartMaximized=false
WizardImageFile=compiler:wizmodernimage.bmp
WizardSmallImageFile=compiler:wizmodernsmallimage.bmp
UninstallFilesDir={app}\uninst
InfoBeforeFile=..\Install.WINDOWS
ShowTasksTreeLines=false
PrivilegesRequired=admin

[Components]
Name: Venue_Client; Description: Basic client software to use Access Grid Virtual Venues.; Types: custom compact full; Flags: fixed
Name: Video_Producer; Description: Basic Node Service that allows you to produce video streams; Types: full
Name: Video_Consumer; Description: Basic Node Service that allows you to receive video streams; Types: custom full
Name: Audio_Service; Description: Basic Node Service that allows you to receive and produce audio streams; Types: full
Name: Venue_Server; Description: Server Software that allows you to host your own Virtual Venue Server; Types: full

[Files]
; The Python Module: AccessGrid
Source: Lib\site-packages\AccessGrid\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.2\PythonPath\win32com,|C:\Python22\Lib\site-packages}\AccessGrid; Flags: recursesubdirs

; Service packages
Source: share\AccessGrid\services\*.zip; DestDir: {app}\services; Components: Venue_Client

; Preinstalled services
Source: var\lib\ag\local_services\AudioService.py; DestDir: {app}\local_services; Components: Audio_Service
Source: var\lib\ag\local_services\AudioService.svc; DestDir: {app}\local_services; Components: Audio_Service
Source: var\lib\ag\local_services\VideoConsumerService.py; DestDir: {app}\local_services; Components: Video_Consumer
Source: var\lib\ag\local_services\VideoConsumerService.svc; DestDir: {app}\local_services; Components: Video_Consumer
Source: var\lib\ag\local_services\VideoProducerService.py; DestDir: {app}\local_services; Components: Video_Producer
Source: var\lib\ag\local_services\VideoProducerService.svc; DestDir: {app}\local_services; Components: Video_Producer

; Programs for the user to run
Source: Scripts\RunMe.py; DestDir: {app}; Components: Venue_Client
Source: Scripts\RunMe.py; DestDir: {app}; DestName: RunMe.pyw; Components: Venue_Client
Source: Scripts\VenueClient.py; DestDir: {app}; Components: Venue_Client
Source: Scripts\VenueClient.py; DestDir: {app}; DestName: VenueClient.pyw; Components: Venue_Client
Source: Scripts\NodeManagement.py; DestDir: {app}; Components: Venue_Client
Source: Scripts\NodeManagement.py; DestDir: {app}; DestName: NodeManagement.pyw; Components: Venue_Client
Source: Scripts\AGNodeService.py; DestDir: {app}; Components: Venue_Client
Source: Scripts\AGNodeService.py; DestDir: {app}; DestName: AGNodeService.pyw; Components: Venue_Client
Source: Scripts\AGServiceManager.py; DestDir: {app}
Source: Scripts\AGServiceManager.py; DestDir: {app}; DestName: AGServiceManager.pyw
Source: Scripts\SetupVideo.py; DestDir: {app}; Components: Video_Producer
Source: Scripts\SetupVideo.py; DestDir: {app}; DestName: SetupVideo.pyw; Components: Video_Producer
Source: Scripts\VenueManagement.py; DestDir: {app}; Components: Venue_Server
Source: Scripts\VenueManagement.py; DestDir: {app}; DestName: VenueManagement.pyw; Components: Venue_Server
Source: Scripts\VenueServer.py; DestDir: {app}; Components: Venue_Server
Source: Scripts\VenueServer.py; DestDir: {app}; DestName: VenueServer.pyw; Components: Venue_Server
Source: Scripts\VenuesServerRegistry.py; DestDir: {app}; Components: Venue_Server
Source: Scripts\VenuesServerRegistry.py; DestDir: {app}; DestName: VenueServer.pyw; Components: Venue_Server

; Default node configuration
Source: share\AccessGrid\nodeConfig\defaultWindows; DestDir: {app}\config; Flags: confirmoverwrite

; AG Icon for programs and stuff
Source: share\AccessGrid\AG.ico; DestDir: {app}\config

; Documentation
Source: share\doc\AccessGrid\*.*; DestDir: {app}\Documentation

; Post install scripts
Source: share\AccessGrid\packaging\windows\Postinstall.py; DestDir: {app}\config; Flags: deleteafterinstall
Source: share\AccessGrid\packaging\windows\AGNodeServicePostinstall.py; DestDir: {app}\config; Flags: deleteafterinstall
Source: share\AccessGrid\packaging\windows\AGServiceManagerPostinstall.py; DestDir: {app}\config; Flags: deleteafterinstall

; Vic Video Tool
Source: ..\..\ag-vic\vic\Release\vic.exe; DestDir: {app}; Components: Video_Consumer Video_Producer

; Rat Audio Tool
Source: ..\..\ag-rat\rat\Release\rat.exe; DestDir: {app}; Components: Audio_Service
Source: ..\..\ag-rat\rat\Release\ratmedia.exe; DestDir: {app}; Components: Audio_Service
Source: ..\..\ag-rat\rat\Release\ratui.exe; DestDir: {app}; Components: Audio_Service


[Icons]
Name: {group}\Venue Client; Filename: {app}\RunMe.pyw; IconFilename: {app}\config\AG.ico; WorkingDir: {app}; Components: Venue_Client
Name: {group}\Uninstall the AGTk; Filename: {uninstallexe}
Name: {group}\Node Manager; IconFilename: {app}\config\AG.ico; Filename: {app}\NodeManagement.pyw; WorkingDir: {app}; Components: Venue_Client
Name: {group}\Setup Video; IconFilename: {app}\config\AG.ico; Filename: {app}\SetupVideo.pyw; WorkingDir: {app}; Components: Video_Producer
Name: {group}\Venue Server; IconFilename: {app}\config\AG.ico; Filename: {app}\VenueServer.pyw; WorkingDir: {app}; Components: Venue_Server
Name: {group}\Venue Management; IconFilename: {app}\config\AG.ico; Filename: {app}\VenueManagement.pyw; WorkingDir: {app}; Components: Venue_Server
Name: {commondesktop}\Access Grid Venue Client; Filename: {app}\RunMe.pyw; IconFilename: {app}\config\AG.ico; WorkingDir: {app}; Tasks: desktopicon; Components: Venue_Client
Name: {userappdata}\Microsoft\Internet Explorer\Quick Launch\Access Grid Venue Client; IconFilename: {app}\config\AG.ico; Filename: {app}\RunMe.py; Tasks: quicklaunchicon; Components: Venue_Client
Name: {group}\Documentation\README; IconFilename: {app}\config\AG.ico; Filename: {app}\Documentation\README
;Name: {group}\Documentation\Developers Documentation; Filename: {app}\Documentation\index.html
Name: {group}\Documentation\License; IconFilename: {app}\config\AG.ico; Filename: {app}\COPYING.txt

[Registry]
Root: HKLM; Subkey: SOFTWARE\Access Grid Toolkit\2.0; ValueType: expandsz; ValueName: InstallPath; ValueData: {app}; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\Access Grid Toolkit\2.0; ValueType: expandsz; ValueName: ConfigPath; ValueData: {app}\config; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\Access Grid Toolkit\2.0; ValueType: expandsz; ValueName: UserConfigPath; ValueData: %USERPROFILE%\Application Data\Access Grid Toolkit\config; Flags: uninsdeletekey

[Types]

[Tasks]
Name: desktopicon; Description: Create &Desktop Icons; GroupDescription: Additional icons:; Components: Audio_Service Video_Consumer Video_Producer Venue_Client
Name: quicklaunchicon; Description: Create a &Quick Launch Icon; GroupDescription: Additional icons:; Flags: unchecked

[Messages]
DirExists=The directory:%n%n%1%n%nalready exists and appears to have an AccessGrid Toolkit installation in it.%n%nIt is recommended that you uninstall any existing AccessGrid Toolkit software before proceeding.  Do you wish to proceed anyway?
WelcomeLabel2=This will install the [name/ver] on your computer.%n%nIt is strongly recommended that you uninstall any previous version of the [name] before continuing.%n%nIt is also strongly recommended that you close all other applications you have running before continuing with this installation.%n%nThese steps will help prevent any conflicts during the installation process.

[Run]
Filename: {app}\config\Postinstall.py; Flags: shellexec runminimized
Filename: {app}\SetupVideo.pyw; WorkingDir: {app}; Description: Setup what video devices will produce video streams; Components: Video_Producer; Flags: postinstall unchecked shellexec
Filename: {app}\config\AGNodeServicePostinstall.py; Flags: shellexec runminimized; Components: Venue_Client
Filename: {app}\config\AGServiceManagerPostinstall.py; Flags: shellexec runminimized; Components: Venue_Client

[UninstallDelete]
Name: {reg:HKLM\Software\Python\PythonCore\2.2\PythonPath\win32com,|C:\Python22\Lib\site-packages}\AccessGrid; Type: filesandordirs

[Dirs]
Name: {app}\config; Components: Venue_Client

