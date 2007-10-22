# New AG port makefile for:	ag-rat
# Date created:			18 October 2007
# Whom:				Chrisw Willing
#
# $FreeBSD$
#

PORTNAME=	ag-rat
PORTVERSION=	4.4.00
CATEGORIES=
SVN_REVID=	r4086
PKGNAMESUFFIX=	-${SVN_REVID}

MASTER_SITES=	http://www.vislab.uq.edu.au/ag3/distfiles/
USE_TGZ=	yes
DISTNAME=	mmedia-${SVN_REVID}
WRKSRC=		${WRKDIR}/rat/rat
PATCH_DIST_STRIP=	-p0

LIB_DEPENDS=	tk84:${PORTSDIR}/${TK84_PORT}
USE_AUTOTOOLS=	autoconf:253
TCLTK_VERSION=	8.4
CONFIGURE_ARGS=	-with-tcl=${LOCALBASE} \
		-with-tk=${LOCALBASE}	\
		--with-tcltk-version=${TCLTK_VERSION}
RAT=		rat-${PORTVERSION}
RAT_SCRIPT=	rat


MAINTAINER=	c.willing@uq.edu.au
COMMENT=	Sumover version of rat

MAN1=		rat.1

post-extract:
	@(mv ${WRKDIR}/${DISTNAME} ${WRKDIR}/rat || true)

pre-build:
	@( \
		cd ${WRKSRC}/../common && ./configure && make -f ./Makefile ;    \
	)
do-install:
	${INSTALL_PROGRAM} ${WRKSRC}/${RAT} ${PREFIX}/bin/${RAT}
	${INSTALL_PROGRAM} ${WRKSRC}/${RAT}-ui ${PREFIX}/bin/${RAT}-ui
	${INSTALL_PROGRAM} ${WRKSRC}/${RAT}-media ${PREFIX}/bin/${RAT}-media
	${INSTALL_PROGRAM} ${WRKSRC}/${RAT}-media ${PREFIX}/bin/${RAT}-kill
	${INSTALL_SCRIPT} ${WRKSRC}/${RAT_SCRIPT} ${PREFIX}/bin/${RAT_SCRIPT}
	${INSTALL_MAN}  ${WRKSRC}/man/man1/rat.1 ${PREFIX}/man/man1



.include <bsd.port.mk>

