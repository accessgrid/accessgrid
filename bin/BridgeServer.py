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
from AccessGrid.Venue import VenueIW
from AccessGrid.VenueServer import VenueServerIW
from AccessGrid.Events import Event, ConnectEvent, HeartbeatEvent
from AccessGrid.EventClient import EventClient, EventClientWriteDataException
from AccessGrid.NetworkAddressAllocator import NetworkAddressAllocator
from AccessGrid.NetworkAddressAllocator import NoFreePortsError
from AccessGrid.NetworkLocation import UnicastNetworkLocation, ProviderProfile
from AccessGrid.Platform.ProcessManager import ProcessManager
from AccessGrid.Platform.Config import UserConfig, AGTkConfig, SystemConfig


class InvalidVenueUrl(Exception):
    pass
    
    
log = None

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


        def Start(self):
            """
            Start the Bridge (actually execute the bridge process)
            """
            log.info("Method Bridge.Start called")

            # Log detail about bridge being started
            log.info("Starting bridge:")
            log.info("  [maddr,mport,mttl] = %s %d %d", 
                           self.maddr, self.mport, self.mttl)
            log.info("  [uaddr,uport] = %s %s", self.uaddr, 
                           str(self.uport))

            # Start the process
            args = [
                    "-g", self.maddr,
                    "-m", '%d' % (self.mport,),
                    "-u", '%s' % (str(self.uport),),
                   ]
            log.info("Starting bridge: %s %s", self.qbexec, str(args))
            self.processManager.StartProcess(self.qbexec,args)

        def Stop(self):
            """
            Stop stops the bridge, terminating bridge processes
            """
            log.info("Method Bridge.Stop called")
            self.processManager.TerminateAllProcesses()


    def __init__(self, qbexec, portRange=None):
        self.qbexec = qbexec
        self.portRange = portRange

        self.bridges = dict()

        self.addressAllocator = NetworkAddressAllocator()
        
        # Use the port range if given
        if portRange:
            self.addressAllocator.SetPortMin(portRange[0])
            self.addressAllocator.SetPortMax(portRange[1])

    def SetBridgeExecutable(self,qbexec):
        self.qbexec = qbexec
        
    def SetPortMin(self,portMin):
        self.addressAllocator.SetPortBase(portMin)
        
    def SetPortMax(self,portMax):
        self.addressAllocator.SetPortMax(portMax)

    def CreateBridge(self,id,maddr,mport,mttl,uaddr,uport):
        """
        This method returns an existing bridge for the given maddr/mport,
        or a new one
        """

        log.info("Method CreateBridge called")

        if not uport:
            # Allocate a port
            allocateEvenPort = 1
            uport = self.addressAllocator.AllocatePort(allocateEvenPort)
            log.info("Allocated port = %s", str(uport))

        retBridge = None

        # - Check for an existing bridge with the given multicast addr/port
        for bridge,refcount in self.bridges.values():
            if bridge.maddr == maddr and bridge.mport == mport:
                log.info("- using existing bridge")
                retBridge = bridge
                refcount += 1
                key = "%s%d" % (maddr,mport)
                self.bridges[key] = (retBridge,refcount)
                break

        # - If bridge does not exist; create one
        if not retBridge:
            # Instantiate a new bridge
            log.info("- creating new bridge")
            retBridge = BridgeFactory.Bridge(self.qbexec,id,maddr,mport,
                                             mttl,uaddr,uport)
            retBridge.Start()
   
            # Add the bridge to the list of bridges
            key = "%s%s" % (retBridge.maddr,retBridge.mport)
            self.bridges[key] = (retBridge,1)

        return retBridge


    def DestroyBridge(self,bridge):
        """
        DestroyBridge deletes the specified bridge from the list of bridges
        """

        log.info("Method DestroyBridge called")

        key = "%s%d" % (bridge.maddr,bridge.mport)
        if self.bridges.has_key(key):
            bridge,refcount = self.bridges[key]
            refcount -= 1
            self.bridges[key] = (bridge,refcount)

            # if the refcount is 0,
            # stop and delete the bridge
            if refcount == 0:
                log.info("- Refcount zero; stopping and deleting bridge")
                bridge.Stop()
                del self.bridges[key]


