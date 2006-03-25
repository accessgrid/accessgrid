#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
# Created:     2004/02/02
# RCS-ID:      $Id: VenueClient.py,v 1.276 2006-03-25 05:20:06 turam Exp $
# Copyright:   (c) 2004
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: VenueClient.py,v 1.276 2006-03-25 05:20:06 turam Exp $"

# Standard Imports
import os
import sys
import signal

from optparse import Option

# GUI related imports
from wxPython.wx import wxPySimpleApp, wxTaskBarIcon
from twisted.internet import threadedselectreactor
threadedselectreactor.install()

# Our imports
from AccessGrid.Toolkit import WXGUIApplication
from AccessGrid import Log
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.VenueClientUI import VenueClientUI
from AccessGrid.VenueClientController import VenueClientController
from AccessGrid.VenueClient import VenueClient
from AccessGrid.UIUtilities import ErrorDialog, ProgressDialog
from AccessGrid import icons
from AccessGrid.Platform import IsOSX,IsWindows
from AccessGrid.Version import GetVersion
from twisted.internet import reactor

from M2Crypto import threading as m2threading


# Signal Handler to block Ctrl-C in shell
# Ideally, we could shut down cleanly here, but the
# signal handler doesn't get called until after
# the next interaction with the UI, which is 
# very non-intuitive
def SignalHandler(signum, frame):
    pass

def main():

    log = None

    signal.signal(signal.SIGINT, SignalHandler)
    signal.signal(signal.SIGTERM, SignalHandler)

    m2threading.init()

    # Create the wxpython app
    wxapp = wxPySimpleApp(clearSigInt=0)
    
    versionText = "Version %s" % str(GetVersion())
    progressDialog = ProgressDialog(None,icons.getSplashBitmap(), 100, versionText)
    progressDialog.UpdateGauge('Starting Venue Client',10)
    progressDialog.Show(1)

    if IsOSX() or IsWindows():
        t = wxTaskBarIcon()
        t.SetIcon(icons.getAGIconIcon())
        
    # Init the toolkit with the standard environment.
    app = WXGUIApplication()

    # build options for this application
    portOption = Option("-p", "--port", type="int", dest="port",
                        default=0, metavar="PORT",
                        help="Set the port the venueclient control interface\
                        should listen on.")
    app.AddCmdLineOption(portOption)
    pnodeOption = Option("--personalNode", type="int", dest="pnode",
                         default=None,
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
    progressDialog.UpdateGauge('Creating VenueClient components',20)
    vc = VenueClient(pnode=pnode, port=port,
                     app=app, progressCB=progressDialog.UpdateGauge)
    progressDialog.UpdateGauge('Creating venue client internals',70)
    vcc = VenueClientController()
    vcc.SetVenueClient(vc)
    progressDialog.UpdateGauge('Creating venue client user interface',80)
    vcui = VenueClientUI(vc, vcc, app)

    # Associate the components with the ui
    vcc.SetGui(vcui)
    vc.AddObserver(vcui)
    
    # Enter the specified venue
    if url:
        progressDialog.UpdateGauge('Entering venue...',90)
        vc.EnterVenue(url)
        
    progressDialog.UpdateGauge('Finished',100)
    progressDialog.Destroy()
    # Spin
    wxapp.SetTopWindow(vcui)

    wxapp.MainLoop()
    m2threading.cleanup()

# The main block
if __name__ == "__main__":
    main()


