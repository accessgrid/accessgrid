#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client side object of the Virtual Venues Services.
#
# Author:      Ivan R. Judson, Thomas D. Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueClient.py,v 1.138 2004-03-04 15:57:24 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
"""

__revision__ = "$Id: VenueClient.py,v 1.138 2004-03-04 15:57:24 turam Exp $"
__docformat__ = "restructuredtext en"

from AccessGrid.hosting import Client
import sys
import string
import threading
import cPickle
import time

import logging, logging.handlers

from pyGlobus.io import GSITCPSocketException

from AccessGrid import Toolkit
from AccessGrid import DataStore
from AccessGrid import Platform
from AccessGrid.Platform import GetUserConfigDir
from AccessGrid.Platform import ProcessManager
from AccessGrid.Venue import VenueIW
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.hosting import Server
from AccessGrid.Utilities import LoadConfig
from AccessGrid.NetUtilities import GetSNTPTime
from AccessGrid.VenueClientObserver import VenueClientObserver
from AccessGrid.scheduler import Scheduler
from AccessGrid.EventClient import EventClient
from AccessGrid.TextClient import TextClient
from AccessGrid.Types import *
from AccessGrid.Events import Event, HeartbeatEvent, ConnectEvent
from AccessGrid.Events import DisconnectEvent, ClientExitingEvent
from AccessGrid.Events import RemoveDataEvent, UpdateDataEvent
from AccessGrid.ClientProfile import ClientProfile, ClientProfileCache, InvalidProfileException
from AccessGrid.Descriptions import ApplicationDescription, ServiceDescription
from AccessGrid.Descriptions import DataDescription, ConnectionDescription
from AccessGrid.Descriptions import CreateDataDescription, CreateVenueState
from AccessGrid.Descriptions import CreateServiceDescription
from AccessGrid.Descriptions import CreateApplicationDescription
from AccessGrid.Venue import VenueIW

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

log = logging.getLogger("AG.VenueClient")
log.setLevel(logging.DEBUG)

class VenueClient:
    """
    This is the client side object that maintains a stateful
    relationship with a Virtual Venue. This object provides the
    programmatic interface to the Access Grid for a Venues User
    Interface.  The VenueClient can only be in one venue at a    time.
    """    
    defaultNodeServiceUri = "https://localhost:11000/NodeService"
    
    def __init__(self, profile=None):
        """
        This client class is used on shared and personal nodes.
        """
        if profile:
            self.profile = profile
        else:
            self.profileFile = os.path.join(GetUserConfigDir(), "profile" )
            self.profile = ClientProfile(self.profileFile)
        
        
        self.nodeServiceUri = self.defaultNodeServiceUri
        self.nodeService = None
        self.homeVenue = None
        self.houseKeeper = Scheduler()
        self.heartbeatTask = None
        self.provider = None

        # For states that matter
        self.state = None

        # takes time
        #self.__CreateVenueClientWebService()
        self.__InitVenueData__()
        self.isInVenue = 0
        self.isIdentitySet = 0

        self.streamDescList = None
        self.transport = "multicast"
        
        # attributes for follow/lead
        self.pendingLeader = None
        self.leaderProfile = None
        self.pendingFollowers = dict()
        self.followerProfiles = dict()
        self.urlToFollow = None
        self.observers = []
               
        # attributes for personal data store
        self.personalDataStorePrefix = "personalDataStore"
        self.personalDataStorePort = 0
        self.personalDataStorePath = os.path.join(GetUserConfigDir(),
                                                  self.personalDataStorePrefix)
        self.personalDataFile = os.path.join(self.personalDataStorePath,
                                             "myData.txt" )
        # If already requested personal data, clients public id is saved
        # in requests.        
        self.requests = [] 

        # Create personal data store
        self.__CreatePersonalDataStore()

        # Manage the currently-exiting state
        self.exiting = 0
        self.exitingLock = threading.Lock()

        self.venueUri = None
        self.venueProxy = None

        # Cache profiles in case we need to look at them later.
        # specifically, the cache makes it easier to add roles when
        # managing venues.
        self.profileCachePrefix = "profileCache"
        self.profileCachePath = os.path.join(GetUserConfigDir(),
                                             self.profileCachePrefix)
        self.cache = ClientProfileCache(self.profileCachePath)

        self.processManager = ProcessManager.ProcessManager()
        
    ###########################################################################################
    #
    # Private Methods

    def __InitVenueData__( self ):
        self.eventClient = None
        self.textClient = None
        self.venueState = None
        self.venueUri = None
        self.venueProxy = None
        self.privateId = None

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
            except OSError, e:
                log.exception("__createPersonalDataStore: Could not create personal data storage path")
                self.personalDataStorePath = None
                
        if self.personalDataStorePath:
            self.transferEngine = DataStore.GSIHTTPTransferServer(('',
                                                                   self.personalDataStorePort))
            self.transferEngine.run()
            self.dataStore = DataStore.DataStore(self, self.personalDataStorePath, 
                                                 self.personalDataStorePrefix,
                                                 self.transferEngine)
                   

            #
            # load personal data from file
            #
            
            log.debug("__createPersonalDataStore: Load personal data from file")
            if os.path.exists(self.personalDataFile):
                try:
                    file = open(self.personalDataFile, 'r')
                    dList = cPickle.load(file)
                    self.dataStore.LoadPersistentData(dList)
                    file.close()
                except:
                    log.exception("__createPersonalDataStore: Personal data could not be added")

    def __CheckForInvalidClock(self):
        """
        Check to see if the local clock is out of synch, a common reason for a
        failed authentication.

        This routine only currently sets self.warningString, and should only be
        invoked from the GSITCPSocketException-handling code in EnterVenue.

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


    def __CreateVenueClientWebService(self):
        from AccessGrid.NetworkAddressAllocator import NetworkAddressAllocator
        port = NetworkAddressAllocator().AllocatePort()

        self.server = Server(('', port))
        #vci = VenueClientI(self)
        #self.server.RegisterObject(vci, path='/VenueClient')
        self.server.RunInThread()
        
        #if(self.profile != None):
        #    self.profile.venueClientURL = self.server.GetURLForObject(self)
        #    log.debug("__CreateVenueClientWebService: venue client serving: %s"
         #             % self.profile.venueClientURL)

    def __Heartbeat(self):
        if self.eventClient != None:
            isSuccess = 1
            try:
                self.eventClient.Send(HeartbeatEvent(self.venueId,
                                                     self.privateId))
                isSuccess = 1
            except:
                log.exception("Heartbeat: Heartbeat exception is caught, exit venue.")
                isSuccess = 0
                self.ExitVenue()


    # end Private Methods
    #
    ###########################################################################################

    ###########################################################################################
    #
    # Event Handlers

    def AddUserEvent(self, event):
        log.debug("AddUserEvent: Got Add User Event")

        profile = event.data
        
        self.venueState.AddUser(profile)
        for s in self.observers:
            s.AddUser(profile)

    def RemoveUserEvent(self, event):
        log.debug("RemoveUserEvent: Got Remove User Event")

        profile = event.data

        self.venueState.RemoveUser(profile)
        for s in self.observers:
            s.RemoveUser(profile)

        log.debug("RemoveUserEvent: Got Remove User Event...done")

        # Remove client from the list of clients who have
        # been requested for personal data

        try:
            index = self.requests.index(data.publicId)
            del self.requests[index]
        except:
            pass
        
    def ModifyUserEvent(self, event):
        log.debug("ModifyUserEvent: Got Modify User Event")

        profile = event.data

        self.venueState.ModifyUser(profile)
        for s in self.observers:
            s.ModifyUser(profile)

    def AddDataEvent(self, event):
        log.debug("AddDataEvent: Got Add Data Event")
          
        data = event.data
      
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

        data = event.data
                
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
        data = event.data

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

        service = event.data
        self.venueState.AddService(service)
        for s in self.observers:
            s.AddService(service)

    def UpdateServiceEvent(self, event):
        log.debug("UpdateServiceEvent: Got Update Service Event")

        data = event.data
        self.venueState.UpdateService(data)
        for s in self.eventSubscribers:
            s.UpdateServiceEvent(event)

    def RemoveServiceEvent(self, event):
        log.debug("RemoveServiceEvent: Got Remove Service Event")

        service = event.data
        self.venueState.RemoveService(service)
        for s in self.observers:
            s.RemoveService(service)

    def AddApplicationEvent(self, event):
        log.debug("AddApplicationEvent: Got Add Application Event")

        app = event.data
        self.venueState.AddApplication(app)
        for s in self.observers:
            s.AddApplication(app)

    def UpdateApplicationEvent(self, event):
        log.debug("UpdateApplicationEvent: Got Update Application Event")
        data = event.data
        self.venueState.UpdateApplication(data)
        for s in self.eventSubscribers:
            s.UpdateApplicationEvent(event)

    def RemoveApplicationEvent(self, event):
        log.debug("RemoveApplicationEvent: Got Remove Application Event")

        app = event.data
        self.venueState.RemoveApplication(app)
        for s in self.observers:
            s.RemoveApplication(app)

    def AddConnectionEvent(self, event):
        log.debug("AddConnectionEvent: Got Add Connection Event")

        connection = event.data
        self.venueState.AddConnection(connection)
        for s in self.observers:
            s.AddConnection(connection)

    def RemoveConnectionEvent(self, event):
        log.debug("RemoveConnectionEvent: Got Remove Connection Event")

        connection = event.data
        self.venueState.RemoveConnection(connection)
        for s in self.observers:
            s.RemoveConnection(connection)

    def SetConnectionsEvent(self, event):
        log.debug("SetConnectionEvent: Got Set Connections Event")

        connectionList = event.data
        self.venueState.SetConnections(connectionList)
        for s in self.observers:
            s.SetConnections(connectionList)

    def AddStreamEvent(self, event):
        log.debug("AddStreamEvent: Got Add Stream Event")
        data = event.data

        # Add the stream to the local stream store
        self.streamDescList.append(data)

        if self.nodeService == None and self.nodeServiceUri != None:
            self.nodeService = NodeServiceIW(self.nodeServiceUri)
           
        self.nodeService.AddStream(data)
        
        for s in self.observers:
            s.AddStream(event)
    
    def ModifyStreamEvent(self, event):
        log.debug("ModifyStreamEvent: Got Modify Stream Event")
        data = event.data

        # Modify the local stream store
        for i in range(len(self.streamDescList)):
            if self.streamDescList[i].id == data.id:
                self.streamDescList[i] = data

        # Update event subscribers (the UI)
        for s in self.observers:
            s.ModifyStream(event)
        
    
    def RemoveStreamEvent(self, event):
        log.debug("RemoveStreamEvent: Got Remove Stream Event")
        data = event.data

        # Remove the stream from the local stream store
        for i in range(len(self.streamDescList)):
            if self.streamDescList[i].id == data.id:
                del self.streamDescList[i]

        if self.nodeService == None and self.nodeServiceUri != None:
            self.nodeService = NodeServiceIW(self.nodeServiceUri)
           
        self.nodeService.RemoveStream(data)

        for s in self.observers:
            s.RemoveStream(event)
            
    def AddTextEvent(self,name, text):
        log.debug("TextEvent: Got Text Event")
        
        for s in self.observers:
            s.AddText(name,text)
            
        
            
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
                    
    # Back argument is true if going to a previous venue (used in UI).
    def EnterVenue(self, URL, back=0):
        """
        EnterVenue puts this client into the specified venue.

        URL : url to the venue
        back : 0|1 - used by the UI to go to the previous venue.
        """
        # Initialize a string of warnings that can be displayed to the user.
        self.warningString = ''
       
        app = Toolkit.GetApplication()
        if not app.certificateManager.HaveValidProxy():
            log.debug("VenueClient::EnterVenue: You don't have a valid proxy")
            app.certificateManager.CreateProxy()


        enterSuccess = 1
        try:
            # Exit the venue you are currently in before entering a new venue
            if self.isInVenue:
                self.ExitVenue()

            # Get capabilities from your node
            errorInNode = 0
            #haveValidNodeService = 0

            try:
                self.profile.capabilities = Client.Handle( self.nodeServiceUri ).GetProxy().GetCapabilities()
                
            except Exception, e:
                # This is a non fatal error, users should be notified
                # but still enter the venue
                log.info("EnterVenue: Get node capabilities failed")
                errorInNode = 1
                        
            #
            # Enter the venue
            #
            self.venueUri = URL
            self.venueProxy = VenueIW(URL)

            log.debug("EnterVenue: Invoke venue enter")
            (venueState, self.privateId, self.streamDescList ) = self.venueProxy.Enter( self.profile )

            self.venueState = CreateVenueState(venueState)
            
            self.venueUri = URL
            self.venueId = self.venueState.GetUniqueId()

            host, port = venueState.eventLocation
        
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
                Event.REMOVE_STREAM: self.RemoveStreamEvent
                }
        
            h, p = self.venueState.eventLocation
            self.eventClient = EventClient(self.privateId,
                                           self.venueState.eventLocation,
                                           self.venueState.uniqueId)
            
            
            for e in coherenceCallbacks.keys():
                self.eventClient.RegisterCallback(e, coherenceCallbacks[e])
            
            self.eventClient.start()
            self.eventClient.Send(ConnectEvent(self.venueState.uniqueId,
                                               self.privateId))
                               
            self.heartbeatTask = self.houseKeeper.AddTask(self.__Heartbeat, 5)
            self.heartbeatTask.start()

            #
            # Get personaldatastore information
            #
            self.dataStoreUploadUrl = self.venueProxy.GetUploadDescriptor()
        
            #
            # Connect the venueclient to the text client
            #
            self.textClient = TextClient(self.profile,
                                         self.venueState.textLocation)
            self.textClient.Connect(self.venueState.uniqueId, self.privateId)
            self.textClient.RegisterOutputCallback(self.AddTextEvent)
            
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
                errorInNode = 1

            # Cache profiles from venue.
            log.debug("Updating client profile cache.")
            for client in self.venueState.clients.values():
                self.UpdateProfileCache(client)

            log.debug("Setting isInVenue flag.")
            # Finally, set the flag that we are in a venue
            self.isInVenue = 1

            #
            # Return a string of warnings that can be displayed to the user 
            #

            if errorInNode:
                self.warningSting = self.warningString + '\n\nA connection to your node could not be established, which means your media tools might not start properly.  If this is a problem, try changing your node configuration by selecting "Preferences-My Node" from the main menu'

        except GSITCPSocketException, e:
            enterSuccess = 0

            log.error("EnterVenue: globus tcp exception: %s", e.args)

            
            if e.args[0] == 'an authentication operation failed':
                self.__CheckForInvalidClock()

            else:
                log.exception("EnterVenue: failed")
                # pass a flag to UI if we fail to enter.
                enterSuccess = 0
                # put error in warningString, in redesign will be raised to UI as exception.
                self.warningString = str(e.faultstring)
                
        except Exception, e:
            log.exception("EnterVenue: failed")
            # pass a flag to UI if we fail to enter.
            enterSuccess = 0
            # put error in warningString, in redesign will be raised to UI as exception.
            #self.warningString = str(e.faultstring)

        for s in self.observers:
            # back is true if user just hit the back button.
            # enterSuccess is true if we entered.
            s.EnterVenue(URL, self.warningString, enterSuccess)

        try:
            self.LeadFollowers()
        except:
            log.exception("Error leading followers")
            self.warningString += '\nError leading followers'


        return self.warningString
        
    def LeadFollowers(self):
        #
        # Update venue clients being led with stream descriptions
        #
        for profile in self.followerProfiles.values():
            try:
                v = VenueClientIW(profile.venueClientURL)
                v.EnterVenue(self.venueUri, 0)
            except:
                raise Exception("LeadFollowers::Exception while leading follower")

    def ExitVenue( self ):
        """
        ExitVenue removes this client from the specified venue.
        """
        log.info("ExitVenue")

        # Clear the list of personal data requests.
        self.requests = []
       
        self.exitingLock.acquire()
        if self.exiting:
            log.debug("ExitVenue: already exiting, returning.")
            self.exitingLock.release()
            return
        self.exiting = 1
        self.exitingLock.release()

        # Tell UI and others that we are exiting.
        for s in self.observers:
            s.ExitVenue()

        # Stop sending heartbeats
        if self.heartbeatTask != None:
            log.info("ExitVenue: Stopping heartbeats")
            self.heartbeatTask.stop()

        #
        # Exit the venue
        #
        # This causes the venue server to do the following:
        #
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
        log.info("ExitVenue: Stopping event client")
        try:
          
          if self.eventClient:
            log.debug("ExitVenue: Send client exiting event")
            self.eventClient.Send(ClientExitingEvent(self.venueState.uniqueId,
                                                     self.privateId))
        except:
            log.exception("ExitVenue: Can not send client exiting event to event client")
        
        try:
            if self.eventClient:
                log.debug("ExitVenue: Stop event client obj")
                self.eventClient.Stop()
                log.debug("ExitVenue: Remove event client reference")
                self.eventClient = None
        except:
            log.exception("ExitVenue: Can not stop event client")

        log.info("ExitVenue: Stopping text client")
        try:
          if self.textClient:
            # Stop the text client
            log.debug("ExitVenue: Sending client disconnect event.")
            self.textClient.Disconnect(self.venueState.uniqueId,
                                       self.privateId)
            log.debug("ExitVenue: Remove text client reference")
            self.textClient = None
          
        except:
            log.exception("ExitVenue: On text client exiting")
        
        try:
            self.venueProxy.Exit( self.privateId )
            
        except Exception, e:
            log.exception("ExitVenue: ExitVenue exception")

        # Stop the node services
        if self.nodeService == None and self.nodeServiceUri != None:
            try:
                self.nodeService = NodeServiceIW(self.nodeServiceUri)
            except Exception, e:
                log.info("ExitVenue: Don't have a node service")

            log.info("ExitVenue: Stopping node services")
            self.nodeService.StopServices()
            self.nodeService.SetStreams([])

        #
        # Save personal data
        #
        # This is done in the data store
        #
        #if self.dataStore:
        #    file = open(self.personalDataFile, 'w')
        #    cPickle.dump(self.dataStore.GetDataDescriptions(), file)
        #    file.close()
        
        self.__InitVenueData__()
        self.isInVenue = 0
        self.exitingLock.acquire()
        self.exiting = 0
        self.exitingLock.release()

         
    #
    # Method support for FOLLOW
    #
        
    def Follow( self, leaderProfile ):
        """
        Follow encapsulates the call to tell another client to lead this client
        """
        # store profile of leader to whom request is being sent
        self.pendingLeader = leaderProfile

        # request permission to follow the leader
        # (response will come in via the LeadResponse method)
        log.debug('Follow: Requesting permission to follow this leader: %s',
                  leaderProfile.name)
        v = VenueClientIW(leaderProfile.venueClientURL)
        v.RequestLead( self.profile )

    def UnFollow( self, leaderProfile ):
        """
        UnFollow tells this venue client to stop following the specified client
        """

        log.debug('UnFollow: Trying to unfollow: %s' %leaderProfile.name)
        v = VenueClientIW(leaderProfile.venueClientURL)
        v.UnLead( self.profile )
        self.leaderProfile = None

    def RequestLead( self, followerProfile):
        """
        RequestLead accepts requests from other clients who wish to be lead
        """
     
        log.debug("RequestLead: Received request to lead %s %s" %
                 (followerProfile.name, followerProfile.venueClientURL))

        # Add profile to list of followers awaiting authorization
        self.pendingFollowers[followerProfile.publicId] = followerProfile

        # Authorize the lead request (asynchronously)
        threading.Thread(target = self.AuthorizeLead,
                         args = (followerProfile,) ).start()


    def AuthorizeLead(self, clientProfile):
        """
        Authorize requests to lead this client.  
        
        Subclasses should override this method to perform their specific 
        authorization, calling SendLeadResponse thereafter.
        """
     
        response = 1

        # For now, the VenueClient authorizes every Lead request
            
        self.SendLeadResponse(clientProfile,response)

    def SendLeadResponse(self, clientProfile, response):
        """
        SendLeadResponse responds to requests to lead other venue clients.
        """

        # remove profile from list of pending followers
        if clientProfile.publicId in self.pendingFollowers.keys():
            del self.pendingFollowers[clientProfile.publicId]

        if response:
            # add profile to list of followers
            log.debug("SendLeadResponse: Authorizing lead request for %s" %clientProfile.name)
            self.followerProfiles[clientProfile.publicId] = clientProfile

            # send the response
            v = VenueClientIW(clientProfile.venueClientURL)
            v.LeadResponse(self.profile, 1)
        else:
            v = VenueClientIW(clientProfile.venueClientURL)
            v.LeadResponse(self.profile, 0)
            log.debug("SendLeadResponse: Rejecting lead request for %s",
                      clientProfile.name)

    def LeadResponse(self, leaderProfile, isAuthorized):
        """
        LeadResponse is called by other venue clients to respond to 
        lead requests sent by this client.  
        """

        # Detect responses from clients other than the pending leader
        if leaderProfile.publicId != self.pendingLeader.publicId:
            log.debug("LeadResponse: Lead response received from client other than pending leader")
            return

        # Check response
        if isAuthorized:
            log.debug("LeadResponse: Leader has agreed to lead you: %s, %s" %(self.pendingLeader.name, self.pendingLeader.distinguishedName))
            self.leaderProfile = self.pendingLeader

            # reset the pending leader
            self.pendingLeader = None
        else:
            log.debug("LeadResponse: Leader has rejected request to lead you: %s", leaderProfile.name)
        self.pendingLeader = None

        for s in self.observers:
            s.LeadResponse(leaderProfile, isAuthorized)

    def UnLead(self, clientProfile):
        """
        UnLead tells this venue client to stop dragging the specified client.
        """

        log.debug( "UnLead: AccessGrid.VenueClient::Received request to unlead %s %s"
                   %(clientProfile.name, clientProfile.venueClientURL))

        if(self.followerProfiles.has_key(clientProfile.publicId)):
            del self.followerProfiles[clientProfile.publicId]

        if(self.pendingFollowers.has_key(clientProfile.publicId)):
            del self.pendingFollowers[clientProfile.publicId]

        threading.Thread(target = self.NotifyUnLead,
                         args = (clientProfile,)).start()
            
    def NotifyUnLead(self, clientProfile):
        """
        Notify requests to stop leading this client.  
        
        Subclasses should override this method to perform their specific 
        notification
        """
        pass

    #
    # Method support for LEAD
    #
    
    def Lead( self, followerProfileList ):
        """
        Lead encapsulates the call to tell another client to follow this client
        """
               
        # request that another client (or clients) follow this client
        # (response will come in via the FollowResponse method)
        for followerProfile in followerProfileList:
            log.debug("Lead: Requesting permission to lead this client: %s", followerProfile.name )
            self.pendingFollowers[followerProfile.publicId] = followerProfile
            v = VenueClientIW(followerProfile.venueClientURL)
            v.RequestFollow( self.profile )


    def RequestFollow( self, leaderProfile):
        """
        RequestFollow accepts requests for other clients to lead this client
        """
        log.debug("RequestFollow: Received request to follow: %s", leaderProfile.name)

        # Store profile of leader making request
        self.pendingLeader = leaderProfile

        # Authorize the follow request (asynchronously)
        threading.Thread(target = self.AuthorizeFollow,
                         args = (leaderProfile,) ).start()

    def AuthorizeFollow(self, leaderProfile):
        """
        Authorize requests to lead this client.  
        
        Subclasses should override this method to perform their specific 
        authorization, calling SendFollowResponse thereafter.
        """
        response = 1

        # For now, the VenueClient authorizes every Lead request
        self.SendFollowResponse(leaderProfile,response)

    def SendFollowResponse(self, leaderProfile, response):
        """
        This method responds to requests to be led by other venue clients.
        """
        
        # clear storage of pending leader
        if leaderProfile.publicId == self.pendingLeader.publicId:
            self.pendingLeader = None

        if response:
            # add profile to list of followers
            log.debug("SendFollowResponse: Authorizing follow request for: %s", leaderProfile.name)
            self.leaderProfile = leaderProfile

            # send the response
            v = VenueClientIW(self.leaderProfile.venueClientURL)
            v.FollowResponse(self.profile,1)
        else:
            log.debug("SendFollowResponse: Rejecting follow request for: %s", leaderProfile.name)

    def FollowResponse(self, followerProfile, isAuthorized):
        """
        FollowResponse is called by other venue clients to respond to 
        follow requests sent by this client.  A UI client would override
        this method to give the user visual feedback to the Follow request.
        """
        
        # Detect responses from clients not in pending followers list
        if followerProfile.publicId not in self.pendingFollowers.keys():
            log.debug("FollowResponse: Follow response received from client not in pending followers list")
            return

        if isAuthorized:
            log.debug("FollowResponse: Follower has agreed to follow you: %s", self.pendingLeader.name)

            # add follower to list of followers
            self.followerProfiles[followerProfile.publicId] = self.pendingFollowers[followerProfile.publicId]

            # remove from pending follower list
            del self.pendingFollowers[followerProfile.publicId]
        else:
            log.debug("FollowResponse: Follower has rejected request to follow you: %s", followerProfile.name)
        self.pendingLeader = None

    #
    # NodeService-related calls
    #

    def UpdateNodeService(self):
        """
        Send venue streams to the node service
        """

        log.debug("UpdateNodeService: Method UpdateNodeService called")
        if self.nodeService == None:
            log.info("UpdateNodeService: Node Service unreachable; skipping")
            log.info("UpdateNodeService: url = %s", self.nodeServiceUri)
            return

        exc = None

        try:
            self.nodeService.IsValid()
        except:
            log.info("UpdateNodeService: Node Service unreachable; skipping")
            log.info("UpdateNodeService: url = %s", self.nodeServiceUri)
            return

        # Set the identity of the user running the node
        if not self.isIdentitySet:
            self.nodeService.SetIdentity(self.profile)
            self.isIdentitySet = 1

        # Set the streams to use the selected transport
        for stream in self.streamDescList:
            if stream.__dict__.has_key('networkLocations'):
                try:
                    self.UpdateStream(stream)
                except NetworkLocationNotFound, e:
                    log.debug("UpdateNodeService: Couldn't update stream with transport/provider info")
                    exc = e

        # Send streams to the node service
        self.nodeService.SetStreams( self.streamDescList )

        # Raise exception if occurred
        if exc:
            raise exc

    def UpdateStream(self,stream):
        """
        Apply selections of transport and netloc provider to the given stream.
        """
        found = 0
        multicastLoc = None
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

