# Copyright 1999-2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
# $Header: /cvs/fl/AccessGrid/packaging/linux/gentoo/portage/globus-misc/gpt/gpt-3.0.1.ebuild,v 1.1 2004-09-14 14:08:22 turam Exp $

DESCRIPTION="Grid Packaging Toolkit"

HOMEPAGE="http://www.gridpackagingtools.org"

SRC_URI="ftp://ftp.ncsa.uiuc.edu/aces/gpt/releases/${P}/${P}-src.tar.gz"

LICENSE="BSD"

SLOT="3.0"

KEYWORDS="x86"

IUSE=""

DEPEND="perl"

S=${WORKDIR}/${P}

src_compile() {
	/bin/true
}

src_install() {
	export GPT_LOCATION=${D}/usr/lib/${PN}-${SLOT}
	./build_gpt
	insinto /etc/env.d
	newins ${FILESDIR}/98gpt-${PV}.env 98gpt-${PV}
}
