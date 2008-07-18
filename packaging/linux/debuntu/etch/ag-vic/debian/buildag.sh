#!/bin/sh


echo "BUILDING in here `pwd`"

builddir=${HERE}

## Do patches
##
#cd ${builddir} || exit 1
#cat ${builddir}/debian/patches/patch-ag-media-vic-build | patch -p0
#cat ${builddir}/debian/patches/patch-ag-media-vic-configure.in.x11 | patch -p0
#cat ${builddir}/debian/patches/patch-common-openssl64bit | patch -p0
#cat ${builddir}/debian/patches/patch-vic-openssl64bit | patch -p0

#cat ${builddir}/debian/patches/patch-vic-configure.in.tk | patch -p0
#(cd vic && autoconf -f)
sleep 3

(cd common && ./configure && make)
(cd vic && ./configure --prefix=/usr && make)


echo "End build - CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"

