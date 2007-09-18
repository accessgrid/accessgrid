#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        CertificateRequestTool.py
# Purpose:     Starts the CertificateRequestTool
# Created:     2003/08/12
# RCS_ID:      $Id: CertificateRequestTool.py,v 1.12 2007-09-18 20:45:21 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
This is the tool used to get certificates.
"""
__revision__ = "$Id: CertificateRequestTool.py,v 1.12 2007-09-18 20:45:21 turam Exp $"

import sys
from AccessGrid.Toolkit import WXGUIApplication
import wx
from AccessGrid.Security.wxgui import CertificateManagerWXGUI

pp = wx.PySimpleApp()
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
