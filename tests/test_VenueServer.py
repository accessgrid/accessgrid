#-----------------------------------------------------------------------------
# Name:        VenueManagementClient.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2002/17/12
# RCS-ID:      $Id: test_VenueServer.py,v 1.3 2003-01-24 04:36:41 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import os
import socket
import sys
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Descriptions import *

#
# Set up the venue space
#
venueServerUri = "https://munich:10000/VenueServer"
venueServerUri = "https://localhost:8000/VenueServer"
if len(sys.argv) > 1:
   venueServerUri = sys.argv[1]
venueServerProxy = Client.Handle( venueServerUri ).get_proxy()

# add venues
outsideVenueDesc = VenueDescription("Outside", "Outside venue", "", None) 
insideVenueDesc = VenueDescription("Inside", "Inside venue", "", None) 

outsideVenueUri = venueServerProxy.AddVenue( outsideVenueDesc )
insideVenueUri = venueServerProxy.AddVenue( insideVenueDesc )
print "outsideVenueUri = ",  outsideVenueUri
print "insideVenueUri = ", insideVenueUri

outsideVenueDesc.uri = outsideVenueUri
insideVenueDesc.uri = insideVenueUri

# make connections between venues, using SetConnections method
connectionList = [ insideVenueDesc ]
Client.Handle( outsideVenueUri ).get_proxy().SetConnections( connectionList )
connectionList = [ outsideVenueDesc ]
Client.Handle( insideVenueUri ).get_proxy().SetConnections( connectionList )

# add some data to each venue
dataDescription = DataDescription( "sample.data", "Sample data", "uri", "icon", "storageType" )
Client.Handle( outsideVenueUri ).get_proxy().AddData( dataDescription )
dataDescription = DataDescription( "moreSample.data", "More sample data", "uri", "icon", "storageType" )
Client.Handle( outsideVenueUri ).get_proxy().AddData( dataDescription )


print "-- Venues -- "
venueList = venueServerProxy.GetVenues()
for venue in venueList:
    print "  ", venue.name, venue.description, venue.uri
    connectionList = Client.Handle( venue.uri ).get_proxy().GetConnections()
    for connection in connectionList:
        print "      connection : ", connection.name, connection.description, connection.uri

outsideVenueDesc.name = "Modified outside venue"
outsideVenueDesc.description = "modified outside venue desc"
venueServerProxy.ModifyVenue( outsideVenueDesc.uri, outsideVenueDesc )

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

print "\nCheckpointing"
venueServerProxy.Checkpoint()

print "\nShutting down"
venueServerProxy.Shutdown(0)
