

class UnknownNetServiceType(Exception):
    pass

class NetService:

    TYPE = "NetService"
    def __init__(self,venue,privateId):
        self.venue = venue
        self.privateId = privateId
        self.type = self.TYPE

    def Stop(self):
        pass

class BridgeNetService(NetService):
    TYPE = "BridgeNetService"
    def Stop(self):
        self.venue.RemoveNetworkLocationsByPrivateId(self.privateId)

def CreateNetService(netServiceType, venue, privateId):

    netService = None
    
    # Create a net service of the requested type
    if netServiceType == BridgeNetService.TYPE:
        netService = BridgeNetService(venue, privateId)
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


