#-----------------------------------------------------------------------------
# Name:        Venue.py
# Purpose:     The Virtual Venue is the object that provides the collaboration
#               scopes in the Access Grid.
#
# Author:      Ivan R. Judson, Thomas D. Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: Venue.py,v 1.37 2003-02-18 21:17:48 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys
import time
import string
import types
import socket
import os.path

from AccessGrid.hosting.pyGlobus import ServiceBase
from AccessGrid.Types import Capability
from AccessGrid.Descriptions import StreamDescription, CreateStreamDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.GUID import GUID
from AccessGrid.TextService import TextService
from AccessGrid.EventService import EventService
from AccessGrid.Events import Event, HeartbeatEvent, TextEvent
from AccessGrid.Utilities import formatExceptionInfo, AllocateEncryptionKey
from AccessGrid.Utilities import GetHostname
from AccessGrid.scheduler import Scheduler
from AccessGrid import DataStore

class StreamDescriptionList:
    """
    Class to represent stream descriptions in a venue.  Entries in the
    list are a tuple of (stream description, producing users).  A stream
    is added to the list with a producer.  Producing users can be added
    to and removed from an existing stream.  When the number of users
    producing a stream becomes zero, the stream is removed from the list.

    Exception:  static streams remain without regard to the number of producers

    """

    def __init__( self ):
        self.streams = []

    def __getstate__(self):
        """
        Remove non-static streams from list for pickling
        """
        odict = self.__dict__.copy()
        staticStreams = []
        for stream,producerList in self.streams:
            if stream.static:
                staticStreams.append( stream )
        odict['streams'] = staticStreams
        return odict

    def AddStream( self, stream ):
        """
        Add a stream to the list
        """
        self.streams.append( ( stream, [] ) )

    def RemoveStream( self, stream ):
        """
        Remove a stream from the list
        """
        try:
            index = self.index( stream )
            del self.streams[index]
        except:
            pass 

    def AddStreamProducer( self, producingUser, inStream ):
        """
        Add a stream to the list, with the given producer
        """
        try:
            index = self.index( inStream )
            stream, producerList = self.streams[index]
            producerList.append( producingUser )
            self.streams[index] = ( stream, producerList )
            print "* * * Added stream producer ", producingUser
        except:   
            self.streams.append( (inStream, [ producingUser ] ) )
            print "* * * Added new stream with producer ", producingUser
            
    def RemoveStreamProducer( self, producingUser, inStream ):
        """
        Remove a stream producer from the given stream.  If the last
        producer is removed, the stream will be removed from the list
        if it is non-static.
        """
        try:
            self.__RemoveProducer( producingUser, inStream )
            streamDesc, producerList = self.streams[index]
            if len(producerList) == 0:  del self.streams[index]
        except:
            pass

    def RemoveProducer( self, producingUser ):
        """
        Remove producer from all streams
        """
        for stream, producerList in self.streams:
            self.__RemoveProducer( producingUser, stream )

        self.CleanupStreams()

    def __RemoveProducer( self, producingUser, inStream ):
        """
        Internal : Remove producer from stream with given index
        """
        index = self.index( inStream )
        stream, producerList = self.streams[index]
        if producingUser in producerList:
            producerList.remove( producingUser )
            self.streams[index] = ( stream, producerList )
    
    def CleanupStreams( self ):
        """
        Remove streams with empty producer list
        """
        streams = []
        for stream, producerList in self.streams:
            if len(producerList) > 0 or stream.static == 1:
                streams.append( ( stream, producerList ) )
        self.streams = streams

    def GetStreams( self ):
        """
        Get the list of streams, without producing user info
        """
        return map( lambda streamTuple: streamTuple[0], self.streams )

    def index( self, inStream ):
        """
        Retrieve the list index of the given stream description
        Note:  streams are keyed on address/port
        """
        try:
            index=0
            for stream, producerList in self.streams:
                print "-- - -- -  Address ", inStream.location.host, stream.location.host
                print "- - - -- - Port ", inStream.location.port, stream.location.port
                if inStream.location.host == stream.location.host and \
                   inStream.location.port == stream.location.port:
                    return index
                index = index + 1
        except:
            print "Exception in StreamDescriptionList.index ", sys.exc_type, sys.exc_value

        raise ValueError


