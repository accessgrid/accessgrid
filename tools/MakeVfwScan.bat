REM
REM this batch file builds vfwscan.exe
REM

cl /Tc vfwscan.c vfw32.lib
copy vfwscan.exe %1\bin