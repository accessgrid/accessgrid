[_ISTool]
EnableISX=false

[Setup]
OutputDir=C:\AccessGridBuild
SourceDir=C:\AccessGridBuild\AG2-Build
OutputBaseFilename=ag-windows-2.0alpha
Compression=zip/9
MinVersion=0,5.00.2195
AppCopyright=Copyright © 2003 University of Chicago. All Rights Reserved.
AppName=Access Grid Toolkit
AppVerName=Access Grid Toolkit 2.0alpha
LicenseFile=C:\AccessGridBuild\AG2-Build\doc\COPYING.txt
AdminPrivilegesRequired=true
ChangesAssociations=true
DisableDirPage=false
DefaultGroupName=Access Grid Toolkit
DefaultDirName={pf}\Access Grid Toolkit
UsePreviousAppDir=false
UserInfoPage=false
WindowVisible=false
AppPublisher=Futures Laboratory / ANL
AppPublisherURL=http://www.mcs.anl.gov/fl
AppSupportURL=http://www.mcs.anl.gov/fl/research/accessgrid
AppUpdatesURL=http://www.mcs.anl.gov/fl/research/accessgrid
AppVersion=2.0alpha
AppID=Access Grid Toolkit 2.0alpha


UninstallDisplayIcon={app}\VenueClient.py
UninstallDisplayName=Access Grid Toolkit
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
InfoBeforeFile=C:\AccessGridBuild\AG2-Build\doc\INSTALL

[Components]
Name: Venue_Client; Description: Component that allows you to connect to Access Grid Venues.; Types: custom compact full
Name: Video_Producer; Description: Component that allows you to produce video streams; Types: full
Name: Video_Consumer; Description: Component that allows you to receive video streams; Types: custom full
Name: Audio_Service; Description: Component that allows you to receive and produce audio streams; Types: full
Name: Venue_Server; Description: Component that allows you to start your own venue server; Types: full

[Files]
Source: Lib\site-packages\AccessGrid\*.*; DestDir: {reg:HKLM\Software\Python\PythonCore\2.2\PythonPath\win32com,|C:\Python22\Lib\site-packages}\AccessGrid; Flags: recursesubdirs
Source: share\AccessGrid\services\*.zip; DestDir: {app}\services; Components: Venue_Client
Source: share\AccessGrid\local_services\AudioService.py; DestDir: {app}\local_services; Components: Audio_Service
Source: share\AccessGrid\local_services\AudioService.svc; DestDir: {app}\local_services; Components: Audio_Service
Source: share\AccessGrid\local_services\VideoConsumerService.py; DestDir: {app}\local_services; Components: Video_Consumer
Source: share\AccessGrid\local_services\VideoConsumerService.svc; DestDir: {app}\local_services; Components: Video_Consumer
Source: share\AccessGrid\local_services\VideoProducerService.py; DestDir: {app}\local_services; Components: Video_Producer
Source: share\AccessGrid\local_services\VideoProducerService.svc; DestDir: {app}\local_services; Components: Video_Producer
Source: Scripts\AGNodeService.py; DestDir: {app}; Components: Venue_Client
Source: Scripts\AGServiceManager.py; DestDir: {app}
Source: Scripts\NodeManagement.py; DestDir: {app}; Components: Venue_Client
Source: Scripts\SetupVideo.py; DestDir: {app}; Components: Video_Producer
Source: Scripts\VenueClient.py; DestDir: {app}; Components: Venue_Client
Source: Scripts\VenueManagement.py; DestDir: {app}; Components: Venue_Server
Source: Scripts\VenueServer.py; DestDir: {app}; Components: Venue_Server
Source: Scripts\VenuesServerRegistry.py; DestDir: {app}; Components: Venue_Server
Source: doc\*.*; DestDir: {app}\Documentation
Source: ..\AccessGrid\packaging\windows\Postinstall.py; DestDir: {app}\config; Flags: deleteafterinstall

[Icons]
Name: {group}\Venue Client; Filename: {app}\VenueClient.py; WorkingDir: {app}; IconFilename: {app}\VenueClient.py; Components: Venue_Client
Name: {group}\Unistall the AGTk; Filename: {uninstallexe}
Name: {group}\Node Manager; Filename: {app}\NodeManagement.py; WorkingDir: {app}; IconFilename: {app}\NodeManagement.py; Components: Venue_Client
Name: {group}\Setup Video; Filename: {app}\SetupVideo.py; WorkingDir: {app}; IconFilename: {app}\SetupVideo.py; Components: Video_Producer
Name: {group}\Venue Server; Filename: {app}\VenueServer.py; WorkingDir: {app}; IconFilename: {app}\VenueServer.py; Components: Venue_Server
Name: {group}\Venue Management; Filename: {app}\VenueManagement.py; WorkingDir: {app}; IconFilename: {app}\VenueManagement.py; Components: Venue_Server
Name: {commondesktop}\Access Grid Venue Client; Filename: {app}\VenueClient.py; Tasks: desktopicon; Components: Venue_Client
Name: {userappdata}\Microsoft\Internet Explorer\Quick Launch\Access Grid Venue Client; Filename: {app}\VenueClient.py; Tasks: quicklaunchicon; Components: Venue_Client
Name: {group}\Documentation\README; Filename: {app}\Documentation\README
Name: {group}\Documentation\License; Filename: {app}\COPYING.txt

[Registry]
Root: HKLM; Subkey: SOFTWARE\Access Grid Toolkit\2.0; ValueType: expandsz; ValueName: InstallPath; ValueData: {app}; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\Access Grid Toolkit\2.0; ValueType: expandsz; ValueName: ConfigPath; ValueData: {app}\config; Flags: uninsdeletekey
Root: HKLM; Subkey: SOFTWARE\Access Grid Toolkit\2.0; ValueType: expandsz; ValueName: UserConfigPath; ValueData: %USERPROFILE%\Application Data\AccessGridToolkit\config; Flags: uninsdeletekey

[Types]

[Tasks]
Name: desktopicon; Description: Create &Desktop Icons; GroupDescription: Additional icons:; Components: Audio_Service Video_Consumer Video_Producer Venue_Client
Name: quicklaunchicon; Description: Create a &Quick Launch Icon; GroupDescription: Additional icons:; Flags: unchecked

[Messages]
DirExists=The directory:%n%n%1%n%nalready exists and appears to have an AccessGrid Toolkit installation in it.%n%nIt is recommended that you uninstall any existing AccessGrid Toolkit software before proceeding.  Do you wish to proceed anyway?
WelcomeLabel2=This will install the [name/ver] on your computer.%n%nIt is strongly recommended that you uninstall any previous version of the [name] before continuing.%n%nIt is also strongly recommended that you close all other applications you have running before continuing with this installation.%n%nThese steps will help prevent any conflicts during the installation process.

[Run]
Filename: {app}\config\Postinstall.py; Flags: shellexec
Filename: {app}\SetupVideo.py; WorkingDir: {app}; Description: Setup what video devices will produce video streams; Components: Video_Producer; Flags: postinstall unchecked

[UninstallDelete]
Name: {reg:HKLM\Software\Python\PythonCore\2.2\PythonPath\win32com,|C:\Python22\Lib\site-packages}\AccessGrid; Type: filesandordirs

[Dirs]
Name: {app}\config; Components: Venue_Client

[_ISToolPreCompile]
Name: C:\AccessGridBuild\AccessGrid\packaging\windows\Prebuild.cmd; Parameters: ; Flags: abortonerror
