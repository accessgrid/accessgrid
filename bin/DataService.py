#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        DataService.py
# Purpose:     This data service provides persistent storage for venues.
#
# Author:      Susanne Lefvert, Robert D. Olson
#
# Created:     2002/12/12
# RCS-ID:      $Id: DataService.py,v 1.6 2003-09-22 14:21:53 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
This program is the data storage service.
"""
__revision__ = "$Id: DataService.py,v 1.6 2003-09-22 14:21:53 judson Exp $"

import os
import sys
import signal
import getopt
import logging, logging.handlers

from AccessGrid.DataStore import DataService
from AccessGrid import Toolkit
from AccessGrid.Platform import GetUserConfigDir

dataService = None

# Signal handler to catch signals and shutdown
def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the DataService
    """
    print "Shutting down..."
    dataService.Shutdown()


def main():
    """
    This is the main routine.
    """
    global dataService

    path = 'DATA'
    dataPort = 8886
    servicePort = 8500
    logFile = os.path.join(GetUserConfigDir(), "DataService.log")
    debugMode = 0

    try:
        opts = getopt.getopt(sys.argv[1:], "l:d:s:h",
                             ["location=", "dataPort=",
                              "servicePort=", "help"])[0]
    except getopt.GetoptError:
        Usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-l", "--location"):
            path = arg
        elif opt in ("-d", "--dataPort"):
            dataPort = int(arg)
        elif opt in ("-s", "--servicePort"):
            servicePort = int(arg)
        elif opt in ("-h", "--help"):
            Usage()
            sys.exit(0)
        else:
            Usage()
            sys.exit(0)

    app = Toolkit.CmdlineApplication()
    app.InitGlobusEnvironment()

    # Start up the logging
    log = logging.getLogger("AG")
    log.setLevel(logging.DEBUG)
    hdlr = logging.handlers.RotatingFileHandler(logFile, "a", 10000000, 0)
    extfmt = logging.Formatter("%(asctime)s %(thread)s %(name)s \
    %(filename)s:%(lineno)s %(levelname)-5s %(message)s", "%x %X")
    fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s",
                            "%x %X")
    hdlr.setFormatter(extfmt)
    log.addHandler(hdlr)
    if debugMode:
        hdlr = logging.StreamHandler()
        hdlr.setFormatter(fmt)
        log.addHandler(hdlr)

    # Register a signal handler so we can shut down cleanly
    signal.signal(signal.SIGINT, SignalHandler)

    dataService = DataService(path, dataPort, servicePort)

    import time
    while dataService.IsRunning():
        time.sleep(1)

    os._exit(1)

def Usage():
    """
    This tells you how to use the program, to get it run with -h.
    """
    print "%s:" % (sys.argv[0])
    print "  --help: Print usage"
    print "  -l|--location: Base path for data storage"
    print "  -d|--dataPort: Port used for data communication"
    print "  -s|--servicePort: Port used for SOAP interface"


if __name__ == "__main__":
    """
    The main block.
    """
    main()
