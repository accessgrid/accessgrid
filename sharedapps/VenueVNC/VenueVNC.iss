;
; RCS-ID: $Id: VenueVNC.iss,v 1.1 2004-03-23 20:32:31 eolson Exp $
;

#define SourceDir "\AccessGridBuild\VenueVNC"
#define OutputDir "\AccessGridBuild\Builds"
#define AppName "Access Grid Venue VNC"
#define AppShortName "VenueVNC"
#define AppVersionLong "1.0-3"
#define AppVersionShort "1.0-3"
#define ClientAppShortName "VenueVNCClient"
#define ServerAppShortName "VenueVNCServer"

;
; This doesn't work.
; #define AppConfigDir "{commonappdata}\AccessGrid"
;

[_ISTool]
EnableISX=true
LogFile=\AccessGridBuild\VenueVNC-installer.log
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
DefaultGroupName=Access Grid Toolkit 2\Shared Apps
;DefaultDirName={reg:HKLM\SOFTWARE\Access Grid Toolkit\2.0,ConfigPath|{commonappdata}\AccessGrid}\applications\{#AppShortName}
;CreateAppDir=false
;DefaultDirName={pf}\Access Grid Toolkit Applications\{#AppShortName}
UsePreviousAppDir=false
DefaultDirName={userappdata}\AccessGrid Apps\{#AppShortName}
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
;PrivilegesRequired=none
PrivilegesRequired=admin
UninstallDisplayIcon={app}\ag.ico

[Icons]
Name: {group}\Uninstall VenueVNC; Filename: {uninstallexe}; Comment: Uninstall the VenueVNC client for the Access Grid Toolkit.

[Files]
Source: ag.ico; DestDir: {app}
Source: {#ClientAppShortName}.py; DestDir: {app}; Components: Client; Flags: deleteafterinstall
Source: vncviewer.exe; DestDir: {app}; Components: Client; Flags: deleteafterinstall
Source: vncviewer; DestDir: {app}; Components: Client; Flags: deleteafterinstall
Source: {#ClientAppShortName}.app; DestDir: {app}; Components: Client
;Source: VenueVNCPostinstall.py; DestDir: {app}; Components: Client; Flags: deleteafterinstall
;Source: server\{#ServerAppShortName}.py; DestDir: {app}; Components: Server

[Messages]
WelcomeLabel2=This will install the [name/ver] on your computer.%n%nIt is strongly recommended that you uninstall any previous version of the [name] before continuing.%n%nIt is also strongly recommended that you close all other applications you have running before continuing with this installation.%n%nThese steps will help prevent any conflicts during the installation process.

#define ClientAppShortName "VenueVNCClient"
; #define ClientExecutable "{app}\runvnc.bat"
#define ClientMimeType "application/x-ag-venuevnc"
#define ClientDescription "Shared VNC scoped within a venue"
#define ClientNameType "%s.venuevnc"

[Run]
;Filename: {app}\VenueVNCPostinstall.py; Parameters: """{app}"""; Components: Client; Flags: shellexec runminimized
;Filename: {reg:HKLM\SOFTWARE\Access Grid Toolkit\2.1.2,InstallPath|{pf}\Access Grid Toolkit}\bin\agpm.py; Flags: shellexec runminimized; Parameters: "--file ""{app}\VenueVNCClient.app"""; Components: Client
Filename: {reg:HKLM\SOFTWARE\Access Grid Toolkit\2.1.2,InstallPath|{pf}\Access Grid Toolkit}\bin\agpm.py; WorkingDir: "{app}"; Flags: shellexec runminimized; Parameters: "--file ""{app}\VenueVNCClient.app"""; Components: Client

[UninstallRun]
;Filename: {reg:HKLM\SOFTWARE\Access Grid Toolkit\2.1.2,InstallPath|{pf}\Access Grid Toolkit}\bin\agpm.py; Flags: shellexec runminimized; Parameters: "--system --unregister --name ""application/x-ag-venuevnc"""; Components: Client
Filename: {reg:HKLM\SOFTWARE\Access Grid Toolkit\2.1.2,InstallPath|{pf}\Access Grid Toolkit}\bin\agpm.py; WorkingDir: "{app}"; Flags: shellexec runminimized; Parameters: "--unregister --file ""{app}\VenueVNCClient.app"""; Components: Client

[Components]
Name: Client; Description: The client components needed to connect to a shared desktop; Types: custom compact full; Flags: fixed
;Name: Server; Description: The server components needed to provide a shared desktop (Requires VenueServer); Types: full

[UninstallDelete]
; Name: {app}\runvnc.bat; Type: files; Components: Client
Type: dirifempty; Name: "{app}"; Components: Client

