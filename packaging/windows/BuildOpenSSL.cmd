@REM
@REM Figure out where VisualStudio .NET is installed and setup some variables so we can
@REM build our VS.NET solutions
@REM

@set VSINSTALLDIR=
@reg.exe query HKLM\SOFTWARE\Microsoft\VisualStudio\7.0\Setup\VS /v EnvironmentDirectory > msid.txt
@for /F "skip=1 tokens=3*" %%i IN (msid.txt) DO set VSINSTALLDIR=%%i %%j
@if exist msid.txt del msid.txt
@set VCINSTALLDIR=
@reg.exe query HKLM\SOFTWARE\Microsoft\VisualStudio\7.0\Setup\VS /v ProductDir > msid.txt
@for /F "skip=1 tokens=3*" %%i IN (msid.txt) DO set VCINSTALLDIR=%%i %%j
@if exist msid.txt del msid.txt

@rem
@rem Root of Visual Studio ide installed files.
@rem
@set DevEnvDir=%VSINSTALLDIR%

@rem
@rem Root of Visual C++ installed files.
@rem
@set MSVCDir=%VCINSTALLDIR%\VC7

@rem
@echo Setting environment for using Microsoft Visual Studio .NET tools.
@echo (If you also have Visual C++ 6.0 installed and wish to use its tools
@echo from the command line, run vcvars32.bat for Visual C++ 6.0.)
@rem

@REM %VCINSTALLDIR%\Common7\Tools dir is added only for real setup.

@set PATH=%DevEnvDir%;%MSVCDir%\BIN;%VCINSTALLDIR%\Common7\Tools;%VCINSTALLDIR%\Common7\Tools\bin\prerelease;%VCINSTALLDIR%\Common7\Tools\bin;%FrameworkSDKDir%\bin;%FrameworkDir%\%FrameworkVersion%;%PATH%;
@set INCLUDE=%MSVCDir%\ATLMFC\INCLUDE;%MSVCDir%\INCLUDE;%MSVCDir%\PlatformSDK\include\prerelease;%MSVCDir%\PlatformSDK\include;%FrameworkSDKDir%\include;%INCLUDE%
@set LIB=%MSVCDir%\ATLMFC\LIB;%MSVCDir%\LIB;%MSVCDir%\PlatformSDK\lib\prerelease;%MSVCDir%\PlatformSDK\lib;%FrameworkSDKDir%\lib;%LIB%

@set OPENSSLDIR=%1
@set DESTDIR=%2

@if not exist %OPENSSLDIR%\out32dll\openssl.exe goto do_compile

:do_copy

@copy %OPENSSLDIR%\out32dll\openssl.exe %DESTDIR%\bin\openssl.exe
@copy %OPENSSLDIR%\out32dll\*.lib %DESTDIR%\lib\.
@copy %OPENSSLDIR%\out32dll\*.dll %DESTDIR%\lib\.
@mkdir %DESTDIR%\include\openssl
@copy %OPENSSLDIR%\inc32\openssl\*.* %DESTDIR%\include\openssl\.


goto end

:do_compile

@echo Building OpenSSL
@cd %OPENSSLDIR%
@perl Configure VC-WIN32
@cd crypto\bn\asm
@perl x86.pl win32 > bn_win32.asm
@cd ..\..\..
@cd crypto\des\asm
@perl des-586.pl win32 > d_win32.asm
@cd ..\..\..
@cd crypto\des\asm
@perl crypt586.pl win32 > y_win32.asm
@cd ..\..\..
@cd crypto\bf\asm
@perl bf-586.pl win32 > b_win32.asm
@cd ..\..\..
@cd crypto\cast\asm
@perl cast-586.pl win32 > c_win32.asm
@cd ..\..\..
@cd crypto\rc4\asm
@perl rc4-586.pl win32 > r4_win32.asm
@cd ..\..\..
@cd crypto\md5\asm
@perl md5-586.pl win32 > m5_win32.asm
@cd ..\..\..
@cd crypto\sha\asm
@perl sha1-586.pl win32 > s1_win32.asm
@cd ..\..\..
@cd crypto\ripemd\asm
@perl rmd-586.pl win32 > rm_win32.asm
@cd ..\..\..
@cd crypto\rc5\asm
@perl rc5-586.pl win32 > r5_win32.asm
@cd ..\..\..
@perl util\mkfiles.pl >MINFO
@perl util\mk1mf.pl dll VC-W31-32 >ms\w31dll.mak
@perl util\mk1mf.pl VC-WIN32 >ms\nt.mak
@perl util\mk1mf.pl dll VC-WIN32 >ms\ntdll.mak
@perl util\mkdef.pl 16 libeay > ms\libeay16.def
@perl util\mkdef.pl 32 libeay > ms\libeay32.def
@perl util\mkdef.pl 16 ssleay > ms\ssleay16.def
@perl util\mkdef.pl 32 ssleay > ms\ssleay32.def
@nmake -f ms\ntdll.mak
@nmake -f ms\nt.mak

goto do_copy

:end
