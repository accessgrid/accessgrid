#-----------------------------------------------------------------------------
# Name:        VenueManagementClient.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2002/17/12
# RCS-ID:      $Id: test_VenueServer.py,v 1.2 2003-01-15 20:32:23 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.Descriptions import VenueDescription

vd1 = VenueDescription("First Venue", "First Venue Description")
vd2 = VenueDescription("Second Venue", "Second Venue Description")
vd3 = VenueDescription("Third Venue", "Third Venue Description")
vd4 = VenueDescription("Fourth Venue", "Fourth Venue Description")

vms = Client.Handle('https://localhost:8000/VenueServer').get_proxy()

try:
    print "\nNew Venue URL: " + vms.AddVenue(vd1)
except:
    print "Add Venue Failed!"
    
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

print "\nShutting down"
vms.Shutdown(0)
