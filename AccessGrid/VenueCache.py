
import os
import ConfigParser

from AccessGrid import Log
from AccessGrid.Descriptions import ConnectionDescription
log = Log.GetLogger("VenueCache")


class VenueCache: 

    def __init__(self,venuesFile,venueServers):
        self.venuesFile = venuesFile
        self.venueServers = venueServers
        self.venues = {}
        
    def Update(self):
        log.debug("Updating venue cache")
        from AccessGrid.interfaces.VenueServer_client import VenueServerIW
        
        venueList = []
        
        for url in self.venueServers:
            try:
                venueList = VenueServerIW(url).GetVenues()
                venueList.sort(cmp=lambda x, y: cmp(x.name, y.name))
                self.venues[url] = VenueCache.VenueList(url,venueList)
                log.debug("Retrieved %d venues from server %s", len(venueList), url)
            except:
                log.exception("Exception retrieving venues from %s", url)

    def GetVenues(self):
        return self.venues.values()
    
    def Store(self):
        log.debug("Storing venue cache in %s", self.venuesFile)
        f = file(self.venuesFile,'w')
        iniBlock = self.AsINIBlock()
        print >> f, iniBlock
        f.close()
        
    def Load(self):
        log.debug("Loading venue cache from %s", self.venuesFile)
        try:
            configParser = ConfigParser.ConfigParser()
            configParser.read(self.venuesFile)
            
            self.venues = {}
            
            for s in configParser.sections():
                if configParser.has_option(s,'venues'):
                    venues = configParser.get(s,'venues')
                    venues = venues.split(':')
                    venueList = []
                    for v in venues:
                        venueList.append(ConnectionDescription( configParser.get(v,'name'),
                                                                configParser.get(v,'description'),
                                                                configParser.get(v,'uri'),
                                                                v
                                                               ))
                    self.venues[s] = VenueCache.VenueList(s,venueList)
        except Exception,e:
           log.exception("Exception loading venues from %s", self.venuesFile)
           
    def AsINIBlock(self):
        out = ""
        for v in self.venues.values():
            out += '[%s]' % (v.venueServerUrl)
            venueIds = map( lambda x: x.id, v.venueList)
            venueIdString = ':'.join(venueIds)
            out += '\nvenues: ' + venueIdString
            for venue in v.venueList:
                venue.description = venue.description.replace('\n',', ')
            
            venueIniBlock = map( lambda x: x.AsINIBlock(), v.venueList)
            venueIniBlock = "".join(venueIniBlock)
            out += venueIniBlock
        return out

    # Internal Class VenueList
    class VenueList(object):
        __slots__ = ['venueServerUrl','venueList']
        def __init__(self,venueServerUrl,venueList):
            self.venueServerUrl = venueServerUrl
            self.venueList = venueList

    
      
if __name__ == '__main__':      
            
    venueServers = ['https://vv3.mcs.anl.gov:8000/VenueServer']
    venuesFile = 'venues'
    

    venueCache = VenueCache(venuesFile,venueServers)
    venueCache.Load()
    venueList = venueCache.GetVenues()
    for v in venueList:
        print v.venueServerUrl
        for venue in v.venueList:
            print venue.name
    venueCache.Store()
    

    venueCache.Update()
    venueList2 = venueCache.GetVenues()
    print len(venueList2), len(venueList2[0].venueList)
    venueCache.Update()
    venueList3 = venueCache.GetVenues()
    print len(venueList3), len(venueList3[0].venueList)
    venueCache.Update()
    venueList4 = venueCache.GetVenues()
    print len(venueList4), len(venueList4[0].venueList)
    
    
    
    



            