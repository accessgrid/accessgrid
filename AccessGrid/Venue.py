#-----------------------------------------------------------------------------
# Name:        Venue.py
# Purpose:     The Virtual Venue is the object that provides the collaboration
#               scopes in the Access Grid.
#
# Author:      Ivan R. Judson, Thomas D. Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: Venue.py,v 1.19 2003-02-03 14:12:37 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys
import time
import string
import types
import socket

from AccessGrid.hosting.pyGlobus import ServiceBase
from AccessGrid.Types import Capability
from AccessGrid.Descriptions import StreamDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.GUID import GUID
from AccessGrid.TextService import TextService
from AccessGrid.EventService import EventService
from AccessGrid.Events import Event, HeartbeatEvent, TextEvent
from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.scheduler import Scheduler

class Venue(ServiceBase.ServiceBase):
    """
    A Virtual Venue is a virtual space for collaboration on the Access Grid.
    """
    def __init__(self, uniqueId, description, administrator,
                 multicastAllocator, dataStore):
        self.connections = dict()
        self.users = dict()
        self.nodes = dict()
        self.data = dict()
        self.services = dict()
        self.clients = dict()
        
        self.networkServices = []
        self.streams = []
        self.administrators = []

        self.uniqueId = uniqueId
        self.description = description
        self.administrators.append(administrator)
        self.multicastAllocator = multicastAllocator
        self.dataStore = dataStore

        self.textHost = socket.getfqdn()
        self.textPort = self.multicastAllocator.AllocatePort()
        
        self.eventHost = socket.getfqdn()
        self.eventPort = self.multicastAllocator.AllocatePort()
        
        self.producerCapabilities = []
        self.consumerCapabilities = []

        self.cleanupTime = 30
        self.nextPrivateId = 1

    def __getstate__(self):
        odict = self.__dict__.copy()
        for k in odict.keys():
            if type(odict[k]) == types.InstanceType:
                if k != "uniqueId" and k != "description":
                    del odict[k]
        return odict

    def __setstate__(self, dict):
        self.__dict__ = dict
        self.Start()

    def Start(self):
        self.eventService = EventService((self.eventHost, self.eventPort))
        self.eventService.RegisterCallback(HeartbeatEvent.HEARTBEAT, 
                                    self.ClientHeartbeat)
        self.eventService.start()
        
#        self.textService = TextService((self.textHost, self.textPort))
#        self.textService.start()
        
        self.houseKeeper = Scheduler()
        self.houseKeeper.AddTask(self.CleanupClients, 45)
        self.houseKeeper.StartAllTasks()

   # Internal Methods
    def GetState(self, connectionInfo):
        """
        GetState enables a VenueClient to poll the Virtual Venue for the
        current state of the Virtual Venue.
        """

        try:
           print "Called GetState on ", self.uniqueId

           venueState = {
               'description' : self.description,
               'connections' : self.connections.values(),
               'users' : self.users.values(),
               'nodes' : self.nodes.values(),
               'data' : self.data.values(),
               'services' : self.services.values(),
               'eventLocation' : self.eventService.GetLocation()
               }
        except:
           print "Exception in GetState ", sys.exc_type, sys.exc_value

