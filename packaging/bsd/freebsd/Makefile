# Date created:        18 October 2007
# Whom:                Christoph Willing
#
# $FreeBSD$
#

PORTNAME=	accessgrid
PKGNAMESUFFIX=	31
CVS_REVID=	20071010
#PORTVERSION=	3.1
PORTVERSION=	${CVS_REVID}
CATEGORIES=	net
MASTER_SITES=	http://www.vislab.uq.edu.au/ag3/freebsd/distfiles/
DISTNAME=	AccessGrid-3.1-cvs${CVS_REVID}
USE_TGZ=	yes

MAINTAINER=	willing@vislab.uq.edu.au
COMMENT=	A port of the Access Grid Toolkit

USE_PYTHON=	yes
ETCDIR=		${TARGETDIR}/etc

NO_INSTALL_MANPAGES=	1

BUILD_DEPENDS=	wsdl2py:ports/ag-zsi

RUN_DEPENDS=	py24-wxPython>=2.6.3.2:${PORTSDIR}/x11-toolkits/py-wxPython26 \
	py24-bsddb>=2.4.3:${PORTSDIR}/databases/py-bsddb	\
	py24-avahi>=0.6.10:${PORTSDIR}/net/py-avahi	\
	py24-dbus>=0.61:${PORTSDIR}/devel/py-dbus	\
	py24-feedparser>=4.1_2:${PORTSDIR}/textproc/py-feedparser	\
        tightvnc>=1.2.9_1:${PORTSDIR}/net/tightvnc	\
	ag-zsi-devel>=r1385:ports/ag-zsi	\
	py24-agtwistedCore>=2.5.0:ports/agtwisted \
	py24-Bajjer-devel>=0.2.5:ports/bajjer	\
	py24-m2crypto>=0.17:ports/py-m2crypto	\
	common>=0.1:ports/common	\
	wxmozilla>=0.5.6_1:ports/wxmozilla


#	pyOpenSSL>=0.5.1:ports/py-openssl	\


WRKSRC=		${WRKDIR}/AccessGrid

do-build:
	@(	\
	cd ${WRKSRC}/packaging; export AGBUILDROOT=${WRKDIR}; python BuildSnapshot.py --no-checkout --dist=freebsd	\
	)
post-build:
	@( ${MV} ${WRKDIR}/dist-* ${WRKDIR}/dist >/dev/null 2>/dev/null || true )

do-install:
	@(	\
	cd ${WRKDIR}/dist;	\
	${INSTALL_SCRIPT} bin/* ${PREFIX}/bin; \
	${INSTALL_SCRIPT} ${PATCHDIR}/agkill ${PREFIX}/bin; \
	cp -R lib/ ${PREFIX}/lib;	\
	rm -rf share/applnk share/gnome;\
	cp -R share/ ${PREFIX}/share;	\
	${MKDIR} ${PREFIX}/share/doc/${PORTNAME}-3.1;	\
	${MV} ${PREFIX}/share/doc/AccessGrid/* ${PREFIX}/share/doc/${PORTNAME}-3.1;	\
	${RMDIR} ${PREFIX}/share/doc/AccessGrid;	\
	cp -R etc/ ${ETCDIR};	\
	cp -R SharedApplications ${ETCDIR}/AccessGrid3;	\
	cp -R NodeServices ${ETCDIR}/AccessGrid3;	\
	${MKDIR} ${ETCDIR}/xdg/menus/gnome-applications-merged/; \
	${INSTALL_DATA} ${WRKSRC}/packaging/linux/xdg/AccessGrid3.menu ${ETCDIR}/xdg/menus/gnome-applications-merged/; \
	${MKDIR} ${PREFIX}/share/gnome/desktop-directories;	\
	${INSTALL_DATA} ${WRKSRC}/packaging/linux/xdg/*3*.directory ${PREFIX}/share/gnome/desktop-directories/;	\
	${MKDIR} ${DESKTOPDIR};	\
	${INSTALL_DATA} ${WRKSRC}/packaging/linux/xdg/*3*.desktop ${DESKTOPDIR};	\
	${MKDIR} -p ${DATADIR};	\
	${INSTALL_DATA} ${WRKSRC}/packaging/linux/ag-ellipse.png ${DATADIR}/;	\
	${INSTALL_DATA} ${PREFIX}/share/AccessGrid/ag.ico ${DATADIR}/;	\
	${RM} -rf ${PREFIX}/share/AccessGrid;	\
	)

.include <bsd.port.pre.mk>
post-install:
	@(PKG_PREFIX=${PREFIX} ${SH} ${PKGINSTALL} ${PKGNAME} POST-INSTALL)
.include <bsd.port.post.mk>

#.include <bsd.port.mk>
