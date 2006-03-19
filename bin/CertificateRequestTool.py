#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        CertificateRequestTool.py
# Purpose:     Starts the CertificateRequestTool
# Created:     2003/08/12
# RCS_ID:      $Id: CertificateRequestTool.py,v 1.11 2006-03-19 23:38:34 willing Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
This is the tool used to get certificates.
"""
__revision__ = "$Id: CertificateRequestTool.py,v 1.11 2006-03-19 23:38:34 willing Exp $"

import sys
from AccessGrid.Toolkit import WXGUIApplication
from wxPython.wx import wxPySimpleApp
from AccessGrid.Security.wxgui import CertificateManagerWXGUI

pp = wxPySimpleApp()
app = WXGUIApplication()

# This will not work if we don't have any certificates
try:
    args = app.Initialize('CertificateRequestTool')
except:
    # Doesn't matter if we have certificates or proxies
    # we just want to request a new certificate
    print "Failed to init toolkit, continuing..."
    pass

certMgrUI = CertificateManagerWXGUI.CertificateManagerWXGUI(app.GetCertificateManager())
certMgrUI.HandleNoCertificateInteraction()