class InvalidConfigFile(Exception):
    pass
    

class BridgeServer:
    def __init__(self, debug=0):

        self.debug = debug

        # Allocate default values
        self.privateId = str(GUID.GUID())
        qbexec = os.path.join(AGTkConfig.instance().GetBinDir(), 
                                   "QuickBridge")
        self.portMin = None
        self.portMax = None

        # Create the bridge factory
        self.bridgeFactory = BridgeFactory(qbexec)

        # Create a provider profile to identify the bridge owner
        self.providerProfile = ProviderProfile("UnspecifiedName", 
                                               "UnspecifiedLocation")

        self.venues = dict()
            
        self.running = 1
        
    def AddVenueServer(self, venueServerUrl):
        """
        AddVenueServer adds venues on the specified venue server to 
        those being bridged by the BridgeServer
        """

        log.info("AddVenueServer: url = %s", venueServerUrl )
        
        # Retrieve venues from the venue server
        venueDescList = VenueServerIW(venueServerUrl).GetVenues()
        venueUrlList = map( lambda venue: venue.uri, venueDescList )

        # Add the venues to the bridge server
        for venueUrl in venueUrlList:
            self.AddVenue(venueUrl)

    def AddVenue(self, venueUrl, venuePortConfig=dict()):
        """
        AddVenue adds the specified venue to those being bridged
        by the BridgeServer
        """
        log.info("AddVenue: url = %s", venueUrl)
        venue = Venue(venueUrl, self.providerProfile, self.bridgeFactory, 
                      self.privateId, venuePortConfig)
        self.venues[venueUrl] = venue

    def RemoveVenue(self, venueUrl):
        """
        RemoveVenue stops the BridgeServer from bridging the 
        specified venue
        """
        log.info("Method BridgeServer.RemoveVenue called")
        if self.venues.has_key(venueUrl):
            self.venues[venueUrl].Shutdown()
            del self.venues[venueUrl]
	    
    def GetVenues(self):
        """
        GetVenues returns the list of venues being bridged
        """
        log.info("Method BridgeServer.GetVenues called")
        return self.venues.keys()

    def RemoveVenues(self):
        """
        RemoveVenues stops the BridgeServer from bridging all
        known venues
        """
        log.info("Method BridgeServer.RemoveVenues called")

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
        log.info("Method BridgeServer.Shutdown called")

        # Remove venues
        self.RemoveVenues()

        # Clear the running state
        self.running = 0
        
    def LoadConfig(self,configFile):
    
        # Define config file keys
        BRIDGESERVER = "BridgeServer"
        QBEXEC = "qbexec"
        NAME = "name"
        LOCATION = "location"
        ID = "id"
        PORTMIN = "portMin"
        PORTMAX = "portMax"
        
        #
        # Load the config file
        #
        
        cp = ConfigParser.ConfigParser()
        cp.optionxform = str
        cp.read(configFile)

        config = dict()
        for sec in cp.sections():
            optdict = dict()
            for opt in cp.options(sec):
                optdict[opt] = cp.get(sec,opt)
            config[sec] = optdict


        #
        # Validate the config
        #
        
        # - Check for BridgeServer section
        if not config.has_key(BRIDGESERVER):
            raise InvalidConfigFile, \
                  "No BridgeServer section found in config file"
                  
        # - Check for required BridgeServer options
        bridgeServerDict = config[BRIDGESERVER]

        # Read the BridgeServer section
        try:
            name = bridgeServerDict[NAME]
            location = bridgeServerDict[LOCATION]
            
            self.SetName(name)
            self.SetLocation(location)
        except KeyError, e:
            raise InvalidConfigFile, \
                "Required option %s missing" %(e.args[0])

        # These options are, well, optional
        if bridgeServerDict.has_key(QBEXEC):
            self.bridgeFactory.SetBridgeExecutable(bridgeServerDict[QBEXEC])
        if bridgeServerDict.has_key(ID):
            self.id = bridgeServerDict[ID]
        if bridgeServerDict.has_key(PORTMIN):
            try:
                self.portMin = int(bridgeServerDict[PORTMIN])
            except ValueError:
                raise InvalidConfigFile, \
                      "portMin must be an integer [%s]" % self.portMin
            self.bridgeFactory.SetPortMin(self.portMin)
        if bridgeServerDict.has_key(PORTMAX):
            try:
                self.portMax = int(bridgeServerDict[PORTMAX])
            except ValueError:
                raise InvalidConfigFile, \
                      "portMax must be an integer [%s]" % self.portMax
            self.bridgeFactory.SetPortMax(self.portMax)

        # Process the remaining sections
        for sec in config.keys():

            # Ignore the "BridgeServer" section
            if sec == BRIDGESERVER:
                continue
            url = sec
            itemConfig = config[url]

            itemType = itemConfig["type"]

            # remove this identifier from the config
            del itemConfig["type"]

            if itemType == "VenueServer" or itemType == "venueserver":
                try:
                    self.AddVenueServer(url)
                except:
                    log.exception("Error adding venue server; url=%s", url)
            elif itemType == "Venue" or itemType == "venue":
                try:
                    for item,value in itemConfig.items():
                        itemConfig[item] = int(value)
                        
                    self.AddVenue(url, itemConfig)
                except:
                    log.exception("Error adding venue; url=%s", url)

    def SetName(self,name):
        self.providerProfile.name = name
        
    def SetLocation(self,location):
        self.providerProfile.location = location
        
    def SetBridgeExecutable(self,qbexec):
        self.bridgeFactory.SetBridgeExecutable(qbexec)

