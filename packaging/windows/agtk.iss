;
; RCS-ID: $Id: agtk.iss,v 1.13 2003-05-30 22:08:34 judson Exp $
;

#define SourceDir "C:\Software\AccessGrid\AccessGrid\Release"
#define OutputDir "C:\xfer"
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

[_ISToolPreCompile]
; It would be a good idea to figure out how to pass the SourceDir as a
; parameter to prebuild. Ti and I have chatted about this, it's on the
; to do list :-)
;
Name: python; Parameters: C:\Software\AccessGrid\AccessGrid\packaging\makeServicePackages.py C:\Software\AccessGrid\AccessGrid\services\node; Flags: abortonerror
Name: C:\Software\AccessGrid\AccessGrid\packaging\windows\BuildAccessGrid.cmd; Parameters: C:\Software\AccessGrid\AccessGrid; Flags: abortonerror
Name: C:\Software\AccessGrid\AccessGrid\packaging\windows\BuildVic.cmd; Parameters: C:\Software\AccessGrid\ag-vic C:\Software\AccessGrid\AccessGrid\Release\bin; Flags: abortonerror
Name: C:\Software\AccessGrid\AccessGrid\packaging\windows\BuildRat.cmd; Parameters: C:\Software\AccessGrid\ag-rat C:\Software\AccessGrid\AccessGrid\Release\bin; Flags: abortonerror

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
AppCopyright=Copyright © 2003 Argonne National Laboratory / University of Chicago. All Rights Reserved.
AppPublisher=Futures Laboratory / Argonne National Laboratory
AppPublisherURL=http://www.mcs.anl.gov/fl
AppSupportURL=http://bugzilla.mcs.anl.gov/accessgrid
AppUpdatesURL=http://www.mcs.anl.gov/fl/research/accessgrid
AppID={907B1500-42CA-4148-8F13-2004654CCA06}
Compression=zip/9
MinVersion=0,5.0.2195
LicenseFile=C:\Software\AccessGrid\AccessGrid\COPYING.txt
DisableDirPage=false
DefaultGroupName={#AppNameShort} {#AppVersionShort}
DefaultDirName={pf}\{#AppNameShort} {#AppVersionShort}
UsePreviousAppDir=false
UserInfoPage=false
WindowVisible=false

UninstallDisplayName={#AppNameShort} {#AppVersionShort}
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
InfoBeforeFile=C:\Software\AccessGrid\AccessGrid\Install.WINDOWS
ShowTasksTreeLines=true
PrivilegesRequired=admin
UninstallDisplayIcon={app}\config\agicons.exe

[Components]
Name: Venue_Client; Description: Minimum AGTk Client software.; Flags: fixed; Types: custom compact full
Name: Video_Producer; Description: Enables the sending of video.; Types: full
Name: Video_Consumer; Description: Enables the recpeption and display of video streams; Types: full
Name: Audio_Service; Description: Enables full-duplex audio.; Types: full
Name: Venue_Server; Description: Server Software that allows you to host your own Virtual Venue Server; Types: custom

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

;Source: Scripts\VenuesServerRegistry.py; DestDir: {app}; Components: Venue_Server

Source: Scripts\MailcapSetup.py; DestDir: {app}

; Default node configuration
Source: share\AccessGrid\nodeConfig\defaultWindows; DestDir: {commonappdata}\AccessGrid\nodeConfig; Flags: confirmoverwrite

; AG Icon for programs and stuff
Source: share\AccessGrid\agicons.exe; DestDir: {app}\config

; Documentation
Source: doc\Developer\*.*; DestDir: {app}\Documentation\Developer
Source: doc\VenueClientManual\*.*; DestDir: {app}\Documentation\VenueClientManual
Source: doc\VenueManagementManual\*.*; DestDir: {app}\Documentation\VenueManagementManual

; Post install scripts
Source: share\AccessGrid\packaging\windows\Postinstall.py; DestDir: {app}\config; Flags: deleteafterinstall

; Vic Video Tool
Source: bin\vic.exe; DestDir: {app}; Components: Video_Consumer Video_Producer

; Rat Audio Tool
Source: bin\rat-kill.exe; DestDir: {app}; Components: Audio_Service
Source: bin\rat.exe; DestDir: {app}; Components: Audio_Service
Source: bin\ratmedia.exe; DestDir: {app}; Components: Audio_Service
Source: bin\ratui.exe; DestDir: {app}; Components: Audio_Service
Source: COPYING.txt; DestDir: {app}
Source: README; DestDir: {app}; Flags: isreadme; DestName: README.txt

[Icons]
Name: {group}\Uninstall the AGTk; Filename: {uninstallexe}; Comment: Uninstall the Access Grid Toolkit.
;Name: {group}\Node Manager; IconFilename: {app}\config\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22\Lib\site-packages}\pythonw.exe; Parameters: NodeManagement.py; WorkingDir: {app}; Components: Venue_Client; IconIndex: 0
;Name: {group}\Debug\Node Manager; IconFilename: {app}\config\agicons.exe; Filename: {app}\NodeManagement.py; WorkingDir: {app}; Components: Venue_Client; IconIndex: 0
;Name: {group}\Debug\Setup Video; IconFilename: {app}\config\agicons.exe; Filename: {app}\SetupVideo.py; WorkingDir: {app}; Components: Video_Producer; IconIndex: 0
;Name: {group}\Debug\Venue Management; IconFilename: {app}\config\agicons.exe; Filename: {app}\VenueManagement.py; Paramters: --debug; WorkingDir: {app}; Components: Venue_Server; IconIndex: 0
Name: {commondesktop}\Access Grid Venue Client; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22\Lib\site-packages}\pythonw.exe; Parameters: VenueClient.py --personalNode; IconFilename: {app}\config\agicons.exe; WorkingDir: {app}; Tasks: desktopicon; Components: Venue_Client; Comment: Run the Venue Client!
Name: {userappdata}\Microsoft\Internet Explorer\Quick Launch\Access Grid Venue Client; IconFilename: {app}\config\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22\Lib\site-packages}\pythonw.exe; Parameters: VenueClient.py --personalNode; WorkingDir: {app}; Tasks: quicklaunchicon; Components: Venue_Client; IconIndex: 0
Name: {group}\Documentation\Venue Client Manual; Filename: {app}\Documentation\VenueClient\index.html; Comment: Read the Venue Client Manual.
Name: {group}\Documentation\Developers Documentation; Filename: {app}\Documentation\Developer\index.html; Comment: Happy Doc generated documentation for developers.
Name: {group}\Documentation\View README; Filename: {app}\README.txt; Flags: createonlyiffileexists; Comment: Read the ReadMe.
Name: {group}\Documentation\View License; IconFilename: {app}\config\ag.ico; Filename: {app}\COPYING.txt; Comment: Read the software license the AGTk is distributed under.
Name: {group}\Venue Server\Venue Server; IconFilename: {app}\config\agicons.exe; Filename: {app}\VenueServer.py; WorkingDir: {app}; Components: Venue_Server; Comment: Run the venue server software.
Name: {group}\Venue Server\Venue Server (Debug); IconFilename: {app}\config\agicons.exe; Filename: {app}\VenueServer.py; Parameters: --debug; WorkingDir: {app}; Components: Venue_Server; Comment: Run the venue server software in debugging mode.
Name: {group}\Venue Server\Manage Venue Servers; IconFilename: {app}\config\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22\Lib\site-packages}\pythonw.exe; Parameters: VenueManagement.py; WorkingDir: {app}; Components: Venue_Server; Comment: Run the venue management tool.
Name: {group}\Venue Client (Debug Mode); IconFilename: {app}\config\agicons.exe; Filename: {app}\VenueClient.py; Parameters: --personalNode --debug; WorkingDir: {app}; Components: Venue_Client; Comment: Run the venue client in debugging mode.
Name: {group}\Search for Video Devices; IconFilename: {app}\config\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22\Lib\site-packages}\pythonw.exe; Parameters: SetupVideo.py; WorkingDir: {app}; Components: Video_Producer; Comment: Search for video devices for the Video Producer service.
Name: {group}\Venue Client; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22\Lib\site-packages}\pythonw.exe; Parameters: VenueClient.py --personalNode; IconFilename: {app}\config\agicons.exe; WorkingDir: {app}; Components: Venue_Client; Comment: Run the venue client software.

