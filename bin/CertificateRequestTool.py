#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        CertificateRequestTool.py
# Purpose:     Starts the CertificateRequestTool
# Created:     2003/08/12
# RCS_ID:      $Id: CertificateRequestTool.py,v 1.7 2004-09-10 18:52:08 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
This is the tool used to get certificates.
"""
__revision__ = "$Id: CertificateRequestTool.py,v 1.7 2004-09-10 18:52:08 judson Exp $"

from AccessGrid.Toolkit import WXGUIApplication

if __name__ == "__main__":
    app = WXGUIApplication()

    # This will not work if we don't have any certificates
    try:
        args = app.Initialize('CertificateRequestTool')
    except:
        # Doesn't matter if we have certificates or proxies
        # we just want to request a new certificate
        pass

    certMgrUI = app.GetCertMgrUI()
    certMgrUI.HandleNoCertificateInteraction()
