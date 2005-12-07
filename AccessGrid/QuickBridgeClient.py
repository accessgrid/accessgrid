#-----------------------------------------------------------------------------
# Name:        QuickBridgeClient.py
# Purpose:     Interface to a QuickBridge server.
# Created:     2005/12/06
# RCS-ID:      $Id: QuickBridgeClient.py,v 1.1 2005-12-07 01:47:34 eolson Exp $
# Copyright:   (c) 2005-2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import xmlrpclib
from NetworkLocation import MulticastNetworkLocation
from GUID import GUID
from BridgeClient import BridgeClient

class QuickBridgeClient(BridgeClient):
    def __init__(self, host, port):
        BridgeClient.__init__(self, host, port)
        self.serverProxy = xmlrpclib.ServerProxy("http://" + host + ":" + str(port))

    def JoinBridge(self, multicastNetworkLocation):
        self.serverProxy.JoinBridge(multicastNetworkLocation)

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