#         if self.server:
#             self.server.Stop()

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
        self.venueProxy.UpdateClientProfile(profile)
        
    def CreateApplication(self, appName, appDescription, appMimeType):
        self.venueProxy.CreateApplication(appName,appDescription,appMimeType)

    def DestroyApplication(self,appId):
        self.venueProxy.DestroyApplication(appId)
        
    def UpdateApplication(self,appDescription):
        self.venueProxy.UpdateApplication(appDescription)
        
    def AddService(self,serviceDescription):
        try:
            self.venueProxy.AddService(serviceDescription)
        except Exception,e:
            if e.faultstring == "ServiceAlreadyPresent":
                raise ServiceAlreadyPresent
            raise

    def UpdateService(self,serviceDescription):
        self.venueProxy.UpdateService(serviceDescription)
            
    def RemoveService(self,serviceDescription):
        self.venueProxy.RemoveService(serviceDescription)
        
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
            self.venueProxy.RemoveData(data)
            
        elif(data.type == self.profile.publicId):
            # My data
            self.dataStore.RemoveFiles(dataList)
            self.eventClient.Send(RemoveDataEvent(self.GetEventChannelId(), data))
            
        else:
            # Ignore this until we have authorization in place.
            raise NotAuthorizedError

    def ModifyData(self, data):
        log.debug("Modify data: %s from venue" %data.name)
        
        if data.type == None or data.type == 'None':
            # Venue data
            self.venueProxy.ModifyData(data)
            
        elif(data.type == self.profile.publicId):
            # My data
            self.dataStore.ModifyData(data)
            self.eventClient.Send(UpdateDataEvent(self.GetEventChannelId(), data))
            
        else:
            # Ignore this until we have authorization in place.
            raise NotAuthorizedError
                        
            
    #
    # Process startup
    #
        
    def StartProcess(self,command,argList):
        pid = self.processManager.start_process(command,argList)
        
    #
    # TextClient wrapping
    #
        
    def SendText(self,text):
        self.textClient.Input(text)
        
    # end Basic Implementation
    #
    ###########################################################################################

    ###########################################################################################
    #
    # Accessors
    

    #
    # Venue State
    #
    
    def GetVenueState(self):
        return self.venueState
        
    def GetEventChannelId(self):
        return self.venueState.GetUniqueId()

    def GetVenueDataDescriptions(self):
        return self.venueState.data.values()

    def GetVenue( self ):
        """
        GetVenue gets the venue the client is currently in.
        """
        return self.venueUri
        
    def GetVenueName(self):
        return self.venueState.name
        
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
            return ""
        else:
            return self.dataStore.GetUploadDescriptor(), self.dataStore.GetLocation()
        
    def GetDataDescriptions(self):
        '''
        Retreive data in the DataStore as a list of DataDescriptions.
        
        **Returns**
            *dataDescriptionList* A list of DataDescriptions representing data currently in the DataStore
        '''
        dataDescriptionList = self.dataStore.GetDataDescriptions()
        
        return dataDescriptionList

    def GetPersonalData(self, clientProfile):
        '''
        Get personal data from client
        
        **Arguements**
            *clientProfile* of the person we want to get data from
        '''
        url = clientProfile.venueClientURL
        id = clientProfile.publicId

        #
        # After initial request, personal data will be updated via events.
        #

        if not id in self.requests:
            log.debug("GetPersonalData: The client has NOT been queried for personal data yet %s", clientProfile.name)
            self.requests.append(id)
                    
            #
            # If this is my data, ignore remote SOAP call
            #
                       
            if url == self.profile.venueClientURL:
                log.debug('GetPersonalData: I am trying to get my own data')
                return self.dataStore.GetDataDescriptions()
            else:
                log.debug("GetPersonalData: This is somebody else's data")
                try:
                    v = VenueClientIW(url)
                    dataDescriptionList = v.GetDataDescriptions()
                except:
                    log.exception("GetPersonalData: GetDataDescriptions call failed")
                    raise GetDataDescriptionsError()
                
                dataList = []
                
                for data in dataDescriptionList:
                    dataDesc = CreateDataDescription(data)
                    dataList.append( dataDesc )
                    
                return dataList
        
        else:
            log.debug("GetPersonalData: The client has been queried for personal %s" %clientProfile.name)
            
    def GetSubjectRoles(self):
        return self.venueProxy.DetermineSubjectRoles()
        
                         
    #
    # NodeService Info
    #
        
    def SetNodeUrl(self, url):
        """
        This method sets the node service url

        **Arguments:**
        
        *url* The string including the new node url address
        """
        log.debug("SerNodeUrl: Set node service url:  %s" %url)
        self.nodeServiceUri = url

        # assume that when the node service uri changes, the node service
        # needs identity info
        self.isIdentitySet = 0
        
    def GetNodeServiceUri(self):
        return self.nodeServiceUri

    def SetVideoEnabled(self,enableFlag):
        self.nodeService.SetServiceEnabledByMediaType("video",enableFlag)
        
    def SetAudioEnabled(self,enableFlag):
        self.nodeService.SetServiceEnabledByMediaType("audio",enableFlag)

    #
    # User Info
    #

    def SetProfile(self, profile):
        self.profile = profile
        if(self.profile != None):
           self.profile.venueClientURL = self.service.get_handle()

    def GetProfile(self):
        return self.profile
        
    def SaveProfile(self):
        self.profile.Save(self.profileFile)
        
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
            if "Venue.Administrators" in self.GetSubjectRoles():
                isVenueAdministrator = 1
            else:
                isVenueAdministrator = 0
        except Exception, e:
            log.exception(e)
            isVenueAdministrator = 0
            if e.faultstring == "No method DetermineSubjectRoles found":
                log.info("Server has no method DetermineSubjectRoles.  Probably 2.0 server.")
            else:
                log.exception(e)
                
        return isVenueAdministrator

    def GetInstalledApps(self):
        app = Toolkit.GetApplication()
        appdb = app.GetAppDatabase()
        appDescList = appdb.ListAppsAsAppDescriptions()
        return appDescList

