# Copyright 1999-2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
# $Header: /cvs/fl/AccessGrid/packaging/linux/gentoo/portage/dev-python/soappy/soappy-0.11.4.ebuild,v 1.1 2004-09-14 14:08:22 turam Exp $

inherit distutils

MY_P="SOAPpy-${PV}"

DESCRIPTION="SOAP implementation for Python"
HOMEPAGE="http://pywebsvcs.sourceforge.net/"
SRC_URI="mirror://sourceforge/pywebsvcs/${MY_P}.tar.gz"

KEYWORDS="x86 ~ppc"
SLOT="0"
LICENSE="GPL-2"
IUSE=""

DEPEND="dev-python/fpconst
		dev-python/pyxml"

S=${WORKDIR}/${MY_P}

src_compile() {
	epatch ${FILESDIR}/Server.py.patch
}
