#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        CreateVenues.py
# Purpose:     This creates venues from a file.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CreateVenues.py,v 1.2 2004-05-27 21:31:27 eolson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
This program is used to create venues for the venue server.
"""
__revision__ = "$Id: CreateVenues.py,v 1.2 2004-05-27 21:31:27 eolson Exp $"

import ConfigParser
import sys
import string

from AccessGrid import Log
from AccessGrid.hosting import Client
from AccessGrid.Descriptions import ConnectionDescription, VenueDescription
from AccessGrid.Descriptions import Capability, StreamDescription 
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.Toolkit import CmdlineApplication

def main():
    """
    This is the function that does all the real work.
    """
    app = CmdlineApplication.instance()
    app.Initialize("CreateVenues")

    venueServerUri = "https://localhost:8000/VenueServer"

    if len(sys.argv) > 2:
        venueServerUri = sys.argv[2]

    configFile = sys.argv[1]

    venueServer = Client.SecureHandle(venueServerUri).GetProxy()
    venueServer.SetEncryptAllMedia(0)

    config = ConfigParser.ConfigParser()
    config.read(configFile)
    venues = {}

    # Start up the logging
    log = Log.GetLogger("CreateVenues")
    hdlr = Log.StreamHandler()
    hdlr.setLevel(Log.INFO)
    Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())

    # We do this in two iterations because we need valid URLs for connections
    for sec in config.sections():
        # Build Venue Descriptions
        vdesc = VenueDescription(config.get(sec, 'name'),
                              config.get(sec, 'description'))
        vdesc.streams = []
    
        # Static Video
        if config.has_option(sec, 'video'):
            (host, port) = string.split(config.get(sec, 'video'), ':')
            vcap = Capability(Capability.PRODUCER, Capability.VIDEO)
            vsd = StreamDescription(vdesc.name, 
                                    MulticastNetworkLocation(host.strip(),
                                                             int(port), 
                                                             127),
                                    vcap, 0, None, 1)
            vdesc.streams.append(vsd)
        
        # Static Audio
        if config.has_option(sec, 'audio'):
            (host, port) = string.split(config.get(sec, 'audio'), ':')
            acap = Capability(Capability.PRODUCER, Capability.AUDIO)
            asd = StreamDescription(vdesc.name, 
                                    MulticastNetworkLocation(host.strip(),
                                                             int(port), 
                                                             127),
                                acap, 0, None, 1)
            vdesc.streams.append(asd)

        # Make the venue, then store the resulting URL
        print "VD #%s : %s" % (sec, vdesc.name)
        vdesc.uri = venueServer.AddVenue(vdesc)
        config.set(sec, 'uri', vdesc.uri)

        if config.has_option(sec, 'default'):
            venueServer.SetDefaultVenue(vdesc.uri)
        
        venues[sec] = vdesc

    for sec in config.sections():
        # Build up connections
        exits = string.split(config.get(sec, 'exits'), ', ')
        for vexit in exits:
            if venues.has_key(vexit):
                toVenue = venues[vexit]
                uri = toVenue.uri
                conn = ConnectionDescription(toVenue.name, toVenue.description,
                                           toVenue.uri)
                venues[sec].connections.append(conn)
            else:
                print "Error making connection to venue: ", vexit

        # Set the connections on the given venue
        print "CD #%s/%s: %s" % (sec, venues[sec].name,
                                 config.get(sec, 'exits'))
	
        # venue = Client.Handle(venues[sec].uri).GetProxy()
        print "URL: %s" % venues[sec].uri
        venue = Client.SecureHandle(venues[sec].uri).GetProxy()
        venue.SetConnections(venues[sec].connections)

if __name__ == "__main__":
    # to profile this:
    # import profile
    # profile.run('run()', 'CreateVenues.prof')
    main()
    
