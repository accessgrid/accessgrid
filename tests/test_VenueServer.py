#-----------------------------------------------------------------------------
# Name:        VenueManagementClient.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2002/17/12
# RCS-ID:      $Id: test_VenueServer.py,v 1.7 2003-04-01 23:28:16 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import os
import socket
import sys
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Descriptions import DataDescription, ConnectionDescription
from AccessGrid.Descriptions import CreateVenueDescription, VenueDescription

#
# Set up the venue space
#
venueServerUri = "https://munich:10000/VenueServer"
venueServerUri = "https://localhost:8000/VenueServer"
if len(sys.argv) > 1:
   venueServerUri = sys.argv[1]
venueServerProxy = Client.Handle( venueServerUri ).get_proxy()

# add venues
outsideDesc = VenueDescription("Outside", "Outside venue description")
insideDesc = VenueDescription("Inside", "Inside venue description")

outsideDesc.uri = venueServerProxy.AddVenue(outsideDesc)
insideDesc.uri = venueServerProxy.AddVenue(insideDesc)

print "outsideVenueUri = ",  outsideDesc.uri
print "insideVenueUri = ", insideDesc.uri

# make connections between venues, using SetConnections method
connectionList = [ ConnectionDescription("Inside", "The inside one.",
                                         insideDesc.uri)]
Client.Handle( outsideDesc.uri ).get_proxy().SetConnections( connectionList )
connectionList = [ ConnectionDescription("Outside", "The outside one.",
                                         outsideDesc.uri)]
Client.Handle( insideDesc.uri ).get_proxy().SetConnections( connectionList )

# add some data to each venue
dataDescription = DataDescription("sample.data")
Client.Handle( outsideDesc.uri ).get_proxy().AddData( dataDescription )
dataDescription = DataDescription("moreSample.data")
Client.Handle( outsideDesc.uri ).get_proxy().AddData( dataDescription )


print "-- Venues -- "
venueList = venueServerProxy.GetVenues()
print venueList, dir(venueList)
for v in venueList:
   venue = CreateVenueDescription(v)
   print "  ", venue.name, venue.description, venue.uri
   connectionList = Client.Handle( venue.uri ).get_proxy().GetConnections()
   for connection in connectionList:
        print "      connection : ", connection.name, connection.description, connection.uri

newname = "Modified outside venue."
newdesc = "modified outside venue desc"

Client.Handle(outsideDesc.uri).get_proxy().SetName(newname)
Client.Handle(outsideDesc.uri).get_proxy().SetDescription(newdesc)

print "-- Venues -- "
venueList = venueServerProxy.GetVenues()
for venue in venueList:
    print "  ", venue.name, venue.description, venue.uri
    connectionList = Client.Handle( venue.uri ).get_proxy().GetConnections()
    for connection in connectionList:
        print "      connection : ", connection.name, connection.description, connection.uri

dv = venueServerProxy.GetDefaultVenue()
print "\nDefault Venue: " + dv

vl = venueServerProxy.GetVenues()
print "\nVenue List: "

for v in vl:
    print v

print "\nShutting down"
venueServerProxy.Shutdown(0)
