#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client side object of the Virtual Venues Services.
#
# Author:      Ivan R. Judson, Thomas D. Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueClient.py,v 1.42 2003-03-26 15:13:25 lefvert Exp $
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
        self.workspaceDock = None
        self.homeVenue = None
        self.followerProfiles = dict()
        self.__InitVenueData__()
        self.houseKeeper = Scheduler()
        self.CreateVenueClientWebService()

        self.leaderProfile = None
        self.pendingFollowers = dict()
        self.pendingLeader = None
                          
    def __InitVenueData__( self ):
        self.eventClient = None
        self.venueState = None
        self.venueUri = None
        self.venueProxy = None
        self.privateId = None
        self.streamDescList = []

    def Heartbeat(self):
        if self.eventClient != None:
            self.eventClient.Send(HeartbeatEvent(self.venueId, self.privateId))
            
    def SetProfile(self, profile):
        self.profile = profile
        if(self.profile != None):
           self.profile.venueClientURL = self.service.get_handle()
                
    def CreateVenueClientWebService(self):

        from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
        port = MulticastAddressAllocator().AllocatePort()

        server = Server.Server(port)
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
        self.venueState.AddUser(data)

    def RemoveUserEvent(self, data):
        self.venueState.RemoveUser(data)

    def ModifyUserEvent(self, data):
        self.venueState.ModifyUser(data)

    def AddDataEvent(self, data):
        self.venueState.AddData(data)

    def UpdateDataEvent(self, data):
        self.venueState.UpdateData(data)

    def RemoveDataEvent(self, data):
        self.venueState.RemoveData(data)

    def AddServiceEvent(self, data):
        self.venueState.AddService(data)

    def RemoveServiceEvent(self, data):
        self.venueState.RemoveService(data)

    def AddApplicationEvent(self, data):
        self.venueState.AddApplication(data)

    def RemoveApplicationEvent(self, data):
        self.venueState.RemoveApplication(data)

    def AddConnectionEvent(self, data):
        self.venueState.AddConnection(data)

    def RemoveConnectionEvent(self, data):
        self.venueState.RemoveConnection(data)

    def SetConnectionsEvent(self, data):
        self.venueState.SetConnections(data)
        
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
        try:
            
            if self.venueUri != None:
                self.ExitVenue()

            #
            # Retrieve list of node capabilities
            #
            if haveValidNodeService:
                self.profile.capabilities = Client.Handle( self.nodeServiceUri ).get_proxy().GetCapabilities()
            
            #
            # Enter the venue
            #
            (venueState, self.privateId, self.streamDescList ) = Client.Handle( URL ).get_proxy().Enter( self.profile )

            if hasattr(venueState, "applications"):
                applications = venueState.applications
            else:
                applications = {}
            try:
                self.venueState = VenueState( venueState.uniqueId,
                                              venueState.name,
                                              venueState.description,
                                              venueState.uri,
                                              venueState.connections, 
                                              venueState.users,
                                              venueState.nodes, 
                                              venueState.data,
                                              venueState.eventLocation,
                                              venueState.textLocation,
                                              applications)
            except:
                log.exception("AccessGrid.VenueClient::Failed to convert venuestate to object")
                
            self.venueUri = URL
            self.venueId = self.venueState.GetUniqueId()
            self.venueProxy = Client.Handle( URL ).get_proxy()

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
            }

            self.eventClient = EventClient(self.venueState.eventLocation,
                                           self.venueState.uniqueId)
            for e in coherenceCallbacks.keys():
                self.eventClient.RegisterCallback(e, coherenceCallbacks[e])

            self.eventClient.start()
            self.eventClient.Send(ConnectEvent(self.venueState.uniqueId))
            
            self.heartbeatTask = self.houseKeeper.AddTask(self.Heartbeat, 5)
            self.heartbeatTask.start()
 
        except:
            log.error("AccessGrid.VenueClient::Exception in EnterVenue")
            raise EnterVenueException("Enter Failed!")

        # 
        # Update the node service with stream descriptions
        #
        #try:
        if haveValidNodeService:
            Client.Handle( self.nodeServiceUri ).get_proxy().ConfigureStreams( self.streamDescList )
        #except:
        #    log.error("AccessGrid.VenueClient::Exception configuring node service streams")

        #
        # Update venue clients being led with stream descriptions
        #
        for profile in self.followerProfiles.values():
            #Try:
            Client.Handle( profile.venueClientURL ).get_proxy().EnterVenue( URL )
            #except:
            #print "Exception: ", sys.exc_type, sys.exc_value
            #print "while leading follower: ", profile.name, profile.venueClientURL
            
        # Finally, set the venue uri now that we have successfully
        # entered the venue
        self.venueUri = URL

    EnterVenue.soap_export_as = "EnterVenue"

    def ExitVenue( self ):
        """
        ExitVenue removes this client from the specified venue.
        """
        self.heartbeatTask.stop()
        self.eventClient.Send(DisconnectEvent(self.venueState.uniqueId))
        self.eventClient.Stop()

        #self.followLeadClient.Stop()
        self.venueProxy.Exit( self.privateId )
        self.__InitVenueData__()

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
        
    def Follow( self, leaderProfile ):
        """
        Follow tells this venue client to follow the specified client
        """
        # store public id of leader to whom request is being sent
        self.pendingLeader = leaderProfile

        # request permission to follow the leader
        # (response will come in via the LeadResponse method)
        log.debug('Requesting permission to follow this leader: %s' %leaderProfile.name)
        Client.Handle( leaderProfile.venueClientURL ).get_proxy().Lead( self.profile )

    def Lead( self, clientProfile):
        """
        Lead tells this venue client to drag the specified client with it.
        """

        log.debug("Received request to lead %s %s" %clientProfile.name, clientProfile.venueClientURL)

        # Add profile to list of followers awaiting authorization
        self.pendingFollowers[clientProfile.publicId] = clientProfile

        # Authorize the lead request (asynchronously)
        threading.Thread(target = self.AuthorizeLead, args = (clientProfile,) ).start()

    Lead.soap_export_as = "Lead"

    def AuthorizeLead(self, clientProfile):
        """
        Authorize requests to lead this client.  
        
        Subclasses should override this method to perform their specific 
        authorization, calling SendLeadResponse thereafter.
        """
        
        # For now, the base VenueClient authorizes every Lead request
        self.SendLeadResponse(clientProfile,True)

    def SendLeadResponse(self, clientProfile, response):
        """
        This method responds to requests to lead other venue clients.
        """
        
        # remove profile from list of pending followers
        del self.pendingFollowers[clientProfile.publicId]

        if response:
            # add profile to list of followers
            log.debug("Authorizing lead request for %s" %clientProfile.name)
            self.followerProfiles[clientProfile.publicId] = clientProfile

            # send the response
            Client.Handle( clientProfile.venueClientURL ).get_proxy().LeadResponse(self.profile, 1)
        else:
            log.debug("Rejecting lead request for %s" %clientProfile.name)

    def LeadResponse(self, leaderProfile, isAuthorized):
        """
        LeadResponse is called by other venue clients to respond to 
        lead requests sent by this client.  A UI client would override
        this method to give the user visual feedback to the Lead request.
        """
        if leaderProfile.publicId == self.pendingLeader.publicId and isAuthorized:
            log.debug("Leader has agreed to lead you: %s, %s" %(self.pendingLeader.name, self.pendingLeader.distinguishedName))
            self.leaderProfile = self.pendingLeader
        else:
            log.debug("Leader has rejected request to lead you: %s", leaderProfile.name)
        self.pendingLeader = None

    LeadResponse.soap_export_as = "LeadResponse"

    def UnLead(self, clientProfile):
        """
        UnLead tells this venue client to stop dragging the specified client.
        """

        log.debug( "AccessGrid.VenueClient::Received request to lead %s %s" %(clientProfile.name, clientProfile.venueClientURL))
        if(self.followerProfiles.has_key(clientProfile.publicId)):
            del self.followerProfiles[clientProfile.publicId]

        if(self.pendingFollowers.has_key(clientProfile.publicId)):
            del self.pendingFollowers[clientProfile.publicId]

        
    def SetNodeServiceUri( self, nodeServiceUri ):
        """
        Bind the given node service to this venue client
        """
        self.nodeServiceUri = nodeServiceUri

