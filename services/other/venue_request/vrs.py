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
    'edu' : 'Educations Institutions',
    'mil' : 'Military Organizations',
    'int' : 'International Treaty Organizations',
    }

CountryDomains = {
    }

domDict = { 'kids': dict(), 'url': None, 'venueurl': None }
serverUrl = "https://wormtongue.mcs.anl.gov/VenueServer"
serverUrl = "https://localhost/VenueServer"
datafile = "vrs-data.pickled"
vDict = dict()

app = Service()

try:
    app.Initialize("VenueRequestService")
except:
    print "Couldn't initialize app, exiting."
    sys.exit(-1)
    
venueServerClient = VenueServerIW(serverUrl)
defVenueUrl = venueServerClient.GetDefaultVenue()
defVenueClient = VenueIW(defVenueUrl)

print "Default Venue: %s" % defVenueUrl

def InitTopLevel():
    global venueServerClient, defVenueClient, TopLevelDomains
    global datafile, initializedTop

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

    pickle.dump(vDict, file(datafile, "ab+"))

    return vDict

def RequestVenue(name, desc, email, url):
    global datafile, venueServerClient, TopLevelDomains, vDict

    print "Got request for:"
    print "name: %s" % name
    print "description: %s" % desc
    print "email: %s" % email
    print "url: %s" % url
    
    hp = urlparse.urlparse(url)[1].split(':')
    domain = hp[0].split('.')
    domain.reverse()
    backDomain = ".".join(domain)

    print "Domain: %s" % backDomain

    if vDict.has_key(backDomain):
        return (0, "Domain already registered with url: %s" vDict[backDomain])

    tld = domain[0]

    if tld in TopLevelDomains.keys():
        tldUrl = vDict[tld]
    else:
        tldUrl = vDict['geo']

    tldVenue = VenueIW(tldUrl)

    print "Got Top Level as: %s for url: %s" % (tldVenue.GetName(), url)
    
    description = "An institutional venue for %s. For more information please see %s. The description submitted by the requestor is: \n%s" % (name, url, desc)
    
    vDesc = VenueDescription(name, description)
    venueUri = ''
    venueUri = venueServerClient.AddVenue(vDesc)
    newVenue = VenueIW(venueUri)
    
    vDict[backDomain] = {
        'name' : name,
        'description' : desc,
        'email' : email,
        'url' : url,
        'venueurl' : venueUri
        }

    # Add connections between the two
    pCd = ConnectionDescription(tldVenue.GetName(),
                                tldVenue.GetDescription(), tldUrl)
    newVenue.AddConnection(pCd)
    
    cCd = ConnectionDescription(name, desc, venueUri)
    tldVenue.AddConnection(cCd)
    
    pickle.dump(vDict, file(datafile, "ab+"))
    
    return (1, venueUri)

port = 6100
server = SimpleXMLRPCServer.SimpleXMLRPCServer(('localhost', port))
server.allow_reuse_address = 1
server.register_function(RequestVenue)

print "Loading data"
if os.path.exists(datafile):
    try:
        vDict = pickle.load(file(datafile, "ab+"))
    except:
        print "Couldn't load pickled data, initializing from memory."
        vDict = InitTopLevel()
else:
    print "No data file, initializing from memory."
    vDict = InitTopLevel()

server.serve_forever()
        
