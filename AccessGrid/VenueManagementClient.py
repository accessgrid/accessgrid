#-----------------------------------------------------------------------------
# Name:        VenueManagementClient.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2002/17/12
# RCS-ID:      $Id: VenueManagementClient.py,v 1.3 2003-01-08 15:26:27 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.Descriptions import VenueDescription

vd = VenueDescription("First Venue", "First Venue Description", "", None)

vms = Client.Handle('https://localhost:8000/VenueServer').get_proxy()
url = vms.AddVenue(vd)

print "\nNew Venue URL: " + url
dv = vms.GetDefaultVenue()

print "\nDefault Venue: " + dv
vl = vms.GetVenues()

print "\nVenue List: "
for v in vl:
    print v

print "\nCheckpointing"
vms.Checkpoint()
