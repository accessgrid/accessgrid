#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
# Author:      Ivan R. Judson
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.3 2003-01-30 01:17:03 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import os
import sys
import signal
import time

from AccessGrid.hosting.pyGlobus import Server, ServiceBase
from AccessGrid.VenueServer import VenueServer

running = 0

def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the VenueServer (and
    all of it's Venues. Then it stops the hostingEnvironment.
    """
    global running
    venueServer.Shutdown(None, 0)
    running = 0

port = 8000
if len(sys.argv)>1:
    port = int(sys.argv[1])

# First thing we do is create a hosting environment
hostingEnvironment = Server.Server(port)

# Then we create a VenueServer, giving it the hosting environment
venueServer = VenueServer(hostingEnvironment)

# Then we create the VenueServer service
serviceObject = hostingEnvironment.create_service_object(pathId = 'VenueServer')
venueServer._bind_to_service(serviceObject)

# Some simple output to advertise the location of the service
print "Service running at: %s" % venueServer.get_handle()

# We register signal handlers for the VenueServer. In the event of
# a signal we just try to shut down cleanly.
signal.signal(signal.SIGINT, SignalHandler)
signal.signal(signal.SIGBREAK, SignalHandler)
signal.signal(signal.SIGTERM, SignalHandler)

# We start the execution
hostingEnvironment.run_in_thread()

running = 1
while running:
    time.sleep(1)
  
# Exit cleanly
os._exit(0)
