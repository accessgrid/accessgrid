@echo off
REM
REM We build all the python modules and stick them somewhere safe
REM

set SOURCE=%1
set AGDIR=%2
set DEST=%3
set PYVER=%4

cd %SOURCE%

if %PYVER%=="2.2" (
	
    echo "Building Logging 0.4.7"

    cd logging-0.4.7
    python setup.py clean --all
    python setup.py build
    python setup.py install --prefix=%DEST% --no-compile
    cd %SOURCE% 

    echo "Building Optik 1.4.1"

    cd Optik-1.4.1
    python setup.py clean --all
    python setup.py build
    python setup.py install --prefix=%DEST% --no-compile
    cd %SOURCE% 
)

echo "Building fpconst 0.6.0"

cd fpconst-0.6.0
python setup.py clean --all
python setup.py build
python setup.py install --prefix=%DEST% --no-compile
cd %SOURCE% 

echo "Building SOAPpy"

cd SOAPpy
python setup.py clean
python setup.py build
python setup.py install --prefix=%DEST% --no-compile
cd %SOURCE% 

echo "Building pyOpenSSL_AG"

cd pyOpenSSL
python setup.py clean --all
python setup.py build
python setup.py install --prefix=%DEST%  --no-compile
cd %SOURCE% 

echo "Building pyGLobus"

cd pyGlobus
python setup.py clean --all
set GLOBUS_LOCATION=%SOURCE%\WinGlobus
python setup.py build --flavor=win32
python setup.py install --flavor=win32 --prefix=%DEST%
cd %SOURCE% 

@cd %AGDIR%\packaging\windows
