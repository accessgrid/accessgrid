#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
# Author:      Ivan R. Judson
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.14 2003-03-21 18:04:29 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import os
import sys
import getopt
import signal
import time
import logging, logging.handlers
import threading

from AccessGrid.hosting.pyGlobus import Server, ServiceBase
from AccessGrid.VenueServer import VenueServer

# defaults
running = 0
port = 8000
configFile = None
logFile = "VenueServer.log"

# Signal Handler for clean shutdown
def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the VenueServer (and
    all of it's Venues. Then it stops the hostingEnvironment.
    """
    global running
    global venueServer
    print "Got Signal!!!!"
    venueServer.Shutdown(0)
    running = 0

# Authorization callback for the server
def AuthCallback(server, g_handle, remote_user, context):
    log.debug("Server gets identity ", remote_user)
    return 1

def Usage():
    print "%s:" % sys.argv[0]
    print "    -h|--help : print usage"
    print "    -p|--port <int> : <port number to listen on>"
    print "    -l|--logFile <filename> : log file name"
    print "    -c|--configFile <filename> : config file name"
    
# Parse command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "p:l:c:h",
                               ["port", "logfile", "configfile", "help"])
except getopt.GetoptError:
    Usage()
    sys.exit(2)

for o, a in opts:
    if o in ("-p", "--port"):
        port = int(a)
    elif o in ("-l", "--logfile"):
        logFile = a
    elif o in ("-c", "--configFile"):
        configFile = a
    elif o in ("-h", "--help"):
        Usage()
        sys.exit(0)

# Start up the logging
log = logging.getLogger("AG.VenueServer")
log.setLevel(logging.DEBUG)
hdlr = logging.handlers.RotatingFileHandler(logFile, "a", 10000000, 0)
fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
hdlr.setFormatter(fmt)
log.addHandler(hdlr)

# First thing we do is create a hosting environment
hostingEnvironment = Server.Server(port, auth_callback=AuthCallback)

# Then we create a VenueServer, giving it the hosting environment
venueServer = VenueServer(hostingEnvironment, configFile)

# Then we create the VenueServer service
serviceObject = hostingEnvironment.CreateServiceObject('VenueServer')
venueServer._bind_to_service(serviceObject)

# Some simple output to advertise the location of the service
print "Service running at: %s" % venueServer.GetHandle()

# We register signal handlers for the VenueServer. In the event of
# a signal we just try to shut down cleanly.n
signal.signal(signal.SIGINT, SignalHandler)
signal.signal(signal.SIGTERM, SignalHandler)

log.debug("Starting Hosting Environment.")
# We start the execution
hostingEnvironment.RunInThread()

# We run in a stupid loop so there is still a main thread
# We might be able to simply join the hostingEnvironmentThread, but
# we have to be able to catch signals.
running = 1
while running:
    time.sleep(1)

log.debug("After main loop!")

# Stop the hosting environment
hostingEnvironment.Stop()
  
log.debug("Stopped Hosting Environment, exiting.")

for t in threading.enumerate():
    print "Thread ", t
    
# Exit cleanly
#sys.exit(0)
os._exit(0)
