#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        AGNodeService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGNodeService.py,v 1.17 2003-04-23 19:37:16 olson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import sys
import signal, time, os
import logging, logging.handlers
import getopt

from AccessGrid.AGNodeService import AGNodeService
from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.Descriptions import AGServiceManagerDescription

from AccessGrid import PersonalNode

# default arguments
port = 11000
logFile = "./agns.log"

def Shutdown():
    global running
    global server
    server.stop()
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
    return 1

# Print usage
def Usage():
    print "%s:" % sys.argv[0]
    print "    -h|--help : print usage"
    print "    -d|--debug <filename> : debug mode  - log to console as well as logfile"
    print "    -p|--port <int> : <port number to listen on>"
    print "    -l|--logFile <filename> : log file name"
    print "    --pnode <arg> : initialize as part of a Personal Node configuration"

# Parse command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "p:l:hd",
                               ["port=", "logfile=", "debug", "pnode=", "help"])
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
    elif o in ("-h", "--help"):
        Usage()
        sys.exit(0)

# Start up the logging
log = logging.getLogger("AG")
log.setLevel(logging.DEBUG)
hdlr = logging.handlers.RotatingFileHandler(logFile, "a", 10000000, 0)
fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
hdlr.setFormatter(fmt)
log.addHandler(hdlr)
if debugMode:
    log.addHandler(logging.StreamHandler())

if pnode is not None:

    log.debug("Starting personal node")

    personalNode = PersonalNode.PN_NodeService(Shutdown)
    serviceManageURL =  personalNode.RunPhase1(pnode)

    log.debug("Got service mgr %s", serviceManageURL)

# Create a Node Service
nodeService = AGNodeService()

# Create a hosting environment
server = Server( port , auth_callback=AuthCallback )

# Create the Node Service Service
service = server.CreateServiceObject("NodeService")
nodeService._bind_to_service( service )

#
# If we are starting as a part of a personal node,
# initialize that state.
#

if pnode is not None:

    log.debug("Starting personal node, phase 2")

    personalNode.RunPhase2(nodeService.GetHandle())

    log.debug("Personal node done")

# Tell the world where to find the service
log.info("Starting service; URI: %s", nodeService.get_handle())

# Register a signal handler so we can shut down cleanly
signal.signal(signal.SIGINT, SignalHandler)

# Run the service
server.run_in_thread()

# Keep the main thread busy so we can catch signals
running = 1
while running:
    time.sleep(1)

# Exit cleanly
nodeService.Stop()
server.Stop()

