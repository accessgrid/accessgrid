#!/bin/sh

echo "Start build  - BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"

echo "BUILDING in here `pwd`"

builddir=${HERE}
pythonversion=${PYTHONVERSION}

echo "python version is ${pythonversion}"
sleep 3

cd ${builddir}/AccessGrid/packaging; export AGBUILDROOT=${builddir}; python BuildSnapshot.py --no-checkout --dist=debian --pythonversion=${pythonversion}


echo "End build - CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"

