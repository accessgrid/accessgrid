#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        Bridge.py
# Purpose:     Provide a bridging service for venues.
# Created:     2005/12/06
# RCS-ID:      $Id: Bridge.py,v 1.3 2005-12-12 20:21:49 eolson Exp $
# Copyright:   (c) 2005-2006
# License:     See COPYING.txt
#-----------------------------------------------------------------------------

import sys, os
from optparse import OptionParser
from AccessGrid.Registry.RegistryClient import RegistryClient
from AccessGrid.Registry.RegistryPeer import AGXMLRPCServer
from AccessGrid.BridgeFactory import BridgeFactory
from AccessGrid.Descriptions import BridgeDescription, QUICKBRIDGE_TYPE, StreamDescription
from AccessGrid.NetworkLocation import UnicastNetworkLocation, ProviderProfile
from AccessGrid.GUID import GUID
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid import Log
from AccessGrid import Toolkit
log = None

class QuickBridgeServer:
    def __init__(self, name, location, listenPort, qbexec, registryUrl, portRange=None):
        if not os.path.exists(qbexec):
            raise Exception("QuickBridge executable does not exist at this location:", qbexec)
        self.bridgeFactory = BridgeFactory(qbexec=qbexec, portRange=portRange, logger=log)
        self.providerProfile = ProviderProfile(name, location)
        self.listenPort = listenPort
        self.listeningServer = AGXMLRPCServer( ("", listenPort) )
        self._RegisterRemoteFunctions()
        self.registryClient = RegistryClient(url=registryUrl)
        hostname = SystemConfig.instance().GetHostname()
        self.portRange = portRange
        if portRange == None:
            self.portMin = None
            self.portMax = None
        else:
            self.portMin = self.portRange[0]
            self.portMax = self.portRange[1]
        self.bridgeDescription = BridgeDescription(guid=GUID(), name=name, host=hostname, port=self.listenPort, serverType="QUICKBRIDGE_TYPE", description="")
        self.registryClient.RegisterBridge(self.bridgeDescription)

    def _RegisterRemoteFunctions(self):
        self.listeningServer.register_function(self.JoinBridge, "JoinBridge")

    def JoinBridge(self,multicastNetworkLocation):
        mnl = multicastNetworkLocation
        uaddr = SystemConfig.instance().GetHostname()
        if self.portRange == None:
            uport = self.bridgeFactory.addressAllocator.AllocatePort(even=True)
        else:
            uport = self.bridgeFactory.addressAllocator.AllocatePortInRange(even=True, portBase=self.portMin, portMax=self.portMax)
        bridge = self.bridgeFactory.CreateBridge(id=mnl["id"], maddr=mnl["host"],
                    mport=mnl["port"], mttl=mnl["ttl"], uaddr=uaddr, uport=uport)
        networkLocation = UnicastNetworkLocation(host=uaddr, port=uport)
        networkLocation.profile = self.providerProfile
        networkLocation.id = GUID()
        networkLocation.privateId = GUID()
        return networkLocation

    def Run(self):
        try:
            self.listeningServer.serve_forever()
        except Exception, e:
            print e

    def SetName(self,name):
        self.providerProfile.name = name
            
    def SetLocation(self,location):
        self.providerProfile.location = location
        
    def SetBridgeExecutable(self,qbexec):
        self.bridgeFactory.SetBridgeExecutable(qbexec)

    def Shutdown(self):
        """
        Shutdown shuts down the BridgeServer. 
        - Stop bridges
        """
        log.info("Method BridgeServer.Shutdown called")


def main():
    import signal
    bridgeServer = None


    defaultListenPort = 20000
    defaultQbexec="/usr/bin/QuickBridge"
    # maxConnections? , maxBridges?, recycleTimeout?
    from optparse import OptionParser 
    parser = OptionParser()
    parser.add_option("-p", "--listenPort", dest="listenPort", default=defaultListenPort, help="Port to listen on.", type="int")
    parser.add_option("-u", "--registryUrl", dest="registryUrl", default=None, help="Url to the registry.  Bridge will register with it.")
    parser.add_option("-r", "--portRange", dest="portRange", default=None, help="Minimum and maximum port.", nargs=2, type="int")
    parser.add_option("-q", "--qbexec", dest="qbexec", default=defaultQbexec, help="Location of QuickBridge executable.")
    parser.add_option("-n", "--name", dest="name", default=None, help="Name.")
    parser.add_option("-l", "--location", dest="location", default=None, help="Location.")

    (options, ret_args) = parser.parse_args(args=sys.argv)

    # Init toolkit with standard environment.
    app = Toolkit.Service.instance()

    try:
        app.Initialize("QuickBridgeServer", args=ret_args)
    except:
        print "Failed to initialize toolkit, exiting."
        sys.exit(-1)

    global log
    log = app.GetLog()

    if options.name == None or options.location == None:
        raise Exception("Please specify both a name and location.")
    if options.registryUrl == None:
        raise Exception("Please specify the registry url.")

    """
    # Signal handler to catch signals and shutdown
    def SignalHandler(signum, frame):
        " SignalHandler catches signals and shuts down the BridgeServer "
        print "Shutting down..."
        bridgeServer.Shutdown() 
        print "SignalHandler exiting."

    # Register a signal handler so we can shut down cleanly
    signal.signal(signal.SIGINT, SignalHandler)
    if sys.platform != 'win32':
        signal.signal(signal.SIGHUP, SignalHandler)
    """

    bridgeServer = QuickBridgeServer(name=options.name, location=options.location, listenPort=options.listenPort, qbexec=options.qbexec, portRange=options.portRange, registryUrl=options.registryUrl)

    bridgeServer.Run()

if __name__ == "__main__":
    main()

# Example: Expects you have started a RegistryPeer.py so it can register somewhere.
#      Once started, QuickBridgeClient.py should be able to request/join this bridge.
# Sample osx commandline 2005/12/06:  python Bridge.py  --name=yorgle --location=Argonne --registryUrl=../tests/localhost_registry_nodes.txt --qbexec=/Applications/AccessGridToolkit.app/Contents/Resources/bin/QuickBridge
