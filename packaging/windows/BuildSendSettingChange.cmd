@REM
@REM Rather than have a huge hairy mess, we use the standard default, those who install it somewhere else, suffer the consequences.
@REM


@set VSINSTALLDIR=
@reg.exe query HKLM\SOFTWARE\Microsoft\VisualStudio\7.0\Setup\VS /v EnvironmentDirectory > msid.txt
@for /F "skip=1 tokens=3*" %%i IN (msid.txt) DO set VSINSTALLDIR=%%i %%j
@if exist msid.txt del msid.txt
@set VCINSTALLDIR=
@reg.exe query HKLM\SOFTWARE\Microsoft\VisualStudio\7.0\Setup\VS /v ProductDir > msid.txt
@for /F "skip=1 tokens=3*" %%i IN (msid.txt) DO set VCINSTALLDIR=%%i %%j
@if exist msid.txt del msid.txt

@rem
@rem Root of Visual Studio ide installed files.
@rem
@set DevEnvDir=%VSINSTALLDIR%

@rem
@rem Root of Visual C++ installed files.
@rem
@set MSVCDir=%VCINSTALLDIR%\VC7

@rem
@echo Setting environment for using Microsoft Visual Studio .NET tools.
@echo (If you also have Visual C++ 6.0 installed and wish to use its tools
@echo from the command line, run vcvars32.bat for Visual C++ 6.0.)
@rem

@REM %VCINSTALLDIR%\Common7\Tools dir is added only for real setup.

@set PATH=%DevEnvDir%;%MSVCDir%\BIN;%VCINSTALLDIR%\Common7\Tools;%VCINSTALLDIR%\Common7\Tools\bin\prerelease;%VCINSTALLDIR%\Common7\Tools\bin;%FrameworkSDKDir%\bin;%FrameworkDir%\%FrameworkVersion%;%PATH%;
@set INCLUDE=%MSVCDir%\ATLMFC\INCLUDE;%MSVCDir%\INCLUDE;%MSVCDir%\PlatformSDK\include\prerelease;%MSVCDir%\PlatformSDK\include;%FrameworkSDKDir%\include;%INCLUDE%
@set LIB=%MSVCDir%\ATLMFC\LIB;%MSVCDir%\LIB;%MSVCDir%\PlatformSDK\lib\prerelease;%MSVCDir%\PlatformSDK\lib;%FrameworkSDKDir%\lib;%LIB%


@set SOURCE=%1
@set DEST=%2

@if not exist %DEST%\bin mkdir %DEST%\bin

@echo Building Preliminary Software
@devenv %SOURCE%\WinGlobus\globus_setup\send_settingchange\send_settingchange.sln /build Release
@copy %SOURCE%\WinGlobus\globus_setup\send_settingchange\send_settingchange\Release\send_settingchange.exe %DEST%\bin
