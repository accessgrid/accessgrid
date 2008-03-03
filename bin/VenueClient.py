#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
# Created:     2004/02/02
# RCS-ID:      $Id: VenueClient.py,v 1.288 2007-09-19 16:45:32 turam Exp $
# Copyright:   (c) 2004
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: VenueClient.py,v 1.288 2007-09-19 16:45:32 turam Exp $"


from AccessGrid.UIUtilities import ErrorDialog, ProgressDialog, MessageDialog, SetIcon
from AccessGrid import icons
import wx
from AccessGrid.Version import GetVersion, GetStatus
from AccessGrid.Preferences import Preferences

# Display the progress dialog as soon as possible
wxapp = wx.PySimpleApp(clearSigInt=0)
versionText = "Version %s %s" % (str(GetVersion()), str(GetStatus()) )
progressDialog = ProgressDialog(None,icons.getSplashBitmap(), 100, versionText)
progressDialog.Show(1)
progressDialog.UpdateGauge('Starting Venue Client',10)


# Standard Imports
import os
import sys
import signal

from optparse import Option

# GUI related imports

try:
    from twisted.internet import _threadedselect as threadedselectreactor
except:
    from twisted.internet import threadedselectreactor
threadedselectreactor.install()

# Our imports
from AccessGrid.Toolkit import WXGUIApplication, MissingDependencyError
from AccessGrid import Log
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.VenueClientUI import VenueClientUI, ProfileDialog
from AccessGrid.VenueClientController import VenueClientController
from AccessGrid.VenueClient import VenueClient
#from AccessGrid.UIUtilities import ErrorDialog, ProgressDialog, MessageDialog, SetIcon
#from AccessGrid import icons
from AccessGrid.Platform import IsOSX,IsWindows
from AccessGrid.Version import GetVersion, GetStatus
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

    import wx

    log = None

    signal.signal(signal.SIGINT, SignalHandler)
    signal.signal(signal.SIGTERM, SignalHandler)

    m2threading.init()


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
        
    # Get the log
    log = app.GetLog()
    pnode = app.GetOption("pnode")
    url = app.GetOption("url")
    port = app.GetOption("port")
    nodeConfig = app.GetOption("configfilename")

    try:
        import wx
        wxversion_str = str(wx.VERSION_STRING)
        log.info("wx version is: " + wxversion_str)
    except:
        log.exception("Unable to log wx version.")
    
    try:
        
        # Create venue client components
        progressDialog.UpdateGauge('Creating VenueClient components',20)
        vc = VenueClient(pnode=pnode, port=port,
                         app=app, progressCB=progressDialog.UpdateGauge,
                         nodeConfigName=nodeConfig)
        progressDialog.UpdateGauge('Creating venue client internals',70)
        vcc = VenueClientController()
        vcc.SetVenueClient(vc)
        progressDialog.UpdateGauge('Creating venue client user interface',80)
        vcui = VenueClientUI(vc, vcc, app,progressDialog.UpdateGauge)
        vc.SetVCUI(vcui)
    
        # Associate the components with the ui
        vcc.SetGui(vcui)
        vc.AddObserver(vcui)
        

        # 
        # If profile is the default profile, do first-time user initialization
        #
        profile = app.preferences.GetProfile()
        if profile.IsDefault():  # not your profile
            log.debug("the profile is the default profile - open profile dialog")

            profileDialog = ProfileDialog(None, -1, 'Fill in your profile', 1)
            profileDialog.SetProfile(profile)
            
            if (profileDialog.ShowModal() != wx.ID_OK):
                profileDialog.Destroy()
                os._exit(0)
                
            profile = profileDialog.GetNewProfile()
            profileDialog.Destroy()    
                    
            # Change profile based on values filled in to the profile dialog
            vcc.ChangeProfile(profile)


            # Build a customized default node configuration
            vc.BuildDefaultNodeConfiguration()
            
            
            # Check multicast status, set to use unicast appropriately
            multicastStatus = vc.GetMulticastStatus()
            if multicastStatus == 0:
                vcui.SetMcastStatus(multicastStatus)
                vcui.UseUnicastCB()
            
                app.preferences.SetPreference(Preferences.MULTICAST,0)
                app.preferences.StorePreferences()

        vcui.Show(True)
        
        
        # Enter the specified venue
        if url:
            vc.EnterVenue(url)
        
        progressDialog.Destroy()
        # Spin
        wxapp.SetTopWindow(vcui)
        SetIcon(vcui)
    
        wxapp.MainLoop()
        m2threading.cleanup()
    except:
        log.exception("Error in VenueClient main")

# The main block
if __name__ == "__main__":
    main()


