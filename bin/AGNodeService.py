#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        AGNodeService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGNodeService.py,v 1.38 2004-03-11 21:12:56 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
This is the Node Service for an AG Node.
"""
__revision__ = "$Id: AGNodeService.py,v 1.38 2004-03-11 21:12:56 eolson Exp $"
__docformat__ = "restructuredtext en"

import sys
import signal, time, os
import getopt

from AccessGrid import Log
from AccessGrid.AGNodeService import AGNodeService, AGNodeServiceI
from AccessGrid.hosting import Server

from AccessGrid.Platform import PersonalNode
from AccessGrid.Platform import GetUserConfigDir
from AccessGrid import Toolkit

# default arguments
port = 11000
logFile = os.path.join(GetUserConfigDir(), "agns.log")
identityCert = None
identityKey = None

def Shutdown():
    """
    This is used by the signal handler to shut down the node service.
    """
    global running
    global server
    server.Stop()
    # shut down the node service, saving config or whatever
    running = 0

# Signal handler to catch signals and shutdown
def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the VenueServer (and
    all of it's Venues. Then it stops the hostingEnvironment.
    """
    Shutdown()

# Authorization callback for globus
def AuthCallback(server, g_handle, remote_user, context):
    """
    The Authorization callback implements null auth, none.
    """
    return 1

# Print usage
def Usage():
    """
    Print out how to run this program.
    """
    print "%s:" % sys.argv[0]
    print """
    -h|--help : print usage
    -d|--debug <filename> : debug mode  - log to console as well as logfile
    -p|--port <int> : <port number to listen on>
    -l|--logFile <filename> : log file name
    --pnode <arg> : initialize as part of a Personal Node configuration
    --cert <filename>: identity certificate
    --key <filename>: identity certificate's private key
    """

# Parse command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "p:l:hd",
                               ["port=", "logfile=", "debug", "pnode=",
                               "help", "key=", "cert="])
except getopt.GetoptError:
    Usage()
    sys.exit(2)

debugMode = 0
pnode = None
for o, a in opts:
    if o in ("-p", "--port"):
        port = int(a)
    elif o in ("-d", "--debug"):
        debugMode = 1
    elif o in ("-l", "--logfile"):
        logFile = a
    elif o == "--pnode":
        pnode = a
    elif o == "--key":
        identityKey = a
    elif o == "--cert":
        identityCert = a
    elif o in ("-h", "--help"):
        Usage()
        sys.exit(0)

if pnode is not None:

    #log.debug("Starting personal node")

    personalNode = PersonalNode.PN_NodeService(Shutdown)
    serviceManagerURL =  personalNode.RunPhase1(pnode)

    #log.debug("Got service mgr %s", serviceManagerURL)

else:
    if identityCert is not None or identityKey is not None:
        #
        # Sanity check on identity cert stuff
        #

        if identityCert is None or identityKey is None:
            #log.critical("Both a certificate and key must be provided")
            print "Both a certificate and key must be provided"
            sys.exit(0)
            
        #
        # Init toolkit with explicit identity.
        #

        app = Toolkit.ServiceApplicationWithIdentity(identityCert, identityKey)

    else:
        #
        # Init toolkit with standard environment.
        #

        app = Toolkit.CmdlineApplication()

    app.InitGlobusEnvironment()

# Start up the logging
log = Log.GetLogger(Log.NodeService)
hdlr = Log.handlers.RotatingFileHandler(logFile, "a", 10000000, 0)
hdlr.setLevel(Log.DEBUG)
fmt = Log.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
hdlr.setFormatter(fmt)
Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())
if debugMode:
    Log.HandleLoggers(Log.StreamHandler(), Log.GetDefaultHandlers())


# Create a Node Service
nodeService = AGNodeService()

# Load default configuration if --personal node option is set
try:
    nodeService.LoadDefaultConfig()
except:
    log.debug("Failed to load default node configuration")

# Create a hosting environment
server = Server( ('localhost',port))

# Create the Node Service Service
nsi = AGNodeServiceI(nodeService)
server.RegisterObject(nsi, path="/NodeService")
url = server.GetURLForObject(nodeService)

#
# If we are starting as a part of a personal node,
# initialize that state.
#

if pnode is not None:

    log.debug("Starting personal node, phase 2")

    personalNode.RunPhase2(nodeService.GetHandle())

    log.debug("Personal node done")

# Tell the world where to find the service
log.info("Starting service; URI: %s", url)

# Register a signal handler so we can shut down cleanly
try:
    signal.signal(signal.SIGINT, SignalHandler)
except SystemError, v:
    log.exception(v)

# Run the service
server.RunInThread()

print "AGNodeService URL: ", url

# Keep the main thread busy so we can catch signals
running = 1
while running:
    time.sleep(1)

# Exit cleanly
nodeService.Stop()
server.Stop()

