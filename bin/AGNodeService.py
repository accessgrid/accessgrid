#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        AGNodeService.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGNodeService.py,v 1.43 2004-03-15 20:53:16 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
This is the Node Service for an AG Node.
"""
__revision__ = "$Id: AGNodeService.py,v 1.43 2004-03-15 20:53:16 eolson Exp $"
__docformat__ = "restructuredtext en"

# The standard imports
import sys
import signal, time, os

if sys.version.startswith('2.2'):
    try:
        from optik import Option
    except:
        raise Exception, "Missing module optik necessary for the AG Toolkit."

if sys.version.startswith('2.3'):
    try:
        from optparse import Option
    except:
        raise Exception, "Missing module optparse, check your python installation."


# Our imports
from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.AGNodeService import AGNodeService, AGNodeServiceI
from AccessGrid import Log
from AccessGrid.Platform import PersonalNode
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid.hosting import Server

# default arguments
log = None
nodeService = None
server = None

# Signal handler for clean shutdown
def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the VenueServer (and
    all of it's Venues. Then it stops the hostingEnvironment.
    """
    global log, server, running

    log.info("Caught signal, going down.")
    log.info("Signal: %d Frame: %s", signum, frame)
    
    if server != None:
        server.Stop()

    running = 0

def main():
    """
    """
    global nodeService, log

    # Instantiate the app
    app = CmdlineApplication()

    # build options for this application
    portOption = Option("-p", "--port", type="int", dest="port",
                        default=12000, metavar="PORT",
                        help="Set the port the service manager should run on.")
    app.AddCmdLineOption(portOption)
    
    pnodeOption = Option("--pnode", dest="pnode", metavar="PNODE_TOKEN",
                         help="Personal node rendezvous token.")
    app.AddCmdLineOption(pnodeOption)    

    # Initialize the app
    try:
        args = app.Initialize(sys.argv[1:], "NodeService")
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)

    log = app.GetLog()
    pnode = app.GetOption("pnode")
    port = app.GetOption("port")
        
    # Create a Node Service
    nodeService = AGNodeService()

    if pnode is not None:
        log.debug("Starting personal node")
        personalNode = PersonalNode.PN_NodeService(nodeService.Stop())
        serviceManagerURL =  personalNode.RunPhase1(pnode)
        log.debug("Got service mgr %s", serviceManagerURL)

    # Load default configuration if --personal node option is set
    try:
        nodeService.LoadDefaultConfig()
    except:
        log.debug("Failed to load default node configuration")

    # Create a hosting environment
    hostname = SystemConfig.instance().GetHostname()
    server = Server((hostname, port), debug = app.GetDebugLevel())
    
    # Create the Node Service Service
    nsi = AGNodeServiceI(nodeService)
    server.RegisterObject(nsi, path="/NodeService")
    url = server.GetURLForObject(nodeService)

    # If we are starting as a part of a personal node,
    # initialize that state.
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

    log.info("Starting Node Service URL: %s", url)

    # Keep the main thread busy so we can catch signals
    global running
    running = 1
    while running:
        time.sleep(1)

    # Exit cleanly
    nodeService.Stop()
    server.Stop()
    sys.exit(0)
    
if __name__ == "__main__":
    main()
    
