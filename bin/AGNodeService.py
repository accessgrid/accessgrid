#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        AGNodeService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGNodeService.py,v 1.7 2003-02-12 17:21:46 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import sys
import signal, time, os

from AccessGrid.AGNodeService import AGNodeService
from AccessGrid.hosting.pyGlobus.Server import Server


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


def AuthCallback(server, g_handle, remote_user, context):
    return 1

nodeService = AGNodeService()

# start the service
port = 11000
if len(sys.argv) > 1:
    port = int(sys.argv[1])
server = Server( port , auth_callback=AuthCallback )
service = server.create_service_object("NodeService")
nodeService._bind_to_service( service )
print "Starting service; URI: ", nodeService.get_handle()
server.run_in_thread()

signal.signal(signal.SIGINT, SignalHandler)

running = 1
while running:
    time.sleep(1)


# Exit cleanly
os._exit(0)

