#!/usr/bin/env python
import sys
from AccessGrid.cache.VenueServer_client import VenueServerSOAP
from AccessGrid.cache.VenueServer_messages import *
from AccessGrid.cache.AccessGrid_Types import www_accessgrid_org_v3_0 as AGTk_types


if __name__ == '__main__':
    VenueServer = VenueServerSOAP("http://localhost:7000/VenueServer",
                                  tracefile=sys.stdout)
    # Go through each interface and see what we can do
    sr = CheckpointRequest()
    sr.secondsFromNow = 10
    msg = VenueServer.Checkpoint(sr)
    print "Checkpoint result: ", msg.result

    avr = AddVenueRequest()
    vd = AGTk_types.VenueDescription()
    vd.id = ""
    vd.uri = ""
    vd.name = "Test"
    vd.description = "This is a description."
    vd.encryptMedia = 0
    vd.encryptionKey = ""
    vd.connections = AGTk_types.ConnectionList()
    vd.streams = AGTk_types.StreamList()

    avr.venueDescription = vd
    
    msg = VenueServer.AddVenue(avr)

    print dir(msg)
