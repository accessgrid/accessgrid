import os, sys, time
import urllib
import socket
import traceback
import random
from optparse import OptionParser
from DocXMLRPCServer import DocXMLRPCServer 
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler, SimpleXMLRPCDispatcher

class RegistryInterface:

    # Bridge Interface, accepts a BridgeDescription
    def RegisterBridge(self, bridgeDescription):
        pass

    # Client Interface
    def LookupBridge(self, maxToReturn=None):
        pass

    # Peer Interface
    def PeerUpdate(self, data):
        pass

class RegistryBase(RegistryInterface):
    def __init__(self, port, peerListUrl=""):
        self.port = port
        self.host = ""
        self.peerUpdateInterval = 3 # 60  # seconds
        self.peerListUrl = peerListUrl
        self.registryPeers = []
        self.localPeerAddr = None
        if peerListUrl.startswith("file://"):
            self._readPeerListLocalTest(self.peerListUrl)
        else:
            self._readPeerList(url=self.peerListUrl)

    def _readPeerList(self,url):
        opener = urllib.FancyURLopener({})
        f = opener.open(url)
        contents = f.read()
        f.close()
        registryPeers = contents.split()
        fqdn = socket.getfqdn(socket.gethostname())
        localPeerName = fqdn + ":%s" % self.port
        if localPeerName not in registryPeers:
            raise Exception ("Error: this peer " + localPeerName + " is not listed in the master list.  The current registry requires all peers to know about each other.")
        registryPeers.remove(localPeerName)
        self.host = localPeerName
        self.registryPeers = registryPeers

    def _readPeerListLocalTest(self,filename):
        opener = urllib.FancyURLopener({})
        #f = opener.open(url)
        f = open(filename, "r")
        contents = f.read()
        f.close()
        registryPeers = contents.split() # split by line
        # make list of (host,port)
        def makeHostPortListFromString(peerList):
            peers = []
            for peer in peerList:
                splitPeer = peer.split(":")
                peers.append( (splitPeer[0], int(splitPeer[1])) )
            return peers
        registryPeers = makeHostPortListFromString(registryPeers)

        # for local test, just find the peer with the same port
        localPeerName = None
        for peer in registryPeers:
            if peer[1] == self.port:
                localPeerAddr = peer

        if localPeerAddr not in registryPeers:
            raise Exception ("Error: this peer " + localPeerAddr + " is not listed in the master list.  The current registry requires all peers to know about each other.")
        registryPeers.remove(localPeerAddr)
        print "localPeer:", localPeerAddr
        print "otherPeers:", registryPeers

        self.registryPeers = []

    def RefreshPeerList(self, url=None):
        # Allows a running peer to refresh its peer list in case a peer has been manually added or removed.
        # Call to this function probably would be initiated manually.
        if url == None:
            url = self.peerListUrl
        self._readPeerList(url)

    def ConnectToRegistries(self):
        for peer in self.registryPeers:
            try:
                print "Would connect to:", peer
            except Exception:
                traceback.print_exc()

    def RandomBridgeLookup(self, maxToReturn=None):
        keys = self.registeredServers.keys()
        if maxToReturn == None or maxToReturn==0:
            numToReturn = len(keys)
        else:
            numToReturn = min(maxToReturn, len(keys))
        serversToReturn = []
        for i in range(numToReturn):
            key = keys[random.randrange(len(keys))]
            print "Key:", key
            keys.remove(key)
            serversToReturn.append(self.registeredServers[key])
        return serversToReturn 

    LookupBridge = RandomBridgeLookup

class AGXMLRPCServer(DocXMLRPCServer):
    def __init__(self, addr, requestHandler=SimpleXMLRPCRequestHandler, logRequests=1):
        self.allow_reuse_address = True
        DocXMLRPCServer.__init__(self, addr, requestHandler=requestHandler, logRequests=logRequests)

class RegistryPeerXMLRPC(RegistryBase):
    def __init__(self, port, peerListUrl):
        RegistryBase.__init__(self, port, peerListUrl)
        self.requestServer = AGXMLRPCServer( ("", self.port) )
        self._RegisterFunctions()
        self.registeredServers = {}

    def _RegisterFunctions(self):
        self.requestServer.register_function(self.LookupBridge, "LookupBridge")
        self.requestServer.register_function(self.RegisterBridge, "RegisterBridge")

    def RegisterBridge(self, bridgeDescription):
        print "Registering bridge:", bridgeDescription
        self.registeredServers[(bridgeDescription["host"], bridgeDescription["port"])] = bridgeDescription
        print self.registeredServers
        return True

    def Run(self):
        self.ConnectToRegistries()
        try:
            self.requestServer.serve_forever()
        except Exception, e:
            print e

RegistryPeer=RegistryPeerXMLRPC


if __name__ == "__main__":
    defaultPort = 8030
    defaultPeerListUrl = "file://../../tests/localhost_registry_nodes.txt"
    # defaultPeerListUrl="http://www.accessgrid.org/registry/peers.txt"
    parser = OptionParser()
    parser.add_option("-p", "--port", dest="port", default=defaultPort, help="Listening port.", type="int")
    parser.add_option("-u", "--peerListUrl", dest="peerListUrl", default=defaultPeerListUrl, help="The url to bootstrap the system.  For the current design, this is a complete list of peers.")
    (options, ret_args) = parser.parse_args(args=sys.argv)

    r = RegistryPeer(peerListUrl=options.peerListUrl, port=options.port)
    r.Run()
    

