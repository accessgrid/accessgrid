rmdir /s /q C:\AccessGridBuild\AccessGrid-Build
rmdir /s /q C:\AccessGrid\build
cd \AccessGridBuild\AccessGrid
python setup.py build
python setup.py install --prefix=C:\AccessGridBuild\AccessGrid-Build --no-compile