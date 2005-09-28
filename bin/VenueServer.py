#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
# Author:      Ivan R. Judson
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.65 2005-09-28 20:33:31 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
This is the venue server program. This will run a venue server.
"""
__revision__ = "$Id: VenueServer.py,v 1.65 2005-09-28 20:33:31 eolson Exp $"
__docformat__ = "restructuredtext en"

# The standard imports
import os
import sys
import signal
import time
import threading
from optparse import Option

# Our imports
from twisted.internet import reactor
from AccessGrid.Toolkit import Service
from AccessGrid.VenueServer import VenueServer
from AccessGrid import Log
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid.hosting import SecureServer, InsecureServer

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
    if reactor.running:
        reactor.stop()

def main():
    """
    The main routine of this program.
    """
    global venueServer, log

    # Init toolkit with standard environment.
    app = Service.instance()

    # build options for this application
    portOption = Option("-p", "--port", type="int", dest="port",
                        default=8000, metavar="PORT",
                        help="Set the port the service manager should run on.")

    app.AddCmdLineOption(portOption)
    
    # Try to initialize
    try:
        args = app.Initialize("VenueServer")
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)
        
    # Get the Log
    log = app.GetLog()
    port = app.GetOption("port")

    # Second thing we do is create a hosting environment
    hostname = app.GetHostname()
    log.info("VenueServer running using hostname: %s", hostname)
    
    if app.GetOption("secure"):
        server = SecureServer((hostname, port),
                              app.GetOption('cert'),
                              app.GetOption('key'),
                              app.GetOption('cadir'))
    else:
        server = InsecureServer((hostname, port))
    
    # Then we create a VenueServer, giving it the hosting environment
    venueServer = VenueServer(server, app.GetOption('configfilename'))

    # We register signal handlers for the VenueServer. In the event of
    # a signal we just try to shut down cleanly.n
    signal.signal(signal.SIGINT, SignalHandler)
    signal.signal(signal.SIGTERM, SignalHandler)

    log.debug("Starting Hosting Environment.")

    # We start the execution
    server.RunInThread()

    """
    # We run in a stupid loop so there is still a main thread
    # We might be able to simply join the hostingEnvironmentThread, but
    # we have to be able to catch signals.
    while server.IsRunning():
        try:
            time.sleep(0.5)
        except IOError, e:
            log.info("Sleep interrupted, exiting.")
    """
    reactor.run()
             
    log.debug("After main loop!")

    # Stop the hosting environment
    try:
        server.Stop()
        log.debug("Stopped Hosting Environment, exiting.")
    except:
        log.exception("Exception stopping server")

    time.sleep(1)
    for thrd in threading.enumerate():
        log.debug("Thread %s", thrd)

    # Exit cleanly
    sys.exit(0)
    
if __name__ == "__main__":
    main()
