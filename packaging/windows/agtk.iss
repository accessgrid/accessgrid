;
; RCS-ID: $Id: agtk.iss,v 1.75 2004-05-06 03:30:29 judson Exp $
;

; Set externally
; SourceDir : The location of the AccessGrid Build Tree
; AppVersion : what version are you packaging
; VersionInformation: a string indicating the more version information
; PythonVersion: a string indicating the version of python (2.2 or 2.3)

#ifndef SourceDir
#error "SourceDir must be defined to build a package."
#endif

#ifndef BuildDir
#error "BuildDir must be defined to build a package."
#endif

#ifndef AppVersion
#error "AppVersion must be defined to build a package."
#endif

#ifndef VersionInformation
#error "VersionInformation must be defined to build a package."
#endif

; used internally
#define AppName "Access Grid Toolkit"
#define AppNameShort "AGTk"

[Setup]
AppVerName={#AppVersion}-{#VersionInformation}
AppVersion={#AppVersion}
SourceDir={#BuildDir}
OutputDir={#SourceDir}
OutputBaseFilename={#AppNameShort}-{#AppVersion}-{#VersionInformation}-Py-2.{#PythonSubVersion}

AppName={#AppName}
AppCopyright=Copyright © 2003-2004 Argonne National Laboratory / University of Chicago. All Rights Reserved.
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

UninstallDisplayName={#AppNameShort} {#AppVersion}
DisableStartupPrompt=true
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
UsePreviousSetupType=true
UsePreviousTasks=false
UsePreviousGroup=true
ShowLanguageDialog=yes

[Files]
; The Python Modules
Source: Lib\site-packages\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages; Flags: recursesubdirs overwritereadonly restartreplace

; Documentation
Source: doc\Developer\*.*; DestDir: {app}\doc\Developer; Flags: recursesubdirs
Source: doc\VenueClientManual\*.*; DestDir: {app}\doc\VenueClientManual; Flags: recursesubdirs
Source: doc\VenueManagementManual\*.*; DestDir: {app}\doc\VenueManagementManual; Flags: recursesubdirs

; Certificates for trusted CA's
Source: config\CAcertificates\*.*; DestDir: {app}\config\CAcertificates

; General setup stuff
Source: COPYING.txt; DestDir: {app}
Source: README; DestDir: {app}; Flags: isreadme; DestName: README.txt

; Program Files
Source: bin\*.*; DestDir: {app}\bin

; Special short cuts to invoke without the python console

Source: bin\CertificateRequestTool.py; DestDir: {app}\bin; DestName: CertificateRequestTool.pyw
Source: bin\NodeManagement.py; DestDir: {app}\bin; DestName: NodeManagement.pyw
Source: bin\NodeSetupWizard.py; DestDir: {app}\bin; DestName: NodeSetupWizard.pyw
Source: bin\SetupVideo.py; DestDir: {app}\bin; DestName: SetupVideo.pyw

; Service packages
Source: NodeServices\*.zip; DestDir: {app}\NodeServices

; Shared Application packages
Source: SharedApplications\*.agpkg; DestDir: {app}\SharedApplications

; System wide files, windows wierdness no doubt
Source: install\agicons.exe; DestDir: {app}\install
Source: install\msvcr70.dll; DestDir: {win}\system32; Flags: restartreplace uninsneveruninstall onlyifdoesntexist
; end system files

[Icons]
Name: {group}\View README; Filename: {app}\README.txt; Flags: createonlyiffileexists; Comment: Read the ReadMe.
Name: {group}\Venue Client; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\VenueClient.py"" --personalNode"; IconFilename: {app}\install\agicons.exe; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the venue client software.
Name: {group}\Venue Client (Debug Mode); IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\VenueClient.py"" -d --personalNode"; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the venue client in debugging mode.
Name: {group}\Venue Management Tool; IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\VenueManagement.py"""; WorkingDir: %APPDATA%\AccessGrid; Comment:Manage venue servers.
Name: {group}\Request a Certificate; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\CertificateRequestTool.pyw"""; WorkingDir: %APPDATA%\AccessGrid; IconFilename: {app}\install\agicons.exe

Name: {group}\Configure\Search for Video Devices (No Output Generated); IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\SetupVideo.pyw"""; WorkingDir: %APPDATA%\AccessGrid; Comment: Search for video devices for the Video Producer service. There is no output for this program.
Name: {group}\Configure\Node Setup Wizard; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\NodeSetupWizard.pyw"""; WorkingDir: %APPDATA%\AccessGrid; IconFilename: {app}\install\agicons.exe; Comment: Run the AG Node Configuration Wizard
Name: {group}\Configure\Node Management; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\NodeManagement.pyw"""; WorkingDir: %APPDATA%\AccessGrid; IconFilename: {app}\install\agicons.exe; Comment: Configure an AG node

Name: {group}\Services\Venue Server (Debug); IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\VenueServer.py"" --debug"; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the venue server software in debugging mode.
Name: {group}\Services\Venue Server; IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\VenueServer.py"" --debug"; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the venue server software in debugging mode.
Name: {group}\Services\Service Manager (Debug); IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\AGServiceManager.py"" --debug"; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the service manager software in debugging mode.
Name: {group}\Services\Service Manager; IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\AGServiceManager.py"" --debug"; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the venue service manager in debugging mode.
Name: {group}\Services\Node Service (Debug); IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\AGNodeService.py"" --debug"; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the node service software in debugging mode.
Name: {group}\Services\Node Service; IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\AGNodeService.py"" --debug"; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the node service software in debugging mode.

Name: {group}\Documentation\Venue Client Manual; Filename: {app}\doc\VenueClientManual\VenueClientManualHTML.htm; Comment: Read the Venue Client Manual.
Name: {group}\Documentation\Venue Management Client Manual; Filename: {app}\doc\VenueManagementManual\VenueManagementManualHTML.htm; Comment: Read the Venue Management Manual.
Name: {group}\Documentation\View License; IconFilename: {app}\install\agicons.exe; Filename: {app}\COPYING.txt; Comment: Read the software license under which the AGTk is distributed
Name: {group}\Documentation\Developers Documentation; Filename: {app}\doc\Developer\index.html; Comment: epydoc-generated documentation for developers.

Name: {group}\Uninstall the AGTk; Filename: {uninstallexe}; Comment: Uninstall the Access Grid Toolkit.

Name: {userappdata}\Microsoft\Internet Explorer\Quick Launch\Access Grid Venue Client; IconFilename: {app}\install\agicons.exe; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\VenueClient.py"" --personalNode"; WorkingDir: %APPDATA%\AccessGrid; Tasks: quicklaunchicon

Name: {commondesktop}\Access Grid Venue Client; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\VenueClient.py"" --personalNode"; IconFilename: {app}\install\agicons.exe; WorkingDir: %APPDATA%\AccessGrid; Tasks: desktopicon; Comment: Run the Venue Client!

[Registry]
Root: HKLM; Subkey: SOFTWARE\{#AppName}; ValueType: none; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\{#AppName}\{#AppVersion}; ValueType: expandsz; ValueName: InstallPath; ValueData: {app}; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\{#AppName}\{#AppVersion}; ValueType: expandsz; ValueName: VersionInformation; ValueData: {#VersionInformation}; Flags: uninsdeletekey

[Tasks]
Name: desktopicon; Description: Create &Desktop Icons; GroupDescription: Additional icons:
Name: quicklaunchicon; Description: Create a &Quick Launch Icon; GroupDescription: Additional icons:; Flags: unchecked

[Messages]
DirExists=The directory:%n%n%1%n%nalready exists and appears to have an {#AppName} installation in it.%n%nIt is recommended that you uninstall any existing {#AppName} software before proceeding.  Do you wish to proceed anyway?
WelcomeLabel2=This will install the {#AppName} {#AppVersion} {#VersionInformation} on your computer.%n%nIt is strongly recommended that you uninstall any previous version of the {#AppName} before continuing.%n%nIt is also strongly recommended that you close all other applications you have running before continuing with this installation.%n%nThese steps will help prevent any conflicts during the installation process.

[Run]
Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; WorkingDir: {app}\bin; Description: Setup what video devices will produce video streams; Flags: runminimized nowait shellexec; Parameters: SetupVideo.pyw
Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; WorkingDir: {app}\bin; Description: Install shared apps system wide.; Flags: runminimized nowait shellexec; Parameters: agpm.py -s --post-install

[UninstallDelete]
Name: {app}; Type: filesandordirs
Name: {app}\bin\*.dat; Type: files
Name: {app}\bin\*.cfg; Type: files

[Dirs]
Name: {app}\config\nodeConfig
Name: {app}\Logs
Name: {app}\PackageCache
Name: {app}\SharedApplications
Name: {app}\Services
Name: {app}\NodeServices

[INI]
Filename: {app}\config\nodeConfig\defaultWindows; Section: node; Key: servicemanagers; String: servicemanager0
Filename: {app}\config\nodeConfig\defaultWindows; Section: service1; Key: packagename; String: VideoConsumerService.zip
Filename: {app}\config\nodeConfig\defaultWindows; Section: service1; Key: resource; String: None
Filename: {app}\config\nodeConfig\defaultWindows; Section: service1; Key: executable; String: {app}\bin\vic.exe
Filename: {app}\config\nodeConfig\defaultWindows; Section: service1; Key: serviceconfig; String: serviceconfig1
Filename: {app}\config\nodeConfig\defaultWindows; Section: service0; Key: packagename; String: AudioService.zip
Filename: {app}\config\nodeConfig\defaultWindows; Section: service0; Key: resource; String: None
Filename: {app}\config\nodeConfig\defaultWindows; Section: service0; Key: executable; String: {app}\bin\rat.exe
Filename: {app}\config\nodeConfig\defaultWindows; Section: service0; Key: serviceconfig; String: serviceconfig0
Filename: {app}\config\nodeConfig\defaultWindows; Section: servicemanager0; Key: url; String: https://localhost:12000/ServiceManager
Filename: {app}\config\nodeConfig\defaultWindows; Section: servicemanager0; Key: services; String: service0 service1
Filename: {app}\config\nodeConfig\defaultWindows; Section: servicemanager0; Key: name; String: localhost:12000
Filename: {app}\config\nodeConfig\defaultWindows; Section: serviceconfig1; Key: ";key"; String: value
Filename: {app}\config\nodeConfig\defaultWindows; Section: serviceconfig0; Key: ";key"; String: value

Filename: {app}\config\AGNodeService.cfg; Section: Node Configuration; Key: defaultNodeConfiguration; String: defaultWindows

[InstallDelete]
Name: {userappdata}\AccessGrid\certmgr.cfg; Type: files
Name: {pf}\Access Grid Toolkit; Type: filesandordirs
