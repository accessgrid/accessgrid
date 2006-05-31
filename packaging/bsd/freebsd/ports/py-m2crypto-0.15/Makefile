# New ports collection makefile for:	py-m2crypto
# Date created:				27 March 2001
# Whom:					Peter Haight <peterh@sapros.com>
#
# $FreeBSD: ports/security/py-m2crypto/Makefile,v 1.13 2005/09/16 17:58:31 mnag Exp $
#

PORTNAME=	m2crypto
PORTVERSION=	0.15
CATEGORIES=	security python
MASTER_SITES=	http://www.vislab.uq.edu.au/ag3/freebsd/distfiles/ \
		http://sandbox.rulemaker.net/ngps/Dist/
PKGNAMEPREFIX=	${PYTHON_PKGNAMEPREFIX}
DISTNAME=	${PORTNAME}-${PORTVERSION:S/.1$//}

PATCH_SITES=	${MASTER_SITES}

MAINTAINER=	mnag@FreeBSD.org
COMMENT=	Crypto and SSL toolkit for Python

#BUILD_DEPENDS=	swig1.3:${PORTSDIR}/devel/swig13
BUILD_DEPENDS=  swig=1.3.24_1:../swig1324

#PATCHFILES+=	patch-SWIG-_m2crypto_wrap.c

DIST_SUBDIR=	python
USE_PYTHON=	yes
USE_PYDISTUTILS=yes
USE_ZIP=	yes
USE_OPENSSL=	yes
USE_REINPLACE=	yes

#`post-patch:
#`	@${REINPLACE_CMD} "s|%%PYTHON_INCLUDEDIR%%|${PYTHON_INCLUDEDIR}|g" ${WRKSRC}/SWIG/Makefile

.include <bsd.port.mk>
