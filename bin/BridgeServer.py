#!/usr/bin/python2

import os
import logging
import Queue
import threading
import getopt

from pyGlobus.io import IOBaseException

from AccessGrid import NetService
from AccessGrid import Toolkit
from AccessGrid import Utilities
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.Events import Event, ConnectEvent, HeartbeatEvent
from AccessGrid.EventClient import EventClient, EventClientWriteDataException
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid.NetworkLocation import UnicastNetworkLocation, ProviderProfile
from AccessGrid.ProcessManagerUnix import ProcessManagerUnix as ProcessManager
from AccessGrid.Platform import GetUserConfigDir


logFile = os.path.join(GetUserConfigDir(), 'BridgeServer.log')


class BridgeFactory:
    """
    The BridgeFactory class is used to create and manage Bridges.
    If multiple bridges are requested for a multicast group, they
    use the same, single bridge.  When the reference count on a
    Bridge goes to zero, the Bridge is actually stopped and 
    deleted
    """

    class Bridge:
        """
        The Bridge class encapsulates execution of the bridge software
        """
        def __init__(self, qbexec,id, maddr, mport, mttl, uaddr, uport):
            self.qbexec = qbexec
            self.id = id
            self.maddr = maddr
            self.mport = mport
            self.mttl = mttl
            self.uaddr = uaddr
            self.uport = uport

            # Instantiate the process manager
            self.processManager = ProcessManager()

            # Setup the log
            self.log = logging.getLogger("AG.BridgeServer")

        def Start(self):
            """
            Start the Bridge (actually execute the bridge process)
            """
            self.log.debug("Method Bridge.Start called")

            # Log detail about bridge being started
            self.log.debug("Starting bridge:")
            self.log.debug("  [maddr,mport,mttl] = %s %d %d", self.maddr, self.mport, self.mttl)
            self.log.debug("  [uaddr,uport] = %s %d", self.uaddr, self.uport)

            # Start the process
            args = [
                    "-g", self.maddr,
                    "-m", '%d' % (self.mport,),
                    "-u", '%d' % (self.uport,),
                   ]
            self.processManager.start_process(self.qbexec,args)

        def Stop(self):
            """
            Stop stops the bridge, terminating bridge processes
            """
            self.log.debug("Method Bridge.Stop called")
            self.processManager.terminate_all_processes()


    def __init__(self, qbexec):
        self.qbexec = qbexec
        self.bridges = dict()
        self.log = logging.getLogger("AG.BridgeServer")

    def CreateBridge(self,id,maddr,mport,mttl,uaddr,uport):
        """
        This method returns an existing bridge for the given maddr/mport,
        or a new one
        """

        self.log.info("Method CreateBridge called")

        retBridge = None

        # - Check for an existing bridge with the given multicast addr/port
        for bridge,refcount in self.bridges.values():
            if bridge.maddr == maddr and bridge.mport == mport:
                self.log.info("- using existing bridge")
                retBridge = bridge
                refcount += 1
                key = "%s%d" % (maddr,mport)
                self.bridges[key] = (retBridge,refcount)

        # - If bridge does not exist; create one
        if not retBridge:
            # Instantiate a new bridge
            self.log.debug("- creating new bridge")
            retBridge = BridgeFactory.Bridge(self.qbexec,id,maddr,mport,mttl,uaddr,uport)
            retBridge.Start()
   
            # Add the bridge to the list of bridges
            key = "%s%d" % (retBridge.maddr,retBridge.mport)
            self.bridges[key] = (retBridge,1)

        return retBridge


    def DestroyBridge(self,bridge):
        """
        DestroyBridge deletes the specified bridge from the list of bridges
        """

        self.log.info("Method DestroyBridge called")

        key = "%s%d" % (bridge.maddr,bridge.mport)
        if self.bridges.has_key(key):
            bridge,refcount = self.bridges[key]
            refcount -= 1
            self.bridges[key] = (bridge,refcount)

            # if the refcount is 0,
            # stop and delete the bridge
            if refcount == 0:
                self.log.info("- Stopping and deleting bridge")
                bridge.Stop()
                del self.bridges[key]


