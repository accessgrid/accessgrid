@REM
@REM Build AccessGrid stuff and stick it in the dist directory
@REM

call %VSCOMNTOOLS%\vsvars32.bat

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
