#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        AGServiceManager.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGServiceManager.py,v 1.32 2004-03-12 05:23:12 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

# The standard imports
import sys
import signal, time, os
import getopt

# Our imports
from AccessGrid.hosting import Server
from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.Platform import PersonalNode, isLinux
from AccessGrid.Platform.Config import UserConfig, AGTkConfig, SystemConfig
from AccessGrid.AGServiceManager import AGServiceManager, AGServiceManagerI
from AccessGrid.Platform import PersonalNode
from AccessGrid import Toolkit

# default arguments
log = None
serviceManager = None
server = None

# Signal handler to shut down cleanly
def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the VenueServer (and
    all of it's Venues. Then it stops the hostingEnvironment.
    """
    global log, serviceManager, running

    log.info("Caught signal, going down.")
    log.info("Signal: %d Frame: %s", signum, frame)

    serviceManager.Shutdown()
    running = 0
    
# Print out the usage
def Usage(agtk):
    """
    """
    print "USAGE: %s:" % os.path.split(sys.argv[0])[1]

    print " Toolkit Options:"
    agtk.Usage()

    print " Service Manager Options:"
    
    print "\t-p|--port <int> : <port number to listen on>"
    print "\t--pnode <arg> : initialize as part of a Personal Node configuration"

def ProcessArgs(app, argv):
    """
    """
    options = dict()

    # Parse command line options
    try:
        opts, args = getopt.getopt(argv, "p:l:hd", ["port=", "pnode="])
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
    global serviceManager, log

    # defaults
    port = 12000

    app = CmdlineApplication()
    try:
        args = app.Initialize(sys.argv[1:], "ServiceManager")
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
        
    # Create the hosting environment
    hostname = SystemConfig.instance().GetHostname()
    server = Server((hostname, port))

    # Create the Service Manager
    serviceManager = AGServiceManager(server)

    # Create the Service Manager Service
    smi = AGServiceManagerI(serviceManager)
    server.RegisterObject(smi,path="/ServiceManager")
    url = server.GetURLForObject(serviceManager)

    # If we are starting as a part of a personal node,
    # initialize that state.

    if pnode is not None:
        def getMyURL(url = url):
            return url

        personalNode = PersonalNode.PN_ServiceManager(getMyURL,
                                                      serviceManager.Shutdown)
        print "PNODE: ", pnode
        personalNode.Run(pnode)

    # Register the signal handler so we can shut down cleanly
    signal.signal(signal.SIGINT, SignalHandler)
    if isLinux():
        signal.signal(signal.SIGHUP, SignalHandler)

    # Start the service
    server.RunInThread()

    # Tell the world where to find the service manager
    log.info("Starting service; URI: %s", url)
    print "AGServiceManager URL: ", url

    # Keep the main thread busy so we can catch signals
    running = 1
    while running:
        time.sleep(1)

    # Exit cleanly
    server.Stop()
    sys.exit(0)
    
if __name__ == "__main__":
    main()
