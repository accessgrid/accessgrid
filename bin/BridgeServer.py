#!/usr/bin/python2

import os
import Queue
import threading
import getopt
import ConfigParser

from pyGlobus.io import IOBaseException

from AccessGrid import Log
from AccessGrid import GUID
from AccessGrid import NetService
from AccessGrid import Platform
from AccessGrid import Toolkit
from AccessGrid import Utilities
from AccessGrid.hosting import Client
from AccessGrid.Events import Event, ConnectEvent, HeartbeatEvent
from AccessGrid.EventClient import EventClient, EventClientWriteDataException
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid.NetworkLocation import UnicastNetworkLocation, ProviderProfile
from AccessGrid.ProcessManager import ProcessManager
from AccessGrid.Platform import GetUserConfigDir


logFile = os.path.join(GetUserConfigDir(), 'BridgeServer.log')


class InvalidVenueUrl(Exception):
    pass

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
            self.log = Log.GetLogger(Log.BridgeServer)

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
        self.log = Log.GetLogger(Log.BridgeServer)

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
    def __init__(self, providerProfile, bridgeFactory, privateId, debug=0):
        self.providerProfile = providerProfile
        self.bridgeFactory = bridgeFactory
        self.privateId = privateId
        self.debug = debug

        self.venues = dict()
        self.running = 1

        self.__setLogger()
        
        self.log.debug("BridgeServer id = %s", privateId)

    def AddVenue(self, venueUrl, venuePortConfig):
        """
        AddVenue adds the specified venue to those being bridged
        by the BridgeServer
        """
        self.log.debug("Method BridgeServer.AddVenue called")
        venue = Venue(venueUrl, self.providerProfile, self.bridgeFactory, self.privateId, venuePortConfig)
        self.venues[venueUrl] = venue

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
        self.log = Log.GetLogger(Log.BridgeServer)

        hdlr = Log.FileHandler(logFile)
        hdlr.setLevel(Log.DEBUG)
        hdlr.setFormatter(Log.GetFormatter())
        Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())

        if self.debug:
            hdlr = Log.StreamHandler()
            hdlr.setFormatter(Log.GetLowDetailFormatter())
            Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())


class Venue:

    EVT_ADDBRIDGE="AddBridge"
    EVT_REMOVEBRIDGE="RemoveBridge"
    EVT_QUIT="Quit"

    def __init__(self, venueUrl, providerProfile, bridgeFactory, id, venuePortConfig ):

        # Init data
        self.venueUrl = venueUrl
        self.providerProfile = providerProfile
        self.bridgeFactory = bridgeFactory
        self.privateId = id
        self.venuePortConfig = venuePortConfig

        self.venueProxy = Client.Handle(venueUrl).GetProxy()
        

        try:
            self.venueProxy._IsValid()
        except:
            raise InvalidVenueUrl

        self.bridges = dict()
        self.queue = Queue.Queue()
        self.running = 1
        self.sendHeartbeats = 1

        self.log = Log.GetLogger(Log.BridgeServer)

        self.ConnectEventClient()
        if self.eventClient.connected:
            # Create bridges for the venue
            self.AddBridges()


        threading.Thread(target=self.RunQueueThread).start()
        threading.Thread(target=self.HeartbeatThread).start()


    def ConnectEventClient(self):
        """ 
        """
        # Register with the venue
        self.venueProxy.AddNetService(NetService.BridgeNetService.TYPE, self.privateId)
        
        # Get the event service location and event channel id
        (self.eventServiceLocation, self.channelId) = self.venueProxy.GetEventServiceLocation()

        # Set up event client
        self.eventClient = EventClient(self.privateId, self.eventServiceLocation, self.channelId)
        self.eventClient.start()
        self.eventClient.Send(ConnectEvent(self.channelId, self.privateId))

        self.eventClient.RegisterCallback(Event.ADD_STREAM, self.EventReceivedCB)
        self.eventClient.RegisterCallback(Event.REMOVE_STREAM, self.EventReceivedCB)
        

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


    def AddBridges(self):
        # Create bridges for the venue streams
        streamList = self.venueProxy.GetStreams()
        for stream in streamList:
            self.AddBridge(stream)


    def RemoveBridges(self):
        # Remove all known bridges 
        for id in self.bridges.keys():
            self.__RemoveBridge(id) 

    
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
        
        uaddr = Utilities.GetHostname()
        
        if self.venuePortConfig.has_key(streamDesc.capability.type):
            # Use the user-specified port
            uport = self.venuePortConfig[streamDesc.capability.type]
            self.log.debug("Using user-specified port; [media,port] = %s,%d", 
                streamDesc.capability.type, uport)
        else:
            # Allocate a port
            uport = MulticastAddressAllocator().AllocatePort()
            self.log.debug("Allocating port; [media,port] = %s,%d", 
                streamDesc.capability.type, uport)
            

    
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
        
            # Sleeeep (in short intervals)
            for i in range(12):
                if self.sendHeartbeats:
                    time.sleep(1)
        
            try:
                if self.eventClient.connected:
                    self.eventClient.Send(HeartbeatEvent(self.channelId, self.privateId))
                else:
                    self.log.debug("Trying to reach venue")
                    try:
                    
                        # Test whether venue is reachable 
                        self.venueProxy._IsValid()
                        self.log.debug("- venue reachable; url=%s" % self.venueUrl)
                        
                        # Try to connect the event client
                        self.ConnectEventClient()
                        
                        # If event client is connected; recreate the bridges
                        if self.eventClient.connected:
                            self.log.debug("event client connected; url=%s" % self.venueUrl)
                            self.log.debug("- re-creating bridges; url=%s" % self.venueUrl)

                            # Event client reconnected; re-bridge venue
                            self.AddBridges()
                        else:
                            self.log.debug("event client NOT connected; url=%s" % self.venueUrl)

                          
                    except:  # pyGlobus.io.GSITCPSocketException
                        self.log.exception("While testing/reconnecting; url=%s" % self.venueUrl)
                        self.log.debug("- venue unreachable; url=%s" % self.venueUrl)
                        
            except EventClientWriteDataException:
                self.log.debug("- EventClientWriteDataException")
                
                if not self.eventClient.connected:
                    # connection broken; remove bridges
                    self.log.debug("Connection lost; shutting down venue; url=%s" % self.venueUrl)
                    self.RemoveBridges()
                else:
                    # couldn't send, but i'm still connected, so just
                    # continue trying to send
                    self.log.debug("- still connected; do nothing; url=%s" % self.venueUrl)
            except:
                self.log.exception("*** Unexpected exception; no action taken ****")


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
            time.sleep(.2)

        # Send stop message to queue thread
        self.log.debug("- Send stop message to queue processor")
        self.queue.put(Venue.EVT_QUIT)

        # Clear the running flag
        self.running = 0

        self.log.debug("Shutdown exiting")



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




