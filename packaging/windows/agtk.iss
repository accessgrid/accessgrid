;
; RCS-ID: $Id: agtk.iss,v 1.12 2003-05-29 18:45:56 leggett Exp $
;

#define SourceDir "C:\AccessGridBuild\AccessGrid\Release"
#define OutputDir "C:\AccessGridBuild\Builds"
#define AppName "Access Grid Toolkit"
#define AppNameShort "AGTk"
#define AppVersionLong "2.0"
#define AppVersionShort "2.0"
;
; This doesn't work.
; #define AppConfigDir "{commonappdata}\AccessGrid"
;

[_ISTool]
EnableISX=true
LogFile=C:\AccessGridBuild\Builds\AGTk-installer.log
LogFileAppend=false

[_ISToolPreCompile]
; It would be a good idea to figure out how to pass the SourceDir as a
; parameter to prebuild. Ti and I have chatted about this, it's on the
; to do list :-)
;
Name: python; Parameters: C:\AccessGridBuild\AccessGrid\packaging\makeServicePackages.py C:\AccessGridBuild\AccessGrid\services\node; Flags: abortonerror
Name: C:\AccessGridBuild\AccessGrid\packaging\windows\BuildAccessGrid.cmd; Parameters: C:\AccessGridBuild\AccessGrid; Flags: abortonerror
Name: C:\AccessGridBuild\AccessGrid\packaging\windows\BuildVic.cmd; Parameters: C:\AccessGridBuild\ag-vic C:\AccessGridBuild\AccessGrid\Release\bin; Flags: abortonerror
Name: C:\AccessGridBuild\AccessGrid\packaging\windows\BuildRat.cmd; Parameters: C:\AccessGridBuild\ag-rat C:\AccessGridBuild\AccessGrid\Release\bin; Flags: abortonerror

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;
;;
;; YOU SHOULDN'T NEED TO MODIFY ANYTHING BELOW HERE
;;
;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; This section sets the standard variables needed for the installer

