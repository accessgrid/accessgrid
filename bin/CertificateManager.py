#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        CertificateManager.py
# Purpose:     User tool for managing certificates.
# Created:     2003/08/02
# RCS-ID:      $Id: CertificateManager.py,v 1.9 2007-09-18 20:45:20 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

# The standard imports
import os, sys
from optparse import Option
import wx

# Our imports
from AccessGrid.Toolkit import WXGUIApplication, MissingDependencyError
from AccessGrid.Security.wxgui import CertificateManagerDialog
from AccessGrid.Security.wxgui import CertificateManagerWXGUI
from AccessGrid.UIUtilities import MessageDialog

def main():
    pyapp = wx.PySimpleApp()

    app = WXGUIApplication()

    try:
        app.Initialize("CertificateManager")
    except MissingDependencyError, e:
        if e.args[0] == 'SSL':
            msg = "The installed version of Python has no SSL support.  Check that you\n"\
                  "have installed Python from python.org, or ensure SSL support by\n"\
                  "some other means."
        else:
            msg = "The following dependency software is required, but not available:\n\t%s\n"\
                    "Please satisfy this dependency and restart the software"
            msg = msg % e.args[0]
        MessageDialog(None,msg, "Initialization Error",
                      style=wx.ICON_ERROR )
        sys.exit(-1)
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        MessageDialog(None,
                      "The following error occurred during initialization:\n\n\t%s %s" % (e.__class__.__name__,e), 
                      "Initialization Error",
                      style=wx.ICON_ERROR )
        sys.exit(-1)

    certMgr = app.GetCertificateManager()
    certMgrGui = CertificateManagerWXGUI.CertificateManagerWXGUI(certMgr)
    d = CertificateManagerDialog.CertificateManagerDialog(None, -1,
                                                 "Certificate Manager",
                                                 certMgr, 
                                                 certMgrGui) 
    d.Show(1)
    
    pyapp.SetTopWindow(d)
    pyapp.MainLoop()
    
if __name__ == "__main__":
    main()
