#-----------------------------------------------------------------------------
# Name:        NetService.py
# Purpose:     This is the base class for Network Services.
#
# Author:      Thomas D. Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: NetService.py,v 1.5 2003-09-16 07:25:34 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: NetService.py,v 1.5 2003-09-16 07:25:34 judson Exp $"
__docformat__ = "restructuredtext en"

class UnknownNetServiceType(Exception):
    pass

class NetService:

    TYPE = "NetService"
    def __init__(self,venue,privateId):
        self.venue = venue
        self.privateId = privateId
        self.type = self.TYPE
        self.connObj = None

    def SetConnection(self, connObj):
        self.connObj = connObj

    def Stop(self):
        pass

class BridgeNetService(NetService):
    TYPE = "BridgeNetService"
    def Stop(self):
        self.venue.RemoveNetworkLocationsByPrivateId(self.privateId)

class DataStoreNetService(NetService):
    TYPE = "DataStoreNetService"
    def Stop(self):
        self.venue.RemoveNetworkLocationsByPrivateId(self.privateId)

        
def CreateNetService(netServiceType, venue, privateId):
    netService = None
    
    # Create a net service of the requested type
    if netServiceType == BridgeNetService.TYPE:
        netService = BridgeNetService(venue, privateId)

    elif netServiceType == DataStoreNetService.TYPE:
        netService = DataStoreNetService(venue, privateId)
        
    else:
        raise UnknownNetServiceType("Unknown net service requested %s" % (netServiceType) )
 
    return netService
    
   
if __name__ == "__main__":


    venue = "Venue"
    privateId = "private id"
    netService = CreateNetService(BridgeNetService.TYPE,venue,privateId)
    print netService.__class__
    print netService.venue
    print netService.privateId