def main():
   

    import sys
    import signal
    import time

    bridgeServer = None


    def usage():
        print """
Usage: BridgeServer.py [-c configFile] [-h|--help] [-d|--debug]

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
    id=None
    
    portConfigFile = None
    
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdc:",
                                   [
                                   "help",
                                   "debug",
                                   "portConfig=",
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
        elif opt in ('-d', '--debug'):
            debugMode = 1
        elif opt in ('--portConfig',):
            portConfigFile = arg



    # If no config file specified, use default config file
    if not configFile:
        configFile = os.path.join(Platform.GetUserConfigDir(),"BridgeServer.cfg")
        
    # Load the config file
    config = Utilities.LoadConfig(configFile)
    venueServerUrl = GetConfigVal(config,"venueServer")
    venueServerFile = GetConfigVal(config,"venueServerFile")
    venueUrl = GetConfigVal(config,"venue")
    venueFile = GetConfigVal(config,"venueFile")
    qbexec = GetConfigVal(config,"qbexec")
    name = GetConfigVal(config,"name")
    location = GetConfigVal(config,"location")
    id = GetConfigVal(config,"id")


    # catch bad arguments
    if (venueServerUrl!=None) + (venueServerFile!=None) + (venueUrl!=None) + (venueFile!=None) ==0:
        print "* Error : One of venueServer|venueServerFile|venue|venueFile args must be specified in config file"
        usage()
        sys.exit(1)
    if (venueServerUrl!=None) + (venueServerFile!=None) + (venueUrl!=None) + (venueFile!=None) > 1:
        print "* Error : Only one of venueServer|venueServerFile|venue|venueFile args can be specified in config file"
        usage()
        sys.exit(1)
    if not name:
        print "* Error : name option must be specified in config file"
        usage()
        sys.exit(1)
    if not location:
        print "* Error : location option must be specified in config file"
        usage()
        sys.exit(1)
    if not qbexec:
        print "* Error : Quickbridge executable must be specified in config file"
        usage()
        sys.exit(1)
    else:
        if not os.path.exists(qbexec):
            print "* Error : Quickbridge executable does not exist"
            print "          (%s)" % (qbexec,)
            sys.exit(1)
    if not id:
        # Allocate an id if none has been specified
        id = config["BridgeServer.id"] = str(GUID.GUID())
        Utilities.SaveConfig(configFile,config)    


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
            try:
                venueDescList = Client.Handle(venueServerUrl).GetProxy().GetVenues()
                venueList += map( lambda venue: venue.uri, venueDescList )
            except:
                print "Can't get venues from venue server: ", venueServerUrl, "; skipping"
    elif venueServerUrl:
        print "Retrieving venues from venue server : ", venueServerUrl
        try:
            venueDescList = Client.Handle(venueServerUrl).GetProxy().GetVenues()
            venueList = map( lambda venue: venue.uri, venueDescList )
        except:
            print "Can't get venues from venue server: ", venueServerUrl, "; skipping"
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
    bridgeServer = BridgeServer(providerProfile,bridgeFactory,id,debugMode)
    
    # Read the port configuration file
    portConfig = ConfigParser.ConfigParser()
    portConfig.optionxform = str
    if portConfigFile:
        portConfig.read(portConfigFile)

    # Bridge those venues !
    for venueUrl in venueList:
        venueUrl = venueUrl.strip()
        print "Bridging venue:", venueUrl
        if len(venueUrl):
            try:
            
                # Get port assignments from portConfig
                venuePortConfig = dict()
                venueId = os.path.split(venueUrl)[-1]
                if portConfig.has_section(venueId):
                    for opt in portConfig.options(venueId):
                        try:
                            port = int(portConfig.get(venueId,opt))
                            venuePortConfig[opt] = int(portConfig.get(venueId,opt))
                        except:
                            print "Invalid port specified in config (%s); ignoring" % portConfig.get(venueId,opt)
            
                # Add the venue to the bridge server
                bridgeServer.AddVenue(venueUrl, venuePortConfig)
            except InvalidVenueUrl:
                print "Bad venue url: ", venueUrl, "; skipping."

    # Loop main thread
    while bridgeServer.IsRunning():
        time.sleep(1)

if __name__ == "__main__":
    main()

