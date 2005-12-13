#-----------------------------------------------------------------------------
# Name:        QuickBridgeClient.py
# Purpose:     Interface to a QuickBridge server.
# Created:     2005/12/06
# RCS-ID:      $Id: QuickBridgeClient.py,v 1.3 2005-12-13 20:32:36 lefvert Exp $
# Copyright:   (c) 2005-2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import xmlrpclib
from NetworkLocation import MulticastNetworkLocation, UnicastNetworkLocation
from GUID import GUID
from BridgeClient import BridgeClient

class QuickBridgeClient(BridgeClient):
    def __init__(self, host, port):
        BridgeClient.__init__(self, host, port)
        self.serverProxy = xmlrpclib.ServerProxy("http://" + host + ":" + str(port))
        self.host = host
        self.port = port

    def JoinBridge(self, multicastNetworkLocation):
        l = self.serverProxy.JoinBridge(multicastNetworkLocation)
        desc = UnicastNetworkLocation(l["host"], l["port"])
        desc.type = l["type"]
        desc.privateId = l["privateId"]
        desc.id = l["id"]
        desc.profile.name = l["profile"]["name"]
        desc.profile.location = l["profile"]["location"] 

        return desc 

if __name__=="__main__":
    # Example below.  You should start Bridge.py first.
    bc = QuickBridgeClient(host="127.0.0.1", port=20000)
    multicastNetworkLocation = MulticastNetworkLocation(host="224.2.2.2", port=9700, ttl=1)
    multicastNetworkLocation.id = GUID()
    multicastNetworkLocation.privateId = GUID()
    multicastNetworkLocation.profile=("","")
    print dir(multicastNetworkLocation)
    print multicastNetworkLocation.__dict__
    bc.JoinBridge(multicastNetworkLocation)

