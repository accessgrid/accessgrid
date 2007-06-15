REM
REM this batch file builds wdmscan.exe
REM

cl /TP wdmscan.cpp /link strmiids.lib ole32.lib oleaut32.lib
copy wdmscan.exe %1\bin