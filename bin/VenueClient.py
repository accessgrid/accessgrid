#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
# Created:     2004/02/02
# RCS-ID:      $Id: VenueClient.py,v 1.251 2004-03-12 21:31:31 judson Exp $
# Copyright:   (c) 2004
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: VenueClient.py,v 1.251 2004-03-12 21:31:31 judson Exp $"

# Standard Imports
import os
import sys

if sys.version.startswith('2.2'):
    try:
        from optik import OptionParser
    except:
        raise Exception, "Missing module optik necessary for the AG Toolkit."

if sys.version.startswith('2.3'):
    try:
        from optparse import OptionParse
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

    # build options for this application
    parser = OptionParser()
    parser.add_option("-p", "--port", type="int", dest="port",
                      default=8000, metavar="PORT",
                      help="Set the port the service manager should run on.")
    parser.add_option("--personalNode", action="store_true", dest="pnode",
                      default = 0,
                  help="specify this should run with personal node services.")

    # Init the toolkit with the standard environment.
    app = WXGUIApplication()

    # Add our options
    app.SetOptionParser(parser)
    
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
    


