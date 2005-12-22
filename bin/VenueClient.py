#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
# Created:     2004/02/02
# RCS-ID:      $Id: VenueClient.py,v 1.271 2005-12-22 21:54:53 turam Exp $
# Copyright:   (c) 2004
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: VenueClient.py,v 1.271 2005-12-22 21:54:53 turam Exp $"

# Standard Imports
import os
import sys

from optparse import Option

# GUI related imports
from wxPython.wx import wxPySimpleApp
from twisted.internet import threadedselectreactor
threadedselectreactor.install()

# Our imports
from AccessGrid.Toolkit import WXGUIApplication
from AccessGrid import Log
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.VenueClientUI import VenueClientUI
from AccessGrid.VenueClientController import VenueClientController
from AccessGrid.VenueClient import VenueClient
from AccessGrid.UIUtilities import ErrorDialog
from twisted.internet import reactor

from M2Crypto import threading as m2threading

def main():
    log = None

    m2threading.init()

    # Create the wxpython app
    wxapp = wxPySimpleApp()

    # Init the toolkit with the standard environment.
    app = WXGUIApplication()

    # build options for this application
    portOption = Option("-p", "--port", type="int", dest="port",
                        default=0, metavar="PORT",
                        help="Set the port the venueclient control interface\
                        should listen on.")
    app.AddCmdLineOption(portOption)
    pnodeOption = Option("--personalNode", action="store_true", dest="pnode",
                         default=0,
                         help="Run NodeService and ServiceManager with the client.")
    app.AddCmdLineOption(pnodeOption)
    urlOption = Option("--url", type="string", dest="url",
                       default="", metavar="URL",
                       help="URL of venue to enter on startup.")
    app.AddCmdLineOption(urlOption)

    # Try to initialize
    try:
        args = app.Initialize("VenueClient")
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)
        
    # Get the log
    log = app.GetLog()
    pnode = app.GetOption("pnode")
    url = app.GetOption("url")
    port = app.GetOption("port")

    try:
        import wxPython
        wxversion_str = str(wxPython.wx.__version__)
        log.info("wx version is: " + wxversion_str)
    except:
        log.exception("Unable to log wx version.")
    
    # Create venue client components
    vc = VenueClient(pnode=pnode, port=port,
                     app=app)
    vcc = VenueClientController()
    vcc.SetVenueClient(vc)
    vcui = VenueClientUI(vc, vcc, app)

    # Associate the components with the ui
    vcc.SetGui(vcui)
    vc.AddObserver(vcui)

    # Enter the specified venue
    if url:
        vc.EnterVenue(url)
        
    # Spin
    wxapp.SetTopWindow(vcui)
    wxapp.MainLoop()
    
    m2threading.cleanup()

# The main block
if __name__ == "__main__":
    main()
    


