#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client side object of the Virtual Venues Services.
#
# Author:      Ivan R. Judson, Thomas D. Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueClient.py,v 1.59 2003-05-12 17:22:07 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
import urlparse
import string
import threading

import logging, logging.handlers

from AccessGrid.hosting.pyGlobus import Server
from AccessGrid.hosting.pyGlobus.ServiceBase import ServiceBase
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.EventClient import EventClient
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Types import *
from AccessGrid.Events import Event, HeartbeatEvent, ConnectEvent
from AccessGrid.Events import DisconnectEvent
from AccessGrid.scheduler import Scheduler
from AccessGrid.hosting import AccessControl
from AccessGrid import Platform
from AccessGrid.Descriptions import ApplicationDescription, ServiceDescription
from AccessGrid.Descriptions import DataDescription, ConnectionDescription
from AccessGrid.Utilities import LoadConfig

class EnterVenueException(Exception):
    pass
   
class AuthorizationFailedError(Exception):
    pass
        
log = logging.getLogger("AG.VenueClient")

class VenueClient( ServiceBase):
    """
    This is the client side object that maintains a stateful
    relationship with a Virtual Venue. This object provides the
    programmatic interface to the Access Grid for a Venues User
    Interface.  The VenueClient can only be in one venue at a
    time.
    """
    urlToFollow = None
    
    def __init__(self, profile=None):
        """
        This client class is used on shared and personal nodes.
        """
        self.profile = profile
        self.nodeServiceUri = "https://localhost:11000/NodeService"
        self.homeVenue = None
        self.houseKeeper = Scheduler()
        self.heartbeatTask = None
        self.CreateVenueClientWebService()
        self.__InitVenueData__()
        self.isInVenue = 0

        # attributes for follow/lead
        self.pendingLeader = None
        self.leaderProfile = None
        self.pendingFollowers = dict()
        self.followerProfiles = dict()
                          
    def __InitVenueData__( self ):
        self.eventClient = None
        self.venueState = None
        self.venueUri = None
        self.venueProxy = None
        self.privateId = None

    def Heartbeat(self):
        if self.eventClient != None:
            self.eventClient.Send(HeartbeatEvent(self.venueId, self.privateId))
            
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

        server = Server.Server(port, auth_callback=AuthCallback)
        self.service = server.CreateServiceObject("VenueClient")
        self._bind_to_service( self.service )
        server.run_in_thread()
        
        if(self.profile != None):
            self.profile.venueClientURL = self.service.get_handle()
            log.debug("AccessGrid.VenueClient::venue client serving : %s" %self.profile.venueClientURL)
                 
    #
    # Event Handlers
    #
    def AddUserEvent(self, data):
        log.debug("Got Add User Event")
        
        self.venueState.AddUser(data)

    def RemoveUserEvent(self, data):
        log.debug("Got Remove User Event")

        self.venueState.RemoveUser(data)

    def ModifyUserEvent(self, data):
        log.debug("Got Modify User Event")

        self.venueState.ModifyUser(data)

    def AddDataEvent(self, data):
        log.debug("Got Add Data Event")

        self.venueState.AddData(data)

    def UpdateDataEvent(self, data):
        log.debug("Got Update Data Event")

        self.venueState.UpdateData(data)

    def RemoveDataEvent(self, data):
        log.debug("Got Remove Data Event")

        self.venueState.RemoveData(data)

    def AddServiceEvent(self, data):
        log.debug("Got Add Service Event")

        self.venueState.AddService(data)

    def RemoveServiceEvent(self, data):
        log.debug("Got Remove Service Event")

        self.venueState.RemoveService(data)

    def AddApplicationEvent(self, data):
        log.debug("Got Add Application Event")

        self.venueState.AddApplication(data)

    def RemoveApplicationEvent(self, data):
        log.debug("Got Remove Application Event")

        self.venueState.RemoveApplication(data)

    def AddConnectionEvent(self, data):
        log.debug("Got Add Connection Event")

        self.venueState.AddConnection(data)

    def RemoveConnectionEvent(self, data):
        log.debug("Got Remove Connection Event")

        self.venueState.RemoveConnection(data)

    def SetConnectionsEvent(self, data):
        log.debug("Got Set Connections Event")

        self.venueState.SetConnections(data)

    def AddStreamEvent(self,data):
        log.debug("Got Add Stream Event")
        if self.nodeServiceUri != None:
            Client.Handle(self.nodeServiceUri).GetProxy().AddStream(data)
    
    def RemoveStreamEvent(self,data):
        log.debug("Got Remove Stream Event")
        if self.nodeServiceUri != None:
            Client.Handle(self.nodeServiceUri).GetProxy().RemoveStream(data)
        
    def EnterVenue(self, URL):
        """
        EnterVenue puts this client into the specified venue.
        """

        # catch unauthorized SOAP calls to EnterVenue
        securityManager = AccessControl.GetSecurityManager()
        if securityManager != None:
            callerDN = securityManager.GetSubject().GetName()
            if callerDN != None and callerDN != self.leaderProfile.distinguishedName:
                raise AuthorizationFailedError("Unauthorized leader tried to lead venue client")
        
        haveValidNodeService = 0
        if self.nodeServiceUri != None:
            haveValidNodeService = Client.Handle( self.nodeServiceUri ).IsValid()

        #
        # Enter the venue and configure the client
        #
                   
        if self.isInVenue:
            self.ExitVenue()

        #
        # Retrieve list of node capabilities
        #
        if haveValidNodeService:
            self.profile.capabilities = Client.Handle( self.nodeServiceUri ).get_proxy().GetCapabilities()
            
        #
        # Enter the venue
        #
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
        # Update the node service with stream descriptions
        #
        try:
            if haveValidNodeService:
                Client.Handle( self.nodeServiceUri ).get_proxy().SetStreams( streamDescList )
        except:
            log.exception("AccessGrid.VenueClient::Exception configuring node service streams")

        #
        # Update venue clients being led with stream descriptions
        #
        #for profile in self.followerProfiles.values():
        #    try:
        #        Client.Handle( profile.venueClientURL ).get_proxy().EnterVenue( URL )
        #    except:
        #        log.exception("AccessGrid.VenueClient::Exception while leading follower")
            
        # Finally, set the flag that we are in a venue
        self.isInVenue = 1

    EnterVenue.soap_export_as = "EnterVenue"

    def LeadFollowers(self):
        #
        # Update venue clients being led with stream descriptions
        #
        for profile in self.followerProfiles.values():
            try:
                Client.Handle( profile.venueClientURL ).get_proxy().EnterVenue(self.venueUri)
            except:
                log.exception("AccessGrid.VenueClient::Exception while leading follower")

    def ExitVenue( self ):
        """
        ExitVenue removes this client from the specified venue.
        """
        log.info("VenueClient.ExitVenue")

        # Exit the venue
        try:         
            self.venueProxy.Exit( self.privateId )
        except Exception:
            log.exception("AccessGrid.VenueClient::ExitVenue exception")

        # Stop sending heartbeats
        if self.heartbeatTask != None:
            log.info(" Stopping heartbeats")
            self.heartbeatTask.stop()

        # Stop the event client
        log.info(" Stopping event client")
        self.eventClient.Send(DisconnectEvent(self.venueState.uniqueId,
                                              self.privateId))
        try:
            self.eventClient.Stop()
        except:
            # An exception is always thrown for some reason when I exit
            # the event client
            pass
            
        # Stop the node services
        try:
            if self.nodeServiceUri != None and Client.Handle(self.nodeServiceUri).IsValid():
                log.info(" Stopping node services")
                Client.Handle(self.nodeServiceUri).GetProxy().StopServices()
                Client.Handle(self.nodeServiceUri).GetProxy().SetStreams([])
        except:
            log.exception("Exception stopping node services")

        self.__InitVenueData__()
        self.isInVenue = 0

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
        Follow tells this venue client to follow the specified client
        """

        log.debug('AccessGrid.VenueClient::Trying to unlead: %s' %leaderProfile.name)
        Client.Handle( leaderProfile.venueClientURL ).get_proxy().UnLead( self.profile )

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

    LeadResponse.soap_export_as = "LeadResponse"

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

