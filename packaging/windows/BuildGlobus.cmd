@echo off
REM
REM Do the magic needed to compile winglobus the old way
REM the magic is, build debuglib, build debugthreadedlib, then
REM rebuild gss_assist and gss_api nonthreaded again
REM

set SOURCE=%1
set AGDIR=%2
set DEST=%3

set PDIR=%SOURCE%\WinGlobus\WinProjects\SourceSolution

devenv %PDIR%\DebugLib\All_Libs.sln /rebuild Debug
devenv %PDIR%\DebugThreadedLib\All_Libs.sln /build Debug
devenv %PDIR%\DebugLib\All_Libs.sln /project gss_assist /rebuild Debug
devenv %PDIR%\DebugLib\All_Libs.sln /project gssapi /rebuild Debug

