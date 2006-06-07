# ex:ts=8
# Ports collection makefile for:	wxmozilla
# Date created:			June 6, 2006
# Whom:				CKW
#
# $FreeBSD$
#

PORTNAME=	wxmozilla
PORTVERSION=	0.5.6
PORTREVISION=	1
CATEGORIES=	x11-toolkits
MASTER_SITES=	${MASTER_SITE_SOURCEFORGE}
MASTER_SITE_SUBDIR=	${PORTNAME}

MAINTAINER=	ports@FreeBSD.org
COMMENT=	Embedding Mozilla in wxWidgets

BUILD_DEPENDS=	py24-wxPython>=2.6.3.2:${PORTSDIR}/x11-toolkits/py-wxPython26
RUN_DEPENDS=	${BUILD_DEPENDS}

GNU_CONFIGURE=	yes
USE_GNOME=	gnomehack gnometarget
USE_GECKO=	mozilla
WXGTK_CONFIG?=	${X11BASE}/bin/wxgtk2-2.6-config
CONFIGURE_ARGS=	--with-wx-config=${WXGTK_CONFIG} --enable-python CPPFLAGS=-I/usr/local/include
INSTALLS_SHLIB=	yes

CONFLICTS=	wxmozilla-0.5.{3-5}*



.include <bsd.port.pre.mk>

.include "${PORTSDIR}/www/mozilla/bsd.gecko.mk"

.if ${OSVERSION} < 500000
IGNORE=	does not build on 4.X
.endif

post-patch:
	@${REINPLACE_CMD} -e 's|mozilla-nspr|nspr|g' \
		${WRKSRC}/configure

.include <bsd.port.post.mk>

