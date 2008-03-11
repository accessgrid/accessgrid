#-----------------------------------------------------------------------------
# Name:        UMTPClient.py
# Purpose:     Interface for UMTP Servers
# Created:     2006/06/22
# RCS-ID:      $Id: UMTPClient.py,v 1.1 2006/06/26 13:29:30 ngkim Exp $
#-----------------------------------------------------------------------------

from AccessGrid.Preferences import Preferences
from AccessGrid.Registry.RegistryClient import RegistryClient
from AccessGrid.UMTP import UMTPAgent
from AccessGrid.BridgeClient import BridgeClient
from AccessGrid import Log
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.GUID import GUID

log = Log.GetLogger("UMTPClient")
            
class UMTPClient(BridgeClient):
    def __init__(self, host=None, port=None,timeout=1):
        BridgeClient.__init__(self, host, port)
        
        self.host = host
        self.port = port
        
        self.agent = UMTPAgent(log)
        
    def SetHostPort(self,host,port):
        self.host = host
        self.port = port
    
    def JoinBridge(self, multicastNetworkLocation):

        
        self.agent.SetStreamList([multicastNetworkLocation])
        self.agent.SetServer((self.host,self.port))
        self.agent.Start()
        return multicastNetworkLocation
        
    def GetBridgeInfo(self):
        return None

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
        raise Exception("Not yet implemented")
         

if __name__ == '__main__':
    bc = UMTPClient(host="milton.mcs.anl.gov", port=52000)
    multicastNetworkLocation = MulticastNetworkLocation(host="224.2.224.15", port=20002, ttl=1)
    multicastNetworkLocation.id = GUID()
    multicastNetworkLocation.privateId = GUID()
    multicastNetworkLocation.profile=("","")
    print dir(multicastNetworkLocation)
    print multicastNetworkLocation.__dict__
    print "Multicast location: ", multicastNetworkLocation
    print "Test: ", bc.TestBridge(multicastNetworkLocation)
    



            