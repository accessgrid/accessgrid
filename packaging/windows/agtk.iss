;
; RCS-ID: $Id: agtk.iss,v 1.24 2003-09-17 17:34:29 judson Exp $
;

#define SourceDir "C:\Software\AccessGrid\AccessGrid"
#define OutputDir "C:\Software\AccessGrid"
#define AppName "Access Grid Toolkit"
#define AppNameShort "AGTk"
#define AppVersionLong "2.1.2"
#define AppVersionShort "2.1.2"
#define VersionInformation "Official Release"

[_ISTool]
EnableISX=true

[_ISToolPreCompile]
Name: mkdir; Parameters: C:\Software\AccessGrid\AccessGrid\dist\bin
Name: mkdir; Parameters: C:\Software\AccessGrid\AccessGrid\dist\services
Name: python; Parameters: C:\Software\AccessGrid\AccessGrid\packaging\makeServicePackages.py C:\Software\AccessGrid\AccessGrid\services\node C:\Software\AccessGrid\AccessGrid\dist\services; Flags: abortonerror
Name: C:\Software\AccessGrid\AccessGrid\packaging\windows\BuildVic.cmd; Parameters: C:\Software\AccessGrid\ag-vic C:\Software\AccessGrid\AccessGrid\dist\bin; Flags: abortonerror
Name: C:\Software\AccessGrid\AccessGrid\packaging\windows\BuildRat.cmd; Parameters: C:\Software\AccessGrid\ag-rat C:\Software\AccessGrid\AccessGrid\dist\bin; Flags: abortonerror
Name: C:\Software\AccessGrid\AccessGrid\packaging\windows\BuildPutty.cmd; Parameters: C:\software\AccessGrid\putty C:\software\AccessGrid\AccessGrid\dist; Flags: abortonerror
Name: C:\Software\AccessGrid\AccessGrid\packaging\windows\BuildSendSettingChange.cmd; Parameters: C:\software\AccessGrid C:\software\AccessGrid\AccessGrid\dist; Flags: abortonerror
Name: C:\Software\AccessGrid\AccessGrid\packaging\windows\BuildPythonModules.cmd; Parameters: C:\Software\AccessGrid C:\Software\AccessGrid\AccessGrid\dist; Flags: abortonerror

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

