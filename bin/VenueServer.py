#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
# Author:      Ivan R. Judson
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.31 2003-08-12 20:57:24 olson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import os
import sys
import getopt
import signal
import time
import logging, logging.handlers
import threading

#
# Preload some stuff. This speeds up app startup drastically.
#

from pyGlobus import utilc, gsic, ioc
from AccessGrid.hosting.pyGlobus import Utilities
utilc.globus_module_activate(gsic.get_module())
utilc.globus_module_activate(ioc.get_module())
Utilities.CreateTCPAttrAlwaysAuth()

#
# Back to your normal imports.
#

from AccessGrid.hosting.pyGlobus import Server, ServiceBase
from AccessGrid.VenueServer import VenueServer
from AccessGrid.Platform import GPI
from AccessGrid import Toolkit

# defaults
log = None
venueServer = None

hostingEnvironment = None
venueServer = None

# Signal Handler for clean shutdown
def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the VenueServer (and
    all of it's Venues. 
    """
    global venueServer
    print "Got Signal!!!!"
    venueServer.Shutdown()

# Authorization callback for the server
def AuthCallback(server, g_handle, remote_user, context):
    global log
    log.debug("Server gets identity %s", remote_user)
    return 1

def Usage():
    print "%s:" % sys.argv[0]
    print "    -h|--help : print usage"
    print "    -p|--port <int> : <port number to listen on>"
    print "    -l|--logFile <filename> : log file name"
    print "    -c|--configFile <filename> : config file name"
    print "    --cert <filename>: identity certificate"
    print "    --key <filename>: identity certificate's private key"

def main():

    global venueServer, log

    # defaults
    port = 8000
    configFile = None
    logFile = "VenueServer.log"
    identityCert = None
    identityKey = None

    # Parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:l:c:hd",
                                   ["port=", "logfile=", "configfile=",
                                    "help", "debug", "key=", "cert="])
    except getopt.GetoptError:
        Usage()
        sys.exit(2)

    debugMode = 0

    for o, a in opts:
        if o in ("-p", "--port"):
            port = int(a)
        elif o in ("-d", "--debug"):
            debugMode = 1
        elif o in ("-l", "--logfile"):
            logFile = a
        elif o in ("-c", "--configFile"):
            configFile = a
        elif o == "--key":
            identityKey = a
        elif o == "--cert":
            identityCert = a
        elif o in ("-h", "--help"):
            Usage()
            sys.exit(0)

    # Start up the logging
    log = logging.getLogger("AG")
    log.setLevel(logging.DEBUG)
    hdlr = logging.handlers.RotatingFileHandler(logFile, "a", 10000000, 0)
    extfmt = logging.Formatter("%(asctime)s %(thread)s %(name)s %(filename)s:%(lineno)s %(levelname)-5s %(message)s", "%x %X")
    fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
    hdlr.setFormatter(extfmt)
    log.addHandler(hdlr)

    if debugMode:
        hdlr = logging.StreamHandler()
        hdlr.setFormatter(fmt)
        log.addHandler(hdlr)

    if identityCert is not None or identityKey is not None:
        # Sanity check on identity cert stuff
        if identityCert is None or identityKey is None:
            log.critical("Both a certificate and key must be provided")
            print "Both a certificate and key must be provided"
            sys.exit(0)

        # Init toolkit with explicit identity.
        app = Toolkit.ServiceApplicationWithIdentity(identityCert, identityKey)

    else:
        # Init toolkit with standard environment.
        app = Toolkit.CmdlineApplication()

    app.Initialize()
    app.InitGlobusEnvironment()

    me = app.GetDefaultIdentityDN()
    log.debug("VenueServer running as %s", me)

    # Second thing we do is create a hosting environment
    hostingEnvironment = Server.Server(port, auth_callback=AuthCallback)

    # Then we create a VenueServer, giving it the hosting environment
    venueServer = VenueServer(hostingEnvironment, configFile)

    # We register signal handlers for the VenueServer. In the event of
    # a signal we just try to shut down cleanly.n
    signal.signal(signal.SIGINT, SignalHandler)
    signal.signal(signal.SIGTERM, SignalHandler)

    log.debug("Starting Hosting Environment.")

    # We start the execution
    hostingEnvironment.RunInThread()

    # We run in a stupid loop so there is still a main thread
    # We might be able to simply join the hostingEnvironmentThread, but
    # we have to be able to catch signals.
    while hostingEnvironment.IsRunning():
        time.sleep(1)

    log.debug("After main loop!")

    # Stop the hosting environment
    hostingEnvironment.Stop()

    log.debug("Stopped Hosting Environment, exiting.")

    for t in threading.enumerate():
        print "Thread ", t

    # Exit cleanly


if __name__ == "__main__":
    main()
