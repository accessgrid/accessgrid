#-----------------------------------------------------------------------------
# Name:        VenueManagementClient.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2002/17/12
# RCS-ID:      $Id: test_VenueServer.py,v 1.8 2004-03-05 21:46:27 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import os
import socket
import sys
from AccessGrid.hosting import Client
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Descriptions import DataDescription, ConnectionDescription
from AccessGrid.Descriptions import CreateVenueDescription, VenueDescription
from AccessGrid.Descriptions import CreateConnectionDescription

#
# Set up the venue space
#
venueServerUri = "https://localhost:8000/VenueServer"
if len(sys.argv) > 1:
   venueServerUri = sys.argv[1]
venueServerProxy = Client.Handle( venueServerUri ).GetProxy()

# List what's there first
print "-- Venues -- "
venueList = venueServerProxy.GetVenues()
for v in venueList:
   print v.uri
   venue = CreateVenueDescription(v)
   connectionList = Client.Handle( v.uri ).GetProxy().GetConnections()
   for connection in connectionList:
      c = CreateConnectionDescription(connection)
      print c

# add venues
outsideDesc = VenueDescription("Outside", "Outside venue description")
insideDesc = VenueDescription("Inside", "Inside venue description")

print "outsideVenueId = ", outsideDesc.id
print "insideVenueId = ", insideDesc.id

outsideDesc.uri = venueServerProxy.AddVenue(outsideDesc)
insideDesc.uri = venueServerProxy.AddVenue(insideDesc)

print "outsideVenueUri = ", outsideDesc.uri
print "insideVenueUri  = ", insideDesc.uri

# make connections between venues, using SetConnections method
conn = ConnectionDescription("Inside", "The inside one.", insideDesc.uri)
Client.Handle( outsideDesc.uri ).GetProxy().SetConnections( [conn] )
conn2 = ConnectionDescription("Outside", "The outside one.", outsideDesc.uri)
Client.Handle( insideDesc.uri ).GetProxy().SetConnections( [conn2] )

# add some data to each venue
dataDescription = DataDescription("sample.data")
Client.Handle( outsideDesc.uri ).GetProxy().AddData( dataDescription )
dataDescription = DataDescription("moreSample.data")
Client.Handle( outsideDesc.uri ).GetProxy().AddData( dataDescription )


print "-- Venues -- "
venueList = venueServerProxy.GetVenues()
for v in venueList:
   print v.uri
   venue = CreateVenueDescription(v)
   connectionList = Client.Handle( v.uri ).GetProxy().GetConnections()
   for connection in connectionList:
      c = CreateConnectionDescription(connection)
      print c

newname = "Modified outside venue."
newdesc = "modified outside venue desc"

Client.Handle(outsideDesc.uri).GetProxy().SetName(newname)
Client.Handle(outsideDesc.uri).GetProxy().SetDescription(newdesc)

print "-- Venues -- "
venueList = venueServerProxy.GetVenues()
for v in venueList:
   venue = CreateVenueDescription(v)
   print v.uri
   connectionList = Client.Handle( v.uri ).GetProxy().GetConnections()
   for connection in connectionList:
      c = CreateConnectionDescription(connection)
      print c

dv = venueServerProxy.GetDefaultVenue()
print "\nDefault Venue: " + dv

vl = venueServerProxy.GetVenues()
print "\nVenue List: "

for v in vl:
    print v

print "\nShutting down"
venueServerProxy.Shutdown(0)
