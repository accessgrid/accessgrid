#-----------------------------------------------------------------------------
# Name:        QuickBridgeClient.py
# Purpose:     Interface to a QuickBridge server.
# Created:     2005/12/06
# RCS-ID:      $Id: QuickBridgeClient.py,v 1.8 2006-12-19 21:50:53 turam Exp $
# Copyright:   (c) 2005-2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket
import xmlrpclib
from NetworkLocation import MulticastNetworkLocation, UnicastNetworkLocation
from GUID import GUID
from BridgeClient import BridgeClient
from AccessGrid.UrllibTransport import UrllibTransport, TimeoutTransport

class ConnectionError(Exception): pass

class QuickBridgeClient(BridgeClient):
    def __init__(self, host, port, proxyHost=None, proxyPort=None,timeout=1):
        BridgeClient.__init__(self, host, port)
        
        transport = None
        if proxyHost:
            if proxyPort:
                proxyURL = "http://%s:%s" % (proxyHost, proxyPort)
            else:
                proxyURL = "http://%s" % (proxyHost)

            transport = UrllibTransport(proxyURL,timeout)
        else:
            transport = TimeoutTransport(timeout)
        url = "http://%s:%s" % (host,str(port))
        self.serverProxy = xmlrpclib.ServerProxy(url, transport = transport, verbose = 0)
        self.host = host
        self.port = port

    def JoinBridge(self, multicastNetworkLocation):
        try:
            l = self.serverProxy.JoinBridge(multicastNetworkLocation)
        except socket.error,e:
            raise ConnectionError(e.args)
        desc = UnicastNetworkLocation(l["host"], l["port"])
        desc.type = l["type"]
        desc.privateId = l["privateId"]
        desc.id = l["id"]
        desc.profile.name = l["profile"]["name"]
        desc.profile.location = l["profile"]["location"] 

        return desc 
        
    def GetBridgeInfo(self):
        try:
            return self.serverProxy.GetBridgeInfo()
        except socket.error,e:
            raise ConnectionError(e.args)

if __name__=="__main__":
    # Example below.  You should start Bridge.py first.
    bc = QuickBridgeClient(host="milton.mcs.anl.gov", port=8030)
    multicastNetworkLocation = MulticastNetworkLocation(host="224.2.2.2", port=9700, ttl=1)
    multicastNetworkLocation.id = GUID()
    multicastNetworkLocation.privateId = GUID()
    multicastNetworkLocation.profile=("","")
    print dir(multicastNetworkLocation)
    print multicastNetworkLocation.__dict__
    desc = bc.JoinBridge(multicastNetworkLocation)
    print desc