class Venue:

    EVT_ADDBRIDGE="AddBridge"
    EVT_REMOVEBRIDGE="RemoveBridge"
    EVT_QUIT="Quit"

    def __init__(self, venueUrl, providerProfile, 
                 bridgeFactory, id, venuePortConfig ):

        # Init data
        self.venueUrl = venueUrl
        self.providerProfile = providerProfile
        self.bridgeFactory = bridgeFactory
        self.privateId = id
        self.venuePortConfig = venuePortConfig

        self.venueProxy = VenueIW(venueUrl)
        

        try:
            self.venueProxy._IsValid()
        except:
            raise InvalidVenueUrl

        self.bridges = dict()
        self.queue = Queue.Queue()
        self.running = 1
        self.sendHeartbeats = threading.Event()
        self.sendHeartbeats.set()

        self.ConnectEventClient()
        if self.eventClient.connected:
            # Create bridges for the venue
            self.AddBridges()


        threading.Thread(target=self.RunQueueThread,
                         name="RunQueueThread").start()
        hbthread = threading.Thread(target=self.HeartbeatThread,
                    name="HeartbeatThread")
        hbthread.setDaemon(1)
        hbthread.start()


    def ConnectEventClient(self):
        """ 
        """
        # Register with the venue
        self.venueProxy.AddNetworkService(NetService.BridgeNetService.TYPE, 
                                          self.privateId)
        
        # Get the event service location and event channel id
        (self.eventServiceLocation, self.channelId) = \
                self.venueProxy.GetEventServiceLocation()

        # Set up event client
        self.eventClient = EventClient(self.privateId, 
                                       self.eventServiceLocation, 
                                       self.channelId)
        self.eventClient.start()
        self.eventClient.Send(ConnectEvent(self.channelId, self.privateId))

        self.eventClient.RegisterCallback(Event.ADD_STREAM, 
                                          self.EventReceivedCB)
        self.eventClient.RegisterCallback(Event.REMOVE_STREAM, 
                                          self.EventReceivedCB)
        

    def EventReceivedCB(self, event):
        """
        EventReceivedCB is a callback for the event client.
        It puts the received event on the queue for processing
        by the queue processing thread.
        """
        log.info("Method Venue.EventReceivedCB called")
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
        for streamId in self.bridges.keys():
            self.__RemoveBridge(streamId) 

    
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

        log.info("Method Venue.AddBridge called")
        
        uaddr = SystemConfig.instance().GetHostname()
        uport = 0
        
        if self.venuePortConfig:
            addressAllocator = NetworkAddressAllocator(
                                        self.venuePortConfig["portMin"],
                                        self.venuePortConfig["portMax"])
            allocateEventPort = 1
            uport = addressAllocator.AllocatePort(allocateEventPort)  
            log.info("Allocating port; port = %s", str(uport))
    
        # Create the bridge and start it
        bridge = None
        try:
            bridge = self.bridgeFactory.CreateBridge(streamDesc.id, 
                            streamDesc.location.host, 
                            streamDesc.location.port, 
                            streamDesc.location.ttl, 
                            uaddr, uport)
        except NoFreePortsError:
            log.exception("Error creating bridge; no free ports")
            return
            
        self.bridges[streamDesc.id] = bridge

        # Add the related network location to the venue
        networkLocation = UnicastNetworkLocation(bridge.uaddr, bridge.uport)
        networkLocation.profile = self.providerProfile
        self.venueProxy.AddNetworkLocationToStream(self.privateId,
                                                   streamDesc.id,
                                                   networkLocation)
        return bridge
        
    def __RemoveBridge(self, streamId):
        """
        RemoveBridge removes the bridge with the specified id
        """
        log.info("Method Venue.RemoveBridge called")
        log.info("  streamId = %s", streamId)
        if self.bridges.has_key(streamId):
            log.info("  removed")
            self.bridgeFactory.DestroyBridge(self.bridges[streamId])
            del self.bridges[streamId]
        else:  
            log.info("  not found")
        
            
    def RunQueueThread(self):
        """
        RunQueueThread loops while the object is active,
        taking events from the queue and handling them
        appropriately
        """

        log.info("Method Venue.RunQueueThread called")
    
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
             
        log.info("RunQueueThread exiting")

    def HeartbeatThread(self):
        """
        HeartbeatThread loops while the object is active,
        to keep the connection with the Venue open
        """
        import time
        while self.sendHeartbeats.isSet():
            # Sleeeep (in short intervals)
            for i in range(60):
                if self.sendHeartbeats.isSet():
                    time.sleep(.2)
                else:
                    log.info("Heartbeat thread exiting (1)")
                    return

            try:
                if self.eventClient.connected:
                    self.eventClient.Send(HeartbeatEvent(self.channelId, self.privateId))
                else:
                    log.info("Trying to reach venue")
                    try:

                        # Test whether venue is reachable 
                        self.venueProxy._IsValid()
                        log.info("- venue reachable; url=%s" % self.venueUrl)

                        # Try to connect the event client
                        self.ConnectEventClient()

                        # If event client is connected; recreate the bridges
                        if self.eventClient.connected:
                            log.info("event client connected; url=%s" % self.venueUrl)
                            log.info("- re-creating bridges; url=%s" % self.venueUrl)

                            # Event client reconnected; re-bridge venue
                            self.AddBridges()
                        else:
                            log.info("event client NOT connected; url=%s" % self.venueUrl)


                    except:  # pyGlobus.io.GSITCPSocketException
                        log.exception("While testing/reconnecting; url=%s" % self.venueUrl)
                        log.info("- venue unreachable; url=%s" % self.venueUrl)

            except EventClientWriteDataException:
                log.info("- EventClientWriteDataException")

                if not self.eventClient.connected:
                    # connection broken; remove bridges
                    log.info("Connection lost; shutting down venue; url=%s" % self.venueUrl)
                    self.RemoveBridges()
                else:
                    # couldn't send, but i'm still connected, so just
                    # continue trying to send
                    log.info("- still connected; do nothing; url=%s", self.venueUrl)
            except:
                log.exception("*** Unexpected exception; no action taken ****")

        log.info("Heartbeat thread exiting (2)")


    def Shutdown(self):
        """
        Shutdown shuts down the Venue
        - Remove Bridges
        - Stop the event client
        - Put an event on the queue, to stop it
        - Clear the running flag
        """
        log.info("Method Venue.Shutdown called")

        # Stop sending heartbeats
        self.sendHeartbeats.clear()

        # Delete bridges
        log.info("- Send stop message to bridges")
        self.RemoveBridges()

        # Shut down the event client
        log.info("- Stopping event client")
        try:

            if self.eventClient:
                self.eventClient.Stop()
                self.eventClient = None
        except IOBaseException:
            log.exception("Exception caught stopping event client; probably negligible")

        # Put an event on the queue
        log.info("- Wait for bridges to shutdown")
        import time
        while len(self.bridges) > 0:
            time.sleep(.2)

        # Send stop message to queue thread
        log.info("- Send stop message to queue processor")
        self.queue.put(Venue.EVT_QUIT)
        
        # Clear the running flag
        self.running = 0

        log.info("Shutdown exiting")

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

