#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        CertificateRequestTool.py
# Purpose:     Starts the CertificateRequestTool
#
# Author:      lefvert 
#
#
# Created:     2003/08/12
# RCS_ID:      $Id: CertificateRequestTool.py,v 1.1 2003-08-13 19:05:44 lefvert Exp $ 
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

from AccessGrid.Toolkit import WXGUIApplication
from AccessGrid.VenueClientUIClasses import VerifyExecutionEnvironment
from wxPython.wx import wxPySimpleApp
from AccessGrid import CertificateManager

def Usage():
        print "%s:" % (sys.argv[0])
        print "  --help:        print usage"
        print "  -i|--identity: request identity certificate"
        print "  -h|--host:     request host certificate"
        print "  -s|--service:  request service certificate"

def Main():
    
    certType = None
   
    #if len(sys.argv) == 1:
    #    certType = None

    #elif len(sys.argv) == 2:
    #    arg = sys.argv[1]
    #    if arg == '-i' or '-identity':
    #        certType = "IDENTITY"
    #        
    #    elif arg == '-s' or '-service':
    #        certType = "SERVICE"
    #        
    #    elif arg == '-h' or '-host':
    #        certType = "HOST"
    #
    #    else:
    #        Usage()
    #        return

    #else:
    #    Usage()
    #    return
    
    VerifyExecutionEnvironment()
    app = WXGUIApplication()
    app.Initialize()
    
    #app.InitGlobusEnvironment()
    # Can not use this because it only opens the dialog when no
    # certs are present.


    # This will not work if we don't have any certificates
    try:
        app.certificateManager.InitEnvironment()
        
    except:
        # Doesn't matter if we have certificates or proxies
        # we just want to request a new certificate
        pass

    app.gui.HandleNoCertificateInteraction()

    
        
if __name__ == "__main__":
    pp = wxPySimpleApp()
    Main()
