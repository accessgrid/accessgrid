#-----------------------------------------------------------------------------
# Name:        QuickBridgeClient.py
# Purpose:     Interface to a QuickBridge server.
# Created:     2005/12/06
# RCS-ID:      $Id: QuickBridgeClient.py,v 1.8 2006-12-19 21:50:53 turam Exp $
# Copyright:   (c) 2005-2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import select
import socket
import xmlrpclib
from AccessGrid.NetworkLocation import MulticastNetworkLocation, UnicastNetworkLocation
from GUID import GUID
from BridgeClient import BridgeClient
from AccessGrid.UrllibTransport import UrllibTransport, TimeoutTransport
from AccessGrid import Utilities
from AccessGrid import Log
log = Log.GetLogger("QuickBridgeClient")

class ConnectionError(Exception): pass

class QuickBridgeClient(BridgeClient):
    def __init__(self, host, port,timeout=1):
        BridgeClient.__init__(self, host, port)
        
        transport = None
        proxyURL = Utilities.BuildPreferencesProxyURL()
        if proxyURL:
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

    def TestBridge(self,multicastNetworkLocation):
        timeout = 1
        MSGSIZE = 500
        ret = 0
        s = None
        try:
            desc = self.JoinBridge(multicastNetworkLocation)
        
            # Create a socket, send some data to the bridge, and listen for data from the bridge
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2)
            s.bind(('', desc.GetPort()))
            s.sendto('qwe',(desc.host,desc.port))
            fdList = select.select([s.fileno()],[],[],timeout)
            if fdList[0] and s.fileno() in fdList[0]:
                data,src_addr = s.recvfrom(MSGSIZE)
                ret = 1
        except Exception, e:
            log.exception("Error testing bridge")
        if s:
            s.close()
            
        return ret
            


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
    print bc.TestBridge("233.4.200.18", 10002)

