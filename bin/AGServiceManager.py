#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        AGServiceManager.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGServiceManager.py,v 1.33 2004-03-12 21:19:23 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

# The standard imports
import sys
import signal, time, os
import getopt

if sys.version.startswith('2.2'):
    try:
        from optik import OptionParser
    except:
        raise Exception, "Missing module optik necessary for the AG Toolkit."

if sys.version.startswith('2.3'):
    try:
        from optparse import OptionParse
    except:
        raise Exception, "Missing module optparse, check your python installation."

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
    
def main():
    """
    """
    global serviceManager, log

    # build options for this application
    parser = OptionParser()
    parser.add_option("-p", "--port", type="int", dest="port",
                      default=12000, metavar="PORT",
                      help="Set the port the service manager should run on.")
    parser.add_option("--pnode", dest="pnode", metavar="PNODE_TOKEN",
                      help="Personal node rendezvous token.")
    
    app = CmdlineApplication()

    app.SetOptionParser(parser)
    
    try:
        args = app.Initialize(sys.argv[1:], "ServiceManager")
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)

    log = app.GetLog()
    pnode = app.GetOption("pnode")
    port = app.GetOption("port")
        
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
        personalNode = PersonalNode.PN_ServiceManager(url, serviceManager.Shutdown)
        personalNode.Run(pnode)

    # Register the signal handler so we can shut down cleanly
    signal.signal(signal.SIGINT, SignalHandler)
    if isLinux():
        signal.signal(signal.SIGHUP, SignalHandler)

    # Start the service
    server.RunInThread()

    # Tell the world where to find the service manager
    log.info("Starting Service Manager URI: %s", url)

    # Keep the main thread busy so we can catch signals
    running = 1
    while running:
        time.sleep(1)

    # Exit cleanly
    server.Stop()
    sys.exit(0)
    
if __name__ == "__main__":
    main()
