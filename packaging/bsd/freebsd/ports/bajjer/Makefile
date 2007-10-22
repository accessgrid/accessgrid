# New ports collection makefile for:	bajjer
# Date created:		16th October 2007
# Whom:	      		Chris Willing <c.willing@uq.edu.au>
#
#

PORTNAME=	Bajjer
DISTVERSION=	0.2.5
#PORTEPOCH=	1
CATEGORIES=	net python
MASTER_SITES=	http://www.vislab.uq.edu.au/ag3/freebsd/distfiles/ \
		http://dsd.lbl.gov/Collaboratories/bajjer/download/dev/
PKGNAMEPREFIX=	${PYTHON_PKGNAMEPREFIX}
PKGNAMESUFFIX=	-devel
DISTNAME=	${PORTNAME}-${DISTVERSION}

MAINTAINER=	
COMMENT=	A Jabber library for Python

BUILD_DEPENDS=	${PYXML} \
		py24-elementtree>=1.2:${PORTSDIR}/devel/py-elementtree
RUN_DEPENDS=	${PYXML} \
		py24-elementtree>=1.2:${PORTSDIR}/devel/py-elementtree

#CONFLICTS=	py*-elementtree-*

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
