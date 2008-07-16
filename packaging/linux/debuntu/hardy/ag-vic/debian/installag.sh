#!/bin/sh


prefix=${PREFIX:-/usr}
name=${NAME:-ag-vic}
pkgdir=${PKGDIR:-${HERE}/debian/tmp}

echo " INSTALLING in ${HERE} (= `pwd` ?)"
echo " PKGDIR = ${pkgdir}"
echo " PREFIX = ${prefix}"
builddir=${HERE}

