#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
# Author:      Ivan R. Judson
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.45 2004-03-10 23:17:09 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
This is the venue server program. This will run a venue server.
"""
__revision__ = "$Id: VenueServer.py,v 1.45 2004-03-10 23:17:09 eolson Exp $"
__docformat__ = "restructuredtext en"

import os
import sys
import getopt
import signal
import time
import threading

from AccessGrid import Log
from AccessGrid.Platform import isWindows

#
# Preload some stuff. This speeds up app startup drastically.
#
# Only do this on windows, Linux is fast enough as it is.
#

if isWindows():
    from pyGlobus import utilc, gsic, ioc
    from AccessGrid.Security import Utilities
    utilc.globus_module_activate(gsic.get_module())
    utilc.globus_module_activate(ioc.get_module())
    Utilities.CreateTCPAttrAlwaysAuth()

#
# Back to your normal imports.
#

from AccessGrid.hosting import Server
from AccessGrid.NetUtilities import GetHostname
from AccessGrid.VenueServer import VenueServer
from AccessGrid.Platform import GetUserConfigDir
from AccessGrid.Toolkit import CmdlineApplication

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
    global venueServer, log
    log.info("Caught signal, going down.")
    log.info("Signal: %d Frame: %s", signum, frame)

    venueServer.Shutdown()

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

    # Start up the logging
    log = Log.GetLogger(Log.VenueServer)
    hdlr = Log.handlers.RotatingFileHandler(logFile, "a", 10000000, 0)
    hdlr.setFormatter(Log.GetFormatter())
    hdlr.setLevel(Log.DEBUG)
    Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())

    # Add a warning level file
    warnLogFile = os.path.join(GetUserConfigDir(), "VenueServerWarn.log")
    #hdlr = Log.handlers.RotatingFileHandler(warnLogFile, "a", 10000000, 0)
    warn_hdlr = Log.FileHandler(warnLogFile)
    warn_hdlr.setFormatter(Log.GetFormatter())
    warn_hdlr.setLevel(Log.WARN)
    Log.HandleLoggers(warn_hdlr, Log.GetDefaultLoggers())


    if debugMode:
        hdlr = Log.StreamHandler()
        hdlr.setFormatter(Log.GetLowDetailFormatter())
        Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())

    # Init toolkit with standard environment.
    app = CmdlineApplication()

    app.Initialize()
    app.InitGlobusEnvironment()

    me = app.GetDefaultIdentityDN()
    hostname = GetHostname()
    
    log.debug("VenueServer running as %s", me)

    # Second thing we do is create a hosting environment
    server = Server((hostname, port), debug = debugMode)
    
    # Then we create a VenueServer, giving it the hosting environment
    venueServer = VenueServer(server, configFile)

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
        print "Thread ", thrd

    # Exit cleanly


if __name__ == "__main__":
    main()
