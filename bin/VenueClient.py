#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
# Created:     2004/02/02
# RCS-ID:      $Id: VenueClient.py,v 1.266 2004-12-08 16:48:20 judson Exp $
# Copyright:   (c) 2004
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: VenueClient.py,v 1.266 2004-12-08 16:48:20 judson Exp $"

# Standard Imports
import os
import sys

from optparse import Option

# GUI related imports
from wxPython.wx import wxPySimpleApp

# Our imports
from AccessGrid.Toolkit import WXGUIApplication
from AccessGrid import Log
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.VenueClientUI import VenueClientUI
from AccessGrid.VenueClientController import VenueClientController
from AccessGrid.VenueClient import VenueClient
from AccessGrid.UIUtilities import ErrorDialog
from AccessGrid.UIUtilities import ProgressDialog

def main():
    log = None

    # Create the wxpython app
    wxapp = wxPySimpleApp()

    # Create a progress dialog
    startupDialog = ProgressDialog("Starting Venue Client...",
                                   "Initializing AccessGrid Toolkit", 4)
    startupDialog.Show()

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
    
    startupDialog.UpdateOneStep("Creating venue client components.")

    # Create venue client components
    vc = VenueClient(pnode=pnode, port=port,
                     progressCB=startupDialog.UpdateOneStep, app=app)
    vcc = VenueClientController()
    vcc.SetVenueClient(vc)
    vcui = VenueClientUI(vc, vcc, app)

    # Associate the components with the ui
    vcc.SetGui(vcui)
    vc.AddObserver(vcui)

    # Enter the specified venue
    if url:
        startupDialog.UpdateOneStep("Entering venue")
        vc.EnterVenue(url)
        
    # Startup complete; kill progress dialog
    startupDialog.Destroy()

    # Spin
    wxapp.SetTopWindow(vcui)
    wxapp.MainLoop()

# The main block
if __name__ == "__main__":
    main()
    


