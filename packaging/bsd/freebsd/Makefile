# Date created:        26 May, 2006
# Whom:                Christoph Willing
#
# $FreeBSD$
#

PORTNAME=	AccessGrid
PORTVERSION=	3.0.1
CATEGORIES=	net
MASTER_SITES=	http://www.vislab.uq.edu.au/ag3/freebsd/distfiles/
DISTNAME=	${PORTNAME}-${PORTVERSION}
EXTRACT_SUFX=	.src.tar.gz

MAINTAINER=	willing@vislab.uq.edu.au
COMMENT=	A port of the Access Grid Toolkit

USE_PYTHON=	yes

NO_INSTALL_MANPAGES=	1

#RUN_DEPENDS=	${PREFIX}/lib/python2.4/site-packages/_bsddb.so:${PORTSDIR}/databases/py-bsddb	\
RUN_DEPENDS=	pkg/py24-bsddb>=2.4.3:${PORTSDIR}/databases/py-bsddb	\
	avahi>=0.6.10_3:${PORTSDIR}/net/avahi	\
	py24-feedparser>=4.1_2:${PORTSDIR}/textproc/py-feedparser	\
	ag-zsi-devel>=0.1:ports/ag-zsi	\
	py24-Bajjer-devel>=0.2.4:ports/bajjer	\
	py24-m2crypto>=0.15:ports/py-m2crypto-0.15	\
	pyOpenSSL>=0.5.1:ports/py-openssl	\
	common>=0.1:ports/common


WRKSRC=		${WRKDIR}/AccessGrid

do-build:
	@(	\
	cd ${WRKSRC}/packaging; export AGBUILDROOT=${WRKDIR}; python BuildSnapshot.py --no-checkout --dist=freebsd	\
	)

do-install:
	@(	\
	if [ ! -d ${WRKDIR}/dist ]; then mv ${WRKDIR}/dist-* ${WRKDIR}/dist; fi; cd ${WRKDIR}/dist;	\
	${INSTALL_SCRIPT} bin/* ${PREFIX}/bin; \
	cp -R lib/ ${PREFIX}/lib;	\
	rm -rf share/applnk share/gnome;\
	cp -R share/ ${PREFIX}/share;	\
	cp -R etc/ ${PREFIX}/etc;	\
	cp -R SharedApplications ${PREFIX}/etc/AccessGrid3;	\
	cp -R NodeServices ${PREFIX}/etc/AccessGrid3;	\
	cp -R ${WRKSRC}/packaging/linux/xdg ${DATADIR};	\
	cp -R ${WRKSRC}/packaging/linux/ag-ellipse.png ${DATADIR};	\
	)


.include <bsd.port.pre.mk>


post-install:
	@(PKG_PREFIX=${PREFIX} ${SH} ${PKGINSTALL} ${PKGNAME} POST-INSTALL)


.include <bsd.port.post.mk>