class VenueException(Exception):
    """
    A generic exception type to be raised by the Venue code.
    """

    pass


class Venue(ServiceBase.ServiceBase):
    """
    A Virtual Venue is a virtual space for collaboration on the Access Grid.
    """
    def __init__(self, uniqueId, description, administrator,
                 multicastAllocator, dataStorePath):
        """
        Venue constructor.

        dataStorePath is the directory which the Venue's data storage object
        should use for storing its files.

        """

        self.connections = dict()
        self.services = dict()
        self.networkServices = []
        self.administrators = []

        self.uniqueId = uniqueId
        # This contains a name, description, uri, icon, extended description
        # eventlocation, and textlocation
        self.description = description
        self.administrators.append(administrator)

        self.data = dict()
        self.streamList = StreamDescriptionList()

        self.users = dict()
        self.clients = dict()
        self.nodes = dict()

        self.multicastAllocator = multicastAllocator
        self.dataStorePath = dataStorePath
        # This is the actual data store object
        self.dataStore = None 

        self.textHost = GetHostname()
        self.eventHost = GetHostname()
        
        self.producerCapabilities = []
        self.consumerCapabilities = []

        self.cleanupTime = 30
        self.nextPrivateId = 1

        self.encryptionKey = AllocateEncryptionKey()

    def __repr__(self):
        return "Venue: name=%s id=%s" % (self.description.name, id(self))

    def __getstate__(self):
        """
        Retrieve the state of object attributes for pickling.

        We don't pickle any object instances, except for the
        uniqueId and description.
        
        """
        odict = self.__dict__.copy()
        # We don't save things in this list
        keys = ("users", "clients", "nodes", "multicastAllocator",
                "producerCapabilities", "consumerCapabilities", "dataStore",
                "textHost", "testPort", "textService",
                "eventHost", "eventPort", "eventService",
                "_service_object", "houseKeeper")
        for k in odict.keys():
            if k in keys:
                del odict[k]

        return odict

    def __setstate__(self, pickledDict):
        """
        Resurrect the state of this object after unpickling.

        Restore  the attribute dictionary and start up the
        services.

        """
        self.__dict__ = pickledDict

        self.__dict__["users"] = dict()
        self.__dict__["clients"] = dict()
        self.__dict__["nodes"] = dict()
        self.__dict__["dataStore"] = None
        self.__dict__["multicastAddressAllocator"] = None
        self.__dict__["cleanupTime"] = 30
        self.__dict__["nextPrivateId"] = 1
        self.__dict__["encryptionKey"] = AllocateEncryptionKey()

    def Start(self):
        """ """
        # We assume the multicast allocator has been set by now
        # this is an icky assumption and can be fixed when I clean up
        # other icky things (description, state, venue) issues -- IRJ
        self.textHost = GetHostname()
        self.textPort = self.multicastAllocator.AllocatePort()
        self.eventHost = GetHostname()
        self.eventPort = self.multicastAllocator.AllocatePort()
        
        self.eventService = EventService((self.eventHost, self.eventPort))
        self.eventService.RegisterCallback(HeartbeatEvent.HEARTBEAT, 
                                    self.ClientHeartbeat)
        self.eventService.start()
        
        self.textService = TextService((self.textHost, self.textPort))
        self.textService.start()
        
        self.houseKeeper = Scheduler()
        self.houseKeeper.AddTask(self.CleanupClients, 45)
        self.houseKeeper.StartAllTasks()

        self.startDataStore()

    def startDataStore(self):
        """
        Start the local datastore server.

        We create a DataStore and a HTTPTransportServer for the actual
        service.  The DataStore is given the Venue's dataStorePath as
        its working directory.  We then loop through the data
        descriptions in the venue, both checking to see that the file
        still exists for each piece of data, and updating the uri
        field in the description with the new download URL.

        Actually, we get to do both steps at once, as
        GetDownloadDescriptor will return None if the file doesn't
        exist in the local data store.
        """

        if self.dataStorePath is None or not os.path.isdir(self.dataStorePath):
            print "Not starting datastore for venue: %s does not exist" % (
                self.dataStorePath)
            return
        self.dataStore = DataStore.DataStore(self, self.dataStorePath)
        transferServer = DataStore.HTTPTransferServer(self.dataStore,
                                                      ('', 0))
        self.dataStore.SetTransferEngine(transferServer)

        print "Have upload url: ", self.dataStore.GetUploadDescriptor()

        for file, desc in self.data.items():
            print "Checking file %s for validity" % (file)
            url = self.dataStore.GetDownloadDescriptor(file)
            if url is None:
                print "File %s has vanished" % (file)
                del self.data[file]
            else:
                desc.SetURI(url)
                self.UpdateData(desc)

        transferServer.run()

    def SetMulticastAddressAllocator(self, multicastAllocator):
        """
        Set the Multicast Address Allocator for the Venue. This is usually
        set to the allocator the venue server uses.
        """
        self.multicastAllocator = multicastAllocator

    def SetDataStore(self, dataStore):
        """
        Set the Data Store for the Venue. This is usually set to the data
        store the venue server uses.
        """
        self.dataStore = dataStore
    
   # Internal Methods
    def GetState(self):
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
               'eventLocation' : self.eventService.GetLocation(),
               'textLocation' : self.textService.GetLocation()
               }
        except:
           print "Exception in GetState ", sys.exc_type, sys.exc_value

        return venueState
    
    GetState.soap_export_as = "GetState"

    def CleanupClients(self):
        now_sec = time.time()
        for privateId in self.clients.keys():
            then_sec = self.clients[privateId]
            if abs(now_sec - then_sec) > self.cleanupTime:
                print "  Removing user : ", self.users[privateId].name
                self.RemoveUser( privateId )
                del self.clients[privateId]
        
    def ClientHeartbeat(self, event):
        privateId = event
        now = time.time()
        self.clients[privateId] = now
