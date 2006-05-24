#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        Bridge.py
# Purpose:     Provide a bridging service for venues.
# Created:     2005/12/06
# RCS-ID:      $Id: Bridge.py,v 1.17 2006-05-24 23:35:31 eolson Exp $
# Copyright:   (c) 2005-2006
# License:     See COPYING.txt
#-----------------------------------------------------------------------------

import sys, os
import time
from optparse import OptionParser
from AccessGrid.Registry.RegistryClient import RegistryClient
from AccessGrid.AGXMLRPCServer import AsyncAGXMLRPCServer
from AccessGrid.BridgeFactory import BridgeFactory
from AccessGrid.Descriptions import BridgeDescription, QUICKBRIDGE_TYPE, StreamDescription
from AccessGrid.NetworkLocation import UnicastNetworkLocation, ProviderProfile
from AccessGrid.GUID import GUID
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid import Log
from AccessGrid import Toolkit
import traceback
import random
log = None

class QuickBridgeServer:
    def __init__(self, name, location, listenPort, qbexec, registryUrl, portRange=None):
        if not os.path.exists(qbexec):
            raise Exception("QuickBridge executable does not exist at this location:", qbexec)
        self.bridgeFactory = BridgeFactory(qbexec=qbexec, portRange=portRange, logger=log)
        self.providerProfile = ProviderProfile(name, location)
        self.listenPort = listenPort
        self.listeningServer = AsyncAGXMLRPCServer( ("", listenPort), intervalSecs=1, 
                                                    callback=self.MaintenanceCallback,
                                                    logRequests=0)
        self._RegisterRemoteFunctions()
        self.registryClient = RegistryClient(url=registryUrl)
        hostname = SystemConfig.instance().GetHostname()
        self.bridgeDescription = BridgeDescription(guid=GUID(), name=name, host=hostname, 
                                                   port=self.listenPort, serverType=QUICKBRIDGE_TYPE, 
                                                   description="", 
                                                   portMin=self.bridgeFactory.GetPortMin(),
                                                   portMax=self.bridgeFactory.GetPortMax())
        self._RegisterWithRegistry()
        self.running = False

    def _RegisterRemoteFunctions(self):
        self.listeningServer.register_function(self.JoinBridge, "JoinBridge")
        self.listeningServer.register_function(self.GetBridgeInfo, "GetBridgeInfo")
        self.listeningServer.register_function(self.Ping, "Ping")

    def JoinBridge(self,multicastNetworkLocation):
        mnl = multicastNetworkLocation
        log.info("Bridge request: mcast %s %s" % (mnl["host"],str(mnl["port"])))
        uaddr = SystemConfig.instance().GetHostname()
        retBridge = self.bridgeFactory.CreateBridge(id=mnl["id"], maddr=mnl["host"],
                    mport=mnl["port"], mttl=mnl["ttl"], uaddr=uaddr,uport=None)
        networkLocation = UnicastNetworkLocation(host=retBridge.uaddr, port=retBridge.uport)
        networkLocation.profile = self.providerProfile
        networkLocation.id = GUID()
        networkLocation.privateId = GUID()
        return networkLocation
        
    def GetBridgeInfo(self):
        ret = []
        bridges = self.bridgeFactory.GetBridges()
        print 'bridges = ', bridges
        for bridge in bridges:
            bridgedata = {'maddr': bridge.maddr,
                          'mport': bridge.mport,
                          'uaddr': bridge.uaddr,
                          'uport': bridge.uport 
                          }
            ret.append(bridgedata)
        return ret

    def Ping(self, data):
        return data

    def _RegisterWithRegistry(self):
        self.validSecs = self.registryClient.RegisterBridge(self.bridgeDescription)
        now = time.time()
        if self.validSecs == True:  # only needed until registry code is updated
            self.validSecs = 120  # expires every 2 minutes
        self.registrationExpirationTime = now + self.validSecs
        self.nextRegistrationTime = now + (self.validSecs * .9 - 10)

    def _RegisterWithRegistryIfNeeded(self):
        if time.time() > self.nextRegistrationTime:
            self._RegisterWithRegistry()

    def MaintenanceCallback(self):
        try:
            self._RegisterWithRegistryIfNeeded()
        except:
            secsToSleep = random.randrange(5,60)
            log.error("Error reregistering, retry in " + str(secsToSleep) + " seconds.")
            time.sleep(secsToSleep)

    def Run(self):
        self.listeningServer.run()

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
    defaultRegistryUrl='http://www.accessgrid.org/registry/peers.txt'
    # maxConnections? , maxBridges?, recycleTimeout?

    parser = OptionParser()
    parser.add_option("-p", "--listenPort", dest="listenPort", default=defaultListenPort, help="Port to listen on.", type="int")
    parser.add_option("-u", "--registryUrl", dest="registryUrl", default=defaultRegistryUrl, help="Url to the registry.  Bridge will register with it.")
    parser.add_option("-r", "--portRange", dest="portRange", default=[50000,52000], help="Minimum and maximum port, space-separated.", nargs=2, type="int")
    parser.add_option("-q", "--qbexec", dest="qbexec", default=defaultQbexec, help="Location of QuickBridge executable.")
    parser.add_option("-n", "--name", dest="name", default=None, help="Name.")
    parser.add_option("-l", "--location", dest="location", default=None, help="Location.")

    (options, ret_args) = parser.parse_args(args=sys.argv)

    # Init toolkit with standard environment.
    app = Toolkit.Service.instance()

    try:
        app.Initialize("Bridge", args=ret_args)
    except:
        print "Failed to initialize toolkit, exiting."
        sys.exit(-1)

    global log
    log = app.GetLog()

    if options.name == None:
        print 'Error: No name specified'
        parser.print_help()
        sys.exit(-1)
    if options.location == None:
        print 'Error: No location specified'
        parser.print_help()
        sys.exit(-1)
    if options.registryUrl == None:
        print 'Error: No registry url specified'
        parser.print_help()
        sys.exit(-1)
        
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

# Sample commandline:  python Bridge.py  --name=yorgle --location=Argonne
