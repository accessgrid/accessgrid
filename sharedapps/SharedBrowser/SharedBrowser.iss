;
; RCS-ID: $Id: SharedBrowser.iss,v 1.4 2003-05-30 08:38:01 judson Exp $
;

#define SourceDir "C:\Software\AccessGrid\AccessGrid\sharedapps\SharedBrowser"
#define OutputDir "C:\xfer"
#define AppName "AG Shared Browser"
#define AppVersionLong "1.0-1"
#define AppVersionShort "1.0-1"
#define AppShortName "SharedBrowser"

;
; This doesn't work.
; #define AppConfigDir "{commonappdata}\AccessGrid"
;

[_ISTool]
EnableISX=true

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

DefaultDirName={reg:HKLM\SOFTWARE\Access Grid Toolkit\2.0,ConfigPath|{commonappdata}\AccessGrid}\applications\{#AppShortName}
UsePreviousAppDir=false
UserInfoPage=false
WindowVisible=false

UninstallDisplayName={#AppName}
DisableStartupPrompt=false
WindowResizable=false
AlwaysShowComponentsList=false
ShowComponentSizes=false
FlatComponentsList=false
AllowNoIcons=true
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
UsePreviousGroup=false
DefaultGroupName=AGTk 2.0

[Files]
; The Python Module: AccessGrid
Source: {#AppShortName}.py; DestDir: {app}
Source: {#AppShortName}.app; DestDir: {app}
Source: ag.ico; DestDir: {app}

[Messages]
WelcomeLabel2=This will install the [name/ver] on your computer.%n%nIt is strongly recommended that you uninstall any previous version of the [name] before continuing.%n%nIt is also strongly recommended that you close all other applications you have running before continuing with this installation.%n%nThese steps will help prevent any conflicts during the installation process.

[Run]
Filename: {reg:HKLM\SOFTWARE\Access Grid Toolkit\2.0,InstallPath|{pf}\Access Grid Tookit}\MailcapSetup.py; Flags: shellexec runminimized; Parameters: "--system --mime-type ""application/x-ag-shared-browser"" --executable ""{app}\SharedBrowser.py"" --description ""This is the shared browser"" --nametemplate ""sharedbrowser"""
Filename: {reg:HKLM\SOFTWARE\Access Grid Toolkit\2.0,InstallPath|{pf}\Access Grid Tookit}\MailcapSetup.py; Flags: shellexec runminimized; Parameters: "--mime-type ""application/x-ag-shared-browser"" --executable ""{app}\SharedBrowser.py"" --description ""This is the shared browser"" --nametemplate ""sharedbrowser"""

[UninstallRun]
Filename: {reg:HKLM\SOFTWARE\Access Grid Toolkit\2.0,InstallPath|{pf}\Access Grid Tookit}\MailcapSetup.py; Flags: shellexec runminimized; Parameters: "--system --uninstall --mime-type ""application/x-ag-shared-browser"""
Filename: {reg:HKLM\SOFTWARE\Access Grid Toolkit\2.0,InstallPath|{pf}\Access Grid Tookit}\MailcapSetup.py; Flags: shellexec runminimized; Parameters: "--uninstall --mime-type ""application/x-ag-shared-browser"""

