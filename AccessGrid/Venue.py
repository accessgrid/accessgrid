#-----------------------------------------------------------------------------
# Name:        Venue.py
# Purpose:     The Virtual Venue is the object that provides the collaboration
#               scopes in the Access Grid.
#
# Author:      Ivan R. Judson, Thomas D. Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: Venue.py,v 1.52 2003-03-12 08:54:59 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys
import time
import string
import types
import socket
import os.path
import logging

from AccessGrid.hosting.pyGlobus import ServiceBase

from AccessGrid.hosting import AccessControl

from AccessGrid.Types import Capability
from AccessGrid.Descriptions import StreamDescription, CreateStreamDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.GUID import GUID
from AccessGrid import DataStore
from AccessGrid.scheduler import Scheduler
from AccessGrid.Events import Event, HeartbeatEvent
from AccessGrid.Utilities import formatExceptionInfo, AllocateEncryptionKey
from AccessGrid.Utilities import GetHostname

log = logging.getLogger("AG.VenueServer")

class VenueException(Exception):
    """
    A generic exception type to be raised by the Venue code.
    """
    pass


class Venue(ServiceBase.ServiceBase):
    """
    A Virtual Venue is a virtual space for collaboration on the Access Grid.
    """
    def __init__(self, uniqueId, description, administrator, dataStorePath):
        """
        Venue constructor.

        dataStorePath is the directory which the Venue's data storage object
        should use for storing its files.

        """
        self.connections = dict()
        self.services = dict()
        self.networkServices = []
        self.administrators = []
        self.encryptMedia = 1

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

        self.dataStorePath = dataStorePath
        self.dataStore = None

        self.producerCapabilities = []
        self.consumerCapabilities = []

        self.cleanupTime = 30
        self.nextPrivateId = 1

        # self.AllowedEntryRole = AccessControl.Role("Venue.AllowedEntry", self)
        # self.VenueUsersRole = AccessControl.Role("Venue.VenueUsers", self)

        if self.encryptMedia == 1:
            self.encryptionKey = AllocateEncryptionKey()

    def _authorize(self):
        """
        """
        sm = AccessControl.GetSecurityManager()
        if sm == None:
            return 1
        elif sm.GetSubject().GetName() in self.administrators:
            return 1
        # call back up to the server
        elif self.server._authorize():
            return 1
        else:
            return 0

    def __repr__(self):
        return "Venue: name=%s id=%s" % (self.description.name, id(self))

    def __getstate__(self):
        """
        Retrieve the state of object attributes for pickling.

        We don't pickle any object instances, except for the
        uniqueId and description.

        """
        odict = self.__dict__.copy()

        # Transform the URI
        venuePath = urlparse.urlparse(odict["description"].uri)[2]
        odict["description"].uri = venuePath
        
        # We don't save things in this list
        keys = ("users", "clients", "nodes", "multicastAllocator",
                "producerCapabilities", "consumerCapabilities",
                "server", "_service_object", "houseKeeper",
                "dataStore")
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

        self.users = dict()
        self.clients = dict()
        self.nodes = dict()
        self.multicastAllocator = None
        self.cleanupTime = 30
        self.nextPrivateId = 1
        self.dataStore = None
        if self.encryptMedia == 1:
            self.encryptionKey = AllocateEncryptionKey()

    def Start(self, server):
        """ """
        self.server = server
        self.server.eventService.AddChannel(self.uniqueId)
        self.server.textService.AddChannel(self.uniqueId)

        log.debug("Registering heartbeat for %s", self.uniqueId)
        self.server.eventService.RegisterCallback(self.uniqueId,
                                           HeartbeatEvent.HEARTBEAT,
                                           self.ClientHeartbeat)

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
            log.warn("Not starting datastore for venue: %s does not exist %s",
                      self.uniqueId, self.dataStorePath)
            return

        self.server.dataTransferServer.RegisterPrefix(str(self.uniqueId), self)

        self.dataStore = DataStore.DataStore(self, self.dataStorePath,
                                             str(self.uniqueId))
        self.dataStore.SetTransferEngine(self.server.dataTransferServer)

        log.info("Have upload url: %s", self.dataStore.GetUploadDescriptor())

        for file, desc in self.data.items():
            log.debug("Checking file %s for validity", file)
            url = self.dataStore.GetDownloadDescriptor(file)
            if url is None:
                log.warn("File %s has vanished", file)
                del self.data[file]
            else:
                desc.SetURI(url)
                self.UpdateData(desc)

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

    def GetState(self):
        """
        GetState returns the current state of the Virtual Venue.
        """

        log.debug("Called GetState on %s", self.uniqueId)

        venueState = {
            'uniqueId' : self.uniqueId,
            'description' : self.description,
            'connections' : self.connections.values(),
            'users' : self.users.values(),
            'nodes' : self.nodes.values(),
            'services' : self.services.values(),
            'eventLocation' : self.server.eventService.GetLocation(),
            'textLocation' : self.server.textService.GetLocation()
            }

        #
        # If we don't have a datastore, don't advertise
        # the existence of any data. We won't be able to get
        # at it anyway.
        #
        if self.dataStore is None:
            venueState['data'] = []
        else:
            venueState['data'] = self.data.values()

        return venueState

    def CleanupClients(self):
        now_sec = time.time()
        for privateId in self.clients.keys():
            then_sec = self.clients[privateId]
            if abs(now_sec - then_sec) > self.cleanupTime:
                log.debug("  Removing user : %s", self.users[privateId].name)
                self.RemoveUser( privateId )

    def ClientHeartbeat(self, event):
        privateId = event
        now = time.time()
        self.clients[privateId] = now
        log.debug("Got Client Heartbeat for %s at %s." % (event, now))
    
    def Shutdown(self):
        """
        This method cleanly shuts down all active threads associated with the
        Virtual Venue. Currently there are a few threads in the Event
        Service.
        """
        self.houseKeeper.StopAllTasks()

    def NegotiateCapabilities(self, clientProfile, privateId):
        """
        This method takes a client profile and matching privateId, then it
        finds a set of streams that matches the client profile. Later this
        method could use network services to find The Best Match of all the
        network services, the existing streams, and all the client
        capabilities.
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
                        self.streamList.AddStreamProducer( privateId,
                                                           streamDesc )
                        streamDescriptions.append( streamDesc )
                        matchesExistingStream = 1
                        log.debug("added user as producer of existent stream")

                # add user as producer of non-existent stream
                if not matchesExistingStream:
                    capability = Capability( clientCapability.role,
                                             clientCapability.type )
                    capability.parms = clientCapability.parms
                    if self.encryptMedia:
                        key = 0
                    else:
                        key = self.encryptionKey

                    addr = self.AllocateMulticastLocation()
                    streamDesc = StreamDescription( self.description.name,
                                                    "noDesc", addr,
                                                    capability, key)
                    log.debug("added user as producer of non-existent stream")
                    self.streamList.AddStreamProducer( privateId,
                                                       streamDesc )


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

    def FindUserByProfile(self, profile):
        """
        Find out if a given user is in the venue from their client profile.
        If they are return their private id, if not, return None.
        """

        for key in self.users.keys():
            user = self.users[key]
            if user.publicId == profile.publicId:
                return key

        return None

    # Management methods
    def AddAdministrator(self, string):
        """
        """
        if string not in self.administrators:
            self.administrators.append(string)
            return string
        else:
            log.exception("Venue.AddAdministrator: Administrator already present")
            raise VenueException("Administrator already present")

    AddAdministrator.soap_export_as = "AddAdministrator"

    def RemoveAdministrator(self, string):
        """
        """
        if string in self.administrators:
            self.administrators.remove(string)
            return string
        else:
            log.exception("Venue.RemoveAdministrator: Administrator not found")
            raise VenueException("Administrator not found")

    RemoveAdministrator.soap_export_as = "RemoveAdministrator"
    
    def SetAdministrators(self, administratorList):
        """
        """
        self.administrators = self.administrators + administratorList

    SetAdministrators.soap_export_as = "SetAdministrators"

    def GetAdministrators(self):
        """
        """
        return self.administrators

    GetAdministrators.soap_export_as = "GetAdministrators"

    def SetEncryptMedia(self, value, key=None):
        """
        Turn media encryption on or off.
        """
        if not self._authorize():
            raise VenueException("You are not authorized to perform this action.")
        self.encryptMedia = value
        if not self.encryptMedia:
            self.encryptionKey = None
        else:
            self.encryptionKey = key

        return self.encryptMedia

    SetEncryptMedia.soap_export_as = "SetEncryptMedia"

    def GetEncryptMedia(self):
        """
        Return whether we are encrypting streams or not.
        """
        return self.encryptionKey

    GetEncryptMedia.soap_export_as = "GetEncryptMedia"

    def AddNetworkService(self, networkServiceDescription):
        """
        AddNetworkService allows an administrator to add functionality to
        the Venue. Network services are described in the design documents.
        """
        if not self._authorize():
            raise VenueException("You are not authorized to perform this action.")
        try:
            self.networkServices[ networkServiceDescription.uri ] = networkServiceDescription
        except:
            log.exception("Exception in Add Network Service!")
            raise VenueException("Add Network Service Failed!")
        
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
        if not self._authorize():
            raise VenueException("You are not authorized to perform this action.")
        try:
            del self.networkServices[ networkServiceDescription.uri ]
        except:
            log.exception("Exception in RemoveNetworkService!")
            raise VenueException("Remove Network Service Failed!")

    RemoveNetworkService.soap_export_as = "RemoveNetworkService"

    def AddConnection(self, connectionDescription):
        """
        AddConnection allows an administrator to add a connection to a
        virtual venue to this virtual venue.
        """
        if not self._authorize():
            raise VenueException("You are not authorized to perform this action.")
        try:
            self.connections[connectionDescription.uri] = connectionDescription
            self.server.eventService.Distribute( self.uniqueId,
                                          Event( Event.ADD_CONNECTION,
                                                 self.uniqueId,
                                                 connectionDescription ) )
        except:
            log.exception("Exception in AddConnection!")
            raise VenueException("Add Connection Failed!")
        
    AddConnection.soap_export_as = "AddConnection"

    def RemoveConnection(self, connectionDescription):
        """
        RemoveConnection removes a connection to another virtual venue
        from this virtual venue. This is an administrative operation.
        """
        if not self._authorize():
            raise VenueException("You are not authorized to perform this action.")
        try:
            del self.connections[ connectionDescription.uri ]
            self.eventService.Distribute( self.uniqueId,
                                          Event( Event.REMOVE_CONNECTION,
                                                 self.uniqueId,
                                                 connectionDescription ) )
        except:
            log.exception("Exception in RemoveConnection.")
            raise VenueException("Remove Connection Failed!")

    RemoveConnection.soap_export_as = "RemoveConnection"

    def GetConnections(self):
        """
        GetConnections returns a list of all the connections to other venues
        that are found within this venue.
        """
        log.debug("Calling GetConnections.")
        
        return self.connections.values()

    GetConnections.soap_export_as = "GetConnections"

    def SetConnections(self, connectionList):
        """
        SetConnections is a convenient aggregate accessor for the list of
        connections for this venue. Alternatively the user could iterate over
        a list of connections adding them one by one, but this is more
        desirable.
        """
        log.debug("Calling SetConnections.")
        
        if not self._authorize():
            raise VenueException("You are not authorized to perform this action.")
        try:
            self.connections = dict()
            for connection in connectionList:
                self.connections[connection.uri] = connection
            self.server.eventService.Distribute( self.uniqueId,
                                          Event( Event.SET_CONNECTIONS,
                                                 self.uniqueId,
                                                 connectionList ) )
        except:
            log.exception("SetConnections failed.")
            raise VenueException("Set Connections Failed!")

    SetConnections.soap_export_as = "SetConnections"

    def SetDescription(self, description):
        """
        SetDescription allows an administrator to set the venues description
        to something new.
        """
        if not self._authorize():
            raise VenueException("You are not authorized to perform this action.")
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
        if not self._authorize():
            raise VenueException("You are not authorized to perform this action.")
        log.debug("%s - Adding Stream: ", self.uniqueId)
        
        streamDescription = CreateStreamDescription( inStreamDescription )
        log.debug("%s - Location: %s %d", self.uniqueId, streamDescription.location.GetHost(),
                  streamDescription.location.GetPort())
        log.debug("%s - Capability: %s %s", self.uniqueId, streamDescription.capability.role,
                  streamDescription.capability.type)
        log.debug("%s - Encyrption Key: %s", self.uniqueId, streamDescription.encryptionKey)
        log.debug("%s - Static: %d", self.uniqueId, streamDescription.static)
        
        self.streamList.AddStream( streamDescription )

    AddStream.soap_export_as = "AddStream"

    def RemoveStream(self, streamDescription):
        """
        Remove the given stream from the venue
        """
        if not self._authorize():
            raise VenueException("You are not authorized to perform this action.")
        self.streamList.RemoveStream( streamDescription )

    RemoveStream.soap_export_as = "RemoveStream"

    def GetStreams(self):
        """
        GetStreams returns a list of stream descriptions to the caller.
        """
        return self.streamList.GetStreams()

    GetStreams.soap_export_as = "GetStreams"

    def GetStaticStreams(self):
        """
        GetStaticStreams returns a list of static stream descriptions
        to the caller.
        """
        log.debug("Called Venue.GetStaticStreams.")
        
        return self.streamList.GetStaticStreams()

    GetStaticStreams.soap_export_as = "GetStaticStreams"

    # Client Methods
    def Enter(self, clientProfile):
        """
        The Enter method is used by a VenueClient to gain access to the
        services, users, and content found within a Virtual Venue.
        """
        privateId = None
        streamDescriptions = []
        state = self.GetState()

        #
        # Authorization management.
        #
        # Get the security manager for this invocation. This will tell
        # us how the user was authenticated for this call.
        #
        # To check to see whether this user can even enter, see if
        # he is in the AllowedEntry role
        #

#          sm = AccessControl.GetSecurityManager()
#          if  sm.ValidateRole(self.AllowedEntryRole):
#              subject = sm.GetSubject()
#              log.info("User %s validated for entry to %s", subject, self)

#              if self.VenueUsersRole.HasSubject(subject):
#                  self.VenueUsersRole.AddSubject(subject)
#          else:
#              log.info("User %s rejected for entry to %s", sm.GetSubject(), self)
#              raise VenueException("Entry denied")


        try:
            log.debug("Called Venue Enter for: ")
            log.debug(dir(clientProfile))

            privateId = self.FindUserByProfile(clientProfile)

            if privateId != None:
                log.debug("* * User already in venue")
            else:
                privateId = self.GetNextPrivateId()
                log.debug("Assigning private id: %s", privateId)
                clientProfile.distinguishedName = AccessControl.GetSecurityManager().GetSubject().GetName()
                self.users[privateId] = clientProfile
                state['users'] = self.users.values()

            # negotiate to get stream descriptions to return
            streamDescriptions = self.NegotiateCapabilities(clientProfile,
                                                            privateId)
            self.server.eventService.Distribute( self.uniqueId,
                                          Event( Event.ENTER,
                                                 self.uniqueId,
                                                 clientProfile ) )

        except:
            log.exception("Exception in Enter!")
            raise VenueException("Enter: ")

        return ( state, privateId, streamDescriptions )

    Enter.soap_export_as = "Enter"

    def Exit(self, privateId ):
        """
        The Exit method is used by a VenueClient to cleanly leave a Virtual
        Venue. Cleanly leaving a Virtual Venue allows the Venue to cleanup
        any state associated (or caused by) the VenueClients presence.
        """
        try:
            log.debug("Called Venue Exit on ...")

            if self.IsValidPrivateId( privateId ):
                log.debug("Deleting user %s %s", privateId,
                          self.users[privateId].name)
                self.RemoveUser( privateId )

            else:
                log.warn("* * Invalid private id %s!!", privateId)
        except:
            log.exception("Exception in Exit!")
            raise VenueException("ExitVenue: ")

    Exit.soap_export_as = "Exit"

    def RemoveUser(self, privateId):
        # Remove user as stream producer
        self.streamList.RemoveProducer(privateId)

        # Distribute event
        clientProfile = self.users[privateId]
        self.server.eventService.Distribute( self.uniqueId,
                                      Event( Event.EXIT,
                                             self.uniqueId,
                                             clientProfile ) )

        # Remove user from venue
        del self.users[privateId]
        del self.clients[privateId]

    def UpdateClientProfile(self, clientProfile):
        """
        UpdateClientProfile allows a VenueClient to update/modify the client
        profile that is stored by the Virtual Venue that they gave to the Venue
        when they called the Enter method.
        """
        for user in self.users.values():
            if user.publicId == clientProfile.publicId:
                self.users[user.privateId] = clientProfile
            self.server.eventService.Distribute( self.uniqueId,
                                          Event( Event.MODIFY_USER,
                                                 self.uniqueId,
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

            log.exception("AddData: data already present: %s", name)
            raise VenueException("AddData: data %s already present" % (name))

        self.data[dataDescription.name] = dataDescription
        log.debug("Send ADD_DATA event %s", dataDescription)
        self.server.eventService.Distribute( self.uniqueId,
                                      Event( Event.ADD_DATA,
                                             self.uniqueId,
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

            log.exception("UpdateData: data not already present: %s", name)
            raise VenueException("UpdateData: data %s not already present" % (name))

        self.data[dataDescription.name] = dataDescription
        log.debug("Send UPDATE_DATA event %s", dataDescription)
        self.server.eventService.Distribute( self.uniqueId,
                                      Event( Event.UPDATE_DATA,
                                             self.uniqueId,
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

        #
        # If we do not have a running datastore, never return a descriptor
        # (So that data doesn't even show up in the venue).
        #
        if self.dataStore is None:
            return ''

        if self.data.has_key(name):
            return self.data[name]
        else:
            return ''

    GetData.soap_export_as = "GetData"

    def RemoveData(self, dataDescription):
        """
        RemoveData removes persistent data from the Virtual Venue.
        """
        try:
            # We actually have to remove the real data, not just the
            # data description -- I guess that's later :-)
            if dataDescription.name in self.data:
                del self.data[ dataDescription.name ]
                self.dataStore.DeleteFile(dataDescription.name)
                self.server.eventService.Distribute( self.uniqueId,
                                                     Event( Event.REMOVE_DATA,
                                                            self.uniqueId,
                                                            dataDescription ) )
            else:
                log.exception("Data not found!")
#                raise DataNotFoundException("Data not found.")
        except:
            log.exception("Exception in RemoveData!")
            raise VenueException("Cannot remove data!")

    RemoveData.soap_export_as = "RemoveData"

    def GetUploadDescriptor(self):
        """
        Retrieve the upload descriptor from the Venue's datastore.

        If the venue has no data store configured, return None.
        """

        #
        # Sigh. Return '' because None marshals as "None".
        #
        if self.dataStore is None:
            return ''
        else:
            return self.dataStore.GetUploadDescriptor()

    GetUploadDescriptor.soap_export_as = "GetUploadDescriptor"

    def AddService(self, serviceDescription):
        """
        This method adds a service description to the Venue.
        """
        log.debug("Adding service %s", serviceDescription.name,
                  serviceDescription.uri)
        try:
            self.services[serviceDescription.uri] = serviceDescription
            self.server.eventService.Distribute( self.uniqueId,
                                          Event( Event.ADD_SERVICE,
                                                 self.uniqueId,
                                                 serviceDescription ) )
        except:
            log.exception("Exception in AddService!")
            raise VenueException("AddService: ")

    AddService.soap_export_as = "AddService"

    def RemoveService(self, serviceDescription):
        """
        This method removes a service description from the list of services
        in the Virtual Venue.
        """

        try:
            del self.services[serviceDescription.uri]
            self.server.eventService.Distribute( self.uniqueId,
                                          Event( Event.REMOVE_SERVICE,
                                                 self.uniqueId,
                                                 serviceDescription ) )
        except:
            log.exception("Exception in removeService!")
            raise VenueException("RemoveService: ")

    RemoveService.soap_export_as = "RemoveService"


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
        Prepare stream list for pickling
        - remove non-static streams
        - strip the producerList from each item, so only the stream descriptions remain
        """
        log.debug("Calling Venue.__getstate__.")

        odict = self.__dict__.copy()
        odict['streams'] = self.GetStaticStreams()
        return odict

    def __setstate__(self, dict):
        """
        Rebuild list tuples from incoming dictionary
        """
        log.debug("Calling Venue.__setstate_.")
        
        dict['streams'] = map( lambda stream: ( stream, [] ), dict['streams'] )
        self.__dict__ = dict

    def AddStream( self, stream ):
        """
        Add a stream to the list, only if it doesn't already exist
        """
        if not self.FindStreamByDescription(stream):
            self.streams.append( ( stream, [] ) )
        
    def RemoveStream( self, stream ):
        """
        Remove a stream from the list
        """
        if self.FindStreamByDescription(stream):
            self.streams.remove(streamListItem)

    def AddStreamProducer( self, producingUser, inStream ):
        """
        Add a stream to the list, with the given producer
        """
        streamListItem = self.FindStreamByDescription(inStream)
        if streamListItem != None:
            (streamDesc, producerList) = streamListItem
            producerList.append( producingUser )
        else:
            self.streams.append( (inStream, [ producingUser ] ) )
            log.debug( "* * * Added stream producer %s", producingUser )

    def RemoveStreamProducer( self, producingUser, inStream ):
        """
        Remove a stream producer from the given stream.  If the last
        producer is removed, the stream will be removed from the list
        if it is non-static.
        """
        self.__RemoveProducer( producingUser, inStream )
        streamListItem = self.FindStreamByDescription(inStream)
        if streamListItem != None:
            (streamDesc, producerList) = streamListItem
            if len(producerList) == 0:
                self.streams.remove((streamDesc, producerList))
            

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
        streamListItem = self.FindStreamByDescription(inStream)
        if streamListItem != None:
            (stream, producerList) = streamListItem
            if producingUser in producerList:
                producerList.remove( producingUser )



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

    def GetStaticStreams(self):
        """
        GetStaticStreams returns a list of static stream descriptions
        to the caller.
        """
        log.debug("Called StreamDescriptionList.GetStaticStreams.")

        staticStreams = []
        for stream, producerList in self.streams:
            log.debug("GetStaticStreams - Location: %s %d", 
                      stream.location.GetHost(),
                      stream.location.GetPort())
            log.debug("GetStaticStreams - Capability: %s %s",
                      stream.capability.role,
                      stream.capability.type)
            log.debug("GetStaticStreams - Encyrption Key: %s",
                      stream.encryptionKey)
            log.debug("GetStaticStreams - Static: %d",
                      stream.static)
            if stream.static:
                staticStreams.append( stream )
        return staticStreams

    def FindStreamByDescription( self, inStream ):
        """
        """
        for stream, producerList in self.streams:
            log.debug("StreamDescriptionList.index Address %s %s",
                      inStream.location.host,
                      stream.location.host)
            log.debug("StreamDescriptionList.index Port %d %d",
                      inStream.location.port,
                      stream.location.port)
            if inStream.location.host == stream.location.host and \
                   inStream.location.port == stream.location.port:
                return (stream, producerList)

        return None
