;
; RCS-ID: $Id: SharedBrowser.iss,v 1.2 2003-05-28 18:01:57 leggett Exp $
;

#define SourceDir "C:\AccessGridBuild\AccessGrid\sharedapps\SharedBrowser"
#define OutputDir "C:\AccessGridBuild\Builds"
#define AppName "Access Grid Shared Browser"
#define AppVersionLong "1.0-1"
#define AppVersionShort "1.0-1"
#define AppShortName "SharedBrowser"
#define MimeType "application/x-ag-shared-browser"
#define Description "This is the shared browser application"
#define NameType "%s.sharedbrowser"

;
; This doesn't work.
; #define AppConfigDir "{commonappdata}\AccessGrid"
;

[_ISTool]
EnableISX=true
LogFile=C:\AccessGridBuild\Builds\{#AppShortName}-installer.log
LogFileAppend=false

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
AppVerName={#AppName} {#AppVersionLong}
; Version information
AppVersion={#AppVersionShort}
; What to build the installer from
SourceDir={#SourceDir}
; Where to put the built installer
OutputDir={#OutputDir}
; Name with version information
OutputBaseFilename={#AppShortName}-{#AppVersionShort}

AppName={#AppName}
AppCopyright=Copyright © 2003 University of Chicago. All Rights Reserved.
AppPublisher=Futures Laboratory / Argonne National Laboratory
AppPublisherURL=http://www.mcs.anl.gov/fl
AppSupportURL=http://bugzilla.mcs.anl.gov/accessgrid
AppUpdatesURL=http://www.mcs.anl.gov/fl/research/accessgrid
AppID={#AppName}
Compression=zip/9
MinVersion=0,5.00.2195

DisableDirPage=false
DefaultGroupName=Access Grid Toolkit
DefaultDirName={reg:HKLM\SOFTWARE\Access Grid Toolkit\2.0,InstallPath}\applications\{#AppShortName}
UsePreviousAppDir=false
UserInfoPage=false
WindowVisible=false

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

ShowTasksTreeLines=true
PrivilegesRequired=admin
UninstallDisplayIcon={app}\ag.ico

[Files]
; The Python Module: AccessGrid
Source: {#AppShortName}.py; DestDir: {app}
Source: {#AppShortName}.app; DestDir: {app}
Source: ag.ico; DestDir: {app}

[Messages]
WelcomeLabel2=This will install the [name/ver] on your computer.%n%nIt is strongly recommended that you uninstall any previous version of the [name] before continuing.%n%nIt is also strongly recommended that you close all other applications you have running before continuing with this installation.%n%nThese steps will help prevent any conflicts during the installation process.

[Run]
Filename: {reg:HKLM\SOFTWARE\Access Grid Toolkit\2.0,InstallPath|{pf}\Access Grid Tookit}\MailcapSetup.py; Flags: shellexec runminimized; Parameters: "--system --mime-type ""{#MimeType}"" --executable ""{app}\{#AppShortName}.py %s"" --description ""{#Description}"" --nametemplate ""{#NameType}"""

[UninstallRun]
Filename: {reg:HKLM\SOFTWARE\Access Grid Toolkit\2.0,InstallPath|{pf}\Access Grid Tookit}\MailcapSetup.py; Parameters: "--system --uninstall --mime-type ""{#MimeType}"""; Flags: shellexec runminimized
