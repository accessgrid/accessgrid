#!/usr/bin/python2

import os
import sys

from AccessGrid.VenueClient import GetVenueClientUrls
from AccessGrid.VenueClient import VenueClientIW
from AccessGrid.Platform import isWindows
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.Toolkit import CmdlineApplication



# Initialize
app = CmdlineApplication()
app.Initialize()


if len(sys.argv) > 1:
    # Use the provided venue client url
    venueClientUrlList = [ sys.argv[1] ]
else:
    # Search for a venue client url
    venueClientUrlList = GetVenueClientUrls()

foundClient = 0
for venueClientUrl in venueClientUrlList:
    try:
        venueClient = VenueClientIW(venueClientUrl)
        venueClient._IsValid()

        foundClient = 1
        break
    except:
        foundClient = 0

if not foundClient:
    print "Venue client unreachable (url=%s)" % (venueClientUrl,)
    sys.exit(1)
    
print "Calling to venue client at ", venueClientUrl
    
print "* GetVenueData"
print venueClient.GetVenueData()

print "* GetPersonalData"
print venueClient.GetPersonalData()

print "* GetUsers"
print venueClient.GetUsers()

print "* GetServices"
print venueClient.GetServices()

print "* GetApplications"
print venueClient.GetApplications()

print "* GetConnections"
print venueClient.GetConnections()

print "* GetVenueURL"
print venueClient.GetVenueURL()

print "* GetClientProfile"
print venueClient.GetClientProfile()

print "* GetNodeServiceURL"
print venueClient.GetNodeServiceURL()

print "* GetStreams"
print venueClient.GetStreams()

