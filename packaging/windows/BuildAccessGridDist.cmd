@echo off
REM
REM Build Release structure so it's ready for the innosetup installer
REM

set SOURCE=%1
set AGDIR=%2
set DEST=%3

mkdir %DEST%\bin
mkdir %DEST%\services
mkdir %DEST%\sharedapps
mkdir %DEST%\doc
mkdir %DEST%\doc\Developer
mkdir %DEST%\doc\VenueClientManual
mkdir %DEST%\doc\VenueManagementManual
mkdir %DEST%\install
mkdir %DEST%\CAcertificates

cd %AGDIR%

packaging\makeServicePackages.py %AGDIR%\services\node %DEST%\services
packaging\makeAppPackages.py %AGDIR%\sharedapps %DEST%\sharedapps

epydoc.py --html -o doc\Developer -n "Access Grid Toolkit" -u "http://www.mcs.anl.gov/fl/research/accessgrid/"  AccessGrid

echo CVS > foo

xcopy /s /exclude:foo /y %AGDIR%\doc\Developer %DEST%\doc\Developer
xcopy /s /exclude:foo /y %AGDIR%\doc\VENUE_CLIENT_MANUAL_HTML %DEST%\doc\VenueClientManual
xcopy /s /exclude:foo /y %AGDIR%\doc\VENUE_MANAGEMENT_MANUAL_HTML %DEST%\doc\VenueManagementManual
del foo

copy %AGDIR%\COPYING.txt %DEST%\COPYING.txt
copy %AGDIR%\Install.WINDOWS %DEST%\Install.WINDOWS
copy %AGDIR%\packaging\windows\agicons.exe %DEST%\install\agicons.exe
copy %AGDIR%\packaging\config\CAcertificates\*.0 %DEST%\CAcertificates
copy %AGDIR%\packaging\config\CAcertificates\*.signing_policy %DEST%\CAcertificates

copy %AGDIR%\README %DEST%\README

cd %AGDIR%\packaging\windows
