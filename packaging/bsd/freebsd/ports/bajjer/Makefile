# New ports collection makefile for:	py-zsi
# Date created:		17 September 2001
# Whom:	      		Johann Visagie <wjv@FreeBSD.org>
#
#

PORTNAME=	Bajjer
DISTVERSION=	0.2.4
#PORTEPOCH=	1
CATEGORIES=	net python
MASTER_SITES=	http://www.vislab.uq.edu.au/ag3/freebsd/distfiles/ \
		http://dsd.lbl.gov/Collaboratories/bajjer/download/dev/
PKGNAMEPREFIX=	${PYTHON_PKGNAMEPREFIX}
PKGNAMESUFFIX=	-devel
DISTNAME=	${PORTNAME}-${DISTVERSION}

MAINTAINER=	
COMMENT=	A Jabber library for Python

BUILD_DEPENDS=	${PYXML}
RUN_DEPENDS=	${PYXML}

CONFLICTS=	py*-elementtree-*

NO_LATEST_LINK=	yes

USE_PYTHON=	2.0+
USE_PYDISTUTILS=	yes

DOCSDIR=	${PREFIX}/share/doc/py-${PORTNAME}${PKGNAMESUFFIX}
PORTDOCS=	*

post-extract:
	@${FIND} -P ${WRKSRC} -name .cvsignore -delete

post-install:
.if !defined(NOPORTDOCS)
	@${MKDIR} ${DOCSDIR}
.for f in CHANGELOG README LICENSE
	${INSTALL_DATA} ${WRKSRC}/${f} ${DOCSDIR}
.endfor
.endif

.include <bsd.port.mk>
