#!/usr/bin/python2

import sys
import traceback
import ConfigParser

from AccessGrid import Toolkit
from AccessGrid.hosting import Client
from AccessGrid.Venue import VenueIW
from AccessGrid.VenueServer import VenueServerIW

a =Toolkit.CmdlineApplication.instance()
a.Initialize('MonitorBridge')


BRIDGESERVER = "BridgeServer"



cp = ConfigParser.ConfigParser()
cp.read(sys.argv[1])

if not cp.has_section(BRIDGESERVER):
    print "No %s section in cfg file; exiting" % BRIDGESERVER
    sys.exit(1)
    
venueUrlList = []

if cp.has_option(BRIDGESERVER, "venueServer"):
    venueServerUrl = cp.get(BRIDGESERVER,"venueServer")
    print "Getting venue list from venueserver", venueServerUrl
    venueDescList = VenueServerIW(venueServerUrl).GetVenues()
    venueUrlList = map( lambda x: x.uri, venueDescList )

if cp.has_option(BRIDGESERVER, "venue"):
    venueUrl =  cp.get(BRIDGESERVER,"venue")
    print "Check venue ", venueUrl
    venueUrlList = [ venueUrl ]

if cp.has_option(BRIDGESERVER, "venueServerFile"):
    print "This tool doesn't support a list of venue servers yet"
    sys.exit(1)

if cp.has_option(BRIDGESERVER, "venueFile"):
    venueFile = cp.get(BRIDGESERVER,"venueFile")
    print "Getting venue list from file ", venueFile
    f = file(venueFile,'r')
    lines = f.readlines()
    f.close()
    venueUrlList = map( lambda x: x.strip(), lines)
    if not venueUrlList[-1]:
        del venueUrlList[-1]

if not venueUrlList:
    secList = []
    for sec in cp.sections():
        if sec.startswith('http'):
           secList.append(sec)

    for sec in secList:
        if cp.get(sec,'type') == 'VenueServer':
            venueServerUrl = sec
            print "Getting venue list from venueserver", venueServerUrl
            venueDescList = VenueServerIW(venueServerUrl).GetVenues()
            venueUrlList = map( lambda x: x.uri, venueDescList )
            

for venueUrl in venueUrlList:
    venue = VenueIW(venueUrl)
    try:
        venueName = venue.GetName()
        print "venue: ", venueName, venueUrl
        streamList = venue.GetStreams()
        for stream in streamList:
            print "  type: ", stream.capability.type
            found = 0
            for networkLocation in stream.networkLocations:
                #if networkLocation.profile.name == bridgeName:
                    print "    bridge: ", networkLocation.profile.name, networkLocation.host, networkLocation.port
                    found = 1
            if not found:
                print "    ** bridge not found **"

    except:
        traceback.print_exc()
