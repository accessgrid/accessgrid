REM
REM this batch file builds vfwscan.exe
REM

DEST = "%1"

cl /Tc vfwscan.c vfw32.lib
copy vfwscan.exe %DEST%\bin