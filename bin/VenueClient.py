#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
#
# Author:      Thomas D. Uram
# Created:     2004/02/02
# RCS-ID:      $Id: VenueClient.py,v 1.246 2004-02-24 17:21:45 turam Exp $
# Copyright:   (c) 2004
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import getopt
import logging
import os
import sys

from wxPython.wx import wxPySimpleApp
from AccessGrid.UIUtilities import ProgressDialog

from AccessGrid import Toolkit

from AccessGrid.VenueClientUI import VenueClientUI
from AccessGrid.VenueClientController import VenueClientController
from AccessGrid.VenueClient import VenueClient
from AccessGrid.PersonalNode import PersonalNodeManager
from AccessGrid.Platform import InitUserEnv, GetUserConfigDir
from AccessGrid.VenueClientUIClasses import VerifyExecutionEnvironment
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
    
    log = logging.getLogger("AG")
    log.setLevel(logging.DEBUG)

    if logFile is None:
        logname = os.path.join(GetUserConfigDir(), "VenueClient.log")
    else:
        logname = logFile
        
    hdlr = logging.FileHandler(logname)
    extfmt = logging.Formatter("%(asctime)s %(thread)s %(name)s %(filename)s:%(lineno)s %(levelname)-5s %(message)s", "%x %X")
    fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
    hdlr.setFormatter(extfmt)
    log.addHandler(hdlr)

    if debugMode:
        hdlr = logging.StreamHandler()
        hdlr.setFormatter(fmt)
        log.addHandler(hdlr)
        
    logging.getLogger("AG.VenueClientController").setLevel(logging.DEBUG)

def Usage():
    print "%s:" % (sys.argv[0])
    print "  -h|--help:      print usage"
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
        opts, args = getopt.getopt(sys.argv[1:], "hdl:",
                                   ["personalNode", "debug", "help", "logfile="])

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

VerifyExecutionEnvironment()

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
        personalNode = PersonalNodeManager( setSvcCallback,
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



