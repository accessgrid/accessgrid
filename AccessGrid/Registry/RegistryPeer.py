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
    def __init__(self, port, nodeListUrl="", localTest=False):
        self.port = port
        self.host = ""
        self.peerUpdateInterval = 3 # 60  # seconds
        self.nodeListUrl = nodeListUrl
        self.registryNodes = []
        if not localTest:
            self._readNodeList(url=self.nodeListUrl)
        else:
            self._readNodeListLocalTest(self.nodeListUrl)
        self.localNodeAddr = None

    def _readNodeList(self,url):
        opener = urllib.FancyURLopener({})
        f = opener.open(url)
        contents = f.read()
        f.close()
        registryNodes = contents.split()
        fqdn = socket.getfqdn(socket.gethostname())
        localNodeName = fqdn + ":%s" % self.port
        if localNodeName not in registryNodes:
            raise Exception ("Error: this node " + localNodeName + " is not listed in the master list.  The current registry requires all nodes to know about each other.")
        registryNodes.remove(localNodeName)
        self.host = localNodeName
        self.registryNodes = registryNodes

    def _readNodeListLocalTest(self,filename):
        opener = urllib.FancyURLopener({})
        #f = opener.open(url)
        f = open(filename, "r")
        contents = f.read()
        f.close()
        registryNodes = contents.split() # split by line
        # make list of (host,port)
        def makeHostPortListFromString(nodeList):
            nodes = []
            for node in nodeList:
                splitNode = node.split(":")
                nodes.append( (splitNode[0], int(splitNode[1])) )
            return nodes
        registryNodes = makeHostPortListFromString(registryNodes)

        # for local test, just find the node with the same port
        localNodeName = None
        for node in registryNodes:
            if node[1] == self.port:
                localNodeAddr = node

        if localNodeAddr not in registryNodes:
            raise Exception ("Error: this node " + localNodeAddr + " is not listed in the master list.  The current registry requires all nodes to know about each other.")
        registryNodes.remove(localNodeAddr)
        print "localNode:", localNodeAddr
        print "otherNodes:", registryNodes

        self.registryNodes = []

    def RefreshNodeList(self, url=None):
        # Allows a running node to refresh its node list in case a node has been manually added or removed.
        # Call to this function probably would be initiated manually.
        if url == None:
            url = self.nodeListUrl
        self._readNodeList(url)

    def ConnectToRegistries(self):
        for node in self.registryNodes:
            try:
                print "Would connect to:", node
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
    def __init__(self, port, nodeListUrl, localTest=False):
        RegistryBase.__init__(self, port, nodeListUrl, localTest)
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
    defaultPort = 16000
    parser = OptionParser()
    parser.add_option("-p", "--port", dest="port", default=defaultPort, help="Listening port.", type="int")
    (options, ret_args) = parser.parse_args(args=sys.argv)

    # r = RegistryPeer(nodeListUrl="http://www.mcs.anl.gov/~eolson/registry_nodes.txt", port=options.port)
    r = RegistryPeer(nodeListUrl="../../tests/localhost_registry_nodes.txt", port=options.port, localTest=True)
    r.Run()
    

