import ConfigParser
import sys
import os
import string
import logging

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Descriptions import ConnectionDescription, VenueDescription
from AccessGrid.Descriptions import Capability, StreamDescription 
from AccessGrid.NetworkLocation import MulticastNetworkLocation

venueServerUri = "https://localhost:8000/VenueServer"

if len(sys.argv) > 2:
    venueServerUri = sys.argv[2]

configFile = sys.argv[1]

venueServer = Client.Handle(venueServerUri).get_proxy()
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
                                MulticastNetworkLocation(host.strip(),int(port), 127),
                                vcap, 0, None, 1)
        vd.streams.append(vsd)
        
    # Static Audio
    if cp.has_option(sec, 'audio'):
        (host, port) = string.split(cp.get(sec, 'audio'), ':')
        acap = Capability(Capability.PRODUCER, Capability.AUDIO)
        asd = StreamDescription(vd.name, 
                                MulticastNetworkLocation(host.strip(),int(port), 127),
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
    current = venues[sec].connections
    exits = string.split(cp.get(sec, 'exits'), ', ')
    print "CE #%s : %s ( %s )" % (sec, venues[sec].name, str(exits))
    for x in exits:
        if venues.has_key(x):
            c = ConnectionDescription(venues[x].name, venues[x].description,
                                      venues[x].uri)
            current[c.uri] = c
        else:
            print "Error finding description for venue: ", x

    # Set the connections on the given venue
    print "CD #%s/%s: %s" % (sec, venues[sec].name, cp.get(sec, 'exits'))
    venue = Client.Handle(venues[sec].uri).get_proxy()
    venue.SetConnections(venues[sec].connections.values())