[Registry]
Root: HKLM; Subkey: SOFTWARE\Access Grid Toolkit\2.0; ValueType: expandsz; ValueName: InstallPath; ValueData: {app}; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\Access Grid Toolkit\2.0; ValueType: expandsz; ValueName: ConfigPath; ValueData: {commonappdata}\AccessGrid; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\Access Grid Toolkit\2.0; ValueType: expandsz; ValueName: UserConfigPath; ValueData: {userappdata}\Access Grid Toolkit\config; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\Access Grid Toolkit; ValueType: none; Flags: uninsdeletekey


[Tasks]
Name: desktopicon; Description: Create &Desktop Icons; GroupDescription: Additional icons:; Components: Audio_Service Video_Consumer Video_Producer Venue_Client
Name: quicklaunchicon; Description: Create a &Quick Launch Icon; GroupDescription: Additional icons:; Flags: unchecked

[Messages]
DirExists=The directory:%n%n%1%n%nalready exists and appears to have an AccessGrid Toolkit installation in it.%n%nIt is recommended that you uninstall any existing AccessGrid Toolkit software before proceeding.  Do you wish to proceed anyway?
WelcomeLabel2=This will install the [name/ver] on your computer.%n%nIt is strongly recommended that you uninstall any previous version of the [name] before continuing.%n%nIt is also strongly recommended that you close all other applications you have running before continuing with this installation.%n%nThese steps will help prevent any conflicts during the installation process.

[Run]
Filename: {app}\config\Postinstall.py; Flags: shellexec runminimized

Filename: {app}\SetupVideo.py; WorkingDir: {app}; Description: Setup what video devices will produce video streams; Components: Video_Producer; Flags: postinstall unchecked shellexec runminimized

[UninstallDelete]
Name: {reg:HKLM\Software\Python\PythonCore\2.2\PythonPath\win32com,|C:\Python22\Lib\site-packages}\AccessGrid; Type: filesandordirs
Name: {userappdata}\AccessGrid\certmgr.cfg; Type: files
Name: {app}; Type: filesandordirs

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
Name: {pf}\Access Grid Toolkit; Type: filesandordirs
