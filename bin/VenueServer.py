#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
# Author:      Ivan R. Judson
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.10 2003-02-27 20:13:54 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import os
import sys
import signal
import time
import logging, logging.handlers

from AccessGrid.hosting.pyGlobus import Server, ServiceBase
from AccessGrid.VenueServer import VenueServer

running = 0

def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the VenueServer (and
    all of it's Venues. Then it stops the hostingEnvironment.
    """
    global running
    venueServer.Shutdown(0)
    running = 0

def AuthCallback(server, g_handle, remote_user, context):
    log.debug("Server gets identity ", remote_user)
    return 1

port = 8000

# Once we have optik command line parsing we can make this more
# elegant and have perhaps
# -p port
# -l logfile
# -f configfile

if len(sys.argv) > 1:
    port = int(sys.argv[1])

configFile = None
if len(sys.argv) > 2:
    configFile = sys.argv[2]
    
logger = logging.getLogger("AG.VenueServer")
logger.setLevel(logging.DEBUG)
logname = "VenueServer.log"
hdlr = logging.handlers.RotatingFileHandler(logname, "a", 10000000, 0)
fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
hdlr.setFormatter(fmt)
logger.addHandler(hdlr)

# First thing we do is create a hosting environment
hostingEnvironment = Server.Server(port, auth_callback=AuthCallback)

# Then we create a VenueServer, giving it the hosting environment
venueServer = VenueServer(hostingEnvironment, configFile)

# Then we create the VenueServer service
serviceObject = hostingEnvironment.create_service_object(pathId = 'VenueServer')
venueServer._bind_to_service(serviceObject)

# Some simple output to advertise the location of the service
print "Service running at: %s" % venueServer.get_handle()

# We register signal handlers for the VenueServer. In the event of
# a signal we just try to shut down cleanly.
signal.signal(signal.SIGINT, SignalHandler)
#signal.signal(signal.SIGBREAK, SignalHandler)
signal.signal(signal.SIGTERM, SignalHandler)

# We start the execution
hostingEnvironment.run_in_thread()

running = 1
while running:
    time.sleep(1)
  
# Exit cleanly
os._exit(0)
