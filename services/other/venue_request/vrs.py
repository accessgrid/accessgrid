#!/usr/bin/python2
#
#
import os, sys
import xml.dom.minidom
import pickle
import SimpleXMLRPCServer
import urlparse
import pprint

from AccessGrid.Toolkit import Service
from AccessGrid.Descriptions import VenueDescription, ConnectionDescription
from AccessGrid.VenueServer import VenueServerIW
from AccessGrid.Venue import VenueIW

TopLevelDomains = {
    'aero' : 'Air Transport Members',
    'biz' : 'Businesses',
    'com' : 'Commercial Organizations',
    'coop' : 'Cooperative Associations',
    'info' : 'Informational Organizations',
    'museum' : 'Museums',
    'name' : 'Indviduals',
    'net' : 'Network Service Providers',
    'org' : 'Not for profit Organizations',
    'pro' : 'Credentialed Professionals',
    'gov' : 'Government Institutions',
    'edu' : 'Educational Institutions',
    'mil' : 'Military Organizations',
    'int' : 'International Treaty Organizations',
    }

CountryDomains = {
    }

serverUrl = "https://ivs.mcs.anl.gov:9000/VenueServer"
datafile = "vrs-data.pickled"

app = Service()

try:
    app.Initialize("VenueRequestService")
except:
    print "Couldn't initialize app, exiting."
    sys.exit(-1)

log = app.GetLog()

venueServerClient = VenueServerIW(serverUrl)
defVenueUrl = venueServerClient.GetDefaultVenue()
defVenueClient = VenueIW(defVenueUrl)

print "Default Venue: %s" % defVenueUrl

def InitTopLevel():
    global venueServerClient, defVenueClient, TopLevelDomains
    global datafile, initializedTop, log

    vDict = dict()

    # Add connections between the two
    pCd = ConnectionDescription(defVenueClient.GetName(),
                                defVenueClient.GetDescription(),
                                defVenueUrl)

    for k in TopLevelDomains.keys():
        vn = TopLevelDomains[k]
        name = "%s Lobby" % vn
        desc = "A Lobby for %s Virtual Venues." % vn
        vd = VenueDescription(name, desc)
        vuri = venueServerClient.AddVenue(vd)
        newVenue = VenueIW(vuri)
        vDict[k] = vuri

        newVenue.AddConnection(pCd)
    
        cCd = ConnectionDescription(name, desc, vuri)
        defVenueClient.AddConnection(cCd)

    name = "Geographic Lobby"
    desc = "A Lobby for Virtual Venues that are identified by country names."
    vd = VenueDescription(name, desc)

    vuri = venueServerClient.AddVenue(vd)
    newVenue = VenueIW(vuri)
    vDict['geo'] = vuri

    # Add connections between the two
    newVenue.AddConnection(pCd)
    
    cCd = ConnectionDescription(name, desc, vuri)
    defVenueClient.AddConnection(cCd)

    initializedTop = 1

    pickle.dump(vDict, file(datafile, "wb+"))

    return vDict

def RequestVenueExt(request, test=0):
    global datafile, venueServerClient, TopLevelDomains, vDict, log

    log.debug("Got request for:")
    log.debug("name: %s", request['name'])
    log.debug("description: %s", request['description'])
    log.debug("email: %s", request['email'])
    log.debug("url: %s", request['www'])

    url = request['www']
    if not url.startswith('http'):
        url = 'http://'+url
    hp = urlparse.urlparse(url)[1].split(':')

    log.debug("HP: %s", hp)
    
    domain = hp[0].split('.')

    log.debug("Domain: %s", domain)
    
    domain.reverse()

    backDomain = ".".join(domain)

    log.debug("Domain: %s", backDomain)

    if vDict.has_key(backDomain):
        log.debug("Venue found for domain.")
        return (1, vDict[backDomain]['venueurl'])
                
    tld = domain[0]

    log.debug("TLD: %s", tld)

    if tld in vDict.keys():
        tldUrl = vDict[tld]
    else:
        log.debug("Didn't find top level domain, url using geo.")
        tldUrl = vDict['geo']

    log.debug("TLD Venue URL: %s", tldUrl)

    tldVenue = VenueIW(tldUrl)

    log.debug("Got Top Level as: %s for url: %s" , tldVenue.GetName(),
              request['www'])

    if test:
        log.debug("Test call")
        return (1, "Didn't do anything though! (%s -> %s)" % (request['www'],
                                                         tldVenue.GetName()))
    else:
        log.debug("Continuing on...")
    
    vDesc = VenueDescription(request['name'], request['description'])
    log.debug("Created venue description.")
    
    venueUri = venueServerClient.AddVenue(vDesc)

    log.debug("Added venue, new url: %s", venueUri)
    
    newVenue = VenueIW(venueUri)

    log.debug("Created IW to new venue.")
   
    description = request['description']

    for s in ["\r", "\r\n", "\n\r", "\n"]:
        description = description.replace(s, " ")

    vDict[backDomain] = {
        'name' : request['name'],
        'description' : request['description'],
        'email' : request['email'],
        'url' : request['www'],
        'venueurl' : venueUri,
        'request' : request
       }

    # Add connections between the two
    pCd = ConnectionDescription(tldVenue.GetName(),
                                tldVenue.GetDescription(), tldUrl)
    newVenue.AddConnection(pCd)
    
    cCd = ConnectionDescription(request['name'], request['description'], venueUri)
    tldVenue.AddConnection(cCd)

    pickle.dump(vDict, file(datafile, "wb+"))
    
    return (1, venueUri)

def Echo(value):
    global log
    log.debug("Echoing: %s", value)
    return value

port = 9003
server = SimpleXMLRPCServer.SimpleXMLRPCServer(('', port), logRequests=1)
server.allow_reuse_address = 1
server.register_function(RequestVenueExt)
server.register_function(Echo)

log.debug("Loading data")
if os.path.exists(datafile):
    try:
        log.debug("Loading from file.")
        vDict = pickle.load(file(datafile, "ab+"))
    except:
        log.debug("Couldn't load pickled data, initializing from memory.")
        vDict = InitTopLevel()
else:
    log.debug("No data file, initializing from memory.")
    vDict = InitTopLevel()

server.serve_forever()
        
