#!/usr/bin/python2

import ConfigParser
import sys
import string
import logging

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.Descriptions import ConnectionDescription, VenueDescription
from AccessGrid.Descriptions import Capability, StreamDescription 
from AccessGrid.NetworkLocation import MulticastNetworkLocation

def run():
    venueServerUri = "https://localhost:8000/VenueServer"

    if len(sys.argv) > 2:
        venueServerUri = sys.argv[2]

    configFile = sys.argv[1]

    venueServer = Client.Handle(venueServerUri).GetProxy()
    venueServer.SetEncryptAllMedia(0)

    cp = ConfigParser.ConfigParser()
    cp.read(configFile)
    venues = {}

    # Start up the logging
    log = logging.getLogger("AG")
    log.setLevel(logging.INFO)
    log.addHandler(logging.StreamHandler())

    # We do this in two iterations because we need valid URLs for connections
    for sec in cp.sections():
        # Build Venue Descriptions
        vd = VenueDescription(cp.get(sec, 'name'), cp.get(sec, 'description'))
        vd.streams = []
    
        # Static Video
        if cp.has_option(sec, 'video'):
            (host, port) = string.split(cp.get(sec, 'video'), ':')
            vcap = Capability(Capability.PRODUCER, Capability.VIDEO)
            vsd = StreamDescription(vd.name, 
                                    MulticastNetworkLocation(host.strip(),
                                                             int(port), 
                                                             127),
                                    vcap, 0, None, 1)
            vd.streams.append(vsd)
        
        # Static Audio
        if cp.has_option(sec, 'audio'):
            (host, port) = string.split(cp.get(sec, 'audio'), ':')
            acap = Capability(Capability.PRODUCER, Capability.AUDIO)
            asd = StreamDescription(vd.name, 
                                    MulticastNetworkLocation(host.strip(),
                                                             int(port), 
                                                             127),
                                acap, 0, None, 1)
            vd.streams.append(asd)

        # Make the venue, then store the resulting URL
        print "VD #%s : %s" % (sec, vd.name)
        vd.uri = venueServer.AddVenue(vd)
        cp.set(sec, 'uri', vd.uri)

        if cp.has_option(sec, 'default'):
            venueServer.SetDefaultVenue(vd.uri)
        
        venues[sec] = vd

    for sec in cp.sections():
        # Build up connections
        exits = string.split(cp.get(sec, 'exits'), ', ')
        for x in exits:
            if venues.has_key(x):
                toVenue = venues[x]
                uri = toVenue.uri
                cd = ConnectionDescription(toVenue.name, toVenue.description,
                                           toVenue.uri)
                venues[sec].connections[uri] = cd
            else:
                print "Error making connection to venue: ", x

        # Set the connections on the given venue
        print "CD #%s/%s: %s" % (sec, venues[sec].name, cp.get(sec, 'exits'))
	
        # venue = Client.Handle(venues[sec].uri).GetProxy()
        print "URL: %s" % venues[sec].uri
        venue = Client.Handle(venues[sec].uri).GetProxy()
        venue.SetConnections(venues[sec].connections.values())

if __name__ == "__main__":
    # to profile this:
    # import profile
    # profile.run('run()', 'CreateVenues.prof')
    run()
    