#        print "Got Client Heartbeat for %s at %s." % (event, now)
    
    def Shutdown(self):
        """
        This method cleanly shuts down all active threads associated with the
        Virtual Venue. Currently there are a few threads in the Event
        Service.
        """
        if self.eventService != None:
            self.eventService.Stop()

        if self.textService != None:
            self.textService.Stop()

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

        for clientCapability in clientProfile.capabilities:
            if clientCapability.role == Capability.PRODUCER:
                matchesExistingStream = 0

                # add user as producer of all existing streams that match
                for stream in self.streamList.GetStreams():
                    if stream.capability.matches( clientCapability ):
                        streamDesc = stream
                        self.streamList.AddStreamProducer( clientProfile.publicId, streamDesc )
                        streamDescriptions.append( streamDesc )
                        matchesExistingStream = 1
                        print "added user as producer of existent stream"
                
                # add user as producer of non-existent stream
                if not matchesExistingStream:
                    capability = Capability( clientCapability.role, clientCapability.type )
                    capability.parms = clientCapability.parms
                    streamDesc = StreamDescription( self.description.name, "noDesc",
                                             self.AllocateMulticastLocation(), 
                                             capability, self.encryptionKey )
                    print "added user as producer of non-existent stream"
#FIXME - uses public id now; should use private id instead
                    self.streamList.AddStreamProducer( clientProfile.publicId, streamDesc )


        #
        # Compare user's consumer capabilities with existing stream
        # description capabilities. The user will receive a list of
        # compatible stream descriptions
        # 
        clientConsumerCapTypes = []
        for capability in clientProfile.capabilities:
            if capability.role == Capability.CONSUMER:
                clientConsumerCapTypes.append( capability.type )
        for stream in self.streamList.GetStreams():
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
    def AddNetworkService(self, networkServiceDescription):
        """
        AddNetworkService allows an administrator to add functionality to
        the Venue. Network services are described in the design documents.
        """
        try:
            self.networkServices[ networkServiceDescription.uri ] = networkServiceDescription
        except:
            print "Network Service already exists ", networkServiceDescription.uri

    AddNetworkService.soap_export_as = "AddNetworkService"
    
    def GetNetworkServices(self):
        """
        GetNetworkServices retreives the list of network service descriptions
        from the venue.
        """
        return self.networkServices
    
    GetNetworkServices.soap_export_as = "GetNetworkServices"
    
    def RemoveNetworkService(selfnetworkServiceDescription):
        """
        RemoveNetworkService removes a network service from a venue, making
        it unavailable to users of the venue.
        """
        try:
            del self.networkServices[ networkServiceDescription.uri ]
        except:
            print "Exception in RemoveNetworkService", sys.exc_type, sys.exc_value
            print "Network Service does not exist ", networkServiceDescription.uri
    RemoveNetworkService.soap_export_as = "RemoveNetworkService"
        
    def AddConnection(self, connectionDescription):
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

    AddConnection.soap_export_as = "AddConnection"

    def RemoveConnection(self, connectionDescription):
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

    RemoveConnection.soap_export_as = "RemoveConnection"

    def GetConnections(self):
        """
        GetConnections returns a list of all the connections to other venues
        that are found within this venue.
        """
        return self.connections.values()

    GetConnections.soap_export_as = "GetConnections"

    def SetConnections(self, connectionList):
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
            self.eventService.Distribute( Event( Event.SET_CONNECTIONS,
                                                 connectionList ) )

        except:
            print "Exception in SetConnections", sys.exc_type, sys.exc_value
            print "Connection does not exist ", connectionDescription.uri

    SetConnections.soap_export_as = "SetConnections"

    def SetDescription(self, description):
        """
        SetDescription allows an administrator to set the venues description
        to something new.
        """
        self.description = description

    SetDescription.soap_export_as = "SetDescription"

    def GetDescription(self):
        """
        GetDescription returns the description for the virtual venue.
        """
        return self.description

    GetDescription.soap_export_as = "GetDescription"

    def AddStream(self, inStreamDescription ):
        """
        Add a stream to the list of streams "in" the venue
        """
        streamDescription = CreateStreamDescription( inStreamDescription )
        self.streamList.AddStream( streamDescription )
    AddStream.soap_export_as = "AddStream"

    def RemoveStream(self, streamDescription):
        """
        Remove the given stream from the venue
        """
        self.streamList.RemoveStream( streamDescription )
    RemoveStream.soap_export_as = "RemoveStream"

    def GetStreams(self):
        """
        GetStreams returns a list of stream descriptions to the caller.
        """
        return self.streamList.GetStreams()

    GetStreams.soap_export_as = "GetStreams"

    # Client Methods
    def Enter(self, clientProfile):
        """
        The Enter method is used by a VenueClient to gain access to the
        services, users, and content found within a Virtual Venue.
        """
        privateId = None
        streamDescriptions = []
        state = self.GetState()

        try:
