#-----------------------------------------------------------------------------
# Name:        QuickBridgeClient.py
# Purpose:     Interface to a QuickBridge server.
# Created:     2005/12/06
# RCS-ID:      $Id: QuickBridgeClient.py,v 1.8 2006-12-19 21:50:53 turam Exp $
# Copyright:   (c) 2005-2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import time
import select
import socket
import xmlrpclib
from AccessGrid.NetworkLocation import MulticastNetworkLocation, UnicastNetworkLocation
from GUID import GUID
from BridgeClient import BridgeClient
from AccessGrid.UrllibTransport import UrllibTransport, TimeoutTransport
from AccessGrid import Utilities
from AccessGrid.Descriptions import BridgeDescription
from AccessGrid import Log
log = Log.GetLogger("QuickBridgeClient")

class ConnectionError(Exception): pass

class QuickBridgeClient(BridgeClient):
    def __init__(self, host=None, port=None,timeout=1):
        BridgeClient.__init__(self, host, port)
        
        transport = None
        self.proxyURL = Utilities.BuildPreferencesProxyURL()
        if self.proxyURL:
            self.transport = UrllibTransport(self.proxyURL,timeout)
        else:
            self.transport = TimeoutTransport(timeout)
        url = "http://%s:%s" % (host,str(port))
        self.serverProxy = xmlrpclib.ServerProxy(url, transport = self.transport, verbose = 0)
        self.host = host
        self.port = port
        
    def SetHostPort(self,host,port):
        self.host = host
        self.port = port
        url = "http://%s:%s" % (host,str(port))
        self.serverProxy = xmlrpclib.ServerProxy(url, transport = self.transport, verbose = 0)
    
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
            
    def PingBridge(self):
        ret = -1
        try:
            startTime = self.serverProxy.Ping(time.time())
            roundTripTime = time.time() - startTime
            if roundTripTime >= 0.0:
                ret = roundTripTime
            else:
                ret = BridgeDescription.UNREACHABLE
        except socket.timeout:
            log.exception('Timeout pinging bridge: %s', self.host)
            ret =  BridgeDescription.UNREACHABLE
        except socket.error,e:
            log.info('Socket error pinging bridge: %s %s', self.host, str(e.args))
            ret =  BridgeDescription.UNREACHABLE
        except Exception,e:
            if 'method "Ping" is not supported' in str(e):
                log.info('Ping not supported, old bridge, regard as unreachable: %s', self.host)
            else:
                log.exception('Exception pinging bridge: %s', self.host )
            ret =  BridgeDescription.UNREACHABLE
        return ret

if __name__=="__main__":
    bc = QuickBridgeClient(host="milton.mcs.anl.gov", port=8030)
    multicastNetworkLocation = MulticastNetworkLocation(host="233.4.200.18", port=10002, ttl=1)
    multicastNetworkLocation.id = GUID()
    multicastNetworkLocation.privateId = GUID()
    multicastNetworkLocation.profile=("","")
    print dir(multicastNetworkLocation)
    print multicastNetworkLocation.__dict__
    desc = bc.JoinBridge(multicastNetworkLocation)
    print "Multicast location: ", multicastNetworkLocation
    print "Unicast location: ", desc
    print "Ping: ", bc.PingBridge()
    print "Test: ", bc.TestBridge(multicastNetworkLocation)

