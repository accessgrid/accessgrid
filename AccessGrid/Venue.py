#-----------------------------------------------------------------------------
# Name:        Venue.py
# Purpose:     The Virtual Venue is the object that provides the collaboration
#               scopes in the Access Grid.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: Venue.py,v 1.7 2003-01-15 22:46:30 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys
from AccessGrid.hosting.pyGlobus import ServiceBase
from AccessGrid.Types import Capability, Event
from AccessGrid.Descriptions import StreamDescription
from AccessGrid import NetworkLocation

class Venue(ServiceBase.ServiceBase):
    """
    A Virtual Venue is a virtual space for collaboration on the Access Grid.
    """
    def __init__(self, server, uniqueId, description, administrator,
                 coherenceService, multicastAddressAllocator, dataStore):
        self.connections = dict()
        self.users = dict()
        self.nodes = dict()
        self.data = dict()
        self.services = dict()

        self.networkServices = []
        self.streams = []
        self.administrators = []

        self.uniqueId = uniqueId
        self.description = description
        self.venueServer = server
        self.administrators.append(administrator)
        self.coherenceService = coherenceService
        self.coherenceService.start()
        self.multicastAddressAllocator = multicastAddressAllocator
        self.dataStore = dataStore

        self.producerCapabilities = []
        self.consumerCapabilities = []

        self.nextPrivateId = 1

        self.defaultTtl = 127


    # Management methods
    def AddNetworkService(self, connectionInfo, networkServiceDescription):
        """ """

        try:
            self.networkServices[ networkServiceDescription.uri ] = networkServiceDescription
        except:
            print "Network Service already exists ", networkServiceDescription.uri

    AddNetworkService.pass_connection_info = 1
    AddNetworkService.soap_export_as = "AddNetworkService"
    
    def GetNetworkServices(self, connectionInfo):
        """ """
        return self.networkServices
    GetNetworkServices.pass_connection_info = 1
    GetNetworkServices.soap_export_as = "GetNetworkServices"
    
    def RemoveNetworkService(self, connectionInfo, networkServiceDescription):
        """ """
        try:
            del self.networkServices[ networkServiceDescription.uri ]
        except:
            print "Exception in RemoveNetworkService", sys.exc_type, sys.exc_value
            print "Network Service does not exist ", networkServiceDescription.uri
    RemoveNetworkService.pass_connection_info = 1
    RemoveNetworkService.soap_export_as = "RemoveNetworkService"
        
    def AddConnection(self, connectionInfo, connectionDescription):
        """ """
        try:
            self.connections[connectionDescription.uri] = connectionDescription
            self.coherenceService.distribute( Event( Event.ADD_CONNECTION, connectionDescription ) )
        except:
            print "Connection already exists ", connectionDescription.uri
    AddConnection.pass_connection_info = 1
    AddConnection.soap_export_as = "AddConnection"

    def RemoveConnection(self, connectionInfo, connectionDescription):
        """ """
        try:
            del self.connections[ connectionDescription.uri ]
            self.coherenceService.distribute( Event( Event.REMOVE_CONNECTION, connectionDescription ) )
        except:
            print "Exception in RemoveConnection", sys.exc_type, sys.exc_value
            print "Connection does not exist ", connectionDescription.uri
    RemoveConnection.pass_connection_info = 1
    RemoveConnection.soap_export_as = "RemoveConnection"

    def GetConnections(self, connectionInfo ):
        """ """
        return self.connections.values()
    GetConnections.pass_connection_info = 1
    GetConnections.soap_export_as = "GetConnections"

    def SetConnections(self, connectionInfo, connectionList ):
        """ """
        try:
            self.connections = dict()
            for connection in connectionList:
                self.connections[connection.uri] = connection
#FIXME - consider whether to push new venue state to all clients
        except:
            print "Exception in SetConnections", sys.exc_type, sys.exc_value
            print "Connection does not exist ", connectionDescription.uri
    SetConnections.pass_connection_info = 1
    SetConnections.soap_export_as = "SetConnections"


        

    def SetDescription(self, connectionInfo, description):
        """ """
        self.description = description
    SetDescription.pass_connection_info = 1
    SetDescription.soap_export_as = "SetDescription"

    def GetDescription(self, connectionInfo):
        """ """
        return self.description
    GetDescription.pass_connection_info = 1
    GetDescription.soap_export_as = "GetDescription"

    def GetStreams(self, connectionInfo):
        """ """
        return self.streams
    GetStreams.pass_connection_info = 1
    GetStreams.soap_export_as = "GetStreams"

    # Client Methods
    def Enter(self, connectionInfo, clientProfile):
        """ """
        privateId = None
        streamDescriptions = None
        state = self.GetState( connectionInfo )


        try:

            print "Called Venue Enter for: "

            print dir(clientProfile)


            userInVenue = False
            for key in self.users.keys():
                user = self.users[key]
                if user.publicId == clientProfile.publicId:
                    print "* * User already in venue"
