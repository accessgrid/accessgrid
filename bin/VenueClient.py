#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
# Created:     2004/02/02
# RCS-ID:      $Id: VenueClient.py,v 1.252 2004-03-15 20:07:02 judson Exp $
# Copyright:   (c) 2004
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: VenueClient.py,v 1.252 2004-03-15 20:07:02 judson Exp $"

# Standard Imports
import os
import sys

if sys.version.startswith('2.2'):
    try:
        from optik import Option
    except:
        raise Exception, "Missing module optik necessary for the AG Toolkit."

if sys.version.startswith('2.3'):
    try:
        from optparse import Option
    except:
        raise Exception, "Missing module optparse, check your python installation."

# GUI related imports
from wxPython.wx import wxPySimpleApp

# Our imports
from AccessGrid.Toolkit import WXGUIApplication
from AccessGrid import Log
from AccessGrid.Platform.PersonalNode import PersonalNodeManager
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
                                   "Initializing AccessGrid Toolkit", 5)
    startupDialog.Show()

    # Init the toolkit with the standard environment.
    app = WXGUIApplication()

    # build options for this application
    portOption = Option("-p", "--port", type="int", dest="port",
                        default=12000, metavar="PORT",
                        help="Set the port the venueclient control interface\
                        should listen on.")
    app.AddCmdLineOption(portOption)
    pnodeOption = Option("--pnode", action="store_true", dest="pnode",
                         default=0,
                         help="Personal node rendezvous token.")
    app.AddCmdLineOption(pnodeOption)

    # Try to initialize
    try:
        args = app.Initialize(sys.argv[1:], "VenueClient")
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)
        
    # Get the log
    log = app.GetLog()
    pnode = app.GetOption("pnode")
    
    startupDialog.UpdateOneStep("Initializing the VenueClient.")

    # Create venue client components
    vc = VenueClient()
    vcc = VenueClientController()
    vcui = VenueClientUI(vc, vcc)

    # Associate the components
    vcc.SetGui(vcui)
    vcc.SetVenueClient(vc)
    vc.AddObserver(vcui)

    # Do personal node stuff if that was specified
    if pnode:
        startupDialog.UpdateOneStep("Starting personal node services.")
        personalNode = PersonalNodeManager(app.GetDebugLevel(),
                                           startupDialog.UpdateOneStep)
        nsUrl = personalNode.Run()
        vc.SetNodeUrl(nsUrl)
    else:
        log.debug("Not starting personal node services.")
        
    # Startup complete; kill progress dialog
    startupDialog.Destroy()

    # Spin
    wxapp.SetTopWindow(vcui)
    wxapp.MainLoop()

    # When we exit, we have to cleanup personal node stuff,
    # if we started it.
    if pnode:
        log.debug("Terminating personal node services.")
        personalNode.Stop()

# The main block
if __name__ == "__main__":
    main()
    