#        print "state:", dir(venueState)
        return venueState
    
    GetState.pass_connection_info = 1
    GetState.soap_export_as = "GetState"

    def CleanupClients(self):
        now_sec = time.time()
        for privateId in self.clients.keys():
           if privateId in self.users.keys():
            then_sec = self.clients[privateId]
            if abs(now_sec - then_sec) > self.cleanupTime:
                print "  Removing user : ", self.users[privateId].name
                if privateId in self.users.keys():
                    clientProfile = self.users[privateId]
                elif privateId in self.nodes.keys():
                    clientProfile = self.nodes[privateId]
                self.eventService.Distribute( Event( Event.EXIT,
                                                         clientProfile ) )
                del self.clients[privateId]
        
    def ClientHeartbeat(self, event):
        privateId = event
        now = time.time()
        self.clients[privateId] = now
        print "Got Client Heartbeat for %s at %s." % (event, now)
    
    def Shutdown(self):
        """
        This method cleanly shuts down all active threads associated with the
        Virtual Venue. Currently there are a few threads in the Event
        Service.
        """
        self.eventService.stop()

    def NegotiateCapabilities(self, clientProfile):
        """
        This method takes a client profile and finds a set of streams that
        matches the client profile. Later this method could use network
        services to find The Best Match of all the network services,
        the existing streams, and all the client capabilities.
        """
        streamDescriptions = []

        #
        # Compare user's producer capabilities with existing stream
        # description capabilities. New producer capabilities are added
        # to the stream descriptions, and an event is emitted to alert
        # current participants about the new stream
        # 
        streamCapTypes = map( lambda streamDesc: streamDesc.capability.type,
                              self.streams )

        for capability in clientProfile.capabilities:
            if capability.role == Capability.PRODUCER:
                if capability.type not in streamCapTypes:
                    # add new stream description

                    print "* * Adding new producer of type ", capability.type
                    encryptionKey = "venue didn't assign an encryption key"
                    streamDesc = StreamDescription( "noName", "noDesc",
                                             self.AllocateMulticastLocation(), 
                                             capability, encryptionKey )
                    self.streams.append( streamDesc )
                    streamDescriptions.append( streamDesc )
        
        #
        # Compare user's consumer capabilities with existing stream
        # description capabilities. The user will receive a list of
        # compatible stream descriptions
        # 
        clientConsumerCapTypes = []
        for capability in clientProfile.capabilities:
            if capability.role == Capability.CONSUMER:
                clientConsumerCapTypes.append( capability.type )
        for stream in self.streams:
            if stream.capability.type in clientConsumerCapTypes:
                streamDescriptions.append( stream )

        return streamDescriptions

    def AllocateMulticastLocation(self):
        """
        This method creates a new Multicast Network Location.
        """
        defaultTtl = 127
        return MulticastNetworkLocation(
            self.multicastAllocator.AllocateAddress(),
            self.multicastAllocator.AllocatePort(), 
            defaultTtl )
       
    def GetNextPrivateId( self ):
        """This method creates the next Private Id."""
        return str(GUID())

    def IsValidPrivateId( self, privateId ):
        """This method verifies the private Id is valid."""
        if privateId in self.users.keys():
            return 1 
        return 0

    # Management methods
    def AddNetworkService(self, connectionInfo, networkServiceDescription):
        """
        AddNetworkService allows an administrator to add functionality to
        the Venue. Network services are described in the design documents.
        """
        try:
            self.networkServices[ networkServiceDescription.uri ] = networkServiceDescription
        except:
            print "Network Service already exists ", networkServiceDescription.uri

    AddNetworkService.pass_connection_info = 1
    AddNetworkService.soap_export_as = "AddNetworkService"
    
    def GetNetworkServices(self, connectionInfo):
        """
        GetNetworkServices retreives the list of network service descriptions
        from the venue.
        """
        return self.networkServices
    
    GetNetworkServices.pass_connection_info = 1
    GetNetworkServices.soap_export_as = "GetNetworkServices"
    
    def RemoveNetworkService(self, connectionInfo, networkServiceDescription):
        """
        RemoveNetworkService removes a network service from a venue, making
        it unavailable to users of the venue.
        """
        try:
            del self.networkServices[ networkServiceDescription.uri ]
        except:
            print "Exception in RemoveNetworkService", sys.exc_type, sys.exc_value
            print "Network Service does not exist ", networkServiceDescription.uri
    RemoveNetworkService.pass_connection_info = 1
    RemoveNetworkService.soap_export_as = "RemoveNetworkService"
        
    def AddConnection(self, connectionInfo, connectionDescription):
        """
        AddConnection allows an administrator to add a connection to a
        virtual venue to this virtual venue.
        """
        try:

            self.connections[connectionDescription.uri] = connectionDescription
            self.eventService.Distribute( Event( Event.ADD_CONNECTION, 
                                                connectionDescription ) )
        except:
            print "Connection already exists ", connectionDescription.uri

    AddConnection.pass_connection_info = 1
    AddConnection.soap_export_as = "AddConnection"

    def RemoveConnection(self, connectionInfo, connectionDescription):
        """
        RemoveConnection removes a connection to another virtual venue
        from this virtual venue. This is an administrative operation.
        """
        try:
            del self.connections[ connectionDescription.uri ]
            self.eventService.Distribute( Event( Event.REMOVE_CONNECTION, connectionDescription ) )
        except:
            print "Exception in RemoveConnection", sys.exc_type, sys.exc_value
            print "Connection does not exist ", connectionDescription.uri

    RemoveConnection.pass_connection_info = 1
    RemoveConnection.soap_export_as = "RemoveConnection"

    def GetConnections(self, connectionInfo ):
        """
        GetConnections returns a list of all the connections to other venues
        that are found within this venue.
        """
        return self.connections.values()

    GetConnections.pass_connection_info = 1
    GetConnections.soap_export_as = "GetConnections"

    def SetConnections(self, connectionInfo, connectionList ):
        """
        SetConnections is a convenient aggregate accessor for the list of
        connections for this venue. Alternatively the user could iterate over
        a list of connections adding them one by one, but this is more
        desirable.
        """
        try:

            self.connections = dict()
            for connection in connectionList:
                self.connections[connection.uri] = connection
