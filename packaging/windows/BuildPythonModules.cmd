@REM
@REM We build all the python modules and stick them somewhere safe
@REM

@set SOURCE=%1
@set DEST=%2

@cd %SOURCE%
@python setup.py clean --all
@cd logging-0.4.7
@python setup.py build
@python setup.py install --prefix=%DEST%

@cd ..\pyDNS-2.3.0
@python setup.py clean --all
@python setup.py build
@python setup.py install --prefix=%DEST%

@cd ..\pyOpenSSL
@python setup.py clean --all
@python setup.py build
@python setup.py install --prefix=%DEST%

@cd ..\AccessGrid
@python setup.py clean --all
@python setup.py build
@python setup.py install --prefix=%DEST%

@cd ..\pyGlobus
@python setup.py clean --all
@set GLOBUS_LOCATION=%SOURCE%\WinGlobus
@python setup.py build --flavor=win32
@python setup.py install --flavor=win32 --prefix=%DEST%