class BridgeServer:
    def __init__(self, providerProfile, bridgeFactory, debug=0):
        self.providerProfile = providerProfile
        self.bridgeFactory = bridgeFactory
        self.debug = debug

        self.venues = dict()
        self.running = 1

        self.__setLogger()

    def AddVenue(self, venueUrl):
        """
        AddVenue adds the specified venue to those being bridged
        by the BridgeServer
        """
        self.log.debug("Method BridgeServer.AddVenue called")
        self.venues[venueUrl] = Venue(venueUrl, self.providerProfile, self.bridgeFactory)

    def RemoveVenue(self, venueUrl):
        """
        RemoveVenue stops the BridgeServer from bridging the 
        specified venue
        """
        self.log.debug("Method BridgeServer.RemoveVenue called")
        if self.venues.has_key(venueUrl):
            self.venues[venueUrl].Shutdown()
            del self.venues[venueUrl]
	    
    def GetVenues(self):
        """
        GetVenues returns the list of venues being bridged
        """
        self.log.debug("Method BridgeServer.GetVenues called")
        return self.venues.keys()

    def RemoveVenues(self):
        """
        RemoveVenues stops the BridgeServer from bridging all
        known venues
        """
        self.log.debug("Method BridgeServer.RemoveVenues called")

        # Shutdown the venues
        for venue in self.venues.values():
            venue.Shutdown()
        
        # Clear the venues dictionary
        self.venues.clear()

    def IsRunning(self):
        """
        IsRunning returns whether the BridgeServer is running
        """
        return self.running
  
    def Shutdown(self):
        """
        Shutdown shuts down the BridgeServer. 
        - Remove venues
        - Clear the running flag
        """
        self.log.debug("Method BridgeServer.Shutdown called")

        # Remove venues
        self.RemoveVenues()

        # Clear the running state
        self.running = 0
        
    def __setLogger(self):
        """
        Sets the logging mechanism.
        """
        self.log = logging.getLogger("AG.BridgeServer")
        self.log.setLevel(logging.DEBUG)

        hdlr = logging.FileHandler(logFile)
        extfmt = logging.Formatter("%(asctime)s %(thread)s %(name)s %(filename)s:%(lineno)s %(levelname)-5s %(message)s", "%x %X")
        fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
        hdlr.setFormatter(extfmt)
        self.log.addHandler(hdlr)

        if self.debug:
            hdlr = logging.StreamHandler()
            hdlr.setFormatter(fmt)
            self.log.addHandler(hdlr)


