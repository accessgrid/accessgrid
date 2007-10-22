# New AG port makefile for:	quickbridge
# Date created:			18 October 2007
# Whom:				Chrisw Willing
#
# $FreeBSD$
#

PORTNAME=	quickbridge
PORTVERSION=	3.1
CATEGORIES=

MASTER_SITES=	http://www.vislab.uq.edu.au/ag3/distfiles/
USE_TGZ=	yes
DISTNAME=	${PORTNAME}-${PORTVERSION}.src
WRKSRC=		${WRKDIR}/${PORTNAME}-${PORTVERSION}
PATCH_DIST_STRIP=	-p0


MAINTAINER=	c.willing@uq.edu.au
COMMENT=	Access Grid quickbridge

do-build:
	@( \
	cd ${WRKSRC}/services/network/QuickBridge ;	\
	gcc -O -o QuickBridge QuickBridge.c ;	\
	)
do-install:
	@(	\
	cp ${WRKSRC}/services/network/QuickBridge/QuickBridge ${PREFIX}/bin/ ;	\
	)

.include <bsd.port.mk>

