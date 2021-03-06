#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
# Author:      Ivan R. Judson
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.78 2007-10-24 22:55:42 willing Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
This is the venue server program. This will run a venue server.
"""
__revision__ = "$Id: VenueServer.py,v 1.78 2007-10-24 22:55:42 willing Exp $"
__docformat__ = "restructuredtext en"

# The standard imports
import os
import sys
import signal
import time
import threading
from optparse import Option

# Our imports
try:
    from twisted.internet import _threadedselect as threadedselectreactor
except:
    from twisted.internet import threadedselectreactor
threadedselectreactor.install()
import twisted
from twisted.internet import reactor
from AccessGrid.Toolkit import Service, MissingDependencyError
from AccessGrid.VenueServer import VenueServer
from AccessGrid import Log
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid.hosting import SecureServer, InsecureServer
from AccessGrid import Toolkit
from AccessGrid.Security import CertificateManager

from M2Crypto import threading as M2Crypto_threading

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
    
    import threading
    M2Crypto_threading.init()

    # Init toolkit with standard environment.
    app = Service.instance()

    # build options for this application
    portOption = Option("-p", "--port", type="int", dest="port",
                        default=8000, metavar="PORT",
                        help="Set the port the service manager should run on.")

    app.AddCmdLineOption(portOption)
    
    # set default options
    app.SetCmdLineDefault('secure',1)
    
    # Try to initialize
    try:
        args = app.Initialize("VenueServer")
    except MissingDependencyError, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: Missing Dependency: ", e
        sys.exit(-1)
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
        log.info('Running in secure mode')
        context = Toolkit.Service.instance().GetContext()
        server = SecureServer((hostname, port),
                              context)
    else:
        log.info('Running in insecure mode')
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

    
    if twisted.version.major < 8:
        reactor.run()
    else:
        # with Twisted 8, threadedselectreactor is not a directly usable
        #   reactor; it is only meant to help in writing other reactors
        #   http://twistedmatrix.com/trac/ticket/2126
        from AccessGrid.TwistedManager import TwistedManager, fakeDeferred
        m = TwistedManager()
        m.start()
        
        #while server.IsRunning():
        #    m.poll(0.05)

        #while server.IsRunning():
        #    res = m.getDeferred(fakeDeferred("got it!"))

        while server.IsRunning():
            time.sleep(0.05)

             
    log.debug("After main loop!")

    # Stop the hosting environment
    try:
        server.Stop()
        log.debug("Stopped Hosting Environment, exiting.")
    except:
        log.exception("Exception stopping server")

    M2Crypto_threading.cleanup()


    time.sleep(1)
    for thrd in threading.enumerate():
        log.debug("Thread %s", thrd)

    # Exit cleanly
    sys.exit(0)
    
if __name__ == "__main__":
    import socket
    try:
        main()
    except socket.error,e:
        if e.args[0] == 98:
            msg = "Network error running server; an application is already running on one of the ports required"
            log.info(msg)
            print msg
        else:
            msg = "Network error running server; %s" % (e.args[1])
            log.info(msg)
            log.exception("Socket error")
            print msg
    except CertificateManager.NoCertificates,e:
        msg = """No certificate is available to start a secure server.  \n\
Please run the CertificateManager to request and retrieve \n\
a certificate before attempting to start the VenueServer again."""
        print msg
        log.exception('Attempt to start VenueServer without a certificate')
    except SystemExit, e:
        pass
    except Exception, e:
        print e
        msg = "Error occurred running server: %s" % (str(e))
        print msg
        log.exception(msg)
        