class Venue:

    EVT_ADDBRIDGE="AddBridge"
    EVT_REMOVEBRIDGE="RemoveBridge"
    EVT_QUIT="Quit"

    def __init__(self, venueUrl, providerProfile, bridgeFactory ):

        # Init data
        self.venueUrl = venueUrl
        self.providerProfile = providerProfile
        self.bridgeFactory = bridgeFactory

        self.venueProxy = Client.Handle(venueUrl).GetProxy()
        self.bridges = dict()
        self.queue = Queue.Queue()
        self.running = 1
        self.sendHeartbeats = 1

        self.log = logging.getLogger("AG.BridgeServer")

        # Register with the venue
        self.privateId = self.venueProxy.AddNetService(NetService.BridgeNetService.TYPE)

        # Create bridges for the venue streams
        streamList = self.venueProxy.GetStreams()
        for stream in streamList:
            self.AddBridge(stream)

        # Get the event service location and event channel id
        (eventServiceLocation, self.channelId) = self.venueProxy.GetEventServiceLocation()


        # Set up event client
        self.eventClient = EventClient(self.privateId, eventServiceLocation, self.channelId)
        self.eventClient.start()
        self.eventClient.Send(ConnectEvent(self.channelId, self.privateId))

        self.eventClient.RegisterCallback(Event.ADD_STREAM, self.EventReceivedCB)
        self.eventClient.RegisterCallback(Event.REMOVE_STREAM, self.EventReceivedCB)
        
        threading.Thread(target=self.RunQueueThread).start()
        threading.Thread(target=self.HeartbeatThread).start()


    def EventReceivedCB(self, event):
        """
        EventReceivedCB is a callback for the event client.
        It puts the received event on the queue for processing
        by the queue processing thread.
        """
        self.log.debug("Method Venue.EventReceivedCB called")
        if event.eventType == Event.ADD_STREAM:
            strDesc = event.data
            self.AddBridge(strDesc)
        elif event.eventType == Event.REMOVE_STREAM:
            strDesc = event.data
            self.RemoveBridge(strDesc.id)


    def AddBridge(self, streamDesc):
        """
        AddBridge puts an ADDBRIDGE event in the queue.
        The bridge will actually be added when the 
        queue processing thread gets the event.
        """
        self.queue.put( [Venue.EVT_ADDBRIDGE,streamDesc] )

    def RemoveBridge(self,id):
        """
        RemoveBridge puts a REMOVEBRIDGE event in the queue.
        The bridge will actually be removed when the
        queue processing thread gets the event.
        """
        self.queue.put( [Venue.EVT_REMOVEBRIDGE,id] )

    def __AddBridge(self, streamDesc):
        """
        AddBridge adds a bridge with the specified parameters
        """

        self.log.debug("Method Venue.AddBridge called")
        
        # Allocate a port for the bridge
        uaddr = Utilities.GetHostname()
        uport = MulticastAddressAllocator().AllocatePort()

        # Create the bridge and start it
        bridge = self.bridgeFactory.CreateBridge(streamDesc.id, 
                        streamDesc.location.host, 
                        streamDesc.location.port, 
                        streamDesc.location.ttl, 
                        uaddr, uport)
        self.bridges[streamDesc.id] = bridge

        # Add the related network location to the venue
        networkLocation = UnicastNetworkLocation(bridge.uaddr, bridge.uport)
        networkLocation.profile = self.providerProfile
        self.venueProxy.AddNetworkLocationToStream(self.privateId,
                                                   streamDesc.id,
                                                   networkLocation)
        return bridge
        
    def __RemoveBridge(self, id):
        """
        RemoveBridge removes the bridge with the specified id
        """
        self.log.debug("Method Venue.RemoveBridge called")
        self.log.debug("  id = %s", id)
        if self.bridges.has_key(id):
            self.log.debug("  removed")
            self.bridgeFactory.DestroyBridge(self.bridges[id])
            del self.bridges[id]
        else:  
            self.log.debug("  not found")
        
            
    def RunQueueThread(self):
        """
        RunQueueThread loops while the object is active,
        taking events from the queue and handling them
        appropriately
        """

        self.log.debug("Method Venue.RunQueueThread called")
    
        while self.running:
            event = self.queue.get(1)
            if event[0]==Venue.EVT_QUIT:
                break
            if event[0]==Venue.EVT_ADDBRIDGE:
                self.__AddBridge(event[1])
                continue
            if event[0]==Venue.EVT_REMOVEBRIDGE:
                self.__RemoveBridge(event[1])
                continue
             
        self.log.debug("RunQueueThread exiting")

    def HeartbeatThread(self):
        """
        HeartbeatThread loops while the object is active,
        to keep the connection with the Venue open
        """
        import time
        while self.sendHeartbeats:
            try:
                self.eventClient.Send(HeartbeatEvent(self.channelId, self.privateId))
            except EventClientWriteDataException:
                self.Shutdown()
                break
            except:
                self.log.exception("BridgeServer:Heartbeat: Heartbeat exception is caught.")
            time.sleep(10)
        self.log.debug("Heartbeat thread exiting")


    def Shutdown(self):
        """
        Shutdown shuts down the Venue
        - Remove Bridges
        - Stop the event client
        - Put an event on the queue, to stop it
        - Clear the running flag
        """
        self.log.debug("Method Venue.Shutdown called")

        # Stop sending heartbeats
        self.sendHeartbeats = 0

        # Delete bridges
        self.log.debug("- Send stop message to bridges")
        for id in self.bridges.keys():
            self.RemoveBridge(id)

        # Shut down the event client
        self.log.debug("- Stopping event client")
        try:

            if self.eventClient:
                self.eventClient.Stop()
                self.eventClient = None
        except IOBaseException:
            self.log.exception("Exception caught stopping event client; probably negligible")

        # Put an event on the queue
        self.log.debug("- Wait for bridges to shutdown")
        import time
        while len(self.bridges) > 0:
            time.sleep(1)

        # Send stop message to queue thread
        self.log.debug("- Send stop message to queue processor")
        self.queue.put(Venue.EVT_QUIT)

        # Clear the running flag
        self.running = 0

        self.log.debug("Shutdown exiting")




