#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
#
# Author:      Thomas D. Uram
# Created:     2004/02/02
# RCS-ID:      $Id: VenueClient.py,v 1.248 2004-03-10 23:17:09 eolson Exp $
# Copyright:   (c) 2004
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import getopt
import os
import sys

from AccessGrid import Log
from wxPython.wx import wxPySimpleApp
from AccessGrid.UIUtilities import ProgressDialog

from AccessGrid import Toolkit

from AccessGrid.VenueClientUI import VenueClientUI
from AccessGrid.VenueClientController import VenueClientController
from AccessGrid.VenueClient import VenueClient
from AccessGrid.Platform import PersonalNode
from AccessGrid.Platform import InitUserEnv, GetUserConfigDir
#from AccessGrid.VenueClientUIClasses import VerifyExecutionEnvironment
from AccessGrid.UIUtilities import ErrorDialog



logFile = None
debugMode = 0
log = None
isPersonalNode = 0

def SetLogger():
    """
    Sets the logging mechanism.
    """
    global log
    
    if logFile is None:
        logname = os.path.join(GetUserConfigDir(), "VenueClient.log")
    else:
        logname = logFile

    log = Log.GetLogger(Log.VenueClient)
        
    Log.SetDefaultLevel(Log.VenueClientController, Log.DEBUG)
    hdlr = Log.FileHandler(logname)
    hdlr.setFormatter(Log.GetFormatter())
    hdlr.setLevel(Log.GetHighestLevel())
    Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())

    if debugMode:
        hdlr = Log.StreamHandler()
        hdlr.setFormatter(Log.GetLowDetailFormatter())
        Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())

    # A log file for warnings and errors
    warn_logname = os.path.join(GetUserConfigDir(), "VenueClientWarn.log")
    warn_hdlr = Log.FileHandler(warn_logname)
    warn_hdlr.setFormatter(Log.GetFormatter())
    warn_hdlr.setLevel(Log.WARN)
    Log.HandleLoggers(warn_hdlr, Log.GetDefaultLoggers())
        

def Usage():
    print "%s:" % (sys.argv[0])
    print "  -h|--help:      print usage"
    print "  -u|--url:       venue url to connect to"
    print "  -d|--debug:     show debugging messages"
    print "  --personalNode: manage services as a personal node"

def ProcessArgs():
    """
    Handle any arguments we're interested in.

    --personalNode: Handle startup of local node services.

    """
    
    global logFile
    global isPersonalNode
    global debugMode

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdl:u:",
                                   ["personalNode", "debug", "help",
                                    "logfile=","url="])

    except getopt.GetoptError:
        Usage()
        sys.exit(2)
        

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            Usage()
            sys.exit(0)
        elif opt == '--personalNode':
            isPersonalNode = 1
        elif opt in ('--debug', '-d'):
            debugMode = 1
        elif opt in ('--logfile', '-l'):
            logFile = arg
        elif opt in ('--url', '-u'):
            venueUrl = arg
            print "This is not working yet."
        else:
            Usage()
            sys.exit(0)


# Process command-line arguments
ProcessArgs()

# Set up logging
SetLogger()

# Create the wxpython app
wxapp = wxPySimpleApp()

# Create a progress dialog
startupDialog = ProgressDialog("Starting Venue Client...", "Loading Venue Client.", 13)
startupDialog.Show()

startupDialog.UpdateOneStep("Starting venue client.")


# We verify first because the Toolkit code assumes a valid
# globus environment.
startupDialog.UpdateOneStep("Verifying environment.")

InitUserEnv()

#VerifyExecutionEnvironment()

try:
    startupDialog.UpdateOneStep("Starting ui.")
    app = Toolkit.WXGUIApplication()

except Exception, e:
    log.exception("bin.VenueClient::OnInit: WXGUIApplication creation failed")

    text = "Application object creation failed\n%s\nThe venue client cannot continue." % (e,)
    
    startupDialog.Destroy()
    ErrorDialog(None, text, "Initialization failed",
                  style = wxOK  | wxICON_ERROR)
    sys.exit(1)

try:
    app.Initialize()

except Exception, e:
    pass
    log.exception("bin.VenueClient::OnInit: App initialization failed")
    ErrorDialog(None, "Application initialization failed. Attempting to continue",
                "Initialization failed")

# Initiate user interface components
startupDialog.UpdateOneStep()

# Initialize globus runtime stuff.
startupDialog.UpdateOneStep("Verifying globus environment.")
app.InitGlobusEnvironment()


# Create venue client components
vc = VenueClient()
vcc = VenueClientController()
vcui = VenueClientUI(vc, vcc)

# Associate the components
vcc.SetGui(vcui)
vcc.SetVenueClient(vc)
vc.AddObserver(vcui)

# Figure out if there are any credentials we can use
# since if there are not, we can't successfully startup a
# personal node.
identity = app.GetDefaultIdentityDN()

log.debug("bin.VenueClient::OnInit: ispersonal=%s",isPersonalNode)
if isPersonalNode:
    if identity == None:
        isPersonalNode = 0
        log.debug("Can't start personal node without an identity.")
        title = "Venue Client startup error."
        message = "You do not have a valid identity. \nThe Venue Client cannot start personal node services \nwithout a valid identity.\n\nShould the venue client\nbe started without the personal node services?"
        response = self.gui.Prompt(message,title)
        if not response:
            startupDialog.Destroy()
            sys.exit(1)
    else:
        startupDialog.UpdateOneStep("Starting personal node services.")
        def setSvcCallback(svcUrl):
            log.debug("bin.VenueClient::OnInit: setting node service \
                       URI to %s from PersonalNode", svcUrl)
            vc.SetNodeUrl(svcUrl)
        personalNode = PersonalNode.PersonalNodeManager( setSvcCallback,
                                                         debugMode,
                                                   startupDialog.UpdateOneStep)
        personalNode.Run()


# Startup complete; kill progress dialog
startupDialog.Destroy()

# Spin
wxapp.SetTopWindow(vcui)
wxapp.MainLoop()

#
# If we're running as a personal node, terminate the services.
#
if isPersonalNode:
    log.debug("Terminating services")
    personalNode.Stop()



