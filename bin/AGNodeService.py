#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        AGNodeService.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGNodeService.py,v 1.40 2004-03-12 05:23:12 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
This is the Node Service for an AG Node.
"""
__revision__ = "$Id: AGNodeService.py,v 1.40 2004-03-12 05:23:12 judson Exp $"
__docformat__ = "restructuredtext en"

# The standard imports
import sys
import signal, time, os
import getopt

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
    
    server.Stop()

    running = 0

# Print usage
def Usage(agtk):
    """
    Print out how to run this program.
    """
    print "USAGE %s:" % os.path.split(sys.argv[0])[1]

    print " Toolkit Options:"
    agtk.Usage()

    print " Node Service Specific Options:"
    print "\t-p|--port <int> : <port number to listen on>"
    print "\t--pnode <arg> : Run as part of a Personal Node"

def ProcessArgs(app, argv):
    """
    """
    global log
    
    options = dict()
    
    # Parse command line options
    try:
        opts, args = getopt.getopt(argv, "p:", ["port=", "pnode="])
    except getopt.GetoptError, e:
        log.exception("Exception processing cmdline args:", e)
        Usage(app)
        sys.exit(2)
        
    for opt, arg in opts:
        if opt in ("-p", "--port"):
            port = int(arg)
            options['port'] = port
            options['p'] = port
        elif opt  == "--pnode":
            pnode = arg
            options['pnode'] = pnode

    if app.GetCmdlineArg('help') or app.GetCmdlineArg('h'):
        Usage(app)
        sys.exit(0)

    return options

def main():
    """
    """
    global nodeService, log

    #defaults
    port = 11000

    app = CmdlineApplication()
    try:
        args = app.Initialize(sys.argv[1:], "NodeService")
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)

    log = app.GetLog()

    options = ProcessArgs(app, args)

    if options.has_key('pnode'):
        pnode = options['pnode']
    else:
        pnode = None

    if options.has_key('port'):
        port = options['port']

    if options.has_key('p'):
        port = options['p']
        
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

    print "AGNodeService URL: ", url

    # Keep the main thread busy so we can catch signals
    running = 1
    while running:
        time.sleep(1)

    # Exit cleanly
    nodeService.Stop()
    server.Stop()
    sys.exit(0)
    
if __name__ == "__main__":
    main()
    
