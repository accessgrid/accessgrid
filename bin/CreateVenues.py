import ConfigParser
import sys
import os
import string

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Descriptions import ConnectionDescription
from AccessGrid.Descriptions import Capability, StreamDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation

venueServerUri = "https://localhost:8000/VenueServer"

if len(sys.argv) > 2:
    venueServerUri = sys.argv[2]

configFile = sys.argv[1]

venueServer = Client.Handle(venueServerUri).get_proxy()

cp = ConfigParser.ConfigParser()
cp.read(configFile)
venues = {}
connections = {}

for sec in cp.sections():
    venues[sec] = {}
    venues[sec]['name'] = cp.get(sec, 'name')
    venues[sec]['description'] = cp.get(sec, 'description')
    print "VD #%s : %s" % (sec, venues[sec]['name'])
    venues[sec]['uri'] = venueServer.AddVenue(venues[sec]['name'],
                                              venues[sec]['description'])
    if cp.has_option(sec, 'default'):
        venueServer.SetDefaultVenue(venues[sec]['uri'])
    cp.set(sec, 'uri', venues[sec]['uri'])

for sec in cp.sections():
    connections[sec] = []
    exits = string.split(cp.get(sec, 'exits'), ', ')
    print "CE #%s : %s ( %s )" % (sec, venues[sec]['name'], str(exits))
    for x in exits:
        if venues.has_key(x):
            connections[sec].append(ConnectionDescription(venues[x]['name'],
                                                          venues[x]['description'],
                                                          venues[x]['uri']))
        else:
            print "Error finding description for venue: ", x
    vcap = Capability(Capability.PRODUCER, Capability.VIDEO)
    if cp.has_option(sec, 'video'):
        (host, port) = string.split(cp.get(sec, 'video'), ':')
    vsd = StreamDescription(venues[sec]['name'], "Static Video",
                            MulticastNetworkLocation(host.strip(),
                                                     int(port), 127), vcap)
    vsd.static = 1
    acap = Capability(Capability.PRODUCER, Capability.AUDIO)
    if cp.has_option(sec, 'audio'):
        (host, port) = string.split(cp.get(sec, 'audio'), ':')
    asd = StreamDescription(venues[sec]['name'], "Static Audio",
                            MulticastNetworkLocation(host.strip(),
                                                     int(port), 127), acap)
    asd.static = 1
    venue = Client.Handle(venues[sec]['uri']).get_proxy()
    print "Name: %s URI: %s" % (venues[sec]['name'], venues[sec]['uri'])
    venue.SetConnections(connections[sec])
    venue.AddStream(asd)
    venue.AddStream(vsd)
    print "Encryption: %s" % venue.GetEncryptMedia()
    venue.SetEncryptMedia(0)

    



