#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client side object of the Virtual Venues Services.
#
# Author:      Ivan R. Judson, Thomas D. Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueClient.py,v 1.29 2003-03-20 22:28:45 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
import urlparse
import string

import logging, logging.handlers

from AccessGrid.hosting.pyGlobus import Server
from AccessGrid.hosting.pyGlobus.ServiceBase import ServiceBase
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.EventClient import EventClient
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Types import *
from AccessGrid.Events import Event, HeartbeatEvent, ConnectEvent
from AccessGrid.scheduler import Scheduler

class EnterVenueException(Exception):
    pass
        
class VenueClient( ServiceBase):
    """
    This is the client side object that maintains a stateful
    relationship with a Virtual Venue. This object provides the
    programmatic interface to the Access Grid for a Venues User
    Interface.  The VenueClient can only be in one venue at a
    time.
    """
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
        self.CreateFollowLeadServer()
                          
    def __InitVenueData__( self ):
        self.eventClient = None
        self.venueState = None
        self.venueUri = None
        self.venueProxy = None
        self.privateId = None
        self.streamDescList = []

    def Heartbeat(self):
        if self.eventClient != None:
            #            print "Sending heartbeat!"
            self.eventClient.Send(HeartbeatEvent(self.venueId, self.privateId))
            
    def SetProfile(self, profile):
        self.profile = profile
        if(self.profile != None):
            self.profile.venueClientURL = self.service.get_handle()
        
    def DoNothing(self, data):
        pass
    
    def CreateFollowLeadServer(self):
        server = Server.Server(10000)
        self.service = server.CreateServiceObject("VenueClient")
        self._bind_to_service( self.service )
        server.run_in_thread()

        if(self.profile != None):
            self.profile.venueClientURL = self.service.get_handle()
      
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
        print "Getting Add Data Event in VenueClient.AddDataEvent"
        self.venueState.AddData(data)

    def UpdateDataEvent(self, data):
        self.venueState.UpdateData(data)

    def RemoveDataEvent(self, data):
        self.venueState.RemoveData(data)

    def AddServiceEvent(self, data):
        self.venueState.AddService(data)

    def RemoveServiceEvent(self, data):
        self.venueState.RemoveService(data)

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
        
        
        haveValidNodeService = 0
        if self.nodeServiceUri != None:
            haveValidNodeService = Client.Handle( self.nodeServiceUri ).IsValid()

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
            
            self.venueState = VenueState( venueState.uniqueId,
                                          venueState.description,
                                          venueState.connections, 
                                          venueState.users, venueState.nodes, 
                                          venueState.data,
                                          venueState.services, 
                                          venueState.eventLocation,
                                          venueState.textLocation,
                                          applications)
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
               Event.ADD_CONNECTION: self.AddConnectionEvent,
               Event.REMOVE_CONNECTION: self.RemoveConnectionEvent,
               Event.SET_CONNECTIONS: self.SetConnectionsEvent,
            }

            self.eventClient = EventClient(self.venueState.eventLocation)

            for e in coherenceCallbacks.keys():
                self.eventClient.RegisterCallback(e, coherenceCallbacks[e])

            self.eventClient.start()
            self.eventClient.Send(ConnectEvent(self.venueState.uniqueId))
            
            self.heartbeatTask = self.houseKeeper.AddTask(self.Heartbeat, 5)
            self.heartbeatTask.start()
 
            # 
            # Update the node service with stream descriptions
            #
            if haveValidNodeService:
                Client.Handle( self.nodeServiceUri ).get_proxy().ConfigureStreams( self.streamDescList )

            #
            # Update venue clients being led with stream descriptions
            #
            for profile in self.followerProfiles.values():
                Client.Handle( profile.venueClientUri ).get_proxy().wsEnterVenue( URL )

            # Finally, set the venue uri now that we have successfully
            # entered the venue
            self.venueUri = URL

        except:
            print "Exception in EnterVenue : ", sys.exc_type, sys.exc_value
            raise EnterVenueException("Enter Failed!")

    EnterVenue.soap_export_as = "EnterVenue"
       
        
    def ExitVenue( self ):
        """
        ExitVenue removes this client from the specified venue.
        """
        self.heartbeatTask.stop()
        self.eventClient.Stop()
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
        
    def Follow( self, venueClientUri ):
        """
        Follow tells this venue client to follow the node
        specified.
        """
        print '------------follow url: ', venueClientUri 
        Client.Handle( venueClientUri ).get_proxy().Lead( self.profile )

    def Unfollow( self, venueClientUri ):
        """
        Unfollow tells this venue client to stop following
        the node specified.
        """
        Client.Handle( venueClientUri ).get_proxy().Unlead( self.profile )

    def Lead( self, clientProfile):
        """
        Lead tells this venue client to drag the specified
        node with it.
        """
        print '--------------this person is following me: ', clientProfile.name
        self.followerProfiles[clientProfile.publicId] = clientProfile
        Lead.soap_export_as = "Lead"

    def Unlead( self, clientProfile):
        """
        Unlead tells this venue client to stop dragging the specified
        node with it.
        """
        for profile in self.followerProfiles.values():
            if profile.publicId == clientProfile.publicId:
                del self.followerProfiles[clientProfile.publicId]
        Unlead.soap_export_as = "Unlead"

    def SetNodeServiceUri( self, nodeServiceUri ):
        """
        Bind the given node service to this venue client
        """
        self.nodeServiceUri = nodeServiceUri

