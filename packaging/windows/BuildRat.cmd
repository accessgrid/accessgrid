@echo off
REM
REM Build rat programs and stick them in the dist directory
REM

set SOURCE=%1
set AGDIR=%2
set DEST=%3

set RATDIR=%SOURCE%\ag-media
set DESTDIR=%DEST%\bin

if not exist %RATDIR%\rat\Release\rat.exe goto do_compile_rat
if not exist %RATDIR%\rat\Release\ratmedia.exe goto do_compile_rat
if not exist %RATDIR%\rat\Release\ratui.exe goto do_compile_rat
if not exist %RATDIR%\rat\Release\rat-kill.exe goto do_compile_rat_kill

:do_copy

copy %RATDIR%\rat\Release\rat-kill.exe %DESTDIR%\rat-kill.exe
copy %RATDIR%\rat\Release\rat.exe %DESTDIR%\rat.exe
copy %RATDIR%\rat\Release\ratmedia.exe %DESTDIR%\ratmedia.exe
copy %RATDIR%\rat\Release\ratui.exe %DESTDIR%\ratui.exe

goto end

:do_compile_rat

echo Building ag-rat
devenv %RATDIR%\rat\rat.2003.sln /rebuild Release

goto do_copy

:do_compile_rat_kill
echo Building Rat Kill
devenv %RATDIR%\rat\rat.sln /rebuild Release /project rat-kill

goto do_copy

:end
cd %AGDIR%\packaging\windows
