#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
# Author:      Ivan R. Judson
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.38 2004-02-19 17:59:02 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
This is the venue server program. This will run a venue server.
"""
__revision__ = "$Id: VenueServer.py,v 1.38 2004-02-19 17:59:02 eolson Exp $"
__docformat__ = "restructuredtext en"

import os
import sys
import getopt
import signal
import time
from AccessGrid.hosting.pyGlobus import Server
import logging, logging.handlers
import threading

#
# Preload some stuff. This speeds up app startup drastically.
#
# Only do this on windows, Linux is fast enough as it is.
#

if sys.platform == "win32":

    from pyGlobus import utilc, gsic, ioc
    from AccessGrid.hosting.pyGlobus import Utilities
    utilc.globus_module_activate(gsic.get_module())
    utilc.globus_module_activate(ioc.get_module())
    Utilities.CreateTCPAttrAlwaysAuth()

#
# Back to your normal imports.
#

from AccessGrid.VenueServer import VenueServer
from AccessGrid.Platform import GetUserConfigDir
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
    """
    This is the authorization callback for globus. It's effectively
    allowing all calls.
    """
    global log
    log.debug("Server gets identity %s", remote_user)
    return 1

def Usage():
    """
    This is the usage method, it prints out how to use this program.
    """
    print "%s:" % sys.argv[0]
    print "    -h|--help : print usage"
    print "    -p|--port <int> : <port number to listen on>"
    print "    -l|--logFile <filename> : log file name"
    print "    -c|--configFile <filename> : config file name"

def main():
    """
    The main routine of this program.
    """
    global venueServer, log, hostingEnvironment, log

    # defaults
    port = 8000
    configFile = None
    logFile = os.path.join(GetUserConfigDir(), "VenueServer.log")
    identityCert = None
    identityKey = None

    # Parse command line options
    try:
        opts = getopt.getopt(sys.argv[1:], "p:l:c:hd",
                                ["port=", "logfile=", "configfile=",
                                "help", "debug", "key=", "cert="])[0]
    except getopt.GetoptError:
        Usage()
        sys.exit(2)

    debugMode = 0
    certWarn = 0

    for opt, arg in opts:
        if opt in ("-p", "--port"):
            port = int(arg)
        elif opt in ("-d", "--debug"):
            debugMode = 1
        elif opt in ("-l", "--logfile"):
            logFile = arg
        elif opt in ("-c", "--configFile"):
            configFile = arg
        elif opt == "--key":
            certWarn = 1
        elif opt == "--cert":
            certWarn = 1
        elif opt in ("-h", "--help"):
            Usage()
            sys.exit(0)

    if certWarn:
        print ""
        print "The --cert/--key options are no longer used. To accomplish"
        print "the same effect, start the venue client, bring up the"
        print "identity certificate browser, and import an identity"
        print "certifiate that has an unencrypted private key."
        print""
        Usage()
        sys.exit(0)

    if identityCert is not None or identityKey is not None:
        # Sanity check on identity cert stuff
        if identityCert is None or identityKey is None:
            print "Both a certificate and key must be provided"
            sys.exit(0)

        # Init toolkit with explicit identity.
        app = Toolkit.ServiceApplicationWithIdentity(identityCert, identityKey)

    else:
        # Init toolkit with standard environment.
        app = Toolkit.CmdlineApplication()

    app.Initialize()
    app.InitGlobusEnvironment()

    # Start up the logging
    log = logging.getLogger("AG")
    log.setLevel(logging.DEBUG)
    hdlr = logging.handlers.RotatingFileHandler(logFile, "a", 10000000, 0)
    extfmt = logging.Formatter("%(asctime)s %(thread)s %(name)s \
    %(filename)s:%(lineno)s %(levelname)-5s %(message)s", "%x %X")
    fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
    hdlr.setFormatter(extfmt)
    log.addHandler(hdlr)

    if debugMode:
        hdlr = logging.StreamHandler()
        hdlr.setFormatter(fmt)
        log.addHandler(hdlr)

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

    for thrd in threading.enumerate():
        print "Thread ", thrd

    # Exit cleanly


if __name__ == "__main__":
    main()