#            print "Called Venue Enter for: "
#            print dir(clientProfile)

            userInVenue = 0
            for key in self.users.keys():
                user = self.users[key]
                if user.publicId == clientProfile.publicId:
                    print "* * User already in venue"
                    userInVenue = 1
                    privateId = key
                    break

            if userInVenue == 0:
                privateId = self.GetNextPrivateId()
                print "Assigning private id: ", privateId
                self.users[privateId] = clientProfile
                state['users'] = self.users.values()

            # negotiate to get stream descriptions to return
            streamDescriptions = self.NegotiateCapabilities(clientProfile)
            self.eventService.Distribute( Event( Event.ENTER,
                                                 clientProfile ) )

        except:
           print "Exception in Enter ", formatExceptionInfo()

        return ( state, privateId, streamDescriptions )

    Enter.soap_export_as = "Enter"
    
    def Exit(self, privateId ):
        """
        The Exit method is used by a VenueClient to cleanly leave a Virtual
        Venue. Cleanly leaving a Virtual Venue allows the Venue to cleanup
        any state associated (or caused by) the VenueClients presence.
        """
        try:
            print "Called Venue Exit on ..."

            if self.IsValidPrivateId( privateId ):
                print "Deleting user ", privateId, self.users[privateId].name
                self.RemoveUser( privateId )

            else:
                print "* * Invalid private id !! ", privateId
        except:
            print "Exception in Exit ", sys.exc_type, sys.exc_value
        
    Exit.soap_export_as = "Exit"

    def RemoveUser(self, privateId):
        # Remove user as stream producer
