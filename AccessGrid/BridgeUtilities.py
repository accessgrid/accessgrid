
from AccessGrid import Log
from AccessGrid.Descriptions import STATUS_ENABLED, STATUS_DISABLED, BridgeDescription
from AccessGrid.QuickBridgeClient import QuickBridgeClient

log = Log.GetLogger("BridgeUtilities")

def TestBridges(bridgeList, multicastNetworkLocation, progressCB=None):
    '''
    '''
    bridgeClient = QuickBridgeClient()

    i = 1
    for b in bridgeList:
        try:
            if progressCB:  progressCB("Testing bridge: %d of %d" % (i,len(bridgeList)), 50)
            bridgeClient.SetHostPort(b.host,b.port)
            b.rank = bridgeClient.PingBridge()
            
            if b.rank != BridgeDescription.UNREACHABLE:
                # test whether we get data from the bridge
                try:
                    ret = bridgeClient.TestBridge(multicastNetworkLocation)
                    if ret:
                        b.status = STATUS_ENABLED
                    else:
                        b.status = STATUS_DISABLED
                except:
                    log.exception("Exception testing bridge %s (%s:%d)", b.name, b.host, b.port)
                    b.status = STATUS_DISABLED
            else:
                b.status = STATUS_DISABLED
        except:
            import traceback
            traceback.print_exc()
            log.exception("Exception testing bridge %s (%s)", b.name, b.host)
        i += 1

    return bridgeList




if __name__ == '__main__':
    from AccessGrid.Registry.RegistryClient import RegistryClient
    from AccessGrid.NetworkLocation import MulticastNetworkLocation
    registryUrl = 'http://www.accessgrid.org/registry/peers.txt'
    registryClient = RegistryClient(registryUrl)
    bridgeList = registryClient.LookupBridge()
    
    def ProgressCB(message,progress):
        print message
    
    mcTestAddr = "233.4.200.18"
    mcTestPort = 10002
    multicastNetworkLocation = MulticastNetworkLocation(mcTestAddr,mcTestPort,1)
    
    TestBridges(bridgeList, multicastNetworkLocation,ProgressCB)
    
    for b in bridgeList:
        print b.name, b.host, b.rank, b.status
        