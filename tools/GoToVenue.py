#!/usr/bin/python2

import os
import sys

from AccessGrid.VenueClient import GetVenueClientUrls
from AccessGrid.VenueClient import VenueClientIW
from AccessGrid.Platform import isWindows
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.Toolkit import CmdlineApplication



if len(sys.argv) < 2:
    print "Usage: %s <venueUrl>" % (sys.argv[1])

venueUrl = sys.argv[1]

# Initialize
app = CmdlineApplication()
app.Initialize()


# Check for the venue client soap server url
venueClientUrlList = GetVenueClientUrls()

enteredVenue = 0
for venueClientUrl in venueClientUrlList:
    try:
        venueClient = VenueClientIW(venueClientUrl)
        venueClient._IsValid()

        # Enter the specified venue
        print "Sending venue client to venue..."
        venueClient.EnterVenue(venueUrl)
        enteredVenue = 1
        break
    except:
        pass
        enteredVenue = 0

if not enteredVenue:
    # Communicating with running venue client failed; 
    # launch the venue client, pointed at the specified venue
    print "Launching the venue client..."
    cmd = "VenueClient.py --url %s" % (venueUrl,)
    if not isWindows():
        cmd += " &"
    os.system(cmd)
