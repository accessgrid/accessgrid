#!/usr/bin/python2

import sys
import traceback
import ConfigParser
from optparse import Option

from AccessGrid import Toolkit
from AccessGrid.hosting import Client
from AccessGrid.Venue import VenueIW
from AccessGrid.VenueServer import VenueServerIW


# nagios return codes
OK = 0
WARN = 1
CRITICAL = 2
UNKNOWN = 3

# default to critical
ret = CRITICAL

BRIDGESERVER = "BridgeServer"


#
# Initialize application
#
a =Toolkit.Service.instance()


# Handle command-line
a.AddCmdLineOption(Option("-t", "--threshold", dest="threshold", default=0.75,type='float',
                   help="The percentage of found bridges below which state becomes critical."))
a.AddCmdLineOption(Option("-v", "--verbose", dest="verbose", default=0,action="store_true",
                   help="Print more detail during processing."))

a.Initialize('MonitorBridge')

threshold = a.GetOption('threshold')
verbose = a.GetOption('verbose')
configFile = a.GetOption('configfilename')

if not configFile:
    print "No config file given; exiting"
    sys.exit(UNKNOWN)


#
# Read config file
#

cp = ConfigParser.ConfigParser()
cp.read(configFile)

if not cp.has_section(BRIDGESERVER):
    print "No %s section in cfg file %s; exiting" % (BRIDGESERVER,configFile)
    sys.exit(UNKNOWN)


# Get id from config file
bridgeId = cp.get(BRIDGESERVER,'id')
bridgeName = cp.get(BRIDGESERVER,'name')


#
# Build venue url list from config file
#
venueUrlList = []
for sec in cp.sections():
    if not cp.has_option(sec,'type'):
        continue
        
    typ = cp.get(sec,'type')
    
    if typ == 'Venue':
        #print "Got venue: ", sec
        venueUrlList.append(sec)
        
    elif typ == 'VenueServer':
        #print "Got venue server: ", sec
        venueDescList = VenueServerIW(venueServerUrl).GetVenues()
        venueUrls = map( lambda x: x.uri, venueDescList )
        venueUrlList += venueUrls


#
# Confirm that streams in venues are bridged
#
numStreams = 0
numBridgedStreams = 0
    
for venueUrl in venueUrlList:
    venue = VenueIW(venueUrl)
    try:
        venueName = venue.GetName()
        streamList = venue.GetStreams()
        if verbose:
            print "Venue: ", venueName
        for stream in streamList:   
            numStreams += 1
            found = 0
            for networkLocation in stream.networkLocations:
                if networkLocation.profile.name == bridgeName:
                    if verbose:
                        print "Found bridge for %s in venue: %s" % (stream.capability.type,venueName)
                    numBridgedStreams += 1
                    found = 1
                    break
            if not found:
                if verbose:
                    print "No bridge for %d in venue: %s" % (stream.capability.type,venueName)

    except Exception,e:
        if verbose:
            traceback.print_exc()
        print "Exception", e
        
#
# Report
#
if numStreams > 0:        
    if numStreams == numBridgedStreams:
        print "OK: %d of %d streams bridged" % (numBridgedStreams,numStreams)
        ret = OK
    elif float(numBridgedStreams)/numStreams < threshold:
        print "CRITICAL: only %d of %d streams are bridged" % (numBridgedStreams,numStreams)
        ret = CRITICAL
    else:
        print "WARNING: only %d of %d streams are bridged" % (numBridgedStreams,numStreams)
        ret = WARN
else:
    print "OK - No streams to bridge"
    ret = OK

sys.exit(ret)
