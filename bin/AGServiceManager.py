#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        AGServiceManager.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGServiceManager.py,v 1.12 2003-03-14 17:55:33 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import sys
import signal, time, os
import logging, logging.handlers
import getopt

from AccessGrid.AGServiceManager import AGServiceManager
from AccessGrid.hosting.pyGlobus.Server import Server

# default arguments
port = 12000
logFile = "./agsm.log"

# Signal handler to shut down cleanly
def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the VenueServer (and
    all of it's Venues. Then it stops the hostingEnvironment.
    """
    global running
    global server
    server.stop()
    # shut down the node service, saving config or whatever
    running = 0

# Authorization callback for Globus security
def AuthCallback(server, g_handle, remote_user, context):
    return 1

# Print out the usage
def Usage():
    print "%s:" % sys.argv[0]
    print "    -h|--help : print usage"
    print "    -p|--port <int> : <port number to listen on>"
    print "    -l|--logFile <filename> : log file name"

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
    elif o in ("-h", "--help"):
        Usage()
        sys.exit(0)

# Start up the logging
log = logging.getLogger("AG.ServiceManager")
log.setLevel(logging.DEBUG)
hdlr = logging.handlers.RotatingFileHandler(logFile, "a", 10000000, 0)
fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
hdlr.setFormatter(fmt)
log.addHandler(hdlr)

# Create the Service Manager
serviceManager = AGServiceManager()

# Create the hosting environment
server = Server( port, auth_callback=AuthCallback )

# Create the Service Manager Service
service = server.CreateServiceObject("ServiceManager")
serviceManager._bind_to_service( service )

# Tell the world where to find the service manager
log.info("Starting service; URI: %s", serviceManager.get_handle())

# Register the signal handler so we can shut down cleanly
signal.signal(signal.SIGINT, SignalHandler)

# Start the service
server.run_in_thread()

# Keep the main thread busy so we can catch signals
running = 1
while running:
    time.sleep(1)

# Exit cleanly
os._exit(0)

