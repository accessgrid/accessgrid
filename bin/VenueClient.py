#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
# Created:     2004/02/02
# RCS-ID:      $Id: VenueClient.py,v 1.249 2004-03-12 05:23:12 judson Exp $
# Copyright:   (c) 2004
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: VenueClient.py,v 1.249 2004-03-12 05:23:12 judson Exp $"

# Standard Imports
import getopt
import os
import sys

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

# Print usage
def Usage(agtk):
    """
    Print usage for the venue client.
    """
    print "USAGE %s:" % os.path.split(sys.argv[0])[1]

    print " Toolkit Options:"
    agtk.Usage()

    print " VenueClient Specific Options:"
    print "\t--personalNode: manage services as a personal node"

# Command line argument processing
def ProcessArgs(app, argv):
    """
    Handle any arguments we're interested in.

    --personalNode: Handle startup of local node services.
    """
    options = dict()

    try:
        opts, args = getopt.getopt(argv, "", ["personalNode"])
    except getopt.GetoptError:
        Usage(app)
        sys.exit(2)

    for opt, arg in opts:
        if opt == '--personalNode':
            options['pnode'] = 1
        else:
            Usage(app)
            sys.exit(0)

    if app.GetCmdlineArg('help') or app.GetCmdlineArg('h'):
        Usage(app)
        sys.exit(0)

    return options

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

    # Try to initialize
    try:
        args = app.Initialize(sys.argv[1:], "VenueClient")
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)
        
    # Process the rest of the cmd line args
    options = ProcessArgs(app, args)

    # Get the log
    log = app.GetLog()

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
    if options.has_key('pnode'):
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
    if options.has_key('pnode'):
        log.debug("Terminating personal node services.")
        personalNode.Stop()

# The main block
if __name__ == "__main__":
    main()
    


