@REM
@REM Build Putty
@REM

@set PUTTYDIR=%1
@set DESTDIR=%2

@if not exist %PUTTYDIR%\pscp.exe goto do_compile

:do_copy

@if not exist %DESTDIR%\bin mkdir %DESTDIR%\bin

@copy %PUTTYDIR%\pscp.exe %DESTDIR%\bin\pscp.exe


goto end

:do_compile

@echo Building Putty
@cd %PUTTYDIR%
@nmake -f makefile.vc

goto do_copy

:end