AppName={#AppName}
AppCopyright=Copyright © 2003 Argonne National Laboratory / University of Chicago. All Rights Reserved.
AppPublisher=Futures Laboratory / Argonne National Laboratory
AppPublisherURL=http://www.mcs.anl.gov/fl
AppSupportURL=http://bugzilla.mcs.anl.gov/accessgrid
AppUpdatesURL=http://www.mcs.anl.gov/fl/research/accessgrid
AppID={907B1500-42CA-4148-8F13-2004654CCA06}
Compression=zip/9
MinVersion=0,5.0.2195
LicenseFile=COPYING.txt
DisableDirPage=false
DefaultGroupName={#AppName}
DefaultDirName={pf}\{#AppName}
UsePreviousAppDir=false
UserInfoPage=false
WindowVisible=false

UninstallDisplayName={#AppNameShort} {#AppVersionShort}
DisableStartupPrompt=false
WindowResizable=false
AlwaysShowComponentsList=false
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
UninstallFilesDir={app}\uninstall
InfoBeforeFile=Install.WINDOWS
ShowTasksTreeLines=true
PrivilegesRequired=admin
UninstallDisplayIcon={app}\install\agicons.exe
DisableReadyPage=true
UsePreviousSetupType=false
UsePreviousTasks=false
UsePreviousGroup=true

[Files]
; The Python Modules
Source: dist\Lib\site-packages\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22}\Lib\site-packages; Flags: recursesubdirs overwritereadonly restartreplace

; Documentation
Source: doc\AccessGrid\*.*; DestDir: {app}\doc\Developer; Flags: recursesubdirs
Source: doc\VENUE_CLIENT_MANUAL_HTML\*.*; DestDir: {app}\doc\VenueClient; Flags: recursesubdirs
Source: doc\VENUE_MANAGEMENT_MANUAL_HTML\*.*; DestDir: {app}\doc\VenueManagement; Flags: recursesubdirs

; Program Files
Source: ..\WinGlobus\globus_setup\globus_init.py; DestDir: {app}\bin; Flags: confirmoverwrite; DestName: globus_init.pyw
Source: ..\WinGlobus\globus_setup\winnet.py; DestDir: {app}\bin; Flags: confirmoverwrite
Source: ..\WinGlobus\globus_setup\network_init.py; DestDir: {app}\bin; Flags: confirmoverwrite; DestName: network_init.pyw
Source: ..\WinGlobus\certificates\42864e48.0; DestDir: {commonappdata}\AccessGrid\certificates; DestName: 42864e48.0
Source: ..\WinGlobus\certificates\45cc9e80.0; DestDir: {commonappdata}\AccessGrid\certificates; DestName: 45cc9e80.0
Source: ..\WinGlobus\certificates\42864e48.signing_policy; DestDir: {commonappdata}\AccessGrid\certificates; DestName: 42864e48.signing_policy
Source: ..\WinGlobus\certificates\45cc9e80.signing_policy; DestDir: {commonappdata}\AccessGrid\certificates; DestName: 45cc9e80.signing_policy

Source: COPYING.txt; DestDir: {app}
Source: README; DestDir: {app}; Flags: isreadme; DestName: README.txt

Source: bin\VenueServer.py; DestDir: {app}\bin
Source: bin\VenueClient.py; DestDir: {app}\bin
Source: bin\AGServiceManager.py; DestDir: {app}\bin
Source: bin\CertificateRequestTool.py; DestDir: {app}\bin; DestName: CertificateRequestTool.pyw
Source: bin\certmgr.py; DestDir: {app}\bin; DestName: certmgr.py
Source: bin\NodeManagement.py; DestDir: {app}\bin; DestName: NodeManagement.pyw
Source: bin\NodeSetupWizard.py; DestDir: {app}\bin; DestName: NodeSetupWizard.pyw
Source: bin\SetupVideo.py; DestDir: {app}\bin; DestName: SetupVideo.pyw
Source: bin\VenueManagement.py; DestDir: {app}\bin; DestName: VenueManagement.py
Source: bin\AGNodeService.py; DestDir: {app}\bin
Source: bin\RegisterApp.py; DestDir: {app}\bin
Source: dist\services\AudioService.zip; DestDir: {commonappdata}\AccessGrid\services; DestName: AudioService.zip
Source: dist\services\VideoConsumerService.zip; DestDir: {commonappdata}\AccessGrid\services; DestName: VideoConsumerService.zip
Source: dist\services\VideoProducerService.zip; DestDir: {commonappdata}\AccessGrid\services; DestName: VideoProducerService.zip
Source: dist\bin\rat.exe; DestDir: {app}\bin; DestName: rat.exe
Source: dist\bin\ratui.exe; DestDir: {app}\bin; DestName: ratui.exe
Source: dist\bin\ratmedia.exe; DestDir: {app}\bin; DestName: ratmedia.exe
Source: dist\bin\vic.exe; DestDir: {app}\bin; DestName: vic.exe
Source: dist\bin\rat-kill.exe; DestDir: {app}\bin; DestName: rat-kill.exe
Source: dist\bin\pscp.exe; DestDir: {app}\bin; DestName: pscp.exe
Source: dist\bin\send_settingchange.exe; DestDir: {app}\bin; DestName: send_settingchange.exe
Source: packaging\windows\agicons.exe; DestDir: {app}\install

; begin VC system files
; (Note: Scroll to the right to see the full lines!)
Source: packaging\windows\msvcr70.dll; DestDir: {win}\system32; Flags: restartreplace uninsneveruninstall
; end VC system files


[Icons]
Name: {group}\View README; Filename: {app}\README.txt; Flags: createonlyiffileexists; Comment: Read the ReadMe.
Name: {group}\Venue Client; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22}\pythonw.exe; Parameters: """{app}\bin\VenueClient.py"" --personalNode"; IconFilename: {app}\install\agicons.exe; WorkingDir: {userappdata}\AccessGrid; Comment: Run the venue client software.
Name: {group}\Venue Client (Debug Mode); IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22}\python.exe; Parameters: """{app}\bin\VenueClient.py"" -d --personalNode"; WorkingDir: {userappdata}\AccessGrid; Comment: Run the venue client in debugging mode.

Name: {group}\Configure\Search for Video Devices (No Output Generated); IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22}\pythonw.exe; Parameters: """{app}\bin\SetupVideo.py"""; WorkingDir: {userappdata}\AccessGrid; Comment: Search for video devices for the Video Producer service. There is no output for this program.
Name: {group}\Configure\Reconfigure Globus; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22}\pythonw.exe; Parameters: """{app}\bin\globus_init.pyw"""; WorkingDir: {userappdata}\AccessGrid; Comment: Set up Globus runtime environment; IconFilename: {app}\install\agicons.exe
Name: {group}\Configure\Reconfigure Network; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22}\pythonw.exe; Parameters: """{app}\bin\network_init.pyw"""; WorkingDir: {userappdata}\AccessGrid; Comment: Set up Globus network configuration; IconFilename: {app}\install\agicons.exe
Name: {group}\Configure\Node Setup Wizard; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22}\pythonw.exe; Parameters: """{app}\bin\NodeSetupWizard.pyw"""; WorkingDir: {userappdata}\AccessGrid; IconFilename: {app}\install\agicons.exe
Name: {group}\Request a Certificate; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22}\pythonw.exe; Parameters: """{app}\bin\CertificateRequestTool.pyw"""; WorkingDir: {userappdata}\AccessGrid; IconFilename: {app}\install\agicons.exe
Name: {group}\Venue Server\Venue Server; IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22}\pythonw.exe; Parameters: """{app}\bin\VenueServer.py"""; WorkingDir: {userappdata}\AccessGrid; Comment: Run the venue server software.
Name: {group}\Venue Server\Venue Server (Debug); IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22}\python.exe; Parameters: """{app}\bin\VenueServer.py"" --debug"; WorkingDir: {userappdata}\AccessGrid; Comment: Run the venue server software in debugging mode.
Name: {group}\Venue Server\Manage Venue Servers; IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22}\pythonw.exe; Parameters: """{app}\bin\VenueManagement.py"""; WorkingDir: {userappdata}\AccessGrid; Comment: Run the venue management tool.

Name: {group}\Documentation\Venue Client Manual; Filename: {app}\doc\VenueClient\VenueClientManualHTML.htm; Comment: Read the Venue Client Manual.
Name: {group}\Documentation\Venue Management Client Manual; Filename: {app}\doc\VenueManagement\VenueManagementManualHTML.htm; Comment: Read the Venue Client Manual.
Name: {group}\Documentation\View License; IconFilename: {app}\install\agicons.exe; Filename: {app}\COPYING.txt; Comment: Read the software license the AGTk is distributed under.
Name: {group}\Documentation\Developers Documentation; Filename: {app}\doc\Developer\index.html; Comment: Happy Doc generated documentation for developers.

Name: {group}\Uninstall the AGTk; Filename: {uninstallexe}; Comment: Uninstall the Access Grid Toolkit.

Name: {userappdata}\Microsoft\Internet Explorer\Quick Launch\Access Grid Venue Client; IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22}\pythonw.exe; Parameters: """{app}\bin\VenueClient.py"" --personalNode"; WorkingDir: {userappdata}\AccessGrid; Tasks: quicklaunchicon

