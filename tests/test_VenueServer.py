#-----------------------------------------------------------------------------
# Name:        VenueManagementClient.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2002/17/12
# RCS-ID:      $Id: test_VenueServer.py,v 1.1 2003-01-09 18:59:24 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.Descriptions import VenueDescription

vd1 = VenueDescription("First Venue", "First Venue Description", "", None)
vd2 = VenueDescription("Second Venue", "Second Venue Description", "", None)
vd3 = VenueDescription("Third Venue", "Third Venue Description", "", None)
vd4 = VenueDescription("Fourth Venue", "Fourth Venue Description", "", None)

vms = Client.Handle('https://localhost:8000/VenueServer').get_proxy()

print "\nNew Venue URL: " + vms.AddVenue(vd1)
print "\nNew Venue URL: " + vms.AddVenue(vd2)
print "\nNew Venue URL: " + vms.AddVenue(vd3)
print "\nNew Venue URL: " + vms.AddVenue(vd4)

dv = vms.GetDefaultVenue()
print "\nDefault Venue: " + dv

vl = vms.GetVenues()
print "\nVenue List: "

for v in vl:
    print v

print "\nCheckpointing"
vms.Checkpoint()
