@REM
@REM We build all the python modules and stick them somewhere safe
@REM

call %VSCOMNTOOLS%\vsvars32.bat

@set SOURCE=%1
@set DEST=%2

@cd %SOURCE%

@cd logging-0.4.7
@python setup.py build
@python setup.py install --prefix=%DEST% --no-compile

@cd ..\pyDNS-2.3.0
@python setup.py clean --all
@python setup.py build
@python setup.py install --prefix=%DEST%  --no-compile

@cd ..\pyOpenSSL
@python setup.py clean --all
@python setup.py build
@python setup.py install --prefix=%DEST%  --no-compile

@cd ..\AccessGrid
@python setup.py clean --all
@python setup.py build
@python setup.py install --prefix=%DEST%  --no-compile

@cd ..\pyGlobus
@python setup.py clean --all
@set GLOBUS_LOCATION=%SOURCE%\WinGlobus
@python setup.py build --flavor=win32
@python setup.py install --flavor=win32 --prefix=%DEST%