def usage():
    print """
Usage: BridgeServer.py [-c configFile] [-h|--help] [-d|--debug]

"""

def main():
    import sys
    import signal
    import time
    
    global log

    # initialization
    bridgeServer = None
    debugMode = 0
    configFile=None
    
    # Signal handler to catch signals and shutdown
    def SignalHandler(signum, frame):
        """
        SignalHandler catches signals and shuts down the VenueServer (and
        all of it's Venues. Then it stops the hostingEnvironment.
        """
        print "Shutting down..."
        bridgeServer.Shutdown()
        print "SignalHandler exiting."

    # Init toolkit with standard environment.
    app = Toolkit.Service.instance()

    try:
        app.Initialize(Log.BridgeServer)
    except:
        print "Failed to initialize toolkit, exiting."
        sys.exit(-1)
    
    log = app.GetLog()
    debugMode = app.GetOption("debug")
    configFile = app.GetOption("configfilename")

    # If no config file specified, use default config file
    if not configFile:
        configFile = os.path.join(UserConfig.instance().GetConfigDir(),
                                  "BridgeServer.cfg")
        
    # Register a signal handler so we can shut down cleanly
    signal.signal(signal.SIGINT, SignalHandler)
    if sys.platform != 'win32':
        signal.signal(signal.SIGHUP, SignalHandler)

    # Create the bridge server
    bridgeServer = BridgeServer(debugMode)
    bridgeServer.LoadConfig(configFile)
    
    # Loop main thread
    while bridgeServer.IsRunning():
        time.sleep(1)

if __name__ == "__main__":
    main()

"""
Usage:

- Bridge single venue
    BridgeServer.py --venue venueUrl

- Bridge venues/venueServers specified in config file
    BridgeServer.py -c configFile

- venue/venueserver specifications on the command line
  would override those in the config file


Format of BridgeServer config file

[BridgeServer]
name = Argonne
location = Chicago
qbexec = /usr/bin/QuickBridge
# use this port range for the bridge server as a whole
portMin = 30000
portMax = 40000

# Lobby of ag-2 server
[https://ag-2:8000/Venues/default]
type = Venue
# use this special port range for this venue
portMin = 24000
portMax = 24006

# Entire transitional venue server
[https://vv2.mcs.anl.gov:9000/VenueServer]
type = VenueServer
"""
