@REM
@REM Build Vic and stick it in the dist directory
@REM

call %VSCOMNTOOLS%\vsvars32.bat

set VICDIR=%1
set DESTDIR=%2

set VIC_EXE=%VICDIR%\vic\DDraw_release\vic.exe

if not exist %VIC_EXE% goto do_compile

:do_copy
copy %VIC_EXE% %DESTDIR%\vic.exe
goto end

:do_compile
echo Building ag-vic
devenv %VICDIR%\vic\vic.2003.sln /rebuild "DDraw Release"
goto do_copy
:end


