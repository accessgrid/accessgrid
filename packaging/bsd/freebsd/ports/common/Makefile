# New ports collection makefile for:   common
# Date created:        23 May 2006
# Whom:                CKW
#
# $FreeBSD$
#

PORTNAME=	common
PORTVERSION=	0.1
CATEGORIES=	net
MASTER_SITES=	http://www.vislab.uq.edu.au/ag3/freebsd/distfiles/

MAINTAINER=	willing@vislab.uq.edu.au
COMMENT=	UCL common with additions for AccessGrid

BUILD_DEPENDS=  swig1.3:${PORTSDIR}/devel/swig13

USE_PYTHON=     yes
USE_PYDISTUTILS=yes
USE_REINPLACE=  yes

WRKSRC=${WRKDIR}/${PORTNAME}-${PORTVERSION}/examples/_common

.include <bsd.port.mk>

