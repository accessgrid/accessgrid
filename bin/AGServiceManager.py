#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        AGServiceManager.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGServiceManager.py,v 1.30 2004-03-11 18:43:24 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
from AccessGrid.hosting import Server
import sys
import signal, time, os
import getopt

from AccessGrid import Log
from AccessGrid import Platform
from AccessGrid.AGServiceManager import AGServiceManager, AGServiceManagerI
from AccessGrid import PersonalNode
from AccessGrid import Toolkit

# default arguments
port = 12000
logFile = os.path.join(Platform.GetUserConfigDir(), "agsm.log")
identityCert = None
identityKey = None

def Shutdown():
    global running
    # shut down the service manager, saving config or whatever
    serviceManager.Shutdown()
    running = 0

# Signal handler to shut down cleanly
def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the VenueServer (and
    all of it's Venues. Then it stops the hostingEnvironment.
    """
    Shutdown()
    
# Authorization callback for Globus security
def AuthCallback(server, g_handle, remote_user, context):
    return 1

# Print out the usage
def Usage():
    print "%s:" % sys.argv[0]
    print "    -h|--help : print usage"
    print "    -p|--port <int> : <port number to listen on>"
    print "    -d|--debug <filename> : debug mode  - log to console as well as logfile"
    print "    -l|--logFile <filename> : log file name"
    print "    --pnode <arg> : initialize as part of a Personal Node configuration"
    print "    --daemonize : start as a daemon"
    print "    --cert <filename>: identity certificate"
    print "    --key <filename>: identity certificate's private key"

# Parse command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "p:l:hd",
                               ["port=", "logfile=", "help", "pnode=",
                                "debug", "daemonize", "key=", "cert="])
except getopt.GetoptError:
    Usage()
    sys.exit(2)

pnode = None
debugMode = 0
for o, a in opts:
    if o in ("-p", "--port"):
        port = int(a)
    elif o in ("-d", "--debug"):
        debugMode = 1
    elif o in ("-l", "--logfile"):
        logFile = a
    elif o == "--pnode":
        pnode = a
    elif o == "daemonize":
        Platform.Daemonize()
    elif o == "--key":
        identityKey = a
    elif o == "--cert":
        identityCert = a
    elif o in ("-h", "--help"):
        Usage()
        sys.exit(0)

# Create the hosting environment
server = Server( ('localhost',port))

# Create the Service Manager
serviceManager = AGServiceManager(server)

# Create the Service Manager Service
smi = AGServiceManagerI(serviceManager)
server.RegisterObject(smi,path="/ServiceManager")
url = server.GetURLForObject(serviceManager)

#
# If we are starting as a part of a personal node,
# initialize that state.
#

if pnode is not None:
    def getMyURL(url = url):
        return url

    personalNode = PersonalNode.PN_ServiceManager(getMyURL, Shutdown)
    personalNode.Run(pnode)
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
log = Log.GetLogger(Log.ServiceManager)
hdlr = Log.handlers.RotatingFileHandler(logFile, "a", 10000000, 0)
hdlr.setLevel(Log.DEBUG)
fmt = Log.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
hdlr.setFormatter(fmt)
Log.HandleLoggers(hdlr, Log.GetDefaultHandlers())
if debugMode:
    Log.HandleLoggers(Log.StreamHandler(), Log.GetDefaultHandlers())





# Register the signal handler so we can shut down cleanly
signal.signal(signal.SIGINT, SignalHandler)
if sys.platform == Platform.LINUX:
    signal.signal(signal.SIGHUP, SignalHandler)

# Start the service
server.RunInThread()

# Tell the world where to find the service manager
log.info("Starting service; URI: %s", url)
print "AGServiceManager URL: ", url

# Keep the main thread busy so we can catch signals
running = 1
while running:
    time.sleep(1)

# Exit cleanly
server.Stop()

