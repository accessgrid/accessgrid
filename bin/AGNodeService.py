#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        AGNodeService.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGNodeService.py,v 1.58 2004-07-26 14:44:33 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
This is the Node Service for an AG Node.
"""
__revision__ = "$Id: AGNodeService.py,v 1.58 2004-07-26 14:44:33 turam Exp $"

# The standard imports
import sys

if sys.platform=="darwin":
    # On osx pyGlobus/globus need to be loaded before various
    # modules such as socket.
    import pyGlobus.ioc

import signal, time, os
from optparse import Option

# Our imports
from AccessGrid import Log
from AccessGrid.Toolkit import Service
from AccessGrid.AGNodeService import AGNodeService, AGNodeServiceI
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid.hosting import SecureServer

# default arguments
log = None
nodeService = None
server = None
running = 0

# Signal handler for clean shutdown
def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the VenueServer (and
    all of it's Venues. Then it stops the hostingEnvironment.
    """
    global log, server, running, nodeService

    log.info("Caught signal, going down.")
    log.info("Signal: %d Frame: %s", signum, frame)
    
    if server != None:
        server.Stop()
        
    if nodeService: 
        nodeService.Stop()

    running = 0

def main():
    """
    """
    global nodeService, log, server

    # Instantiate the app
    app = Service().instance()

    # build options for this application
    portOption = Option("-p", "--port", type="int", dest="port",
                        default=11000, metavar="PORT",
                        help="Set the port the service manager should run on.")
    app.AddCmdLineOption(portOption)
    
    # Initialize the app
    try:
        app.Initialize("NodeService")
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)

    log = app.GetLog()
    Log.SetDefaultLevel(Log.NodeService, Log.DEBUG)

    port = app.GetOption("port")
        
    # Create a Node Service
    nodeService = AGNodeService(app=app)

    # Create a hosting environment
    hostname = app.GetHostname()
    server = SecureServer((hostname, port), debug = app.GetDebugLevel())
    
    # Create the Node Service Service
    nsi = AGNodeServiceI(nodeService)
    server.RegisterObject(nsi, path="/NodeService")
    url = server.FindURLForObject(nodeService)

    # Tell the world where to find the service
    log.info("Starting service; URI: %s", url)

    # Register a signal handler so we can shut down cleanly
    try:
        signal.signal(signal.SIGINT, SignalHandler)
    except SystemError, v:
        log.exception(v)

    # Run the service
    server.RunInThread()
    
    log.info("Starting Node Service URL: %s", url)
    print "Starting Node Service URL:", url

    # Load the default node config
    try:
        nodeService.LoadDefaultConfig()
    except:
        print "Error loading default node configuration"

    # Keep the main thread busy so we can catch signals
    global running
    running = 1
    while running:
        try:
            time.sleep(1)
        except IOError, e:
            log.info("Sleep interrupted, exiting.")

    # Exit cleanly
    nodeService.Stop()
    server.Stop()
    sys.exit(0)
    
if __name__ == "__main__":
    main()
    
