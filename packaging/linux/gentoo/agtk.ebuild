# Copyright 1999-2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
# $Header: /cvs/fl/AccessGrid/packaging/linux/gentoo/agtk.ebuild,v 1.1 2004-08-18 20:03:14 turam Exp $

inherit eutils distutils

DESCRIPTION="The Access Grid Toolkit"

HOMEPAGE="http://www.mcs.anl.gov/fl/research/accessgrid/"

SRC_URI="http://www.mcs.anl.gov/fl/research/accessgrid/software/releases/${PV}/source/${P}.tar.bz2"

LICENSE="AGTPL"

SLOT="0"

KEYWORDS="~x86"

IUSE=""

DEPEND=">=python-2.3
	>=globus-client/globus-data-management-client-2.4.3
	>=pyglobus-0.9.7
	>=soappy-0.11.4
	>=pyOpenSSL_AG-0.5.1
	>=wxGTK-2.4.2
	>=wxpython-2.4.2.4
        >=xawtv-3.86
        >=ag-media/rat-4.2.22
        >=ag-media/vic-1.1.13"

src_compile() {
	epatch ${FILESDIR}/Config.py-2.3-beta1.patch
	distutils_src_compile
        echo "--- Building QuickBridge" ${WORKDIR}/${P}/services/network/QuickBridge
        pushd ${WORKDIR}/${P}/services/network/QuickBridge
        echo " - list files"
        ls
        gcc -O -o QuickBridge QuickBridge.c
        popd
}

src_install() {
        
	${python} setup.py install --root=${D} --no-compile
	rm -rf ${D}/usr/bin ${D}/usr/etc/init.d ${D}/usr/share/AccessGrid ${D}/usr/share/applnk ${D}/usr/share/gnome
	mv ${D}/usr/etc ${D}/etc
	dodoc COPYING.txt ChangeLog README README-developers TODO
	mv ${D}/usr/share/doc/AccessGrid/Documentation ${D}/usr/share/doc/${PF}/.
	rm -rf ${D}/usr/share/doc/AccessGrid
	install -d ${D}/etc/AccessGrid/Services
	install -d ${D}/etc/AccessGrid/Logs
        echo "--- Building node service packages"
        mkdir ${D}/etc/AccessGrid/NodeServices
        pushd ${WORKDIR}/${P}/services/node
        echo " - list files"
        ls
        echo "  - VideoService"
        cp /usr/bin/vic .
        zip ${D}/etc/AccessGrid/NodeServices/VideoService.zip VideoService.{py,svc} vic
        unzip -l ${D}/etc/AccessGrid/NodeServices/VideoService.zip
        echo "  - VideoProducerService"
        zip ${D}/etc/AccessGrid/NodeServices/VideoProducerService.zip VideoProducerService.{py,svc} vic
        unzip -l ${D}/etc/AccessGrid/NodeServices/VideoProducerService.zip
        echo "  - VideoConsumerService"
        zip ${D}/etc/AccessGrid/NodeServices/VideoConsumerService.zip VideoConsumerService.{py,svc} vic
        unzip -l ${D}/etc/AccessGrid/NodeServices/VideoConsumerService.zip
        echo "  - AudioService"
        cp /usr/bin/rat* .
        mv rat-4.2.22-kill rat-kill
        zip ${D}/etc/AccessGrid/NodeServices/AudioService.zip AudioService.{py,svc} rat rat-4.2.22 rat-4.2.22-media rat-4.2.22-ui rat-kill
        unzip -l ${D}/etc/AccessGrid/NodeServices/AudioService.zip
        popd
        echo "--- Copying shared application packages"
	cp -a ${FILESDIR}/SharedApplications ${D}/etc/AccessGrid
        echo "--- Copying QuickBridge"
        ls ${WORKDIR}/${P}/services/network/QuickBridge/QuickBridge
        mkdir ${D}/usr/bin
        cp -a -v ${WORKDIR}/${P}/services/network/QuickBridge/QuickBridge ${D}/usr/bin
        echo "--- Configuring executable scripts"
	dobin   bin/AGNodeService.py            \
            bin/AGServiceManager.py             \
            bin/BridgeServer.py                 \
            bin/CertificateManager.py           \
            bin/CertificateRequestTool.py       \
            tools/GoToVenue.py                  \
            bin/NodeManagement.py               \
            bin/NodeSetupWizard.py              \
            bin/VenueClient.py                  \
            bin/VenueManagement.py              \
            bin/VenueServer.py                  \
            bin/agpm.py                         \
            bin/certmgr.py                      
}
