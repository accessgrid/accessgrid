import ConfigParser
import sys
import os
import string

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Descriptions import VenueDescription, DataDescription
from AccessGrid.Descriptions import Capability, StreamDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation

venueServerUri = "https://localhost:8000/VenueServer"

if len(sys.argv) > 2:
    venueServerUri = sys.argv[2]

configFile = sys.argv[1]

venueServer = Client.Handle(venueServerUri).get_proxy()

cp = ConfigParser.ConfigParser()
cp.read(configFile)
descriptions = {}
connections = {}

for sec in cp.sections():
    name = cp.get(sec, 'name')
    description = cp.get(sec, 'description')
    descriptions[sec] = VenueDescription(name, description, "", None)
    print "VD #%s : %s" % (sec, name)
    descriptions[sec].uri = venueServer.AddVenue(descriptions[sec])
    if cp.has_option(sec, 'default'):
        venueServer.SetDefaultVenue(descriptions[sec].uri)
    cp.set(sec, 'uri', descriptions[sec].uri)

for sec in cp.sections():
    connections[sec] = []
    exits = string.split(cp.get(sec, 'exits'), ', ')
    print "CE #%s : %s ( %s )" % (sec, descriptions[sec].name, str(exits))
    for x in exits:
        if descriptions.has_key(x):
            connections[sec].append(descriptions[x])
        else:
            print "Error finding description for venue: ", x
    vcap = Capability(Capability.PRODUCER, Capability.VIDEO)
    if cp.has_option(sec, 'video'):
        (host, port) = string.split(cp.get(sec, 'video'), ':')
    vsd = StreamDescription(descriptions[sec].name, "Static Video",
                            MulticastNetworkLocation(host.strip(),
                                                     int(port), 127), vcap)
    vsd.static = 1
    acap = Capability(Capability.PRODUCER, Capability.AUDIO)
    if cp.has_option(sec, 'audio'):
        (host, port) = string.split(cp.get(sec, 'audio'), ':')
    asd = StreamDescription(descriptions[sec].name, "Static Audio",
                            MulticastNetworkLocation(host.strip(),
                                                     int(port), 127), acap)
    asd.static = 1
    venue = Client.Handle(descriptions[sec].uri).get_proxy()
    print "Name: %s URI: %s" % (descriptions[sec].name, descriptions[sec].uri)
    venue.SetConnections(connections[sec])
    venue.AddStream(asd)
    venue.AddStream(vsd)
    print "Encryption: %s" % venue.GetEncryptMedia()
    venue.SetEncryptMedia(0)

    



