#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        CertificateManager.py
# Purpose:     User tool for managing certificates.
# Created:     2003/08/02
# RCS-ID:      $Id: CertificateManager.py,v 1.4 2005-10-07 22:44:51 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

# The standard imports
import os, sys
from optparse import Option
from wxPython.wx import *

# Our imports
from AccessGrid.Toolkit import WXGUIApplication
from AccessGrid.Security.wxgui import CertificateManagerDialog

def main():
    pyapp = wxPySimpleApp()

    app = WXGUIApplication()

    try:
        app.Initialize("CertificateManager")
    except Exception, e:
        print "Exception initializing toolkit:", e
        print "Exiting."
        sys.exit(-1)

    d = CertificateManagerDialog.CertificateManagerDialog(None, -1,
                                                 "Certificate Manager",
                                                 app.GetCertificateManager()) 
    d.Show(1)
    
    pyapp.SetTopWindow(d)
    pyapp.MainLoop()
    
if __name__ == "__main__":
    main()
