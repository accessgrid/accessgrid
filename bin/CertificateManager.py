#!/usr/bin/python2

import os, sys
from optparse import Option

from wxPython.wx import *

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
