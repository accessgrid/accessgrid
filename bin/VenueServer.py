#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
# Author:      Ivan R. Judson
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.46 2004-03-12 05:23:13 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
This is the venue server program. This will run a venue server.
"""
__revision__ = "$Id: VenueServer.py,v 1.46 2004-03-12 05:23:13 judson Exp $"
__docformat__ = "restructuredtext en"

# The standard imports
import os
import sys
import getopt
import signal
import time
import threading

# Our imports
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.VenueServer import VenueServer
from AccessGrid import Log
from AccessGrid.hosting import Server

# Global defaults
log = None
venueServer = None

# Signal Handler for clean shutdown
def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the VenueServer (and
    all of it's Venues. 
    """
    global venueServer, log
    log.info("Caught signal, going down.")
    log.info("Signal: %d Frame: %s", signum, frame)

    venueServer.Shutdown()

def Usage(agtk):
    """
    This is the usage method, it prints out how to use this program.
    """
    print "USAGE: %s:" % os.path.split(sys.argv[0])[1]

    print " Toolkit Options:"
    agtk.Usage()

    print " VenueServer Specific Options:"
    print "\t-p|--port <int> : <port number to listen on>"
    print "\t-h|--help : print usage"

def ProcessArgs(app, argv):
    """
    """
    options = dict()
    
    # Parse command line options
    try:
        opts = getopt.getopt(argv, "p:l:c:hd", ["port="])[0]
    except getopt.GetoptError:
        Usage(app)
        sys.exit(2)
        
    for opt, arg in opts:
        if opt in ("-p", "--port"):
            port = int(arg)
            options['port'] = port
            options['p'] = port
        else:
            Usage(app)
            sys.exit(0)
            

    if app.GetCmdlineArg('help') or app.GetCmdlineArg('h'):
        Usage(app)
        sys.exit(0)

    return options
        
def main():
    """
    The main routine of this program.
    """
    global venueServer, log

    # defaults
    port = 8000

    # Init toolkit with standard environment.
    app = CmdlineApplication()

    # Try to initialize
    try:
        args = app.Initialize(sys.argv, "VenueServer")
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)

    # Process the rest of the cmd line args
    options = ProcessArgs(app, args)

    # Get the Log
    log = app.GetLog()

    if options.has_key('port') or options.has_key('p'):
        port = options['port']
    else:
        log.warn("Using default port: %d", port)

    # Second thing we do is create a hosting environment
    hostname = SystemConfig.instance().GetHostname()
    server = Server((hostname, port), debug = app.GetDebugLevel())
    
    # Then we create a VenueServer, giving it the hosting environment
    venueServer = VenueServer(server, app.GetCmdlineArg('configFile'))

    # We register signal handlers for the VenueServer. In the event of
    # a signal we just try to shut down cleanly.n
    signal.signal(signal.SIGINT, SignalHandler)
    signal.signal(signal.SIGTERM, SignalHandler)

    log.debug("Starting Hosting Environment.")

    # We start the execution
    server.RunInThread()

    # We run in a stupid loop so there is still a main thread
    # We might be able to simply join the hostingEnvironmentThread, but
    # we have to be able to catch signals.
    while server.IsRunning():
        time.sleep(1)

    log.debug("After main loop!")

    # Stop the hosting environment
    server.Stop()

    log.debug("Stopped Hosting Environment, exiting.")

    for thrd in threading.enumerate():
        log.debug("Thread ", thrd)

    # Exit cleanly
    sys.exit(0)
    
if __name__ == "__main__":
    main()