[Setup]
; Name with version information
AppVerName={#AppVersionLong}
; Version information
AppVersion={#AppVersionShort}
; What to build the installer from
SourceDir={#SourceDir}
; Where to put the built installer
OutputDir={#OutputDir}
; Name with version information
OutputBaseFilename={#AppNameShort}-{#AppVersionShort}

AppName=AGTk
AppCopyright=Copyright © 2003 University of Chicago. All Rights Reserved.
AppPublisher=Futures Laboratory / Argonne National Laboratory
AppPublisherURL=http://www.mcs.anl.gov/fl
AppSupportURL=http://bugzilla.mcs.anl.gov/accessgrid
AppUpdatesURL=http://www.mcs.anl.gov/fl/research/accessgrid
AppID={907B1500-42CA-4148-8F13-2004654CCA06}
Compression=zip/9
MinVersion=0,5.0.2195sp3
LicenseFile=C:\AccessGridBuild\AccessGrid\COPYING.txt
DisableDirPage=false
DefaultGroupName={#AppName} {#AppVersionShort}
DefaultDirName={pf}\{#AppName}
UsePreviousAppDir=false
UserInfoPage=false
WindowVisible=false

UninstallDisplayName={#AppName} {#AppVersionLong}
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
InfoBeforeFile=C:\AccessGridBuild\AccessGrid\Install.WINDOWS
ShowTasksTreeLines=true
PrivilegesRequired=admin
UninstallDisplayIcon={app}\config\agicons.exe

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
Source: Scripts\VenueClient.py; DestDir: {app}; Components: Venue_Client
Source: Scripts\NodeManagement.py; DestDir: {app}; Components: Venue_Client
Source: Scripts\AGNodeService.py; DestDir: {app}; Components: Venue_Client
Source: Scripts\AGServiceManager.py; DestDir: {app}
Source: Scripts\SetupVideo.py; DestDir: {app}; Components: Video_Producer
Source: Scripts\VenueManagement.py; DestDir: {app}; Components: Venue_Server
Source: Scripts\VenueServer.py; DestDir: {app}; Components: Venue_Server
Source: Scripts\MailcapSetup.py; DestDir: {app}

; Default node configuration
Source: share\AccessGrid\nodeConfig\defaultWindows; DestDir: {commonappdata}\AccessGrid\nodeConfig; Flags: confirmoverwrite

; AG Icon for programs and stuff
Source: share\AccessGrid\agicons.exe; DestDir: {app}\config

; Documentation
;Source: doc\AccessGrid\*.*; DestDir: {app}\Documentation

; Post install scripts
Source: share\AccessGrid\packaging\windows\Postinstall.py; DestDir: {app}\config; Flags: deleteafterinstall

; Vic Video Tool
Source: bin\vic.exe; DestDir: {app}; Components: Video_Consumer Video_Producer

; Rat Audio Tool
Source: bin\rat-kill.exe; DestDir: {app}; Components: Audio_Service
Source: bin\rat.exe; DestDir: {app}; Components: Audio_Service
Source: bin\ratmedia.exe; DestDir: {app}; Components: Audio_Service
Source: bin\ratui.exe; DestDir: {app}; Components: Audio_Service

[Icons]
Name: {group}\Uninstall the AGTk; Filename: {uninstallexe}
Name: {group}\Venue Client; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22\Lib\site-packages}\pythonw.exe; Parameters: VenueClient.py --personalNode; IconFilename: {app}\config\agicons.exe; WorkingDir: {app}; Components: Venue_Client; IconIndex: 0
Name: {group}\Node Manager; IconFilename: {app}\config\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22\Lib\site-packages}\pythonw.exe; Parameters: NodeManagement.py; WorkingDir: {app}; Components: Venue_Client; IconIndex: 0
Name: {group}\Setup Video; IconFilename: {app}\config\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22\Lib\site-packages}\pythonw.exe; Parameters: SetupVideo.py; WorkingDir: {app}; Components: Video_Producer; IconIndex: 0
Name: {group}\Venue Server; IconFilename: {app}\config\agicons.exe; Filename: {app}\VenueServer.py; WorkingDir: {app}; Components: Venue_Server; IconIndex: 0
Name: {group}\Venue Management; IconFilename: {app}\config\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22\Lib\site-packages}\pythonw.exe; Parameters: VenueManagement.py; WorkingDir: {app}; Components: Venue_Server; IconIndex: 0
Name: {group}\Debug\Venue Client; IconFilename: {app}\config\agicons.exe; Filename: {app}\VenueClient.py; Parameters: --personalNode --debug; WorkingDir: {app}; Components: Venue_Client; IconIndex: 0
Name: {group}\Debug\Node Manager; IconFilename: {app}\config\agicons.exe; Filename: {app}\NodeManagement.py; WorkingDir: {app}; Components: Venue_Client; IconIndex: 0
Name: {group}\Debug\Setup Video; IconFilename: {app}\config\agicons.exe; Filename: {app}\SetupVideo.py; WorkingDir: {app}; Components: Video_Producer; IconIndex: 0
Name: {group}\Debug\Venue Server; IconFilename: {app}\config\agicons.exe; Filename: {app}\VenueServer.py; WorkingDir: {app}; Components: Venue_Server; IconIndex: 0
Name: {group}\Debug\Venue Management; IconFilename: {app}\config\agicons.exe; Filename: {app}\VenueManagement.py; WorkingDir: {app}; Components: Venue_Server; IconIndex: 0
Name: {commondesktop}\Access Grid Venue Client; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22\Lib\site-packages}\pythonw.exe; Parameters: VenueClient.py --personalNode; IconFilename: {app}\config\agicons.exe; WorkingDir: {app}; Tasks: desktopicon; Components: Venue_Client; IconIndex: 0
Name: {userappdata}\Microsoft\Internet Explorer\Quick Launch\Access Grid Venue Client; IconFilename: {app}\config\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22\Lib\site-packages}\pythonw.exe; Parameters: VenueClient.py --personalNode; WorkingDir: {app}; Tasks: quicklaunchicon; Components: Venue_Client; IconIndex: 0
Name: {group}\Documentation\README; Filename: {app}\Documentation\README
Name: {group}\Documentation\Developers Documentation; Filename: {app}\Documentation\index.html
Name: {group}\Documentation\License; IconFilename: {app}\config\ag.ico; Filename: {app}\COPYING.txt

[Registry]
Root: HKLM; Subkey: SOFTWARE\Access Grid Toolkit\2.0; ValueType: expandsz; ValueName: InstallPath; ValueData: {app}; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\Access Grid Toolkit\2.0; ValueType: expandsz; ValueName: ConfigPath; ValueData: {commonappdata}\AccessGrid; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\Access Grid Toolkit\2.0; ValueType: expandsz; ValueName: UserConfigPath; ValueData: {userappdata}\Access Grid Toolkit\config; Flags: uninsdeletekey

[Types]

[Tasks]
Name: desktopicon; Description: Create &Desktop Icons; GroupDescription: Additional icons:; Components: Audio_Service Video_Consumer Video_Producer Venue_Client
Name: quicklaunchicon; Description: Create a &Quick Launch Icon; GroupDescription: Additional icons:; Flags: unchecked

[Messages]
DirExists=The directory:%n%n%1%n%nalready exists and appears to have an AccessGrid Toolkit installation in it.%n%nIt is recommended that you uninstall any existing AccessGrid Toolkit software before proceeding.  Do you wish to proceed anyway?
WelcomeLabel2=This will install the [name/ver] on your computer.%n%nIt is strongly recommended that you uninstall any previous version of the [name] before continuing.%n%nIt is also strongly recommended that you close all other applications you have running before continuing with this installation.%n%nThese steps will help prevent any conflicts during the installation process.

[Run]
Filename: {app}\config\Postinstall.py; Flags: shellexec runminimized
Filename: {app}\SetupVideo.py; WorkingDir: {app}; Description: Setup what video devices will produce video streams; Components: Video_Producer; Flags: postinstall unchecked shellexec

[UninstallDelete]
Name: {reg:HKLM\Software\Python\PythonCore\2.2\PythonPath\win32com,|C:\Python22\Lib\site-packages}\AccessGrid; Type: filesandordirs
Name: {userappdata}\Access Grid Toolkit\certmgr.cfg; Type: files

[Dirs]
Name: {app}\config; Components: Venue_Client
Name: {commonappdata}\AccessGrid; Components: Venue_Client
Name: {app}\include

[INI]
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: node; Key: servicemanagers; String: servicemanager0
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service1; Key: packagename; String: VideoConsumerService.zip
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service1; Key: resource; String: None
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service1; Key: executable; String: {app}\vic.exe
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service1; Key: serviceconfig; String: serviceconfig1
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service0; Key: packagename; String: AudioService.zip
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service0; Key: resource; String: None
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service0; Key: executable; String: {app}\rat.exe
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service0; Key: serviceconfig; String: serviceconfig0
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: servicemanager0; Key: url; String: https://localhost:12000/ServiceManager
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: servicemanager0; Key: services; String: service0 service1
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: servicemanager0; Key: name; String: localhost:12000
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: serviceconfig1
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: serviceconfig0

Filename: {commonappdata}\AccessGrid\AGNodeService.cfg; Section: Node Configuration; Key: servicesDirectory; String: {app}\services
Filename: {commonappdata}\AccessGrid\AGNodeService.cfg; Section: Node Configuration; Key: configDirectory; String: {commonappdata}\AccessGrid\nodeConfig
Filename: {commonappdata}\AccessGrid\AGNodeService.cfg; Section: Node Configuration; Key: defaultNodeConfiguration; String: defaultWindows

Filename: {commonappdata}\AccessGrid\AGServiceManager.cfg; Section: Service Manager; Key: servicesDirectory; String: {app}\local_services

[InstallDelete]
Name: {userappdata}\Access Grid Toolkit\certmgr.cfg; Type: files