def main():
   

    import sys
    import signal
    import time

    bridgeServer = None
    global logFile


    def usage():
        print """
Usage: BridgeServer.py <<--venueServer venueServerUrl>|
                        <--venueServerFile venueServerFile>|
                        <--venue venueUrl>>
                        <--venueFile venueUrlFile>|
                       <--qbexec quickbridgeExecutable>
                       [--cert certpath]
                       [--key keypath]
                       [--name name]
                       [--location location]
                       [-h|--help]
                       [-d|--debug]
"""


    # Signal handler to catch signals and shutdown
    def SignalHandler(signum, frame):
        """
        SignalHandler catches signals and shuts down the VenueServer (and
        all of it's Venues. Then it stops the hostingEnvironment.
        """
        print "Shutting down..."
        bridgeServer.Shutdown()
  

    # initialization
    venueServerUrl = venueServerFile = venueUrl = venueFile = None
    debugMode = 0
    identityCert = None
    identityKey = None
    name=None
    location=None
    configFile=None
    qbexec=None

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdlc:",
                                   [
                                   "venueServer=", 
                                   "venueServerFile=",
                                   "venue=",
                                   "venueFile=",
                                   "qbexec=",
                                   #"cert=",
                                   #"key=",
                                   "name=",
                                   "location="
                                   ])

    except getopt.GetoptError:
        usage()
        sys.exit(2)


    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt == '-c':
            configFile = arg
        elif opt == '--venueServer':
            venueServerUrl = arg
        elif opt == '--venueServerFile':
            venueServerFile = arg
        elif opt == '--venue':
            venueUrl = arg
        elif opt == '--file':
            venueFile = arg
        elif opt == '--qbexec':
            qbexec = arg
        elif opt in ('--debug', '-d'):
            debugMode = 1
        elif opt in ('--logfile', '-l'):
            logFile = arg
        elif opt == "--key":
            identityKey = arg
        elif opt == "--cert":
            identityCert = arg
        elif opt == "--name": 
            name = arg
        elif opt == "--location":
            location = arg


    # Read config file, if given
    if configFile:

        def GetConfigVal(config,varName):
            """
            SetConfigVal sets the given variable to the value in
            the configuration dict, if it exists, and if the var
            was not already set
            """
            configKey = "BridgeServer."+varName
            if config.has_key(configKey):
                return config[configKey]
            return None

        config = Utilities.LoadConfig(configFile)
        if not venueServerUrl: 
            venueServerUrl = GetConfigVal(config,"venueServerUrl")
        if not venueServerFile: 
            venueServerFile = GetConfigVal(config,"venueServerFile")
        if not venueUrl:
            venueUrl = GetConfigVal(config,"venueUrl")
        if not venueFile:
            venueFile = GetConfigVal(config,"venueFile")
        if not qbexec: 
            qbexec = GetConfigVal(config,"qbexec")
        if not identityCert: 
            identityCert = GetConfigVal(config,"cert")
        if not identityKey: 
            identityKey = GetConfigVal(config,"key")
        if not name: 
            name = GetConfigVal(config,"name")
        if not location: 
            location = GetConfigVal(config,"location")
        if not logFile: 
            logFile = GetConfigVal(config,"logFile")

    # catch bad arguments
    if (venueServerUrl!=None) + (venueServerFile!=None) + (venueUrl!=None) + (venueFile!=None) > 1:
        print "* Error : Only one of venueServer|venueServerFile|venue|file args can be specified"
        usage()
        sys.exit(1)
    if not qbexec:
        print "* Error : Quickbridge executable not given"
        usage()
        sys.exit(1)
    else:
        if not os.path.exists(qbexec):
            print "* Error : Quickbridge executable does not exist"
            print "          (%s)" % (qbexec,)
            sys.exit(1)

    # Initialize the application
    if identityCert is not None or identityKey is not None:
        # Sanity check on identity cert stuff
        if identityCert is None or identityKey is None:
            print "Both a certificate and key must be provided"
            sys.exit(0)

        # Init toolkit with explicit identity.
        app = Toolkit.ServiceApplicationWithIdentity(identityCert, identityKey)

    else:
        # Init toolkit with standard environment.
        app = Toolkit.CmdlineApplication()
    app.InitGlobusEnvironment()



    # Determine venue(s) to bridge
    venueList = []
    if venueServerFile:
        f = open(venueServerFile,"r")
        venueServerList = f.readlines()
        f.close()
        print "vslist = ", venueServerList
        for venueServerUrl in venueServerList:
            print "Retrieving venues from venue server : ", venueServerUrl
            venueDescList = Client.Handle(venueServerUrl).GetProxy().GetVenues()
            venueList += map( lambda venue: venue.uri, venueDescList )
    elif venueServerUrl:
        print "Retrieving venues from venue server : ", venueServerUrl
        venueDescList = Client.Handle(venueServerUrl).GetProxy().GetVenues()
        venueList = map( lambda venue: venue.uri, venueDescList )
    elif venueFile:
        # Bridge venues specified in the given file
        print "Retrieving venues from file :", venueFile
        f = open(venueFile,"r")
        venueList = f.readlines()
        f.close()
    elif venueUrl:
        venueList = [ venueUrl ]


    # Register a signal handler so we can shut down cleanly
    signal.signal(signal.SIGINT, SignalHandler)

    # Create a provider profile to identify the bridge owner
    providerProfile = ProviderProfile(name, location)

    # Create the bridge server
    bridgeFactory = BridgeFactory(qbexec)
    bridgeServer = BridgeServer(providerProfile,bridgeFactory,debugMode)

    # Bridge those venues !
    for venueUrl in venueList:
        venueUrl = venueUrl.strip()
        print "venueUrl = ", venueUrl
        if len(venueUrl):
            bridgeServer.AddVenue(venueUrl)

    # Loop main thread
    while bridgeServer.IsRunning():
        time.sleep(1)

if __name__ == "__main__":
    main()

