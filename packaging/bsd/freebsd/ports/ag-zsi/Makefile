# New ports collection makefile for:	py-zsi
# Date created:		17 September 2001
# Whom:	      		Johann Visagie <wjv@FreeBSD.org>
#
#

PORTNAME=	ag-zsi
DISTVERSION=	0.1
CATEGORIES=	net python
MASTER_SITES=	http://www.vislab.uq.edu.au/ag3/freebsd/distfiles/
#PKGNAMEPREFIX=	${PYTHON_PKGNAMEPREFIX}
PKGNAMESUFFIX=	-devel
#DISTNAME=	${PORTNAME}-${DISTVERSION}
USE_BZIP2=	yes
DISTNAME=	ZSI-20060601svn
WRKSRC=		${WRKDIR}/zsi

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