Name: {commondesktop}\Access Grid Venue Client; Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22}\pythonw.exe; Parameters: """{app}\bin\VenueClient.py"" --personalNode"; IconFilename: {app}\install\agicons.exe; WorkingDir: {userappdata}\AccessGrid; Tasks: desktopicon; Comment: Run the Venue Client!

[Registry]
Root: HKLM; Subkey: SOFTWARE\{#AppName}; ValueType: none; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\{#AppName}\{#AppVersionShort}; ValueType: expandsz; ValueName: InstallPath; ValueData: {app}; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\{#AppName}\{#AppVersionShort}; ValueType: expandsz; ValueName: ConfigPath; ValueData: {commonappdata}\AccessGrid; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\{#AppName}\{#AppVersionShort}; ValueType: expandsz; ValueName: UserConfigPath; ValueData: {userappdata}\AccessGrid\config; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\{#AppName}\{#AppVersionShort}; ValueType: expandsz; ValueName: VersionInformation; ValueData: {#VersionInformation}
Root: HKLM; Subkey: SYSTEM\CurrentControlSet\Control\Session Manager\Environment; ValueType: expandsz; ValueName: GLOBUS_LOCATION; ValueData: {commonappdata}\AccessGrid
Root: HKLM; Subkey: SYSTEM\CurrentControlSet\Control\Session Manager\Environment; ValueType: expandsz; ValueName: GLOBUS_HOSTNAME
Root: HKLM; Subkey: SOFTWARE\Globus; ValueType: expandsz; ValueName: GLOBUS_LOCATION; ValueData: {commonappdata}\AccessGrid; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\Globus\GSI; ValueType: expandsz; ValueName: x509_cert_dir; ValueData: {commonappdata}\AccessGrid\certificates; Flags: uninsdeletekey
Root: HKCU; Subkey: Software\Globus; Flags: uninsdeletekey; ValueType: none
Root: HKCU; Subkey: Software\Globus\GSI; ValueType: expandsz; ValueName: x509_user_proxy; ValueData: {%TEMP|{win}\temp}\proxy; Flags: uninsdeletekey
Root: HKCU; Subkey: Software\Globus\GSI; ValueType: expandsz; ValueName: x509_user_key; ValueData: {userappdata}\globus\userkey.pem; Flags: uninsdeletekey
Root: HKCU; Subkey: Software\Globus\GSI; ValueType: expandsz; ValueName: x509_user_cert; ValueData: {userappdata}\globus\usercert.pem; Flags: uninsdeletekey
Root: HKCU; Subkey: Software\Globus\GSI; ValueType: expandsz; ValueName: x509_cert_dir; ValueData: {commonappdata}\AccessGrid\certificates; Flags: uninsdeletekey
Root: HKCU; Subkey: Software\Globus\GSI; Flags: uninsdeletekey; ValueType: none
Root: HKCU; Subkey: Environment; ValueType: expandsz; ValueName: GLOBUS_LOCATION; ValueData: {commonappdata}\AccessGrid

[Tasks]
Name: desktopicon; Description: Create &Desktop Icons; GroupDescription: Additional icons:
Name: quicklaunchicon; Description: Create a &Quick Launch Icon; GroupDescription: Additional icons:; Flags: unchecked

[Messages]
DirExists=The directory:%n%n%1%n%nalready exists and appears to have an {#AppName} installation in it.%n%nIt is recommended that you uninstall any existing {#AppName} software before proceeding.  Do you wish to proceed anyway?
WelcomeLabel2=This will install the {#AppName} {#AppVersionLong} on your computer.%n%nIt is strongly recommended that you uninstall any previous version of the {#AppName} before continuing.%n%nIt is also strongly recommended that you close all other applications you have running before continuing with this installation.%n%nThese steps will help prevent any conflicts during the installation process.

[Run]
Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22}\python.exe; WorkingDir: {app}\bin; Description: Setup what video devices will produce video streams; Flags: runminimized nowait shellexec; Parameters: SetupVideo.pyw
Filename: {app}\bin\send_settingchange.exe; Flags: runminimized waituntilidle; Description: Update system settings with globus configuration.
Filename: {reg:HKLM\Software\Python\PythonCore\2.2\InstallPath,|C:\Python22}\pythonw.exe; Description: Set up Globus runtime environment; Flags: postinstall waituntilidle; Parameters: globus_init.pyw; WorkingDir: {app}\bin

[UninstallDelete]
Name: {app}; Type: filesandordirs
Name: {app}\bin\*.dat; Type: files
Name: {app}\bin\*.cfg; Type: files

[Dirs]
Name: {app}\config
Name: {userappdata}\AccessGrid\local_services
Name: {commonappdata}\AccessGrid\nodeConfig
Name: {userappdata}\AccessGrid\certificates
Name: {userappdata}\globus

[INI]
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: node; Key: servicemanagers; String: servicemanager0
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service1; Key: packagename; String: VideoConsumerService.zip
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service1; Key: resource; String: None
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service1; Key: executable; String: {app}\bin\vic.exe
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service1; Key: serviceconfig; String: serviceconfig1
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service0; Key: packagename; String: AudioService.zip
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service0; Key: resource; String: None
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service0; Key: executable; String: {app}\bin\rat.exe
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: service0; Key: serviceconfig; String: serviceconfig0
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: servicemanager0; Key: url; String: https://localhost:12000/ServiceManager
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: servicemanager0; Key: services; String: service0 service1
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: servicemanager0; Key: name; String: localhost:12000
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: serviceconfig1; Key: ";key "; String: value
Filename: {commonappdata}\AccessGrid\nodeConfig\defaultWindows; Section: serviceconfig0; Key: ";key"; String: value

Filename: {commonappdata}\AccessGrid\AGNodeService.cfg; Section: Node Configuration; Key: defaultNodeConfiguration; String: defaultWindows

[InstallDelete]
Name: {userappdata}\AccessGrid\certmgr.cfg; Type: files
Name: {pf}\Access Grid Toolkit; Type: filesandordirs
