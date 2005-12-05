#!/usr/bin/env python

import xmlrpclib
import urllib

class RegistryClient:
    def __init__(self, url):
        self.url = url
        self.registryPeers = self._readPeerList(url=self.url)
        self.sortedRegistryPeers = self._getSortedRegistryPeers()
        self.serverProxy = xmlrpclib.ServerProxy("http://" + self.sortedRegistryPeers[0])

    def Register(self, registeredServerInfo):
        return self.serverProxy.Register(registeredServerInfo)

    def Lookup(self, maxToReturn=10):
        return self.serverProxy.Lookup(maxToReturn)
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

