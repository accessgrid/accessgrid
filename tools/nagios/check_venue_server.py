#!/usr/bin/python2

#
# VenueServer test plug-in for Nagios
#
# Tries to enter the specified venue
#
# Exit codes defined as follows:
# 0 - Enter success
# 1 - Something went wrong
# 2 - Enter failed
#
# It prints one line of text to describe the problem when
# exiting with status 1 or 2


import os
import sys
import threading
import time

from AccessGrid import Toolkit
from AccessGrid.hosting import Client
from AccessGrid.ClientProfile import ClientProfile

from optparse import Option

# nagios return codes
OK = 0
WARN = 1
CRITICAL = 2

privateId = None
retval = -1
retstring = ""
enteredFlag = threading.Event()
enteredFlag.clear()
warnFlag = threading.Event()
warnFlag.clear()
runningFlag = threading.Event()
runningFlag.clear()

# initialize app
app=Toolkit.Service()

app.AddCmdLineOption( Option("-v", "--venueUrl", type="string", dest="venueUrl",
                      default="https://localhost:8000/Venues/default",
                      metavar="VENUE_URL",
                      help="Set the url of the venue to enter"))
app.AddCmdLineOption( Option("-t", "--timeout", type="int", dest="timeout",
                      default=10,
                      metavar="TIMEOUT",
                      help="Set the timeout"))

app.Initialize('EnterVenue')

venueUrl = app.GetOption("venueUrl")
timeout = app.GetOption("timeout")

proxy = Client.SecureHandle(venueUrl).GetProxy()

log = app.GetLog()
# create client profile
profile = ClientProfile()
profile.SetName("nagios")


def Enter(venueUrl):
    # enter

    runningFlag.set()
    try:
        (state,privateId,streamDescList) = proxy.Enter(profile)
        enteredFlag.set()
    except:
        log.exception("Enter exception")
        runningFlag.clear()
        return

    # exit
    try:
        proxy.Exit(privateId)
    except:
        log.exception("Exit exception")
        warnFlag.set()
    runningFlag.clear()


th = threading.Thread(target=Enter, args = [ venueUrl ] )
th.start()

# wait for run to start
runningFlag.wait(timeout)

# wait for enter or timeout
if runningFlag.isSet():
    enteredFlag.wait(timeout)

# check status
if enteredFlag.isSet():
    retstring = "Reached venue"
    retval = OK
    if warnFlag.isSet():
        retval = WARN
        retstring = "Failed to exit venue %s" % (venueUrl,)
else:
    retval = CRITICAL
    retstring = "Failed to reach venue %s after %s seconds" % (venueUrl,timeout)

print retstring
sys.stdout.flush()
os._exit(retval)
