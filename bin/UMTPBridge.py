#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        Bridge.py
# Purpose:     Provide a bridging service for venues.
# Created:     2005/12/06
# RCS-ID:      $Id: UMTPServer3.py,v 1.1 2006/06/29 01:07:06 ngkim Exp $
# Copyright:   (c) 2005-2006
# License:     See COPYING.txt
#-----------------------------------------------------------------------------

import sys, os
import time
from optparse import OptionParser
from AccessGrid.Registry.RegistryClient import RegistryClient
from AccessGrid.AGXMLRPCServer import AsyncAGXMLRPCServerThreaded
from AccessGrid.Descriptions import BridgeDescription, UMTP_TYPE, StreamDescription
from AccessGrid.NetworkLocation import UnicastNetworkLocation, ProviderProfile
from AccessGrid.NetworkAddressAllocator import NetworkAddressAllocator
from AccessGrid.Platform import IsWindows, IsLinux, IsOSX
from AccessGrid.Platform.ProcessManager import ProcessManager
from AccessGrid.GUID import GUID
from AccessGrid.Platform.Config import SystemConfig, AGTkConfig
from AccessGrid import Log
from AccessGrid import Toolkit
import random
log = None

class UMTPServer:
    def __init__(self, name, location, listenPort, umtpexec, registryUrlList, dataPort=None):
        if not os.path.exists(umtpexec):
            raise Exception("UMTP executable does not exist at this location:", umtpexec)
        self.umtpexec = umtpexec
        self.providerProfile = ProviderProfile(name, location)
        self.listenPort = listenPort
        self.dataPort = dataPort

        self.listeningServer = AsyncAGXMLRPCServerThreaded( ("", listenPort), intervalSecs=1, 
                                                    callback=self.MaintenanceCallback,
                                                    logRequests=0)
        
        self._RegisterRemoteFunctions()
        self.registryClients = []
        for registryUrl in registryUrlList:
            self.registryClients.append(RegistryClient(url=registryUrl))
        self.hostname = SystemConfig.instance().GetHostname()
        self.hostip = SystemConfig.instance().GetLocalIPAddress()
        self.addressAllocator = NetworkAddressAllocator()
        self.bridgeDescription = BridgeDescription(guid=GUID(), name=name, host=self.hostname, 
                                                   port=self.listenPort, serverType=UMTP_TYPE, 
                                                   description="", 
                                                   portMin=dataPort,
                                                   portMax=dataPort)
        self._RegisterWithRegistry()

        # Instantiate the process manager
        self.processManager = ProcessManager()
        self.processManager.WaitForChildren(self.OnProcessDeath)

        self.running = False

    def _RegisterRemoteFunctions(self):
        self.listeningServer.register_function(self.Ping, "Ping")

    def Ping(self, data):
        return data

    def _RegisterWithRegistry(self):
        self.validSecs = -1
        for registry in self.registryClients:
            try:
                secs = registry.RegisterBridge(self.bridgeDescription)
                if self.validSecs == -1 or self.validSecs > secs:
                    self.validSecs = secs;
            except:
                print("Error connecting to bridge registry at " + registry.url)
                log.error("Error connecting to bridge registry at " + registry.url)
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
        except Exception,e:
            secsToSleep = random.randrange(5,60)
            log.error("Error reregistering, retry in " + str(secsToSleep) + " seconds.")
            time.sleep(secsToSleep)

    def Run(self):
        self.running = True
        self.ExecuteProcess()
        self.listeningServer.run()        

    def ExecuteProcess(self):
        """
        Start the UMTP Server (actually execute the UMTP Server process)
        """
        log.info("Method UMTPServer.ExecuteProcess called")

        # Start the process
        args = [
                "-s", self.hostip, self.dataPort
               ]
        log.info("Starting UMTP Server: %s %s", self.umtpexec, str(args))
        print "Starting UMTP Server: %s %s" % (self.umtpexec, str(args))
        self.processManager.StartProcess(self.umtpexec,args)

    def StopProcess(self):
        """
        StopProcess stops the UMTP Server, terminating UMTP Server process
        """
        log.info("Method UMTPServer.StopProcess called")
        print "Method UMTPServer.StopProcess called"
        self.processManager.TerminateAllProcesses()
        self.listeningServer.stop()
        self.running = False

    def OnProcessDeath(self):
        self.running = False
        self.Shutdown()

    def SetName(self,name):
        self.providerProfile.name = name
            
    def SetLocation(self,location):
        self.providerProfile.location = location
        
    def Shutdown(self):
        """
        Shutdown shuts down the UMTPServer. 
        - Stop UMTP Server
        """
        if self.running:
           print "UMTPServer.Shutdown stop process"
           self.listeningServer.stop()
           self.StopProcess()
           self.running = False
        log.info("Method UMTPServer.Shutdown called")


def main():
    import signal
    bridgeServer = None

    defaultListenPort = 20000
    defaultUMTPPort = 50000
    
    executable = None
    if   IsWindows() : 
        executable = "umtp.exe"
    elif IsLinux(): 
        executable = "umtp"
        os.chmod(executable, 0755) # make umtp_linux file executable 
    elif IsOSX(): 
        executable = "umtp"
        os.chmod(executable, 0755) # make umtp_linux file executable 

    defaultexec = os.path.join(AGTkConfig.instance().GetBinDir(), executable)
    print 'defaultexec = ', defaultexec
    defaultRegistryUrlList=['http://www.accessgrid.org/registry/peers.txt']
    # maxConnections? , maxBridges?, recycleTimeout?

    parser = OptionParser()
    parser.add_option("-p", "--listenPort", dest="listenPort", default=defaultListenPort, help="Port to listen on.", type="int")
    parser.add_option("-u", "--registryUrl", action="append", dest="registryUrlList", default=defaultRegistryUrlList, help="Url to the registry.  UMTP Server will register with it.")
    parser.add_option("-r", "--port", dest="port", default=defaultUMTPPort, help="Minimum and maximum port, space-separated.", type="int")
    parser.add_option("-x", "--exec", dest="umtpexec", default=defaultexec, help="Location of UMTP executable.")
    parser.add_option("-n", "--name", dest="name", default=None, help="Name.")
    parser.add_option("-l", "--location", dest="location", default=None, help="Location.")

    (options, ret_args) = parser.parse_args(args=sys.argv)

    # Init toolkit with standard environment.
    app = Toolkit.Service.instance()

    try:
        app.Initialize("UMTPBridge", args=ret_args)
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
    if options.registryUrlList == None:
        print 'Error: No registry url specified'
        parser.print_help()
        sys.exit(-1)
        
    # Signal handler to catch signals and shutdown
    def SignalHandler(signum, frame):
        " SignalHandler catches signals and shuts down the UMTP Server "
        print "Shutting down..."
        umtpServer.Shutdown() 
        print "SignalHandler exiting."

    # Register a signal handler so we can shut down cleanly
    signal.signal(signal.SIGINT, SignalHandler)
    if sys.platform != 'win32':
        signal.signal(signal.SIGHUP, SignalHandler)

    umtpServer = UMTPServer(name=options.name, location=options.location, listenPort=options.listenPort, umtpexec=options.umtpexec, dataPort=options.port, registryUrlList=options.registryUrlList)

    umtpServer.Run()

if __name__ == "__main__":
    main()

# Sample commandline:  python UMTPServer3.py  --name=yorgle --location=Argonne