class VenueClientI(SOAPInterface):
    def __init__(self, impl):
        SOAPInterface.__init__(self, impl)
        
    def _authorize(self, *args, **kw):
        return 1
    
    def EnterVenue(self, url):
        return self.impl.EnterVenue(url)

    def RequestLead(self, followerProfile):
        p = CreateClientProfile(followProfile)
        self.impl.RequestLead(p)
        
    def LeadResponse(self, leaderProfile, isAuthorized):
        p = CreateClientProfile(leaderProfile)
        self.impl.LeadResponse(p, isAuthorized)

    def Unlead(self, clientProfile):
        p = CreateClientProfile(clientProfile)
        self.impl.Unlead(p)

    def RequestFollow(self, leaderProfile):
        p = CreateClientProfile(leaderProfile)
        self.impl.RequestFollow(p)
        
    def FollowResponse(self, followerProfile, isAuthorized):
        p = CreateClientProfile(followProfile)
        self.impl.FollowResponse(p, isAuthorized)

    def GetDataStoreInformation(self):
        r = self.impl.GetDataStoreInformation()
        return r

    def GetDataDescriptions(self):
        dl = self.impl.GetDataDescriptions()
        return dl

class VenueClientIW(SOAPIWrapper):
    def __init__(self, url=None):
        SOAPIWrapper.__init__(self, url)

    def EnterVenue(self, url):
        return self.proxy.EnterVenue(url)

    def RequestLead(self, followerProfile):
        self.proxy.RequestLead(followerProfile)

    def LeadResponse(self, leaderProfile, isAuthorized):
        self.proxy.LeadResponse(leaderProfile, isAuthorized)

    def Unlead(self, clientProfile):
        self.proxy.Unlead(clientProfile)

    def RequestFollow(self, leaderProfile):
        self.proxy.RequestFollow(leaderProfile)
        
    def FollowResponse(self, followerProfile, isAuthorized):
        self.proxy.FollowResponse(followerProfile, isAuthorized)

    def GetDataStoreInformation(self):
        r = self.proxy.GetDataStoreInformation()
        return r

    def GetDataDescriptions(self):
        dl = self.proxy.GetDataDescriptions()
        return dl

