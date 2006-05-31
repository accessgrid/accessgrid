# New ports makefile for:	pyOpenSSL
# Date created:			27 May, 2006
# Whom:				Chris Willing <willing@vislab.uq.edu.au>
#
# $FreeBSD$
#

PORTNAME=	pyOpenSSL
PORTVERSION=	0.5.1
CATEGORIES=	security python
MASTER_SITES=	http://www.vislab.uq.edu.au/ag3/freebsd/distfiles/ \
		http://sandbox.rulemaker.net/ngps/Dist/
DISTNAME=	${PORTNAME}-${PORTVERSION}

PATCH_SITES=	${MASTER_SITES}

MAINTAINER=	mnag@FreeBSD.org
COMMENT=	Crypto and SSL toolkit for Python

BUILD_DEPENDS=	swig1.3:${PORTSDIR}/devel/swig13


USE_PYTHON=	yes
USE_PYDISTUTILS=yes
#USE_ZIP=	no
USE_OPENSSL=	yes
USE_REINPLACE=	yes


.include <bsd.port.mk>
