@echo off
REM
REM Build Vic and stick it in the dist directory
REM

set SOURCE=%1
set AGDIR=%2
set DEST=%3

set VICDIR=%SOURCE%\ag-media

set VIC_EXE=%VICDIR%\vic\DDraw_release\vic.exe

if not exist %VIC_EXE% goto do_compile

:do_copy
copy %VIC_EXE% %DEST%\bin\vic.exe
goto end

:do_compile
echo Building ag-vic
devenv %VICDIR%\vic\vic.2003.sln /rebuild "DDraw Release"
goto do_copy

:end
cd %AGDIR%\packaging\windows


