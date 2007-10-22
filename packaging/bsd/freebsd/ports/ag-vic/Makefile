# New AG port makefile for:	ag-vic
# Date created:			17 October 2007
# Whom:				Chrisw Willing
#
# $FreeBSD$
#

PORTNAME=	ag-vic2.8ucl
PORTVERSION=	1.3.0r4086
CATEGORIES=

MASTER_SITES=	http://www.vislab.uq.edu.au/ag3/distfiles/
USE_TGZ=	yes
DISTNAME=	mmedia-r4086
WRKSRC=		${WRKDIR}/vic/vic
PATCH_DIST_STRIP=	-p0

LIB_DEPENDS=	tk84:${PORTSDIR}/${TK84_PORT}
USE_AUTOTOOLS=	autoconf:253
CONFIGURE_ARGS=	-with-tcl=${LOCALBASE} \
		-with-tk=${LOCALBASE}

MAINTAINER=	c.willing@uq.edu.au
COMMENT=	Sumover version of vic.1

MAN1=		vic.1

post-extract:
	@(mv ${WRKDIR}/${DISTNAME} ${WRKDIR}/vic || true)

pre-build:
	@( \
		cd ${WRKSRC}/../common && ./configure && make -f ./Makefile ;    \
	)
#do-build:
#	@( \
#		cd ${WRKSRC}/common && ./configure && make ;	\
#		cd ${WRKSRC}/vic && autoconf253 -f && ./configure --with-tcl=/usr/local --with-tk=/usr/local && make) ;	\
#	)

.include <bsd.port.mk>

