@REM
@REM Build send_settingchange and stick it in the dist directory
@REM

call %VSCOMNTOOLS%\vsvars32.bat

@set SOURCE=%1
@set DEST=%2

@if not exist %DEST%\bin mkdir %DEST%\bin

@echo Building Preliminary Software
@devenv %SOURCE%\WinGlobus\globus_setup\send_settingchange\send_settingchange.sln /build Release
@copy %SOURCE%\WinGlobus\globus_setup\send_settingchange\send_settingchange\Release\send_settingchange.exe %DEST%\bin
