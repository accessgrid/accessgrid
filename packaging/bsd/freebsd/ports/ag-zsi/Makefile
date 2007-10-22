# New ports collection makefile for:	py-zsi
# Date created:				16 October 2007
# Whom:	      				Chris Willing <c.willing@uq.edu.au>
#
#

PORTNAME=	ag-zsi
DISTVERSION=	r1385
CATEGORIES=	net python
MASTER_SITES=	http://www.vislab.uq.edu.au/ag3/freebsd/distfiles/
#PKGNAMEPREFIX=	${PYTHON_PKGNAMEPREFIX}
PKGNAMESUFFIX=	-devel
#DISTNAME=	${PORTNAME}-${DISTVERSION}
USE_TGZ=	yes
DISTNAME=	zsi-${DISTVERSION}
WRKSRC=		${WRKDIR}/zsi-${DISTVERSION}

MAINTAINER=	
COMMENT=	Zsi for AccessGrid

BUILD_DEPENDS=	${PYXML}
RUN_DEPENDS=	${PYXML}

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
.for f in CHANGES README RELEASE
	${INSTALL_DATA} ${WRKSRC}/${f} ${DOCSDIR}
.endfor
.endif

.include <bsd.port.mk>
