# Copyright 1999-2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
# $Header: /cvs/fl/AccessGrid/packaging/linux/gentoo/portage/dev-python/pyglobus/pyglobus-0.9.7-r1.ebuild,v 1.1 2004-09-14 14:08:22 turam Exp $

inherit distutils

MY_P="pyGlobus-${PV}"

DESCRIPTION="Globus interface for Python"

HOMEPAGE="http://www-itg.lbl.gov/gtg/pyGlobus/"

SRC_URI="http://www.mcs.anl.gov/fl/research/accessgrid/software/required/source/${MY_P}.tar.gz"

KEYWORDS="x86"

SLOT="0"

LICENSE=""

IUSE="debug"

#DEPEND=">=globus-sdk/globus-data-management-sdk-2.4.3"

DEPEND=">=globus-client/globus-data-management-client-2.4.3
        >=dev-lang/swig-1.3.21"


RDEPEND=">=globus-client/globus-data-management-client-2.4.3"

S=${WORKDIR}/${MY_P}

FLAVOR="gcc32dbg"
use debug && FLAVOR="${FLAVOR}dbg" && export RESTRICT="nostrip"
FLAVOR="${FLAVOR}pthr"

src_compile() {
	unset CFLAGS CXXFLAGS
	distutils_src_compile --run-swig --flavor=${FLAVOR}
}

src_install() {
	distutils_src_install --flavor=${FLAVOR}
}
