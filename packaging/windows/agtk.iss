;
; RCS-ID: $Id: agtk.iss,v 1.126 2006-04-24 20:44:13 turam Exp $
;

; Set externally
; SourceDir : The location of the AccessGrid Build Tree
; BuildDir : The location of the prebuilt distribution
; AppVersion : what version are you packaging
; DirName : name of program files directory
; VersionInformation: a string indicating the more version information
; PythonSubVersion: a string indicating the version of python (2.2 or 2.3)

;#define SourceDir "\software\AccessGrid\build"
;#define BuildDir "\software\AccessGrid\build\dist-20040908_130651"
;#define AppVersion "3.0"
;#define VersionInformation "Test Final"
;#define PythonSubVersion "3"

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

#ifndef PythonSubVersion
#error "PythonSubVersion must be defined to build a package."
#endif

; used internally
#define AppName "Access Grid Toolkit"
#define AppNameShort "AGTk"
#define DirName "3"

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
AppID=2CD98D2E-F3D2-438E-91F7-D74860A70953
MinVersion=0,5.0.2195
LicenseFile=COPYING.txt
DisableDirPage=false
DefaultGroupName={#AppName} {#DirName}
DefaultDirName={pf}\{#AppNameShort}-{#DirName}
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
UninstallDisplayIcon={app}\install\ag.ico
DisableReadyPage=true
UsePreviousSetupType=true
UsePreviousTasks=false
UsePreviousGroup=true
ShowLanguageDialog=yes
Compression=lzma

[Files]
; The Python Modules
Source: Lib\site-packages\_xmlplus\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\_xmlplus; Flags: recursesubdirs overwritereadonly restartreplace
Source: Lib\site-packages\AccessGrid3\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\AccessGrid3; Flags: recursesubdirs overwritereadonly restartreplace
Source: Lib\site-packages\feedparser.py; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages; Flags: recursesubdirs overwritereadonly restartreplace
Source: Lib\site-packages\ZSI\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\ZSI; Flags: recursesubdirs overwritereadonly restartreplace
Source: Lib\site-packages\zope\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\zope; Flags: recursesubdirs overwritereadonly restartreplace
Source: Lib\site-packages\OpenSSL_AG\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\OpenSSL_AG; Flags: recursesubdirs overwritereadonly restartreplace uninsneveruninstall
Source: Lib\site-packages\M2Crypto\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\M2Crypto; Flags: recursesubdirs overwritereadonly restartreplace
Source: Lib\site-packages\twisted\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\twisted; Flags: recursesubdirs overwritereadonly restartreplace
Source: Lib\site-packages\bonjour\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\bonjour; Flags: recursesubdirs overwritereadonly restartreplace
Source: Lib\site-packages\common\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\common; Flags: recursesubdirs overwritereadonly restartreplace
Source: Lib\site-packages\elementtree\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\elementtree; Flags: recursesubdirs overwritereadonly restartreplace
Source: Lib\site-packages\gov\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\gov; Flags: recursesubdirs overwritereadonly restartreplace

; Documentation
; Source: doc\Developer\*.*; DestDir: {app}\doc\Developer; Flags: recursesubdirs

; Certificates for trusted CA's
Source: config\CAcertificates\*.*; DestDir: {app}\config\CAcertificates

; General setup stuff
Source: COPYING.txt; DestDir: {app}
Source: README; DestDir: {app}; Flags: isreadme; DestName: README.txt

; Program Files
Source: bin\*.*; DestDir: {app}\bin
Source: bin\GoToVenue3.py; DestDir: {app}\bin; DestName: GoToVenue3.pyw

; Special short cuts to invoke without the python console

Source: bin\CertificateRequestTool3.py; DestDir: {app}\bin; DestName: CertificateRequestTool3.pyw
Source: bin\NodeManagement3.py; DestDir: {app}\bin; DestName: NodeManagement3.pyw
Source: bin\NodeSetupWizard3.py; DestDir: {app}\bin; DestName: NodeSetupWizard3.pyw

; Service packages
Source: NodeServices\*.zip; DestDir: {app}\NodeServices

; Shared Application packages
Source: SharedApplications\*.agpkg; DestDir: {app}\SharedApplications

; Default node configuration
Source: config\nodeConfig\default; DestDir: {app}\config\nodeConfig

; System wide files, windows wierdness no doubt
Source: install\ag.ico; DestDir: {app}\install
Source: install\msvcr70.dll; DestDir: {win}\system32; Flags: uninsneveruninstall onlyifdoesntexist
Source: install\msvcr71.dll; DestDir: {win}\system32; Flags: uninsneveruninstall onlyifdoesntexist
Source: install\msvcr71d.dll; DestDir: {win}\system32; Flags: uninsneveruninstall onlyifdoesntexist
;Source: install\ssleay32.dll; DestDir: {win}\system32; Flags: uninsneveruninstall onlyifdoesntexist
;Source: install\libeay32.dll; DestDir: {win}\system32; Flags: uninsneveruninstall onlyifdoesntexist
Source: install\ssleay32.dll; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\M2Crypto; 
Source: install\libeay32.dll; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\M2Crypto; 
Source: install\ssleay32.dll; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\OpenSSL_AG; 
Source: install\libeay32.dll; DestDir: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\OpenSSL_AG; 

; end system files

[Icons]
Name: {group}\View README; Filename: {app}\README.txt; Flags: createonlyiffileexists; Comment: Read the ReadMe.
Name: {group}\Venue Client; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\runag3.py"" ""{app}\bin\VenueClient.py"" --personalNode=1"; IconFilename: {app}\install\ag.ico; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the venue client software.
Name: {group}\Venue Client (Debug Mode); IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\runag3.py"" ""{app}\bin\VenueClient.py"" -d --personalNode=1"; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the venue client in debugging mode.
Name: {group}\Venue Management Tool; IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\runag3.py"" ""{app}\bin\VenueManagement.py"""; WorkingDir: %APPDATA%\AccessGrid; Comment: Manage venue servers.
Name: {group}\Request a Certificate; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\runag3.py"" ""{app}\bin\CertificateRequestTool.pyw"""; WorkingDir: %APPDATA%\AccessGrid; IconFilename: {app}\install\ag.ico

Name: {group}\Configure\Node Setup Wizard; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\runag3.py"" ""{app}\bin\NodeSetupWizard.pyw"""; WorkingDir: %APPDATA%\AccessGrid; IconFilename: {app}\install\ag.ico; Comment: Run the AG Node Configuration Wizard
Name: {group}\Configure\Node Management; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\runag3.py"" ""{app}\bin\NodeManagement.pyw"""; WorkingDir: %APPDATA%\AccessGrid; IconFilename: {app}\install\ag.ico; Comment: Configure an AG node

Name: {group}\Services\Venue Server (Debug); IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\runag3.py"" ""{app}\bin\VenueServer.py"" --debug"; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the venue server software in debugging mode.
Name: {group}\Services\Venue Server; IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\runag3.py"" ""{app}\bin\VenueServer.py"" --debug"; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the venue server software in debugging mode.
Name: {group}\Services\Service Manager (Debug); IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\runag3.py"" ""{app}\bin\AGServiceManager.py"" --debug"; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the service manager software in debugging mode.
Name: {group}\Services\Service Manager; IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\runag3.py"" ""{app}\bin\AGServiceManager.py"" --debug"; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the venue service manager in debugging mode.
Name: {group}\Services\Node Service (Debug); IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\runag3.py"" ""{app}\bin\AGServiceManager.py"" -n --debug"; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the node service software in debugging mode.
Name: {group}\Services\Node Service; IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Parameters: """{app}\bin\runag3.py"" ""{app}\bin\AGServiceManager.py"" -n"; WorkingDir: %APPDATA%\AccessGrid; Comment: Run the node service software in debugging mode.

Name: {group}\Documentation\View License; IconFilename: {app}\install\ag.ico; Filename: {app}\COPYING.txt; Comment: Read the software license under which the AGTk is distributed
; Name: {group}\Documentation\Developers Documentation; Filename: {app}\doc\Developer\index.html; Comment: epydoc-generated documentation for developers.

Name: {group}\Uninstall the AGTk; Filename: {uninstallexe}; Comment: Uninstall the Access Grid Toolkit.

Name: {userappdata}\Microsoft\Internet Explorer\Quick Launch\Access Grid Venue Client; IconFilename: {app}\install\ag.ico; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\runag3.py"" ""{app}\bin\VenueClient3.py"" --personalNode=1"; WorkingDir: %APPDATA%\AccessGrid; Tasks: quicklaunchicon

Name: {commondesktop}\Access Grid 3 Venue Client; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\runag3.py"" ""{app}\bin\VenueClient3.py"" --personalNode=1"; IconFilename: {app}\install\ag.ico; WorkingDir: %APPDATA%\AccessGrid; Tasks: desktopicon; Comment: Run the Venue Client!
Name: {group}\Manage Certificates; Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\pythonw.exe; Parameters: """{app}\bin\runag3.py"" ""{app}\bin\CertificateManager3.py"""; WorkingDir: %APPDATA%\AccessGrid; IconFilename: {app}\install\ag.ico

[Registry]
Root: HKLM; Subkey: SOFTWARE\{#AppName} {#DirName}; ValueType: none; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\{#AppName} {#DirName}\{#AppVersion}; ValueType: expandsz; ValueName: InstallPath; ValueData: {app}; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\{#AppName} {#DirName}\{#AppVersion}; ValueType: expandsz; ValueName: VersionInformation; ValueData: {#VersionInformation}; Flags: uninsdeletekey
Root: HKCR; Subkey: MIME\Database\Content Type\application/x-ag-venueclient; ValueType: string; ValueName: Extension; ValueData: .vv3d
Root: HKCR; Subkey: .vv3d; ValueType: string; ValueData: x-ag-venueclient; Flags: uninsdeletekey
Root: HKCR; Subkey: .vv3d; ValueType: string; ValueName: Content Type; ValueData: application/x-ag-venueclient; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag-venueclient; ValueType: dword; ValueName: EditFlags; ValueData: 00010000; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag-venueclient; ValueType: dword; ValueName: BrowserFlags; ValueData: 00000008; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag-venueclient; ValueType: string; ValueData: Access Grid Virtual Venue Description; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag-venueclient\shell; ValueType: string; ValueData: Open; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag-venueclient\shell\Open\command; ValueType: string; ValueData: """{reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe"" ""{app}\bin\runag3.py"" ""{app}\bin\GoToVenue3.py"" --file ""%1"""; Flags: uninsdeletekey

Root: HKCR; Subkey: .agpkg; ValueType: string; ValueData: x-ag-pkg; Flags: uninsdeletekey
Root: HKCR; Subkey: .agpkg; ValueType: string; ValueName: Content Type; ValueData: application/x-ag-pkg; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag-pkg; ValueType: dword; ValueName: EditFlags; ValueData: 00010000; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag-pkg; ValueType: dword; ValueName: BrowserFlags; ValueData: 00000008; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag-pkg; ValueType: string; ValueData: Access Grid Package; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag-pkg\shell; ValueType: string; ValueData: Open; Flags: uninsdeletekey
Root: HKCR; Subkey: x-ag-pkg\shell\Open\command; ValueType: string; ValueData: """{reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe"" ""{app}\bin\runag3.py"" ""{app}\bin\agpm3.py"" --gui --package ""%1"""; Flags: uninsdeletekey

[Tasks]
Name: desktopicon; Description: Create &Desktop Icons; GroupDescription: Additional icons:
Name: quicklaunchicon; Description: Create a &Quick Launch Icon; GroupDescription: Additional icons:; Flags: unchecked

[Messages]
DirExists=The directory:%n%n%1%n%nalready exists and appears to have an {#AppName} installation in it.%n%nIt is recommended that you uninstall any existing {#AppName} 3 software before proceeding.  Do you wish to proceed anyway?
WelcomeLabel2=This will install the {#AppName} {#AppVersion} {#VersionInformation} on your computer.%n%nIt is strongly recommended that you uninstall any previous version of the {#AppName} 3 before continuing.%n%nIt is also strongly recommended that you close all other applications you have running before continuing with this installation.%n%nThese steps will help prevent any conflicts during the installation process.

[Run]
Filename: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\python.exe; Description: Install shared apps system wide.; Flags: runhidden; Parameters: runag3.py agpm3.py -s --post-install; WorkingDir: {app}\bin

[UninstallDelete]
Name: {app}; Type: filesandordirs
Name: {app}\bin\*.dat; Type: files
Name: {app}\bin\*.cfg; Type: files
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\AccessGrid3; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\common; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\elementtree; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\feedparser; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\gov; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\twisted; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\zope; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\M2Crypto; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\ZSI; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\_xmlplus; Type: filesandordirs
Name: {reg:HKLM\Software\Python\PythonCore\2.{#PythonSubVersion}\InstallPath,|C:\Python2{#PythonSubVersion}}\Lib\site-packages\bonjour; Type: filesandordirs

[Dirs]
Name: {app}\config\nodeConfig
Name: {app}\Logs
Name: {app}\PackageCache
Name: {app}\SharedApplications
Name: {app}\Services
Name: {app}\NodeServices

