#!/usr/bin/python2

import logging
import Queue
import threading
import getopt

from AccessGrid.EventClient import EventClient
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.NetworkLocation import UnicastNetworkLocation
from AccessGrid.ProcessManagerUnix import ProcessManagerUnix as ProcessManager
from AccessGrid import Utilities
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid.Events import Event, ConnectEvent, HeartbeatEvent


quickBridgeExec = None
logFile = 'BridgeServer.log'


class BridgeServer:
    def __init__(self, debug=0):
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
        self.venues[venueUrl] = Venue(venueUrl)

    def RemoveVenue(self, venueUrl):
        """
        RemoveVenue stops the BridgeServer from bridging the 
        specified venue
        """
        self.log.debug("Method BridgeServer.RemoveVenue called")
        if self.venues.has_key(venueUrl):
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
    def __init__(self, venueUrl):

        # Init data
        self.venueUrl = venueUrl
        self.venueProxy = Client.Handle(venueUrl).GetProxy()
        self.bridges = dict()
        self.queue = Queue.Queue()
        self.running = 1

        self.log = logging.getLogger("AG.BridgeServer")

        # Register with the venue
        self.privateId = self.venueProxy.RegisterNetService("bridge")

        # Create bridges for the venue streams
        streamList = self.venueProxy.GetStreams()
        for stream in streamList:

            # Create the bridge
            bridge = self.AddBridge(stream)


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
        self.queue.put(event)

    def AddBridge(self, streamDesc):
        """
        AddBridge adds a bridge with the specified parameters
        """

        self.log.debug("Method Venue.AddBridge called")
        
        # Allocate a port for the bridge
        uaddr = Utilities.GetHostname()
        uport = MulticastAddressAllocator().AllocatePort()
 
        # Create the bridge and start it
        bridge = Bridge(streamDesc.id, 
                        streamDesc.location.host, 
                        streamDesc.location.port, 
                        streamDesc.location.ttl, 
                        uaddr, uport)
        bridge.Start()
        self.bridges[streamDesc.id] = bridge

        # Add the related network location to the venue
        networkLocation = UnicastNetworkLocation(bridge.uaddr, bridge.uport)
        self.venueProxy.AddNetworkLocationToStream(self.privateId,
                                                   streamDesc.id,
                                                   networkLocation)
        return bridge
        
    def RemoveBridge(self, id):
        """
        RemoveBridge removes the bridge with the specified id
        """
        self.log.debug("Method Venue.RemoveBridge called")
        self.log.debug("  id = %s", id)
        if self.bridges.has_key(id):
            self.bridges[id].Stop()
            del self.bridges[id]
            
    def RunQueueThread(self):
        """
        RunQueueThread loops while the object is active,
        taking events from the queue and handling them
        appropriately
        """

        self.log.debug("Method Venue.RunQueueThread called")
    
        while self.running:
            event = self.queue.get(1)
            if event == "quit":
                break
            if event.eventType == Event.ADD_STREAM:
                strDesc = event.data
                self.AddBridge(strDesc)
            if event.eventType == Event.REMOVE_STREAM:
                strDesc = event.data
                self.RemoveBridge(strDesc.id)
        self.log.debug("RunQueueThread exiting")

    def HeartbeatThread(self):
        """
        HeartbeatThread loops while the object is active,
        to keep the connection with the Venue open
        """
        import time
        while self.running:
            try:
                self.eventClient.Send(HeartbeatEvent(self.channelId, self.privateId))
            except:
                self.log.exception("BridgeServer:Heartbeat: Heartbeat exception is caught.")
                pass
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
        # Delete bridges
        self.log.debug(" - Stopping bridges")
        while len(self.bridges) > 0:
            self.RemoveBridge(self.bridges.keys()[0])

        # Shut down the event client
        self.log.debug(" - Stopping event client")
        self.eventClient.Stop()

        # Put an event on the queue
        #self.queue.put(Event(Event.EXIT,self.channelId,None))
        self.queue.put("quit")

        # Clear the running flag
        self.running = 0

class Bridge:
    def __init__(self, id, maddr, mport, mttl, uaddr, uport):
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
        self.processManager.start_process(quickBridgeExec,args)

    def Stop(self):
        """
        Stop stops the bridge, terminating bridge processes
        """
        self.log.debug("Method Bridge.Stop called")
	self.processManager.terminate_all_processes()




def usage():
    print """
Usage: BridgeServer.py <<-vs venueServerUrl>|<-f|--file venueUrlFile>|<-v|--venue venueUrl>
                       <-qbexec quickbridgeExecutable>
                       [-h|--help]
                       [-d|--debug]
"""

def main():
   

    bridgeServer = None


    # Signal handler to catch signals and shutdown
    def SignalHandler(signum, frame):
        """
        SignalHandler catches signals and shuts down the VenueServer (and
        all of it's Venues. Then it stops the hostingEnvironment.
        """
        print "Shutting down..."
        bridgeServer.Shutdown()
  
    import sys
    import signal
    import time

    # initialization
    venueServerUrl = venueUrl = venueFile = None
    numExclusiveArgs = 0
    debugMode = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdlv:f:",
                                   [
                                   "venueServer=", 
                                   "venue=",
                                   "file=",
                                   "qbexec="
                                   ])

    except getopt.GetoptError:
        usage()
        sys.exit(2)


    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt == '--venueServer':
            venueServerUrl = arg
            numExclusiveArgs += 1
        elif opt in ('--venue', '-v'):
            venueUrl = arg
            numExclusiveArgs += 1
        elif opt in ('--file', '-f'):
            venueFile = arg
            numExclusiveArgs += 1
        elif opt == '--qbexec':
            global quickBridgeExec
            quickBridgeExec = arg
        elif opt in ('--debug', '-d'):
            debugMode = 1
        elif opt in ('--logfile', '-l'):
            global logFile
            logFile = arg

    # catch bad arguments
    if numExclusiveArgs > 1:
        print "* Error : Only one of venueServer|venue|file args can be specified"
        usage()
        sys.exit(1)
    if not quickBridgeExec:
        print "* Error : Quickbridge executable not given"
        usage()
        sys.exit(1)

    # Determine venue(s) to bridge
    venueList = []
    if venueServerUrl:
        print "Fetching venues from venue server : ", venueServerUrl
        venueDescList = Client.Handle(venueServerUrl).GetProxy().GetVenues()
        venueList = map( lambda venue: venue.uri, venueDescList )
    elif venueFile:
        # Bridge venues specified in the given file
        print "Fetching venues from file :", venueFile
        f = open(venueFile,"r")
        venueList = f.readlines()
        f.close()
        print "done"
    elif venueUrl:
        venueList = [ venueUrl ]


    # Create the bridge server
    bridgeServer = BridgeServer(debugMode)

    # Bridge those venues !
    for venueUrl in venueList:
        venueUrl = venueUrl.strip()
        print "bridging venue ", venueUrl
        if len(venueUrl):
            bridgeServer.AddVenue(venueUrl)

    # Register a signal handler so we can shut down cleanly
    signal.signal(signal.SIGINT, SignalHandler)

    # Loop main thread
    while bridgeServer.IsRunning():
        time.sleep(1)
        

if __name__ == "__main__":
    main()

