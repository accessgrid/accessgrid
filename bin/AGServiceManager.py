#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        AGServiceManager.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGServiceManager.py,v 1.43 2004-04-27 19:22:52 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

# The standard imports
import sys

if sys.platform=="darwin":
    # On osx pyGlobus/globus need to be loaded before various modules such as socket.
    import pyGlobus.ioc

import signal, time, os
from optparse import Option

# Our imports
from AccessGrid.hosting import SecureServer
from AccessGrid.Toolkit import Service
from AccessGrid.Platform import IsLinux
from AccessGrid.Platform.Config import AGTkConfig, SystemConfig
from AccessGrid.AGServiceManager import AGServiceManager, AGServiceManagerI
from AccessGrid.AGNodeService import AGNodeService, AGNodeServiceI

# default arguments
log = None
serviceManager = None
nodeService = None
server = None

# Signal handler to shut down cleanly
def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the VenueServer (and
    all of it's Venues. Then it stops the hostingEnvironment.
    """
    global log, serviceManager, nodeService, running

    log.info("Caught signal, going down.")
    log.info("Signal: %d Frame: %s", signum, frame)

    serviceManager.Shutdown()

    if nodeService is not None:
        nodeService.Stop()
        
    running = 0
    
def main():
    """
    """
    global serviceManager, nodeService, log, running

    # Create the app
    app = Service.instance()
    
    # build options for this application
    portOption = Option("-p", "--port", type="int", dest="port",
                        default=12000, metavar="PORT",
                        help="Set the port the service manager should run on.")
    app.AddCmdLineOption(portOption)

    nsOption = Option("-n", "--nodeService", action="store_true", dest="ns",
                        help="Run a node service interface too.")
    app.AddCmdLineOption(nsOption)
    
    # Initialize the application
    try:
        args = app.Initialize("ServiceManager")
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)

    log = app.GetLog()
    port = app.GetOption("port")
        
    # Create the hosting environment
    hostname = app.GetHostname()
    server = SecureServer((hostname, port))

    # Create the Service Manager
    serviceManager = AGServiceManager(server)

    # Create the Service Manager Service
    smi = AGServiceManagerI(serviceManager)
    server.RegisterObject(smi,path="/ServiceManager")
    url = server.FindURLForObject(serviceManager)

    if app.GetOption("ns") is not None:
        # Create a Node Service
        nodeService = AGNodeService()
        # Create the Node Service Service
        nsi = AGNodeServiceI(nodeService)
        server.RegisterObject(nsi, path="/NodeService")
        url = server.FindURLForObject(nodeService)
    
    # Register the signal handler so we can shut down cleanly
    signal.signal(signal.SIGINT, SignalHandler)

    if IsLinux():
        signal.signal(signal.SIGHUP, SignalHandler)

    # Start the service
    server.RunInThread()

    # Tell the world where to find the service manager
    log.info("Starting Service Manager URI: %s", server.GetURLBase())

    # Keep the main thread busy so we can catch signals
    running = 1
    while running:
        time.sleep(1)

    # Exit cleanly
    server.Stop()
    sys.exit(0)
    
if __name__ == "__main__":
    main()
