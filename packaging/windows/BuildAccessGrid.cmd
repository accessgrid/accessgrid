@REM
@REM Figure out where VisualStudio .NET is installed and setup some variables so we can
@REM build our VS.NET solutions
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

@set AGDIR=%1
@set DESTDIR=%AGDIR%\Release

@rmdir /s /q %AGDIR%\Release
@rmdir /s /q %AGDIR%\build
@cd %AGDIR%

@mkdir %DESTDIR%\doc
@mkdir %DESTDIR%\doc\Developer
@mkdir %DESTDIR%\doc\VenueClientManual
@mkdir %DESTDIR%\doc\VenueManagementManual
@xcopy %AGDIR%\doc\AccessGrid %DESTDIR%\doc\Developer
@echo CVS > foo
@xcopy /s /exclude:foo /y %AGDIR%\doc\VENUE_CLIENT_MANUAL_HTML %DESTDIR%\doc\VenueClientManual
@xcopy /s /exclude:foo /y %AGDIR%\doc\VENUE_MANAGEMENT_MANUAL_HTML %DESTDIR%\doc\VenueManagementManual
@del foo
@copy %AGDIR%\COPYING.txt %DESTDIR%\COPYING.txt
@copy %AGDIR%\README %DESTDIR%\README

@echo Building AG
@python setup.py build
@python setup.py install --prefix=%DESTDIR% --no-compile
