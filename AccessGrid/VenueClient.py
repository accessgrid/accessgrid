#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client side object of the Virtual Venues Services.
# Created:     2002/12/12
# RCS-ID:      $Id: VenueClient.py,v 1.208 2005-05-06 15:58:11 eolson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
"""
__revision__ = "$Id: VenueClient.py,v 1.208 2005-05-06 15:58:11 eolson Exp $"

from AccessGrid.hosting import Client
import sys
import os
import string
import threading
import cPickle
import time

from AccessGrid import Log
from AccessGrid import DataStore
from AccessGrid import hosting
from AccessGrid.Toolkit import Application, Service
from AccessGrid.Preferences import Preferences
from AccessGrid.Platform.Config import UserConfig, SystemConfig
from AccessGrid.Platform.ProcessManager import ProcessManager
from AccessGrid.Venue import ServiceAlreadyPresent
from AccessGrid.interfaces.Venue_client import VenueIW
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.hosting import InsecureServer, SecureServer
from AccessGrid.Utilities import LoadConfig
from AccessGrid.NetUtilities import GetSNTPTime
from AccessGrid.VenueClientObserver import VenueClientObserver
from AccessGrid.scheduler import Scheduler
from AccessGrid.AsyncoreEventClient import EventClient
from AccessGrid.AsyncoreEventService import PickledEvent
#from AccessGrid.TextClient import TextClient
from AccessGrid.Events import Event, ConnectEvent
from AccessGrid.Events import DisconnectEvent, ClientExitingEvent
from AccessGrid.Events import RemoveDataEvent, UpdateDataEvent
from AccessGrid.ClientProfile import ClientProfile, ClientProfileCache, InvalidProfileException
from AccessGrid.Descriptions import ApplicationDescription, ServiceDescription
from AccessGrid.Descriptions import DataDescription, ConnectionDescription
from AccessGrid.Descriptions import CreateDataDescription, CreateVenueState
from AccessGrid.Descriptions import CreateConnectionDescription
from AccessGrid.Descriptions import CreateClientProfile
from AccessGrid.Descriptions import CreateServiceDescription
from AccessGrid.Descriptions import CreateApplicationDescription
from AccessGrid.Descriptions import CreateStreamDescription
from AccessGrid.AGNodeService import AGNodeServiceIW
from AccessGrid.Security.AuthorizationManager import AuthorizationManagerIW
from AccessGrid.Descriptions import VenueState

class EnterVenueException(Exception):
    pass
   
class AuthorizationFailedError(Exception):
    pass

class GetDataStoreInfoError(Exception):
    pass

class GetDataDescriptionsError(Exception):
    pass

class NotAuthorizedError(Exception):
    pass

class NetworkLocationNotFound(Exception):
    pass

class DisconnectError(Exception):
    pass

log = Log.GetLogger(Log.VenueClient)

class VenueClient:
    """
    This is the client side object that maintains a stateful
    relationship with a Virtual Venue. This object provides the
    programmatic interface to the Access Grid for a Venues User
    Interface.  The VenueClient can only be in one venue at a    time.
    """    
    
    
    def __init__(self, profile=None, pnode=0, port=0, progressCB=None,
                 app=None):
        """
        This client class is used on shared and personal nodes.
        """
        self.userConf = UserConfig.instance()
        self.isPersonalNode = pnode

        if app is not None:
            self.app = app
        else:
            self.app = Application()

        self.preferences = self.app.GetPreferences()
        self.profile = self.preferences.GetProfile()
       
        self.defaultNodeServiceUri = self.preferences.GetPreference(Preferences.NODE_URL) 
        
#        if pnode == 0:
#            pnode = int(self.preferences.GetPreference(Preferences.STARTUP_MEDIA))
#            self.isPersonalNode = pnode

        self.capabilities = []
        self.nodeServiceUri = self.defaultNodeServiceUri
        if hosting.GetHostingImpl() == "SOAPpy":
            self.nodeService = AGNodeServiceIW(self.nodeServiceUri)
        self.homeVenue = None
        self.houseKeeper = Scheduler()
        self.provider = None
        self.heartBeatTimer = None
        self.heartBeatTimeout = 10

        if progressCB: 
            if pnode:   progressCB("Starting personal node.")
            else:       progressCB("Starting web service.")

        if int(self.preferences.GetPreference(Preferences.CLIENT_PORT)) != 0:
            port = int(self.preferences.GetPreference(Preferences.CLIENT_PORT))
        
        self.__StartWebService(pnode, port)
        self.__InitVenueData()
        self.isInVenue = 0
        self.isIdentitySet = 0

        self.streamDescList = []
        self.transport = "multicast"
        
        self.observers = []

        # attributes for personal data store
        self.personalDataStorePrefix = "personalDataStore"
        self.personalDataStorePort = 0
        self.personalDataStorePath = os.path.join(self.userConf.GetConfigDir(),
                                                  self.personalDataStorePrefix)
        self.personalDataFile = os.path.join(self.personalDataStorePath,
                                             "myData.txt" )
        # If already requested personal data, clients public id is saved
        # in requests.        
        self.requests = [] 

        # Create personal data store
        if progressCB: progressCB("Starting personal data store")
        self.__CreatePersonalDataStore()

        # Manage the currently-exiting state
        self.exiting = 0
        self.exitingLock = threading.Lock()

        self.venueUri = None
        self.__venueProxy = None

        # Cache profiles in case we need to look at them later.
        # specifically, the cache makes it easier to add roles when
        # managing venues.
        self.profileCachePrefix = "profileCache"
        self.profileCachePath = os.path.join(self.userConf.GetConfigDir(),
                                             self.profileCachePrefix)
        self.cache = ClientProfileCache(self.profileCachePath)

    ##########################################################################
    #
    # Private Methods

    def __InitVenueData( self ):
        self.eventClient = None
#        self.textClient = None
        self.venueState = None
        self.venueUri = None
        self.__venueProxy = None
        #self.privateId = None

    def __CreatePersonalDataStore(self):
        """
        Creates the personal data storage and loads personal data
        from file to a dictionary of DataDescriptions. If the file is removed
        from local path, the description is not added to the list.
        """
        
        log.debug("__createPersonalDataStore: Creating personal datastore at %s using prefix %s and port %s" %(self.personalDataStorePath, self.personalDataStorePrefix,self.personalDataStorePort))
        
        if not os.path.exists(self.personalDataStorePath):
            try:
                os.mkdir(self.personalDataStorePath)
            except OSError:
                log.exception("__createPersonalDataStore: Could not create personal data storage path")
                self.personalDataStorePath = None

        if self.personalDataStorePath:
            self.transferEngine = DataStore.HTTPTransferServer(('',
                                                   self.personalDataStorePort))
            self.transferEngine.run()
            self.dataStore = DataStore.DataStore(self,
                                                 self.personalDataStorePath, 
                                                 self.personalDataStorePrefix,
                                                 self.transferEngine)
                   
            # load personal data from file
            
            log.debug("__createPersonalDataStore: Load personal data from file")
            if os.path.exists(self.personalDataFile):
                try:
                    fileH = open(self.personalDataFile, 'r')
                    dList = cPickle.load(fileH)
                    self.dataStore.LoadPersistentData(dList)
                    fileH.close()
                except:
                    log.exception("__createPersonalDataStore: Personal data could not be added")

    def __CheckForInvalidClock(self):
        """
        Check to see if the local clock is out of synch, a common reason for a
        failed authentication.

        This routine only currently sets self.warningString, and should only be
        invoked from the TCPSocketException-handling code in EnterVenue.

        """

        timeserver = "ntp-1.accessgrid.org"
        timeout = 0.3
        maxOffset = 10

        try:
            serverTime = GetSNTPTime(timeserver, timeout)
        except:
            log.exception("__CheckForValideClock: Connection to sntp server at %s failed", timeserver)
            serverTime = None

        if serverTime is not None:

            diff = int(time.time() - serverTime)
            absdiff = abs(diff)

            if absdiff > maxOffset:

                if diff > 0:
                    direction = "fast"
                else:
                    direction = "slow"

                self.warningString = ("Authorization failure connecting to server. \n" + \
                                     "This may be due to the clock being incorrect on\n" + \
                                     "your computer: it is %s seconds %s with respect\n" + \
                                     "to the time server at %s.") % \
                                     (absdiff, direction, timeserver)
            else:
                #
                # Time is okay.
                #
                log.exception("__CheckForValideClock: failed; time is okay (offset=%s", diff)

                self.warningString = "Authorization failure connecting to server."
        else:
            self.warningString = "Authorization failure connecting to server. \n" + \
                                 "Please check the time on your computer; an incorrect\n" + \
                                 "local clock can cause authorization to fail."


    def __StartWebService(self, pnode, port):
        from AccessGrid.NetworkAddressAllocator import NetworkAddressAllocator
        if port == 0:
            if pnode:
                port = 11000
            else:
                port = NetworkAddressAllocator().AllocatePort()
                        
        # First, check cmd line option
        if self.app.GetOption("secure"):
            self.server = SecureServer((self.app.GetHostname(), int(port)))
        # Second, check preferences
        elif int(self.preferences.GetPreference(Preferences.SECURE_CLIENT_CONNECTION)):
            self.server = SecureServer((self.app.GetHostname(), int(port)))
        else:
            self.server = InsecureServer((self.app.GetHostname(), port))

        # VenueClient interface not fully defined yet.
        #from AccessGrid.interfaces.VenueClient_interface import VenueClient as VenueClientI
        #vci = VenueClientI(impl=self)
        """
        uri = self.server.RegisterObject(vci, path='/VenueClient')

        if(self.profile != None):
            self.profile.venueClientURL = uri
            log.debug("__StartWebService: venueclient: %s", uri)

        if pnode:
            from AccessGrid.AGServiceManager import AGServiceManager
            from AccessGrid.AGServiceManager import AGServiceManagerI
            self.sm = AGServiceManager(self.server, self.app)
            smi = AGServiceManagerI(self.sm)
            uri = self.server.RegisterObject(smi, path="/ServiceManager")
            self.sm.SetUri(uri)
            log.debug("__StartWebService: service manager: %s",
                      uri)

            from AccessGrid.AGNodeService import AGNodeService, AGNodeServiceI
            self.ns = AGNodeService(self.app)
            nsi = AGNodeServiceI(self.ns)
            uri = self.server.RegisterObject(nsi, path="/NodeService")
            self.ns.SetUri(uri)
            log.debug("__StartWebService: node service: %s",
                      uri)
            self.SetNodeUrl(self.server.FindURLForObject(self.ns))
            
        self.server.RunInThread()
        """

#FIXME: default node configuration needs to be stored in preferences,
#       and retrieved from preferences here
#         if pnode:
#             try:
#                 defaultConfig = self.ns.GetDefaultConfiguration()
#             except:
#                 log.exception("Error loading default configuration")
            
        # Save the location of the venue client url
        # for other apps to communicate with the venue client
        self.urlFile = os.path.join(UserConfig.instance().GetTempDir(),
                               "venueClientUrl%d" % (os.getpid()))
        try:
            fileH = open(self.urlFile,"w")
            fileH.write(self.GetWebServiceUrl())
            fileH.close()
        except:
            log.exception("Error writing web service url file")
        
    def __StopWebService(self):
    
        if self.isPersonalNode:
            self.ns.Stop()
            self.sm.Shutdown()
    
        # Stop the ws server
        if self.server:
            self.server.Stop()
            
        # Remove the file
        try:
            os.remove(self.urlFile)
        except:
            log.exception("Error removing url file %s", self.urlFile)
            
    def GetWebServiceUrl(self):
        return self.server.FindURLForObject(self)
        
    def Heartbeat(self):
        try:
            log.debug("Calling Heartbeat, time now: %d", time.time())
            if self.heartBeatTimer is not None:
                self.heartBeatTimer.cancel()

            self.nextTimeout = self.__venueProxy.UpdateLifetime(
                self.profile.connectionId,self.heartBeatTimeout)
            log.debug("Next Heartbeat needed before: %d", self.nextTimeout)
            
            self.heartBeatTimer = threading.Timer(self.nextTimeout - 5.0,
                                                  self.Heartbeat)
            self.heartBeatTimer.start()
                
        except Exception, e:
            log.exception("Error sending heartbeat, reconnecting.")
            #self.__Reconnect()
                
    def __Reconnect(self):
    
        """
        Reconnect to venue
        """
        numTries = 0

        log.info("Try to reconnect to venue")
        
        venueUri = self.venueUri

        # Client no longer in venue
        self.isInVenue = 0
        
        # Exit the venue (internally)
        try:
            self.__ExitVenue()
        except Exception:
            log.info("Exception exiting from venue before reconnect -- not critical")

        # Try to enter the venue
        while (not self.isInVenue and
               numTries < int(self.preferences.GetPreference(Preferences.MAX_RECONNECT)) and 
               int(self.preferences.GetPreference(Preferences.RECONNECT))): 
        
            try:
                self.__EnterVenue(venueUri)
                self.failedHeartbeats = 0
            
                # If we're connected, stop trying
                if self.isInVenue:
                    break
            except:
                log.exception("Exception reconnecting to venue")
            
            time.sleep(int(self.preferences.GetPreference(Preferences.RECONNECT_TIMEOUT)))
            numTries += 1

        if self.isInVenue:
            # Update observers
            
            for s in self.observers:
                s.ExitVenue()

            for s in self.observers:
                try:
                    # enterSuccess is true if we entered.
                    s.EnterVenue(venueUri)
                except:
                    log.exception("Exception in observer")

        else:
            log.info("Failed to reconnect")
            self.ExitVenue()
            for s in self.observers:
                s.HandleError(DisconnectError())

    # end Private Methods
    #
    ##########################################################################

    ##########################################################################
    #
    # Event Handlers

    def AddUserEvent(self, event):
        log.debug("AddUserEvent: Got Add User Event")

        profile = event.GetData()
        
        # Pre-2.3 server compatability code
        if not profile.connectionId:
            profile.connectionId = profile.venueClientURL

        self.venueState.AddUser(profile)
        for s in self.observers:
            s.AddUser(profile)

    def RemoveUserEvent(self, event):
        log.debug("RemoveUserEvent: Got Remove User Event")

        profile = event.GetData()
        
        # Pre-2.3 server compatability code
        if not profile.connectionId:
            profile.connectionId = profile.venueClientURL

        # Handle removal of self
        if profile.connectionId == self.profile.connectionId:
            # Get out and stay out
            self.ExitVenue()
            for s in self.observers:
                s.HandleError(DisconnectError())
            return

        self.venueState.RemoveUser(profile)
        for s in self.observers:
            s.RemoveUser(profile)

        log.debug("RemoveUserEvent: Got Remove User Event...done")

        # Remove client from the list of clients who have
        # been requested for personal data
        if profile.publicId in self.requests:
            self.requests.remove(profile.publicId)
        
    def ModifyUserEvent(self, event):
        log.debug("ModifyUserEvent: Got Modify User Event")

        profile = event.GetData()

        # Pre-2.3 server compatability code
        if not profile.connectionId:
            profile.connectionId = profile.venueClientURL

        self.venueState.ModifyUser(profile)
        for s in self.observers:
            s.ModifyUser(profile)

    def AddDataEvent(self, event):
        log.debug("AddDataEvent: Got Add Data Event")
          
        data = event.GetData()
      
        if data.type == "None" or data.type == None:
            # Venue data gets saved in venue state
            self.venueState.AddData(data)
                      
        elif data.type not in self.requests:
            # If we haven't done an initial request of this
            # persons data, don't react on events.
            return

        for s in self.observers:
            s.AddData(data)

    def UpdateDataEvent(self, event):
        log.debug("UpdateDataEvent: Got Update Data Event")

        data = event.GetData()
                
        if data.type == "None" or data.type == None:
            # Venue data gets saved in venue state
            self.venueState.UpdateData(data)
                      
        elif data.type not in self.requests:
            # If we haven't done an initial request of this
            # persons data, don't react on events.
            return

        for s in self.observers:
            s.UpdateData(data)

    def RemoveDataEvent(self, event):
        log.debug("RemoveDataEvent: Got Remove Data Event")
        data = event.GetData()

        if data.type == "None" or data.type == None:
            # Venue data gets removed from venue state
            self.venueState.RemoveData(data)
            
        elif data.type not in self.requests:
            # If we haven't done an initial request of this
            # persons data, don't react on events.
            return

        for s in self.observers:
            s.RemoveData(data)
                
    def AddServiceEvent(self, event):
        log.debug("AddServiceEvent: Got Add Service Event")

        service = event.GetData()
        self.venueState.AddService(service)
        for s in self.observers:
            s.AddService(service)

    def UpdateServiceEvent(self, event):
        log.debug("UpdateServiceEvent: Got Update Service Event")

        service = event.GetData()
        self.venueState.UpdateService(service)
        for s in self.observers:
            s.UpdateService(service)

    def RemoveServiceEvent(self, event):
        log.debug("RemoveServiceEvent: Got Remove Service Event")

        service = event.GetData()
        self.venueState.RemoveService(service)
        for s in self.observers:
            s.RemoveService(service)

    def AddApplicationEvent(self, event):
        log.debug("AddApplicationEvent: Got Add Application Event")

        app = event.GetData()
        self.venueState.AddApplication(app)
        for s in self.observers:
            s.AddApplication(app)

    def UpdateApplicationEvent(self, event):
        log.debug("UpdateApplicationEvent: Got Update Application Event")
        app = event.GetData()
        self.venueState.UpdateApplication(app)
        for s in self.observers:
            s.UpdateApplication(app)

    def RemoveApplicationEvent(self, event):
        log.debug("RemoveApplicationEvent: Got Remove Application Event")

        app = event.GetData()
        self.venueState.RemoveApplication(app)
        for s in self.observers:
            s.RemoveApplication(app)

    def AddConnectionEvent(self, event):
        log.debug("AddConnectionEvent: Got Add Connection Event")

        connection = event.GetData()
        self.venueState.AddConnection(connection)
        for s in self.observers:
            s.AddConnection(connection)

    def RemoveConnectionEvent(self, event):
        log.debug("RemoveConnectionEvent: Got Remove Connection Event")

        connection = event.GetData()
        self.venueState.RemoveConnection(connection)
        for s in self.observers:
            s.RemoveConnection(connection)

    def SetConnectionsEvent(self, event):
        log.debug("SetConnectionEvent: Got Set Connections Event")

        connectionList = event.GetData()
        #self.venueState.SetConnections(connectionList)
        for s in self.observers:
            s.SetConnections(connectionList)

    def AddStreamEvent(self, event):
        log.debug("AddStreamEvent: Got Add Stream Event")
        streamDesc = event.GetData()

        # Add the stream to the local stream store
        self.streamDescList.append(streamDesc)

        try:
            self.nodeService.AddStream(streamDesc)
        except:
            log.info("Error adding stream to node")
        
        for s in self.observers:
            s.AddStream(streamDesc)
    
    def ModifyStreamEvent(self, event):
        log.debug("ModifyStreamEvent: Got Modify Stream Event")
        streamDesc = event.GetData()

        # Modify the local stream store
        for i in range(len(self.streamDescList)):
            if self.streamDescList[i].id == streamDesc.id:
                self.streamDescList[i] = streamDesc

        # Update event subscribers (the UI)
        for s in self.observers:
            s.ModifyStream(streamDesc)
        
    
    def RemoveStreamEvent(self, event):
        log.debug("RemoveStreamEvent: Got Remove Stream Event")
        streamDesc = event.GetData()

        # Remove the stream from the local stream store
        for i in range(len(self.streamDescList)):
            if self.streamDescList[i].id == streamDesc.id:
                del self.streamDescList[i]

        try:
            self.nodeService.RemoveStream(streamDesc)
        except:
            log.info("Error removing stream from node")

        for s in self.observers:
            s.RemoveStream(streamDesc)

    def OpenAppEvent(self, event):
        appCmdDesc = event.GetData()
        log.debug("OpenAppEvent: Got Start App Event %s %s %s"
                  %(appCmdDesc.appDesc, appCmdDesc.command, appCmdDesc.verb))
       
        for s in self.observers:
            s.OpenApplication(appCmdDesc)
                   
    def AddTextEvent(self,name, text):
        log.debug("TextEvent: Got Text Event")
        
        for s in self.observers:
            s.AddText(name,text)
            
    def SOAPFaultHandler(self, proxy, ex):
        """
        Handle a fault raised by an invocation through the venue server
        proxy.

        @param proxy: SOAPpy proxy through which the invocation failed
        @param ex: The exception that was raised

        @return: a true value if the invocation should be retried.

        """
        log.debug("SOAP FAULT: %s %s", proxy, ex)
        
        log.exception("SOAP fault occurred")

        return 0
        
            
    # end Event Handlers
    #
    ##########################################################################

    ##########################################################################
    #
    # Basic Implementation
        
    def AddObserver(self, observer):
        if not observer:
            raise ValueError, "Attempt to add null Observer"

        if not isinstance(observer,VenueClientObserver):
            raise ValueError, "Attempt to add non-Observer"
        
        self.observers.append(observer)
        
    #
    # Enter/Exit
    #
    
    def __EnterVenue(self,URL):
            #
            # Enter the venue
            #
            self.venueUri = URL
            self.__venueProxy = VenueIW(URL, tracefile=sys.stdout)

            log.debug("EnterVenue: Invoke venue enter")
            self.profile.connectionId = self.__venueProxy.Enter( self.profile )
            """
            evtLocation = ('',-1)

            a = ["state"]
            venueStateDict = self.__venueProxy.GetProperty(a)
            uniqueId = "" ; vname = "" ; description=""; uri = ""
            for entry in venueStateDict.entries:
                if entry.key == "venueid":
                    uniqueId = entry.value
                elif entry.key == "name":
                    vname = entry.value
                elif entry.key == "description":
                    description = entry.value
                elif entry.key == "uri":
                    uri = entry.value
                elif entry.key == "eventLocationStr":
                    # convert back from string to tuple until we can
                    #   pass tuples here
                    evtLocation = entry.value.split(":")
                    if len(evtLocation) > 1:
                        evtLocation = (str(evtLocation[0]), int(evtLocation[1]))
                    else:
                        evtLocation = ('',-1)
                elif entry.key == "clients":
                    clients = entry.value
                    for c in clients:
                        print type(c), c
            self.venueState = VenueState(uniqueId=uniqueId, name=vname, description=description, uri=uri, connections="", clients=[], data=[], eventLocation=evtLocation, textLocation="", applications=[], services=[])
            """
            state = self.__venueProxy.GetState()
            # tuple of two different types doesn't serialize easily.
            evtLocation = state.eventLocation.split(":")
            if len(evtLocation) > 1:
                evtLocation = (str(evtLocation[0]), int(evtLocation[1]))
            # next line needed needed until zsi can handle dictionaries.
            self.venueState = VenueState(uniqueId=state.uniqueId, name=state.name, description=state.description, uri=state.uri, connections=state.connections, clients=state.clients, data=state.data, eventLocation=evtLocation, textLocation=state.textLocation, applications=state.applications, services=state.services)

            # Retreive stream descriptions
            if len(self.capabilities) > 0:
                self.streamDescList = self.__venueProxy.NegotiateCapabilities(self.profile.connectionId,
                                                                              self.capabilities)

            self.venueUri = URL
                        
            #
            # Create the event client
            #
        
            coherenceCallbacks = {
                Event.ENTER: self.AddUserEvent,
                Event.EXIT: self.RemoveUserEvent,
                Event.MODIFY_USER: self.ModifyUserEvent,
                Event.ADD_DATA: self.AddDataEvent,
                Event.UPDATE_DATA: self.UpdateDataEvent,
                Event.REMOVE_DATA: self.RemoveDataEvent,
                Event.ADD_SERVICE: self.AddServiceEvent,
                Event.UPDATE_SERVICE: self.UpdateServiceEvent,
                Event.REMOVE_SERVICE: self.RemoveServiceEvent,
                Event.ADD_APPLICATION: self.AddApplicationEvent,
                Event.UPDATE_APPLICATION: self.UpdateApplicationEvent,
                Event.REMOVE_APPLICATION: self.RemoveApplicationEvent,
                Event.ADD_CONNECTION: self.AddConnectionEvent,
                Event.REMOVE_CONNECTION: self.RemoveConnectionEvent,
                Event.SET_CONNECTIONS: self.SetConnectionsEvent,
                Event.ADD_STREAM: self.AddStreamEvent,
                Event.MODIFY_STREAM: self.ModifyStreamEvent,
                Event.REMOVE_STREAM: self.RemoveStreamEvent,
                Event.OPEN_APP: self.OpenAppEvent
                }

            self.Heartbeat()

            #evtLocation = self.__venueProxy.GetEventServiceLocation()
                      
            # Create event client
            self.eventClient = EventClient(evtLocation, 
                                           self.profile.connectionId,
                                           self.venueState.GetUniqueId())
                                           
            for e in coherenceCallbacks.keys():
                self.eventClient.RegisterCallback(e, coherenceCallbacks[e])
                
            self.eventClient.Start()
            self.eventClient.Send("connect", self.profile.connectionId)                               

            # Create text client
            #  textLocation = self.__venueProxy.GetTextServiceLocation()
            #self.textClient = TextClient(evtLocation, #self.venueState.eventLocation,
            #                              self.privateId,
            #                              self.venue.GetUniqueId())
            #print 'register callback'
            # for e in coherenceCallbacks.keys():
            #    self.textClient.RegisterCallback("Event.Text", self.ReceiveText)
            #
            #print 'start'
            #self.eventClient.Start()
           
            #            self.eventClient.Send(ConnectEvent(self.venueState.uniqueId,
            #                                               self.privateId))

            # Get personaldatastore information
            #self.dataStoreUploadUrl = self.__venueProxy.GetUploadDescriptor()
            # FIXME, ECO
            self.dataStoreUploadUrl = None
        
            # Connect the venueclient to the text client
            #            self.textClient = TextClient(self.profile,
            #                                         self.venueState.textLocation)
            #            self.textClient.Connect(self.venueState.uniqueId, self.privateId)
            #            self.textClient.RegisterOutputCallback(self.AddTextEvent)

            log.debug("Setting isInVenue flag.")

            # Finally, set the flag that we are in a venue
            self.isInVenue = 1

            # 
            # Update the node service with stream descriptions
            #
            try:
                self.UpdateNodeService()
            except NetworkLocationNotFound, e:
                self.warningString += '\nError connecting media tools'
            except Exception, e:
                # This is a non fatal error, users should be notified
                # but still enter the venue
                log.warn("EnterVenue: Error updating node service")
                    
    def EnterVenue(self, URL):
        """
        EnterVenue puts this client into the specified venue.

        URL : url to the venue
        """
        log.debug("EnterVenue; url=%s", URL)
        
        # Initialize a string of warnings that can be displayed to the user.
        self.warningString = ''
        enterSuccess = 1
        errorInNode = 0
        
        try:
            self.profile.capabilities = self.nodeService.GetCapabilities()

        except:
            # This is a non fatal error, users should be notified
            # but still enter the venue
            log.info("EnterVenue: Error getting node capabilities")
            errorInNode = 1
            
            try:
                self.capabilities = self.nodeService.GetCapabilities()
            except:
                # This is a non fatal error, users should be notified
                # but still enter the venue
                log.info("EnterVenue: Error getting node capabilities")
                errorInNode = 1

        try:
            # Enter the venue
            self.__EnterVenue(URL)
            
            # Cache profiles from venue.
            try:
                log.debug("Updating client profile cache.")
                clients = self.venueState.clients
                for client in clients.values():
                    self.UpdateProfileCache(client)
            except Exception, e:
                log.exception("Unable to update client profile cache.")
                
            # Return a string of warnings that can be displayed to the user 
            if errorInNode:
                self.warningSting = self.warningString + '\n\nA connection to your node could not be established, which means your media tools might not start properly.  If this is a problem, try changing your node configuration by selecting "Preferences->Manage My Node..." from the main menu'

        except Exception, e:
            log.exception("EnterVenue: failed")
            enterSuccess = 0
            # put error in warningString, in redesign will be raised
            # to UI as exception.

            #self.warningString = str(e.faultstring)

        for s in self.observers:
            try:
                # enterSuccess is true if we entered.
                s.EnterVenue(URL, self.warningString, enterSuccess)
            except:
                log.exception("Exception in observer")

        return self.warningString

    def __ExitVenue(self):
        # Clear the list of personal data requests.
        self.requests = []

        # Cancel the heartbeat
        self.heartBeatTimer.cancel()

        self.exitingLock.acquire()
        if self.exiting:
            log.debug("ExitVenue: already exiting, returning.")
            self.exitingLock.release()
            return
        self.exiting = 1
        self.exitingLock.release()

        try:
            self.__venueProxy.Exit( self.profile.connectionId )
            
        except Exception:
            log.exception("ExitVenue: ExitVenue exception")

        try:
            if self.eventClient:
                log.debug("ExitVenue: Stop event client obj")
                self.eventClient.Stop()
                log.debug("ExitVenue: Remove event client reference")
                self.eventClient = None
        except:
            log.exception("ExitVenue: Can not stop event client")
            
        log.info("ExitVenue: Stopping text client")
        #         try:
        #           if self.textClient:
        #             # Stop the text client
        #             log.debug("ExitVenue: Sending client disconnect event.")
        #             self.textClient.Disconnect(self.venueState.uniqueId,
        #                                        self.privateId)
        #             log.debug("ExitVenue: Remove text client reference")
        #             self.textClient = None
        
        #         except:
        #             log.exception("ExitVenue: On text client exiting")

        self.__InitVenueData()
        self.isInVenue = 0
        self.exitingLock.acquire()
        self.exiting = 0
        self.exitingLock.release()
        
    def ExitVenue( self ):
        """
        ExitVenue removes this client from the specified venue.
        """
        log.info("ExitVenue")

        # Tell UI and others that we are exiting.
        for s in self.observers:
            s.ExitVenue()

        # Exit the venue
        # This causes the venue server to do the following:
        # Remove producers for this client.
        # Remove personal data (causes remove data events?)
        # Distribute an EXIT event.
        # Remove client from venue list of clients.
        #
        # The distribution of the EXIT event may arrive back at the
        # client if the event client has not been stopped first.
        #
        # Unfortunately there's a bit of a race here, as stopping
        # the event client causes the server to see an EOF,
        # which it interprets as a client disconnection, which will
        # in turn trigger the RemoveUser logic above.
        #
        # Ah, a likely solution is to stop the event client with a
        # special "I'm disconnecting and it's okay" event that
        # doesn't trigger the RemoveUser logic.
        # 

        # Stop the event client
        # NOT USED, so comment out for now
        #log.info("ExitVenue: Stopping event client")
        #try:
          #
          #if self.eventClient:
            #log.debug("ExitVenue: Send client exiting event")
            #self.eventClient.Send(ClientExitingEvent(self.venueState.uniqueId,
                                                     #self.privateId))
        #except:
            #log.exception("ExitVenue: Can not send client exiting event to event client")
        
        # Stop the node services
        try:
            log.info("ExitVenue: Stopping node services")
            self.nodeService.StopServices()
            self.nodeService.SetStreams([])
        except Exception:
            log.info("ExitVenue: Error stopping node services")
            
        self.__ExitVenue()

         
    #
    # NodeService-related calls
    #

    def UpdateNodeService(self):
        """
        Send venue streams to the node service
        """

        log.debug("UpdateNodeService: Method UpdateNodeService called")
        exc = None

        try:
            self.nodeService.IsValid()
        except:
            log.info("UpdateNodeService: Node Service unreachable; skipping")
            log.info("UpdateNodeService: url = %s", self.nodeServiceUri)
            return

        # Set the identity of the user running the node
        if not self.isIdentitySet:
            try:
                self.nodeService.SetIdentity(self.profile)
                self.isIdentitySet = 1
            except:
                log.exception("Error setting identity")

        # Set the streams to use the selected transport
        for stream in self.streamDescList:
            if stream.__dict__.has_key('networkLocations'):
                try:
                    self.UpdateStream(stream)
                except NetworkLocationNotFound, e:
                    log.debug("UpdateNodeService: Couldn't update stream with transport/provider info")
                    exc = e

        # Send streams to the node service
        try:
            self.nodeService.SetStreams( self.streamDescList )
        except:
            log.info("Error setting streams")

        # Raise exception if occurred
        if exc:
            raise exc

    def UpdateStream(self,stream):
        """
        Apply selections of transport and netloc provider to the given stream.
        """
        found = 0
        for netloc in stream.networkLocations:
            # use the stream if it's the right transport and
            # if transport is multicast OR the provider matches
            if netloc.type == self.transport and (self.transport == 'multicast' or netloc.profile.name == self.provider.name):
                log.debug("UpdateStream: Setting stream %s to %s",
                          stream.id, self.transport)
                stream.location = netloc   
                found = 1
                
        if not found:
            raise NetworkLocationNotFound("transport=%s; provider=%s %s" % 
                                          (self.transport, self.provider.name, self.provider.location))
    
    def SendEvent(self,event):
        self.eventClient.Send(event)

    def Shutdown(self):

        #
        # stop personal data server
        #  
        if self.transferEngine:
            self.transferEngine.stop()

        self.__StopWebService()
        
        if self.server:
            try:
                self.server.Stop()
            # FIXME THIS IS SO WRONG XXXX
            except:
                pass
             
        if self.dataStore:
            self.dataStore.Shutdown()

    def UpdateProfileCache(self, profile):
        try:
            self.cache.updateProfile(profile)
        except InvalidProfileException:
            log.info("UpdateProfileCache: InvalidProfile when storing a venue user's profile in the cache.")
            

    #
    # Venue calls
    #

    def UpdateClientProfile(self,profile):
        self.__venueProxy.UpdateClientProfile(profile)
        
    def CreateApplication(self, appName, appDescription, appMimeType):
        self.__venueProxy.CreateApplication(appName,appDescription,appMimeType)

    def DestroyApplication(self,appId):
        self.__venueProxy.DestroyApplication(appId)
        
    def UpdateApplication(self,appDescription):
        self.__venueProxy.UpdateApplication(appDescription)
        
    def AddService(self,serviceDescription):
        try:
            self.__venueProxy.AddService(serviceDescription)
        except Exception,e:
            if e.faultstring == "ServiceAlreadyPresent":
                raise ServiceAlreadyPresent
            raise

    def UpdateService(self,serviceDescription):
        self.__venueProxy.UpdateService(serviceDescription)
            
    def RemoveService(self,serviceDescription):
        self.__venueProxy.RemoveService(serviceDescription)
        
    def RemoveData(self, data):
        """
        This method removes a data from the venue. If the data is personal, this method
        also removes the data from the personal data storage.
        
        **Arguments:**
        
        *data* The DataDescription we want to remove from vnue
        """
        log.debug("Remove data: %s from venue" %data.name)

        dataList = []
        dataList.append(data)
    
        if data.type == None or data.type == 'None':
            # Venue data
            self.__venueProxy.RemoveData(data)
            
        elif(data.type == self.profile.publicId):
            # My data
            self.dataStore.RemoveFiles(dataList)
            self.eventClient.Send(Event.REMOVE_DATA, data)
            #self.eventClient.Send(RemoveDataEvent(self.GetEventChannelId(), data))
            
        else:
            # Ignore this until we have authorization in place.
            raise NotAuthorizedError

    def UpdateData(self, data):
        log.debug("Update data: %s from venue" %data.name)
        
        if data.type == None or data.type == 'None':
            # Venue data
            try:
                self.__venueProxy.UpdateData(data)
            except:
                log.exception("Error updating data")
                raise
            
        elif(data.type == self.profile.publicId):
            # My data
            try:
                self.dataStore.ModifyData(data)
                self.eventClient.Send(Event.REMOVE_DATA, data)
                #self.eventClient.Send(UpdateDataEvent(self.GetEventChannelId(), data))
            except:
                log.exception("Error modifying personal data")
                raise
        else:
            # Ignore this until we have authorization in place.
            raise NotAuthorizedError
                        
            
    #
    # TextClient wrapping
    #
        
    def SendText(self,text):
        pass
#         if self.textClient != None:
#             self.textClient.Input(text)
#         else:
#             raise Exception, "Text Client Not Connected"
        
    # end Basic Implementation
    #
    ########################################################################

    ########################################################################
    #
    # Accessors
    

    #
    # Venue State
    #
    
    def GetVenueState(self):
        return self.venueState

    def GetVenueStreams(self):
        return self.streamDescList
        
    def GetEventChannelId(self):
        return self.venueState.GetUniqueId()

    def GetVenueData(self):
        return self.venueState.GetData()

    def GetVenue( self ):
        """
        GetVenue gets the venue the client is currently in.
        """
        return self.venueUri
        
    def GetVenueName(self):
        return self.venueState.GetName()

    def GetVenueDescription(self):
        return self.venueState.GetDescription()
    
    def GetDataStoreUploadUrl(self):
        return self.dataStoreUploadUrl

    #
    # Personal Data
    #

    def GetDataStoreInformation(self):
        """
        Retrieve an upload descriptor and a URL to personal DataStore 
        
        **Returns:**
        
        *(upload description, url)* the upload descriptor to the DataStore
        and the url to the DataStore SOAP service.
        
        """
               
        if self.dataStore is None:
            return (None, None)
        else:
            return self.dataStore.GetUploadDescriptor(), self.dataStore.GetLocation()
        
    def GetPersonalData(self, clientProfile=None):
        '''
        Get personal data from client
        
        **Arguments**
            *clientProfile* of the person we want to get data from
        '''
        
        # Handle request for my own data
        # (bleh, multipurpose code)
        if not clientProfile or clientProfile.publicId == self.profile.publicId:
            log.debug('GetPersonalData: I am trying to get my own data')
            self.requests.append(self.profile.publicId)
            return self.dataStore.GetDataDescriptions()

        
        
        url = clientProfile.venueClientURL
        publicId = clientProfile.publicId

        dataList = []
                
        #
        # After initial request, personal data will be updated via events.
        #

        if not publicId in self.requests:
            log.debug("GetPersonalData: The client has NOT been queried for personal data yet %s", clientProfile.name)

            self.requests.append(publicId)
                    
            log.debug("GetPersonalData: This is somebody else's data")
            try:
                v = VenueClientIW(url)
                dataDescriptionList = v.GetPersonalData()
            except:
                log.exception("GetPersonalData: call failed")
                raise GetDataDescriptionsError()
            
            for data in dataDescriptionList:
                dataDesc = CreateDataDescription(data)
                dataList.append( dataDesc )
        
        else:
            log.debug("GetPersonalData: The client has been queried for personal %s" %clientProfile.name)
            
        return dataList

    def GetUsers(self):
        return self.venueState.GetUsers()
        
    def GetServices(self):
        return self.venueState.GetServices()
        
    def GetApplications(self):
        return self.venueState.GetApplications()
                
    def GetConnections(self):
        return self.venueState.GetConnections()
        
    def GetVenueURL(self):
        return self.venueState.GetUri()
        
    def GetNodeServiceURL(self):
        return self.nodeServiceUri
        
    def GetStreams(self):
        return self.streamDescList
        
    

    #
    # NodeService Info
    #
        
    def SetNodeUrl(self, url):
        """
        This method sets the node service url

        **Arguments:**
        
        *url* The string including the new node url address
        """
        log.debug("SetNodeUrl: Set node service url:  %s" %url)
        self.nodeServiceUri = url
        self.nodeService = AGNodeServiceIW(url)

        # assume that when the node service uri changes, the node service
        # needs identity info
        self.isIdentitySet = 0
        
    def GetNodeServiceUri(self):
        return self.nodeServiceUri

    def SetVideoEnabled(self,enableFlag):
        try:
            self.nodeService.SetServiceEnabledByMediaType("video",enableFlag)
        except:
            log.info("Error enabling video")
        
    def SetAudioEnabled(self,enableFlag):
        try:
            self.nodeService.SetServiceEnabledByMediaType("audio",enableFlag)
        except:
            log.info("Error enabling audio")

    #
    # User Info
    #

    def SaveProfile(self):
        self.preferences.SetProfile(self.profile)
        self.preferences.StorePreferences()
    
    def SavePreferences(self):
        self.preferences.StorePreferences()
        
    def GetPreferences(self):
        return self.preferences
    #
    # Bridging Info
    #
        
    def GetNetworkLocationProviders(self):
        """
        GetNetworkLocationProviders returns a list of entities providing
        network locations to the current venue.

        Note:  To do this, it looks for providers in the first stream.
               For now, this assumption is safe.
        """

        transport = 'unicast'

        providerList = []
        if self.streamDescList and self.streamDescList[0].__dict__.has_key('networkLocations'):
            networkLocations = self.streamDescList[0].networkLocations
            for netLoc in networkLocations:
                if netLoc.type == transport:
                    providerList.append(netLoc.profile)

        return providerList
                    
    def SetProvider(self,provider):
        self.provider = provider

    def GetProvider(self):
        return self.provider

    def SetTransport(self,transport):

        # Update the transport
        self.transport = transport

    def GetTransport(self):
        return self.transport

    def GetTransportList(self):
        transportDict = dict()
        for stream in self.streamDescList:
            if stream.__dict__.has_key('networkLocations'):
                for netloc in stream.networkLocations:
                    transportDict[netloc.type] = 1
        return transportDict.keys()

    #
    # Other
    #
    
    def IsInVenue(self):
        return self.isInVenue
        
    def IsVenueAdministrator(self):
        # Determine if we are an administrator so we can add
        # administrator features to UI.
        
        isVenueAdministrator = 0
        try:
            authUrl = self.venueUri + '/Authorization'

            authClient = AuthorizationManagerIW(authUrl)
            roles = authClient.GetRolesForSubject(Application.instance().GetDefaultSubject())

            for r in roles:            
                if r.name == "Administrators":
                    isVenueAdministrator = 1

        except Exception:
        
            log.exception("Error retrieving admin list; possibly old server")
            try:
                # Try legacy method (2.1.2 and earlier)
                log.info("Trying legacy method for getting admin list")
                prox = Client.SecureHandle(self.venueUri).GetProxy()
                roleNameList = prox.DetermineSubjectRoles()
                if "Venue.Administrators" in roleNameList :        
                    isVenueAdministrator = 1
            except Exception:
                log.exception("Error retrieving admin list using legacy method")
                
        return isVenueAdministrator
    

# Retrieve a list of urls of (presumably) running venue clients
def GetVenueClientUrls():
    urlList = dict()
    tdir = UserConfig.instance().GetTempDir()
    fileList = os.listdir(tdir)
    for filepath in fileList:
        if filepath.startswith("venueClientUrl"):
            fn = os.path.join(tdir, filepath)
            ctime = os.path.getctime(fn)
            f = open(fn,"r")
            venueClientUrl = f.read()
            f.close()

            urlList[ctime] = venueClientUrl         

    # This optimization makes the search for the venue client start with
    # the latest url first.
    keys = urlList.keys()
    keys.sort()
    
    nlist = map(urlList.get, keys)

    nlist.reverse()

    return nlist[0:4]
                                    

class VenueClientI(SOAPInterface):
    def __init__(self, impl):
        SOAPInterface.__init__(self, impl)
        
    def _authorize(self, *args, **kw):
        return 1
    
    def EnterVenue(self, url):
        return self.impl.EnterVenue(url)
        
    def ExitVenue(self):
        self.impl.ExitVenue()

    def GetDataStoreInformation(self):
        r = self.impl.GetDataStoreInformation()
        return r

    def GetPersonalData(self):
        dl = self.impl.GetPersonalData()
        return dl

    def GetVenueData(self):
        dl = self.impl.GetVenueData()
        return dl

    def GetUsers(self):
        profileStructList = self.impl.GetUsers()
        
        profileList = list()
        for profileStruct in profileStructList:
            profileList.append(CreateClientProfile(profileStruct))
        return profileList
        
    def GetServices(self):
        serviceStructList = self.impl.GetServices()
        
        serviceList = list()
        for serviceStruct in serviceStructList:
            serviceList.append(CreateServiceDescription(serviceStruct))
        return serviceList
        
    def GetApplications(self):
        appStructList = self.impl.GetApplications()
        
        appList = list()
        for appStruct in appStructList:
            appList.append(CreateApplicationDescription(appStruct))
        return appList
        
    def GetConnections(self):
        connStructList = self.impl.GetConnections()
        
        connList = list()
        for connStruct in connStructList:
            connList.append(CreateConnectionDescription(connStruct))
        return connList
        
    def GetVenueURL(self):
        return self.impl.GetVenueURL()
        
    def GetClientProfile(self):
        profileStruct = self.impl.GetProfile()
        profile = CreateClientProfile(profileStruct)
        return profile
        
    def GetNodeServiceURL(self):
        return self.impl.GetNodeServiceURL()
        
    def GetStreams(self):
        return self.impl.GetStreams()
    

class VenueClientIW(SOAPIWrapper):
    def __init__(self, url=None):
        SOAPIWrapper.__init__(self, url)

    def EnterVenue(self, url):
        return self.proxy.EnterVenue(url)

    def GetDataStoreInformation(self):
        r = self.proxy.GetDataStoreInformation()
        return r

    def GetVenueData(self):
        dataStructList = self.proxy.GetVenueData()
        
        dataList = list()
        for dataStruct in dataStructList:
            dataList.append(CreateDataDescription(dataStruct))
        return dataList
        
    def GetPersonalData(self):
        dataStructList = self.proxy.GetPersonalData()
        
        dataList = list()
        for dataStruct in dataStructList:
            dataList.append(CreateDataDescription(dataStruct))
        return dataList
        
    def GetUsers(self):
        profileStructList = self.proxy.GetUsers()
        
        profileList = list()
        for profileStruct in profileStructList:
            profileList.append(CreateClientProfile(profileStruct))
        return profileList
        
    def GetServices(self):
        serviceStructList = self.proxy.GetServices()
        
        serviceList = list()
        for serviceStruct in serviceStructList:
            serviceList.append(CreateServiceDescription(serviceStruct))
        return serviceList
        
    def GetApplications(self):
        appStructList = self.proxy.GetApplications()
        
        appList = list()
        for appStruct in appStructList:
            appList.append(CreateApplicationDescription(appStruct))
        return appList
        
    def GetConnections(self):
        connStructList = self.proxy.GetConnections()
        
        connList = list()
        for connStruct in connStructList:
            connList.append(CreateConnectionDescription(connStruct))
        return connList
        
    def GetVenueURL(self):
        return self.proxy.GetVenueURL()
        
    def GetClientProfile(self):
        profileStruct = self.proxy.GetClientProfile()
        profile = CreateClientProfile(profileStruct)
        return profile
        
    def GetNodeServiceURL(self):
        return self.proxy.GetNodeServiceURL()
        
    def GetStreams(self):
        streamStructList = self.proxy.GetStreams()
        
        streamList = list()
        for streamStruct in streamStructList:
            streamList.append(CreateStreamDescription(streamStruct))
        return streamList

