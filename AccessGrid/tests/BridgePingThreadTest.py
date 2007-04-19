import time

from AccessGrid.Preferences import Preferences
from AccessGrid.VenueClient import BridgePingThread
from AccessGrid.Registry.RegistryClient import RegistryClient
from AccessGrid.Descriptions import BridgeDescription

def main():
    prefs = Preferences()
    registryClient = RegistryClient('http://www.accessgrid.org/registry/peers.txt')
    bridgeList = prefs.GetBridges()
    bridgePinger = BridgePingThread(prefs,registryClient,bridgeList.values())
    bridgePinger.start()

    while 1:
        bridges = prefs.GetBridges().values()
        bridges.sort(lambda x,y: BridgeDescription.sort(x, y, 1))
        for b in bridges:
            print '%2.5f %s' % (b.rank, b.name)
        print 'sleeping for ', bridgePinger.refreshDelay
        time.sleep(bridgePinger.refreshDelay)

main()
