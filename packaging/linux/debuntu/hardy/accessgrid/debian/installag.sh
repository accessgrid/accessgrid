#!/bin/sh


prefix=${PREFIX:-/usr}
name=${NAME:-accessgrid}
version=${VERSION:-3.2}
pythonversion=${PYTHONVERSION}
pkgdir=${PKGDIR:-${HERE}/debian/accessgrid3.2}
#AGTKDATABASE=/usr/share
AGTKDATABASE=/etc
SYSTEMCONFIGBASE=/etc

echo " INSTALLING in ${HERE} (= `pwd` ?)"
echo " PKGDIR = ${pkgdir}"
echo " PREFIX = ${prefix}"
builddir=${HERE}

echo "python version is ${pythonversion}"
sleep 3

#if [ ! -d ${builddir}/dist ]; then mv ${builddir}/dist-* ${builddir}/dist; fi;
cd ${builddir}/dist-${pythonversion} || exit 1


mkdir -p ${pkgdir}/${prefix}/bin
install -m 0755 ${HERE}/debian/patches/agkill ${pkgdir}/${prefix}/bin
install -m 0755 bin/* ${pkgdir}/${prefix}/bin

install -d ${pkgdir}/${prefix}/share/python-support/AccessGrid
cp -R lib/python${pythonversion}/site-packages/* ${pkgdir}/${prefix}/share/python-support/AccessGrid/

rm -rf share/applnk share/gnome
install -d ${pkgdir}/${prefix}/share
mkdir -p ${pkgdir}/${prefix}/share/doc/${name}${version}
cp -R share/doc/AccessGrid/* ${pkgdir}/${prefix}/share/doc/${name}${version}/
cp ${builddir}/AccessGrid/README ${pkgdir}/${prefix}/share/doc/${name}${version}/
cp -R share/* ${pkgdir}/${prefix}/share/
rm -rf ${pkgdir}/${prefix}/share/doc/AccessGrid
mkdir -p ${pkgdir}/${prefix}/share/${name}${version}
cp -R share/AccessGrid/* ${pkgdir}/${prefix}/share/${name}${version}/
rm -rf ${pkgdir}/${prefix}/share/AccessGrid
cp -R ${builddir}/AccessGrid/packaging/linux/ag-ellipse.png \
        ${pkgdir}/${prefix}/share/${name}${version}/

install -d ${pkgdir}/${SYSTEMCONFIGBASE}
cp -R etc/AccessGrid3 ${pkgdir}/${SYSTEMCONFIGBASE}/
install -d ${pkgdir}/${AGTKDATABASE}/AccessGrid3
install -d ${pkgdir}/${AGTKDATABASE}/AccessGrid3/SharedApplications
install -d ${pkgdir}/${AGTKDATABASE}/AccessGrid3/Services
install -d ${pkgdir}/${AGTKDATABASE}/AccessGrid3/NodeServices
install -d ${pkgdir}/${AGTKDATABASE}/AccessGrid3/Plugins
cp -R SharedApplications ${pkgdir}/${AGTKDATABASE}/AccessGrid3/
cp -R Services ${pkgdir}/${AGTKDATABASE}/AccessGrid3/
cp -R NodeServices ${pkgdir}/${AGTKDATABASE}/AccessGrid3/
cp -R Plugins ${pkgdir}/${AGTKDATABASE}/AccessGrid3/

# Gnome desktop menus
#
mkdir -p ${pkgdir}/${SYSTEMCONFIGBASE}/xdg/menus/applications-merged
cp ${builddir}/AccessGrid/packaging/linux/xdg/AccessGrid3.menu \
        ${pkgdir}/${SYSTEMCONFIGBASE}/xdg/menus/applications-merged/

# KDE menus
#
mkdir -p ${pkgdir}/${SYSTEMCONFIGBASE}/xdg/menus/kde-applications-merged
cp ${builddir}/AccessGrid/packaging/linux/xdg/AccessGrid3.menu \
        ${pkgdir}/${SYSTEMCONFIGBASE}/xdg/menus/kde-applications-merged/

mkdir -p ${pkgdir}/${prefix}/share/desktop-directories
cp ${builddir}/AccessGrid/packaging/linux/xdg/*3*.directory \
        ${pkgdir}/${prefix}/share/desktop-directories/
for f in ${pkgdir}/${prefix}/share/desktop-directories/*3* ; do
  sed -i "/Icon/s/AccessGrid/${name}${version}/g" $f
done
mkdir -p ${pkgdir}/${prefix}/share/applications
cp ${builddir}/AccessGrid/packaging/linux/xdg/*3*.desktop \
        ${pkgdir}/${prefix}/share/applications/
for f in ${pkgdir}/${prefix}/share/applications/*3* ; do
  sed -i "/Icon/s/AccessGrid/${name}${version}/g" $f
done

#mkdir -p ${pkgdir}/${AGTKDATABASE}/AccessGrid3/PackageCache


