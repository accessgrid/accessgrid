REM set PATH=%1

REM echo "PATH is ", %PATH%

rmdir /s /q C:\AccessGridBuild\AccessGrid\Release
rmdir /s /q C:\AccessGridBuild\AccessGrid\build
cd \AccessGridBuild\AccessGrid
python setup.py build
python setup.py install --prefix=C:\AccessGridBuild\AccessGrid\Release --no-compile