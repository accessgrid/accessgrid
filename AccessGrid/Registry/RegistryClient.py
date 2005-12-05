#!/usr/bin/env python

import xmlrpclib
import urllib

class RegistryClient:
    def __init__(self, url):
        self.url = url
        self.registryPeers = self._readPeerList(url=self.url)
        self.sortedRegistryPeers = self._getSortedRegistryPeers()
        self.serverProxy = xmlrpclib.ServerProxy("http://" + self.sortedRegistryPeers[0])

    def RegisterBridge(self, registeredServerInfo):
        return self.serverProxy.RegisterBridge(registeredServerInfo)

    def LookupBridge(self, maxToReturn=10):
        return self.serverProxy.LookupBridge(maxToReturn)
        # TODO, retry with other nodes on failure?

    def _getSortedRegistryPeers(self, maxToReturn=5):
        # TODO, ping (and cache) and sort registries.
        selection = self.registryPeers[:maxToReturn]
        return selection

    def _readPeerList(self,url):
        if url.startswith("file://"):
            filename = url[7:]
            f = open(filename, "r")
        else:
            opener = urllib.FancyURLopener({})
            f = opener.open(url)
        contents = f.read()
        f.close()
        registryPeers = contents.split()
        return registryPeers

if __name__=="__main__":
    rc = RegistryClient(url="file://../../tests/localhost_registry_nodes.txt")
    from AccessGrid.GUID import GUID
    from AccessGrid.Descriptions import BridgeDescription, QUICKBRIDGE_TYPE

    # Register a bridge using the RegistryClient
    info = BridgeDescription(guid=GUID(), name="defaultName", host="localhost", port="9999", serverType=QUICKBRIDGE_TYPE, description="")
    rc.RegisterBridge(info)
    
    # Lookup a bridge using the RegistryClient
    print "Found:", rc.LookupBridge()    # or rc.Lookup(10)