#FIXME - uses public id now; should use private id instead
        self.streamList.RemoveProducer( self.users[privateId].publicId )

        # Distribute event
        clientProfile = self.users[privateId]
        self.eventService.Distribute( Event( Event.EXIT,
                                             clientProfile ) )

        # Remove user from venue
        del self.users[privateId]


    def UpdateClientProfile(self, clientProfile):
        """
        UpdateClientProfile allows a VenueClient to update/modify the client
        profile that is stored by the Virtual Venue that they gave to the Venue
        when they called the Enter method.
        """
        for user in self.users.values():
            if user.publicId == clientProfile.publicId:
                self.users[user.privateId] = clientProfile
            self.eventService.Distribute( Event( Event.MODIFY_USER,
                                                 clientProfile ) )
        
    UpdateClientProfile.soap_export_as = "UpdateClientProfile"

    def wsAddData(self, dataDescription ):
        return self.AddData(dataDescription)

    wsAddData.soap_export_as = "AddData"

    def AddData(self, dataDescription ):
        """
        The AddData method enables VenuesClients to put data in the Virtual
        Venue. Data put in the Virtual Venue through AddData is persistently
        stored.
        """

        name = dataDescription.name

        if self.data.has_key(name):
            #
            # We already have this data; raise an exception.
            #

            print "AddData: data already present: ", name
            raise VenueException("AddData: data %s already present" % (name))

        self.data[dataDescription.name] = dataDescription
        self.eventService.Distribute( Event( Event.ADD_DATA,
                                             dataDescription ) )

    def wsUpdateData(self, dataDescription):
        return self.UpdateData(dataDescription)

    wsUpdateData.soap_export_as = "UpdateData"
        
    def UpdateData(self, dataDescription):
        """
        Replace the current description for dataDescription.name with
        this one.

        Send out an update event.
        """

        name = dataDescription.name

        if not self.data.has_key(name):
            #
            # We don't already have this data; raise an exception.
            #

            print "UpdateData: data not already present: ", name
            raise VenueException("UpdateData: data %s not already present" % (name))

        self.data[dataDescription.name] = dataDescription
        self.eventService.Distribute( Event( Event.UPDATE_DATA,
                                             dataDescription ) )

    def wsGetData(self, name):
        return self.GetData(name)

    wsGetData.soap_export_as = "GetData"
        
    def GetData(self, name):
        """
        GetData is the method called by a VenueClient to retrieve information
        about the data. This might also be the operation that the VenueClient
        uses to actually retrieve the real data.
        """

        if self.data.has_key(name):
            return self.data[name]
        else:
            return None

    GetData.soap_export_as = "GetData"

    def RemoveData(self, dataDescription):
        """
        RemoveData removes persistent data from the Virtual Venue.
        """
        try:
            # We actually have to remove the real data, not just the
            # data description -- I guess that's later :-)
            del self.data[ dataDescription.name ]
            self.dataStore.DeleteFile(dataDescription.name)
            self.eventService.Distribute( Event( Event.REMOVE_DATA,
                                                     dataDescription ) )
        except:
            print "Exception in RemoveData", sys.exc_type, sys.exc_value
            print "Data does not exist", dataDescription.name

    RemoveData.soap_export_as = "RemoveData"

    def GetUploadDescriptor(self):
        """
        Retrieve the upload descriptor from the Venue's datastore.

        If the venue has no data store configured, return None.
        """
        
        if self.dataStore is not None:
            return self.dataStore.GetUploadDescriptor()
        else:
            return None

    GetUploadDescriptor.soap_export_as = "GetUploadDescriptor"

    def AddService(self, serviceDescription):
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

    AddService.soap_export_as = "AddService"

    def RemoveService(self, serviceDescription):
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

    RemoveService.soap_export_as = "RemoveService"

 