#FIXME - how to push new connection list to clients?
        except:
            print "Exception in SetConnections", sys.exc_type, sys.exc_value
            print "Connection does not exist ", connectionDescription.uri

    SetConnections.pass_connection_info = 1
    SetConnections.soap_export_as = "SetConnections"

    def SetDescription(self, connectionInfo, description):
        """
        SetDescription allows an administrator to set the venues description
        to something new.
        """
        self.description = description

    SetDescription.pass_connection_info = 1
    SetDescription.soap_export_as = "SetDescription"

    def GetDescription(self, connectionInfo):
        """
        GetDescription returns the description for the virtual venue.
        """
        return self.description

    GetDescription.pass_connection_info = 1
    GetDescription.soap_export_as = "GetDescription"

    def GetStreams(self, connectionInfo):
        """
        GetStreams returns a list of stream descriptions to the caller.
        """
        return self.streams

    GetStreams.pass_connection_info = 1
    GetStreams.soap_export_as = "GetStreams"

    # Client Methods
    def Enter(self, connectionInfo, clientProfile):
        """
        The Enter method is used by a VenueClient to gain access to the
        services, users, and content found within a Virtual Venue.
        """
        privateId = None
        streamDescriptions = None
        state = self.GetState( connectionInfo )

        try:
#            print "Called Venue Enter for: "
#            print dir(clientProfile)

            userInVenue = 0
            for key in self.users.keys():
                user = self.users[key]
                if user.publicId == clientProfile.publicId:
                    print "* * User already in venue"
