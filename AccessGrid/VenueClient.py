#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client side object of the Virtual Venues Services.
#
# Author:      Ivan R. Judson, Thomas D. Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueClient.py,v 1.84 2003-07-15 20:19:38 eolson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
import urlparse
import string
import threading
import cPickle

import logging, logging.handlers

from AccessGrid.hosting.pyGlobus import Server
from AccessGrid.hosting.pyGlobus.ServiceBase import ServiceBase
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.EventClient import EventClient
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Types import *
from AccessGrid.Events import Event, HeartbeatEvent, ConnectEvent
from AccessGrid.Events import DisconnectEvent, ClientExitingEvent
from AccessGrid.scheduler import Scheduler
from AccessGrid.hosting import AccessControl
from AccessGrid import Platform
from AccessGrid.Descriptions import ApplicationDescription, ServiceDescription
from AccessGrid.Descriptions import DataDescription, ConnectionDescription
from AccessGrid.Utilities import LoadConfig
from AccessGrid import DataStore
from AccessGrid.Platform import GetUserConfigDir
from AccessGrid.Toolkit import AG_TRUE, AG_FALSE

class EnterVenueException(Exception):
    pass
   
class AuthorizationFailedError(Exception):
    pass

class GetDataStoreInfoError(Exception):
    pass

class GetDataDescriptionsError(Exception):
    pass


        
log = logging.getLogger("AG.VenueClient")

