# Copyright 1999-2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
# $Header: /cvs/fl/AccessGrid/packaging/linux/gentoo/portage/globus-client/globus-data-management-client/globus-data-management-client-2.4.3-r1.ebuild,v 1.1 2004-09-14 14:08:22 turam Exp $

DESCRIPTION="Globus Data Grid Clients"

HOMEPAGE="http://www.globus.org/"

SRC_URI="ftp://ftp.globus.org/pub/gt2/2.4/${PV}/bundles/src/${P}-src_bundle.tar.gz"

LICENSE="BSD"

SLOT="2.4"

KEYWORDS="x86"

IUSE=""

DEPEND="virtual/glibc
	>=globus-misc/gpt-3.0.1"

S=${WORKDIR}/${P}

src_unpack() {
	cp ${DISTDIR}/${A} ${WORKDIR}
}

src_compile() {
	/bin/true
}

src_install() {
	unset CFLAGS CXXFLAGS
	if [ -z ${GPT_LOCATION} ]; then
		die "Then environment variable GPT_LOCATION must be set"
	fi
	einfo "GPT_LOCATION :: ${GPT_LOCATION}"
	export GLOBUS_LOCATION=${D}/usr/lib/globus-${SLOT}
	einfo "GLOBUS_LOCATION :: ${GLOBUS_LOCATION}"
	cd ${WORKDIR}
	${GPT_LOCATION}/sbin/gpt-build ${WORKDIR}/${A} gcc32dbg
	${GPT_LOCATION}/sbin/gpt-build ${WORKDIR}/${A} gcc32dbgpthr
	insinto /etc/env.d
	GLOBUS_ENV=${FILESDIR}/99globus-${PV}.env
	newins ${GLOBUS_ENV} 99globus-${PV}
}

pkg_postinst() {
	env-update
	source /etc/profile
	${GPT_LOCATION}/sbin/gpt-postinstall 2>&1 >/dev/null
	${GPT_LOCATION}/sbin/gpt-verify 2>&1 >/dev/null
	einfo ""
	einfo "You should run ${GPT_LOCATION}/sbin/gpt-postinstall to finalize the installation"
	einfo "You should run ${GPT_LOCATION}/sbin/gpt-verify to make sure the installation is sane"
	einfo ""
}