#FIXME - temporarily ignore that user is already in venue, for testing
                    userInVenue = 1
                    privateId = key
                    break
            
            if userInVenue == 0:
                privateId = self.GetNextPrivateId()
                print "Assigning private id: ", privateId
                self.users[privateId] = clientProfile
                state['users'] = self.users.values()

                # negotiate to get stream descriptions to return
                streamDescriptions = self.NegotiateCapabilities( clientProfile )
                self.eventService.Distribute( Event( Event.ENTER, clientProfile ) )

        except:
           print "Exception in Enter ", formatExceptionInfo()
        
        return ( state, privateId, streamDescriptions )

    Enter.pass_connection_info = 1
    Enter.soap_export_as = "Enter"
    
    def Exit(self, connectionInfo, privateId ):
        """
        The Exit method is used by a VenueClient to cleanly leave a Virtual
        Venue. Cleanly leaving a Virtual Venue allows the Venue to cleanup
        any state associated (or caused by) the VenueClients presence.
        """
        try:
            print "Called Venue Exit on " + str(connectionInfo)

            if self.IsValidPrivateId( privateId ):
                print "Deleting user ", privateId, self.users[privateId].name
                clientProfile = self.users[privateId]
                del self.users[privateId]

                self.eventService.Distribute( Event( Event.EXIT, clientProfile ) )
            else:
                print "* * Invalid private id !! ", privateId
        except:
            print "Exception in Exit ", sys.exc_type, sys.exc_value
        
    Exit.pass_connection_info = 1
    Exit.soap_export_as = "Exit"

    def UpdateClientProfile(self, connectionInfo, clientProfile):
        """
        UpdateClientProfile allows a VenueClient to update/modify the client
        profile that is stored by the Virtual Venue that they gave to the Venue
        when they called the Enter method.
        """
        for user in self.users.values():
            if user.publicId == clientProfile.publicId:
                self.users[user.privateId] = clientProfile
            self.eventService.Distribute( Event( Event.MODIFY_USER, clientProfile ) )
        
    UpdateClientProfile.pass_connection_info = 1
    UpdateClientProfile.soap_export_as = "UpdateClientProfile"

    def AddData(self, connectionInfo, dataDescription ):
        """
        The AddData method enables VenuesClients to put data in the Virtual
        Venue. Data put in the Virtual Venue through AddData is persistently
        stored.
        """
        try:
            # We also have to actually add real data, but not yet
            self.data[dataDescription.name] = dataDescription
            self.eventService.Distribute( Event( Event.ADD_DATA,
                                                     dataDescription ) )
        except:
            print "Exception in AddData ", sys.exc_type, sys.exc_value
            print "Data already exists ", dataDescription.name

    AddData.pass_connection_info = 1
    AddData.soap_export_as = "AddData"

    def GetData(self, connectionInfo, dataDescription):
        """
        GetData is the method called by a VenueClient to retrieve information
        about the data. This might also be the operation that the VenueClient
        uses to actually retrieve the real data.
        """

        # Do something with the data store

    GetData.pass_connection_info = 1
    GetData.soap_export_as = "GetData"

    def RemoveData(self, connectionInfo, dataDescription):
        """
        RemoveData removes persistent data from the Virtual Venue.
        """
        try:
            # We actually have to remove the real data, not just the
            # data description -- I guess that's later :-)
            del self.data[ dataDescription.name ]
            self.eventService.Distribute( Event( Event.REMOVE_DATA,
                                                     dataDescription ) )
        except:
            print "Exception in RemoveData", sys.exc_type, sys.exc_value
            print "Data does not exist", dataDescription.name

    RemoveData.pass_connection_info = 1
    RemoveData.soap_export_as = "RemoveData"

    def AddService(self, connectionInfo, serviceDescription):
        """
        This method adds a service description to the Venue.
        """
        print "Adding service ", serviceDescription.name, serviceDescription.uri
        try:
            self.services[serviceDescription.uri] = serviceDescription
            self.eventService.Distribute( Event( Event.ADD_SERVICE,
                                                     serviceDescription ) )
        except:
            print "Exception in AddService ", sys.exc_type, sys.exc_value
            print "Service already exists ", serviceDescription.name

    AddService.pass_connection_info = 1
    AddService.soap_export_as = "AddService"

    def RemoveService(self, connectionInfo, serviceDescription):
        """
        This method removes a service description from the list of services
        in the Virtual Venue.
        """
        
        try:
            del self.services[serviceDescription.uri]
            self.eventService.Distribute( Event( Event.REMOVE_SERVICE,
                                                     serviceDescription ) )
        except:
            print "Exception in RemoveService", sys.exc_type, sys.exc_value
            print "Service does not exist ", serviceDescription.name

    RemoveService.pass_connection_info = 1
    RemoveService.soap_export_as = "RemoveService"

    def Ping( self ):
        """ I don't know, ask Tom """
        print "Ping!"
        return 1

    Ping.pass_connection_info = 0
    Ping.soap_export_as = "Ping"

 