#FIXME - temporarily ignore that user is already in venue, for testing
                    #userInVenue = True
                    privateId = key
                    break
            
            if userInVenue == False:
                privateId = self.GetNextPrivateId()
                self.users[privateId] = clientProfile
                state['users'] = self.users.values()

                # negotiate to get stream descriptions to return
                streamDescriptions = self.NegotiateCapabilities( clientProfile )
                self.coherenceService.distribute( Event( Event.ENTER, clientProfile ) )

        except:
           print "Exception in Enter ", sys.exc_type, sys.exc_value
        
        return ( state, privateId, streamDescriptions )

    Enter.pass_connection_info = 1
    Enter.soap_export_as = "Enter"
    
    def Exit(self, connectionInfo, privateId ):
        """ """
        try:
            print "Called Venue Exit on " + str(connectionInfo)

            if self.IsValidPrivateId( privateId ):
                print "Deleting user ", privateId, self.users[privateId].name
                clientProfile = self.users[privateId]
                del self.users[privateId]

                self.coherenceService.distribute( Event( Event.EXIT, clientProfile ) )
            else:
                print "* * Invalid private id !! "
        except:
            print "Exception in Exit ", sys.exc_type, sys.exc_value
        
    Exit.pass_connection_info = 1
    Exit.soap_export_as = "Exit"

    def GetState(self, connectionInfo):
        """ """

        try:
           print "Called GetState on ", self.uniqueId
           venueState = {
               'description' : self.description,
               'connections' : self.connections.values(),
               'users' : self.users.values(),
               'nodes' : self.nodes.values(),
               'data' : self.data.values(),
               'services' : self.services.values(),
               'coherenceLocation' : self.coherenceService.GetLocation()
               }
        except:
           print "Exception in GetState ", sys.exc_type, sys.exc_value

        return venueState
    
    GetState.pass_connection_info = 1
    GetState.soap_export_as = "GetState"

    def UpdateClientProfile(self, connectionInfo, clientProfile):
        """ """
        
        evt = {
            'event' : 'UpdateClientProfile',
            'data' : clientProfile
            }
        
        self.coherenceService.distribute(evt)
        
    UpdateClientProfile.pass_connection_info = 1
    UpdateClientProfile.soap_export_as = "UpdateClientProfile"

    def AddData(self, connectionInfo, dataDescription ):
        """ """
        try:
            self.data[dataDescription.name] = dataDescription
            self.coherenceService.distribute( Event( Event.ADD_DATA, dataDescription ) )
        except:
            print "Exception in AddData ", sys.exc_type, sys.exc_value
            print "Data already exists ", dataDescription.name
    AddData.pass_connection_info = 1
    AddData.soap_export_as = "AddData"

    def GetData(self, connectionInfo, dataDescription):
        """ """

        # Do something with the data store

    GetData.pass_connection_info = 1
    GetData.soap_export_as = "GetData"

    def RemoveData(self, connectionInfo, dataDescription):
        """ """
        try:
            del self.data[ dataDescription.name ]
            self.coherenceService.distribute( Event( Event.REMOVE_DATA, dataDescription ) )
        except:
            print "Exception in RemoveData", sys.exc_type, sys.exc_value
            print "Data does not exist", dataDescription.name
    RemoveData.pass_connection_info = 1
    RemoveData.soap_export_as = "RemoveData"

    def AddService(self, connectionInfo, serviceDescription):
        """
        This method should add a service description to the Venue.
        """
        print "Adding service ", serviceDescription.name, serviceDescription.uri
        try:
            self.services[serviceDescription.uri] = serviceDescription
            self.coherenceService.distribute( Event( Event.ADD_SERVICE, serviceDescription ) )
        except:
            print "Exception in AddService ", sys.exc_type, sys.exc_value
            print "Service already exists ", serviceDescription.name
    AddService.pass_connection_info = 1
    AddService.soap_export_as = "AddService"

    def RemoveService(self, connectionInfo, serviceDescription):
        """ """
        
        try:
            del self.services[serviceDescription.uri]
            self.coherenceService.distribute( Event( Event.REMOVE_SERVICE, serviceDescription ) )
        except:
            print "Exception in RemoveService", sys.exc_type, sys.exc_value
            print "Service does not exist ", serviceDescription.name

    RemoveService.pass_connection_info = 1
    RemoveService.soap_export_as = "RemoveService"

    def Ping( self ):
      print "Ping!"
      return 1
    Ping.pass_connection_info = 0
    Ping.soap_export_as = "Ping"





    # Internal Methods
    def Shutdown(self):
        """ """
        self.coherenceService.stop()

    def NegotiateCapabilities(self, clientProfile):
        """ """
        streamDescriptions = []

        #
        # Compare user's producer capabilities with existing stream description capabilities.
        # New producer capabilities are added to the stream descriptions, and an event
        # is emitted to alert current participants about the new stream
        # 
        streamCapTypes = map( lambda streamDesc: streamDesc.capability.type, self.streams )
        for capability in clientProfile.capabilities:
            if capability.role == Capability.PRODUCER:
                if capability.type not in streamCapTypes:
                    # add new stream description

                    print "* * Adding new producer of type ", capability.type
                    encryptionKey = "venue didn't assign an encryption key"
                    streamDesc = StreamDescription( "noName", "noDesc", self.AllocateMulticastLocation(), 
                                                    capability, encryptionKey )
                    self.streams.append( streamDesc )
                    streamDescriptions.append( streamDesc )

        
        #
        # Compare user's consumer capabilities with existing stream description capabilities.
        # The user will receive a list of compatible stream descriptions
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
        return NetworkLocation.MulticastNetworkLocation( self.multicastAddressAllocator.AllocateAddress(),
                                                         self.multicastAddressAllocator.AllocatePort(), 
                                                         self.defaultTtl )
       
    def GetNextPrivateId( self ):
        privateId = self.nextPrivateId
        self.nextPrivateId = self.nextPrivateId + 1
        return privateId

    def IsValidPrivateId( self, privateId ):
        if privateId in self.users.keys():
            return True 
        return False
    