class VenueClient( ServiceBase):
    """
    This is the client side object that maintains a stateful
    relationship with a Virtual Venue. This object provides the
    programmatic interface to the Access Grid for a Venues User
    Interface.  The VenueClient can only be in one venue at a    time.
    """    

    def __init__(self, profile=None):
        """
        This client class is used on shared and personal nodes.
        """
        self.profile = profile
        self.nodeServiceUri = "https://localhost:11000/NodeService"
        self.homeVenue = None
        self.houseKeeper = Scheduler()
        self.heartbeatTask = None
        # takes time
        self.CreateVenueClientWebService()
        self.__InitVenueData__()
        self.isInVenue = 0
        self.isIdentitySet = 0
        
        # attributes for follow/lead
        self.pendingLeader = None
        self.leaderProfile = None
        self.pendingFollowers = dict()
        self.followerProfiles = dict()
        self.urlToFollow = None
        self.eventSubscribers = []
               
        # attributes for personal data store
        self.personalDataStorePrefix = "personalDataStore"
        self.personalDataStorePort = 0
        self.personalDataStorePath = os.path.join(GetUserConfigDir(), self.personalDataStorePrefix)
        self.personalDataFile = os.path.join(self.personalDataStorePath, "myData.txt" )
        self.requests = [] # If already requested personal data, clients public id is saved in requests.

        # Create personal data store
        self.__createPersonalDataStore()

        # Manage the currently-exiting state
        self.exiting = 0
        self.exitingLock = threading.Lock()

        self.client = None
        self.clientHandle = None
        self.venueUri = None
                          
    def __InitVenueData__( self ):
        self.eventClient = None
        self.venueState = None
        self.venueUri = None
        self.venueProxy = None
        self.privateId = None

    def Heartbeat(self):
        if self.eventClient != None:
            isSuccess = AG_TRUE
            try:
                self.eventClient.Send(HeartbeatEvent(self.venueId, self.privateId))
                isSuccess = AG_TRUE
            except:
                log.exception("AccessGrid::VenueClient:Heartbeat: Heartbeat exception is caught, exit venue.")
                isSuccess = AG_FALSE

            # Send whether Heartbeat succeeded or failed to UI.
            for s in self.eventSubscribers:
                s.Heartbeat(isSuccess)
            
                                  
    def SetProfile(self, profile):
        self.profile = profile
        if(self.profile != None):
           self.profile.venueClientURL = self.service.get_handle()
                
    def CreateVenueClientWebService(self):

        # Authorization callback for the server
        def AuthCallback(server, g_handle, remote_user, context):
            return 1
        
        from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
        port = MulticastAddressAllocator().AllocatePort()

        self.server = Server.Server(port, auth_callback=AuthCallback)
        self.service = self.server.CreateServiceObject("VenueClient")
        self._bind_to_service( self.service )
        self.server.run_in_thread()
        
        if(self.profile != None):
            self.profile.venueClientURL = self.service.get_handle()
            log.debug("AccessGrid.VenueClient::venue client serving : %s" %self.profile.venueClientURL)

    def __createPersonalDataStore(self):
        """
        Creates the personal data storage and loads personal data
        from file to a dictionary of DataDescriptions. If the file is removed
        from local path, the description is not added to the list.
        """
        
        log.debug("bin.VenueClient::__createPersonalDataStore: Creating personal datastore at %s using prefix %s and port %s" %(self.personalDataStorePath, self.personalDataStorePrefix,self.personalDataStorePort))
        
        if not os.path.exists(self.personalDataStorePath):
            try:
                os.mkdir(self.personalDataStorePath)
            except OSError, e:
                log.exception("bin.VenueClient::__createPersonalDataStore: Could not create personal data storage path")
                self.personalDataStorePath = None
                
        if self.personalDataStorePath:
            self.dataStore = DataStore.DataStore(self.personalDataStorePath, self.personalDataStorePrefix)
            self.transferEngine = DataStore.GSIHTTPTransferServer(('',
                                                                   self.personalDataStorePort))
            self.transferEngine.run()
            self.transferEngine.RegisterPrefix(self.personalDataStorePrefix, self)
            self.dataStore.SetTransferEngine(self.transferEngine)

            #
            # load personal data from file
            #
            
            log.debug("AccessGrid.VenueClient::__createPersonalDataStore: Load personal data from file")
            if os.path.exists(self.personalDataFile):
                try:
                    file = open(self.personalDataFile, 'r')
                    dList = cPickle.load(file)
                    self.dataStore.LoadPersistentData(dList)
                    file.close()
                except:
                    log.exception("Personal data could not be added")

    # General EventHandler
    # handler should have functions, AddUser, RemoveUser, etc.
    def AddEventSubscriber(self, handler):
        if handler != None:
            self.eventSubscribers.append(handler)
                    
    #
    # Event Handlers
    #
    def AddUserEvent(self, event):
        log.debug("Got Add User Event")

        data = event.data
        
        self.venueState.AddUser(data)
        for s in self.eventSubscribers:
            s.AddUserEvent(event)

    def RemoveUserEvent(self, event):
        log.debug("Got Remove User Event")

        data = event.data

        self.venueState.RemoveUser(data)
        for s in self.eventSubscribers:
            s.RemoveUserEvent(event)

        log.debug("Got Remove User Event...done")
        
    def ModifyUserEvent(self, event):
        log.debug("Got Modify User Event")

        data = event.data

        self.venueState.ModifyUser(data)
        for s in self.eventSubscribers:
            s.ModifyUserEvent(event)

    def AddDataEvent(self, event):
        log.debug("Got Add Data Event")

        data = event.data

        try:
            self.venueState.AddData(data)
        except:
            pass
        
        for s in self.eventSubscribers:
            s.AddDataEvent(event)

    def UpdateDataEvent(self, event):
        log.debug("Got Update Data Event")

        data = event.data
        # Venue data (personal data handled in VenueClientUIClasses)
        if data.type == "None" or data.type == None:
            self.venueState.UpdateData(data)

        for s in self.eventSubscribers:
            s.UpdateDataEvent(event)

    def RemoveDataEvent(self, event):
        log.debug("Got Remove Data Event")

        data = event.data
        # Venue data (personal data handled in VenueClientUIClasses)
        if data.type == "None" or data.type == None:
            self.venueState.RemoveData(data)
            
        for s in self.eventSubscribers:
            s.RemoveDataEvent(event)

    def AddServiceEvent(self, event):
        log.debug("Got Add Service Event")

        data = event.data
        self.venueState.AddService(data)
        for s in self.eventSubscribers:
            s.AddServiceEvent(event)

    def RemoveServiceEvent(self, event):
        log.debug("Got Remove Service Event")

        data = event.data
        self.venueState.RemoveService(data)
        for s in self.eventSubscribers:
            s.RemoveServiceEvent(event)

    def AddApplicationEvent(self, event):
        log.debug("Got Add Application Event")

        data = event.data
        self.venueState.AddApplication(data)
        for s in self.eventSubscribers:
            s.AddApplicationEvent(event)

    def RemoveApplicationEvent(self, event):
        log.debug("Got Remove Application Event")

        data = event.data
        self.venueState.RemoveApplication(data)
        for s in self.eventSubscribers:
            s.RemoveApplicationEvent(event)

    def AddConnectionEvent(self, event):
        log.debug("Got Add Connection Event")

        data = event.data
        self.venueState.AddConnection(data)
        for s in self.eventSubscribers:
            s.AddConnectionEvent(event)

    def RemoveConnectionEvent(self, event):
        log.debug("Got Remove Connection Event")

        data = event.data
        self.venueState.RemoveConnection(data)
        for s in self.eventSubscribers:
            s.RemoveConnectionEvent(event)

    def SetConnectionsEvent(self, event):
        log.debug("Got Set Connections Event")

        data = event.data
        self.venueState.SetConnections(data)
        for s in self.eventSubscribers:
            s.SetConnectionEvent(event)

    def AddStreamEvent(self, event):
        log.debug("Got Add Stream Event")
        data = event.data
        if self.nodeServiceUri != None:
            Client.Handle(self.nodeServiceUri).GetProxy().AddStream(data)
        for s in self.eventSubscribers:
            s.AddStreamEvent(event)
    
    def RemoveStreamEvent(self, event):
        log.debug("Got Remove Stream Event")
        data = event.data
        if self.nodeServiceUri != None:
            Client.Handle(self.nodeServiceUri).GetProxy().RemoveStream(data)
        for s in self.eventSubscribers:
            s.RemoveStreamEvent(event)
        
    # Back argument is true if going to a previous venue (used in UI).
    def EnterVenue(self, URL, back=AG_FALSE):
        """
        EnterVenue puts this client into the specified venue.
        """

        # Initialize a string of warnings that can be displayed to the user.
        self.warningString = ''

        for s in self.eventSubscribers:
            s.PreEnterVenue(URL, back)

        enterSuccess = AG_TRUE
        try:
            #
            # if this venue url has a valid web service then enter venue
            #

            self.venueUri = URL
            
            self.clientHandle = Client.Handle(self.venueUri)
            self.client = self.clientHandle.GetProxy()

            # catch unauthorized SOAP calls to EnterVenue
            securityManager = AccessControl.GetSecurityManager()
            if securityManager != None:
                callerDN = securityManager.GetSubject().GetName()
                if callerDN != None and callerDN != self.leaderProfile.distinguishedName:
                    raise AuthorizationFailedError("Unauthorized leader tried to lead venue client")

            #
            # Exit the venue you are currently in before entering a new venue
            #
            if self.isInVenue:
                self.ExitVenue()

            #
            # Get capabilities from your node
            #

            errorInNode = 0
            #haveValidNodeService = 0
            try:
                #if self.nodeServiceUri != None:
                #    try:
                #        Client.Handle( self.nodeServiceUri ).IsValid()
                #        haveValidNodeService = 1
                #    except Client.InvalidHandleException:
                #        log.exception("Invalid Node Service URI (%s)"
                #                      % self.nodeServiceUri)
                
                    #
                    # Retrieve list of node capabilities
                    #
                #if haveValidNodeService:
                self.profile.capabilities = Client.Handle( self.nodeServiceUri ).get_proxy().GetCapabilities()
                
            except Exception, e:
                #
                # This is a non fatal error, users should be notified but still enter the venue
                #
                log.info("AccessGrid.VenueClient::Get node capabilities failed")
                errorInNode = 1
                        
            #
            # Enter the venue
            #

            log.debug("Invoke venue enter")
            (venueState, self.privateId, streamDescList ) = Client.Handle( URL ).get_proxy().Enter( self.profile )

       
                
            #
            # construct a venue state that consists of real objects
            # instead of the structs we get back from the SOAP call
            # (this code can be removed when SOAP returns real objects)
            #
            connectionList = []
            for conn in venueState.connections:
                connectionList.append( ConnectionDescription( conn.name, conn.description, conn.uri ) )

            clientList = []
            for client in venueState.clients:
                profile = ClientProfile()
                profile.profileFile = client.profileFile
                profile.profileType = client.profileType
                profile.name = client.name
                profile.email = client.email
                profile.phoneNumber = client.phoneNumber
                profile.icon = client.icon
                profile.publicId = client.publicId
                profile.location = client.location
                profile.venueClientURL = client.venueClientURL
                profile.techSupportInfo = client.techSupportInfo
                profile.homeVenue = client.homeVenue
                profile.privateId = client.privateId
                profile.distinguishedName = client.distinguishedName

                # should also objectify the capabilities, but not doing it 
                # for now (until it's a problem ;-)
                profile.capabilities = client.capabilities

                clientList.append( profile )

            dataList = []
            for data in venueState.data:
                dataDesc = DataDescription( data.name )
                dataDesc.status = data.status
                dataDesc.size = data.size
                dataDesc.checksum = data.checksum
                dataDesc.owner = data.owner
                dataDesc.type = data.type
                dataDesc.uri = data.uri
                dataList.append( dataDesc )

            applicationList = []
            for application in venueState.applications:
                applicationList.append( ApplicationDescription( application.id, application.name,
                                                                application.description,
                                                                application.uri, application.mimeType) )

            serviceList = []
            for service in venueState.services:
                serviceList.append( ServiceDescription( service.name, service.description,
                                                        service.uri, service.mimeType ) )
        
            self.venueState = VenueState( venueState.uniqueId,
                                          venueState.name,
                                          venueState.description,
                                          venueState.uri,
                                          connectionList, 
                                          clientList,
                                          dataList,
                                          venueState.eventLocation,
                                          venueState.textLocation,
                                          applicationList,
                                          serviceList)
            self.venueUri = URL
            self.venueId = self.venueState.GetUniqueId()
            self.venueProxy = Client.Handle( URL ).get_proxy()

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
                Event.REMOVE_SERVICE: self.RemoveServiceEvent,
                Event.ADD_APPLICATION: self.AddApplicationEvent,
                Event.REMOVE_APPLICATION: self.RemoveApplicationEvent,
                Event.ADD_CONNECTION: self.AddConnectionEvent,
                Event.REMOVE_CONNECTION: self.RemoveConnectionEvent,
                Event.SET_CONNECTIONS: self.SetConnectionsEvent,
                Event.ADD_STREAM: self.AddStreamEvent,
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
                               
            self.heartbeatTask = self.houseKeeper.AddTask(self.Heartbeat, 5)
            self.heartbeatTask.start()

            #
            # Send eventClient to personal dataStore and get personaldatastore information
            #
            self.dataStore.SetEventDistributor(self.eventClient, self.venueState.uniqueId)
            self.dataStoreUploadUrl = self.venueProxy.GetUploadDescriptor()
            #self.dataStoreUploadUrl,self.dataStoreLocation = Client.Handle( URL ).get_proxy().GetDataStoreInformation()
        
            # 
            # Update the node service with stream descriptions
            #
            try:
                #if haveValidNodeService:
                if not self.isIdentitySet:
                    """
                    Inform the node of the identity of the person driving it
                    """
                    Client.Handle(self.nodeServiceUri).GetProxy().SetIdentity(self.profile)
                    self.isIdentitySet = 1
                
                Client.Handle( self.nodeServiceUri ).GetProxy().SetStreams( streamDescList )

            except Exception, e:
                #
                # This is a non fatal error, users should be notified but still enter the venue
                #
                log.info("AccessGrid.VenueClient::Exception configuring node service streams")
                errorInNode = 1
                 
            # Finally, set the flag that we are in a venue
            self.isInVenue = 1

            #
            # Return a string of warnings that can be displayed to the user 
            #

            if errorInNode:
                self.warningSting = self.warningString + '\n\nA connection to your node could not be established, which means your media tools might not start properly.  If this is a problem, try changing your node configuration by selecting "Preferences-My Node" from the main menu'

        except Exception, e:
            log.exception("AccessGrid.VenueClient::EnterVenue failed")
            # pass a flag to UI if we fail to enter.
            enterSuccess = AG_FALSE

        for s in self.eventSubscribers:
            # back is true if user just hit the back button.
            # enterSuccess is true if we entered.
            s.EnterVenue(URL, back, self.warningString, enterSuccess)

        return self.warningString
        
    EnterVenue.soap_export_as = "EnterVenue"

    def LeadFollowers(self):
        #
        # Update venue clients being led with stream descriptions
        #
        for profile in self.followerProfiles.values():
            try:
                Client.Handle( profile.venueClientURL ).get_proxy().EnterVenue(self.venueUri, 0)
            except:
                log.exception("AccessGrid.VenueClient::Exception while leading follower")

    def ExitVenue( self ):
        """
        ExitVenue removes this client from the specified venue.
        """
        log.info("VenueClient.ExitVenue")

        self.exitingLock.acquire()
        if self.exiting:
            log.debug("VenueClient already exiting, returning.")
            self.exitingLock.release()
            return
        self.exiting = 1
        self.exitingLock.release()

        # Tell UI and others that we are exiting.
        for s in self.eventSubscribers:
            s.ExitVenue()

        # Stop sending heartbeats
        if self.heartbeatTask != None:
            log.info(" Stopping heartbeats")
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
        log.info(" Stopping event client")
        try:
            log.debug("  send client exiting event")
            self.eventClient.Send(ClientExitingEvent(self.venueState.uniqueId,
                                                     self.privateId))
            log.debug("  stop event client obj")
            self.eventClient.Stop()
            log.debug("  remove reference")
            self.eventClient = None
        except:
            # An exception is always thrown for some reason when I exit
            # the event client
            log.exception("on client exiting")
            
        try:         
            self.venueProxy.Exit( self.privateId )
        except Exception, e:
            log.exception("AccessGrid.VenueClient::ExitVenue exception")

        # Stop the node services
        if self.nodeServiceUri != None:
            try:
                nodeHandle = Client.Handle(self.nodeServiceUri)

                #if nodeHandle.IsValid():
                log.info(" Stopping node services")
                nodeHandle.GetProxy().StopServices()
                nodeHandle.GetProxy().SetStreams([])
            except Exception, e:
                log.info("don't have a node service")

        #
        # Save personal data
        #
        if self.dataStore:
            file = open(self.personalDataFile, 'w')
            cPickle.dump(self.dataStore.GetDataDescriptions(), file)
            file.close()

        self.__InitVenueData__()
        self.isInVenue = 0
        self.exitingLock.acquire()
        self.exiting = 0
        self.exitingLock.release()

    def GetVenue( self ):
        """
        GetVenue gets the venue the client is currently in.
        """
        return self.venueUri
        
    def GetHomeVenue( self ):
        """
        GetHomeVenue returns the default venue for this venue client.
        """
        return self.homeVenue
        
    def SetHomeVenue( self, venueURL):
        """
        SetHomeVenue sets the default venue for this venue client.
        """
        self.homeVenue = venueURL

    def SetNodeServiceUri( self, nodeServiceUri ):
        """
        Bind the given node service to this venue client
        """
        self.nodeServiceUri = nodeServiceUri

        # assume that when the node service uri changes, the node service
        # needs identity info
        self.isIdentitySet = 0

    def GetInstalledApps(self):
        """
        Return a list of installed applications
        """
        applicationList = []
    
        # Determine the applications directory
        installDir = Platform.GetSystemConfigDir()
        appsDir = os.path.join(installDir,"applications")
        log.info("Applications dir = %s" % appsDir )

        if os.path.exists(appsDir):
            # Find directories in the apps directory
            dirList = []
            entryList = os.listdir(appsDir)
            for entry in entryList:
                dir = os.path.join(appsDir,entry)
                if os.path.isdir(dir):
                    dirList.append(dir)

            # Find app files in the app directories
            for dir in dirList:
                fileList = os.listdir(dir)
                for file in fileList:
                    if file.endswith(".app"):
                        pathfile = os.path.join(dir,file)

                        # read app file contents
                        config = LoadConfig(pathfile)

                        # construct application description therefrom
                        appName = config["application.name"]
                        appDescription = config["application.description"]
                        appMimetype = config["application.mimetype"]
                        app = ApplicationDescription( None, appName,    
                                                      appDescription,
                                                      None,
                                                      appMimetype )
                        log.info("Found installed application: %s" % appName )
                        applicationList.append( app )
        return applicationList

    #
    # Method support for personal data
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
        
    GetDataStoreInformation.soap_export_as = "GetDataStoreInformation"

    def RemoveData(self, data, ownerProfile):
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
            #Client.Handle(self.venueClient.dataStoreLocation).GetProxy().RemoveFiles(dataList)
            
        elif(data.type == self.profile.publicId):
            # My data
            self.dataStore.RemoveFiles(dataList)
            
        else:
            # Somebody else's personal data
                       
            if ownerProfile != None:
                uploadDescriptor, dataStoreUrl = Client.Handle(ownerProfile.venueClientURL).get_proxy().GetDataStreInformation()
                Client.Handle(dataStoreUrl).get_proxy().RemoveFiles(dataList)
                
    def GetPersonalData(self, clientProfile):
        '''
        Get personal data from client
        
        **Arguements**
            *clientProfile* of the person we want to get data from
        '''
        url = clientProfile.venueClientURL
        id = clientProfile.publicId

        log.debug("bin.VenueClient.GetPersonalData")

        #
        # After initial request, personal data will be updated via events.
        #
      
        if not id in self.requests:
            log.debug("bin.VenueClient.GetPersonalData: The client has NOT been queried for personal data yet %s", clientProfile.name)
            self.requests.append(id)
         
            #
            # If this is my data, ignore remote SOAP call
            #
                       
            if url == self.profile.venueClientURL:
                log.debug('bin.VenueClient.GetPersonalData: I am trying to get my own data')
                return self.dataStore.GetDataDescriptions()
            else:
                log.debug("bin.VenueClient.GetPersonalData: This is somebody else's data")
                try:
                    uploadDescriptor, dataStoreUrl = Client.Handle(url).get_proxy().GetDataStoreInformation()
                except:
                    raise GetDataStoreInfoError()
                    
                try:
                    dataDescriptionList = Client.Handle(dataStoreUrl).get_proxy().GetDataDescriptions()
                except:
                    raise GetDataDescriptionsError()
                
                dataList = []
                
                for data in dataDescriptionList:
                    dataDesc = DataDescription( data.name )
                    dataDesc.status = data.status
                    dataDesc.size = data.size
                    dataDesc.checksum = data.checksum
                    dataDesc.owner = data.owner
                    dataDesc.type = data.type
                    dataDesc.uri = data.uri
                    dataList.append( dataDesc )
                    
                return dataList
        
        else:
            log.debug("bin.VenueClient.GetPersonalData: The client has been queried for personal %s" %clientProfile.name)
                        
         
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
        log.debug('AccessGrid.VenueClient::Requesting permission to follow this leader: %s' %leaderProfile.name)
        Client.Handle( leaderProfile.venueClientURL ).get_proxy().RequestLead( self.profile )

    def UnFollow( self, leaderProfile ):
        """
        UnFollow tells this venue client to stop following the specified client
        """

        log.debug('AccessGrid.VenueClient::Trying to unfollow: %s' %leaderProfile.name)
        Client.Handle( leaderProfile.venueClientURL ).get_proxy().UnLead( self.profile )
        self.leaderProfile = None

    def RequestLead( self, followerProfile):
        """
        RequestLead accepts requests from other clients who wish to be lead
        """

        log.debug("AccessGrid.VenueClient::Received request to lead %s %s" %
                 (followerProfile.name, followerProfile.venueClientURL))

        # Add profile to list of followers awaiting authorization
        self.pendingFollowers[followerProfile.publicId] = followerProfile

        # Authorize the lead request (asynchronously)
        threading.Thread(target = self.AuthorizeLead, args = (followerProfile,) ).start()

    RequestLead.soap_export_as = "RequestLead"

    def AuthorizeLead(self, clientProfile):
        """
        Authorize requests to lead this client.  
        
        Subclasses should override this method to perform their specific 
        authorization, calling SendLeadResponse thereafter.
        """
        response = 1

        # For now, the base VenueClient authorizes every Lead request
            
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
            log.debug("AccessGrid.VenueClient::Authorizing lead request for %s" %clientProfile.name)
            self.followerProfiles[clientProfile.publicId] = clientProfile

            # send the response
            Client.Handle( clientProfile.venueClientURL ).get_proxy().LeadResponse(self.profile, 1)
        else:
            Client.Handle( clientProfile.venueClientURL ).get_proxy().LeadResponse(self.profile, 0)
            log.debug("AccessGrid.VenueClient::Rejecting lead request for %s" %clientProfile.name)

    def LeadResponse(self, leaderProfile, isAuthorized):
        """
        LeadResponse is called by other venue clients to respond to 
        lead requests sent by this client.  A UI client would override
        this method to give the user visual feedback to the Lead request.
        """

        # Detect responses from clients other than the pending leader
        if leaderProfile.publicId != self.pendingLeader.publicId:
            log.debug("Lead response received from client other than pending leader")
            return

        # Check response
        if isAuthorized:
            log.debug("AccessGrid.VenueClient::Leader has agreed to lead you: %s, %s" %(self.pendingLeader.name, self.pendingLeader.distinguishedName))
            self.leaderProfile = self.pendingLeader

            # reset the pending leader
            self.pendingLeader = None
        else:
            log.debug("AccessGrid.VenueClient::Leader has rejected request to lead you: %s", leaderProfile.name)
        self.pendingLeader = None

        for s in self.eventSubscribers:
            s.LeadResponse(leaderProfile, isAuthorized)

    LeadResponse.soap_export_as = "LeadResponse"

    def UnLead(self, clientProfile):
        """
        UnLead tells this venue client to stop dragging the specified client.
        """

        log.debug( "AccessGrid.VenueClient::AccessGrid.VenueClient::Received request to unlead %s %s"
                   %(clientProfile.name, clientProfile.venueClientURL))

        if(self.followerProfiles.has_key(clientProfile.publicId)):
            del self.followerProfiles[clientProfile.publicId]

        if(self.pendingFollowers.has_key(clientProfile.publicId)):
            del self.pendingFollowers[clientProfile.publicId]

        threading.Thread(target = self.NotifyUnLead, args = (clientProfile,)).start()
            
    UnLead.soap_export_as = "UnLead"

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
            log.debug("Requesting permission to lead this client: %s", followerProfile.name )
            self.pendingFollowers[followerProfile.publicId] = followerProfile
            Client.Handle( followerProfile.venueClientURL ).get_proxy().RequestFollow( self.profile )


    def RequestFollow( self, leaderProfile):
        """
        RequestFollow accepts requests for other clients to lead this client
        """

        log.debug("Received request to follow: %s", leaderProfile.name)

        # Store profile of leader making request
        self.pendingLeader = leaderProfile

        # Authorize the follow request (asynchronously)
        threading.Thread(target = self.AuthorizeFollow, args = (leaderProfile,) ).start()

    RequestFollow.soap_export_as = "RequestFollow"

    def AuthorizeFollow(self, leaderProfile):
        """
        Authorize requests to lead this client.  
        
        Subclasses should override this method to perform their specific 
        authorization, calling SendFollowResponse thereafter.
        """
        response = 1

        # For now, the base VenueClient authorizes every Lead request
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
            log.debug("Authorizing follow request for: %s", leaderProfile.name)
            self.leaderProfile = leaderProfile

            # send the response
            Client.Handle( self.leaderProfile.venueClientURL ).get_proxy().FollowResponse(self.profile,1)
        else:
            log.debug("Rejecting follow request for: %s", leaderProfile.name)

    def FollowResponse(self, followerProfile, isAuthorized):
        """
        FollowResponse is called by other venue clients to respond to 
        follow requests sent by this client.  A UI client would override
        this method to give the user visual feedback to the Follow request.
        """

        # Detect responses from clients not in pending followers list
        if followerProfile.publicId not in self.pendingFollowers.keys():
            log.debug("Follow response received from client not in pending followers list")
            return

        if isAuthorized:
            log.debug("Follower has agreed to follow you: %s", self.pendingLeader.name)

            # add follower to list of followers
            self.followerProfiles[followerProfile.publicId] = self.pendingFollowers[followerProfile.publicId]

            # remove from pending follower list
            del self.pendingFollowers[followerProfile.publicId]
        else:
            log.debug("Follower has rejected request to follow you: %s", followerProfile.name)
        self.pendingLeader = None

    FollowResponse.soap_export_as = "FollowResponse"

    def SetNodeUrl(self, url):
        """
        This method sets the node service url

        **Arguments:**
        
        *url* The string including the new node url address
        """
        log.debug("Set node service url:  %s" %url)
        self.nodeServiceUri = url

    def Shutdown(self):

        #
        # stop personal data server
        #  
        if self.transferEngine:
            self.transferEngine.stop()

        if self.server:
            self.server.Stop()

        if self.dataStore:
            self.dataStore.Shutdown()

