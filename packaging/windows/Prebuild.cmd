rmdir /s /q C:\AccessGridBuild\AG2-Build
rmdir /s /q C:\AccessGrid\build
cd \AccessGridBuild\AccessGrid
python setup.py build
python setup.py install --prefix=C:\AccessGridBuild\AG2-Build --no-compile