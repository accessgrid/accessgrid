#-----------------------------------------------------------------------------
# Name:        Venue.py
# Purpose:     The Virtual Venue is the object that provides the collaboration
#               scopes in the Access Grid.
#
# Author:      Ivan R. Judson, Thomas D. Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: Venue.py,v 1.100 2003-05-28 13:25:45 olson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys
import time
import string
import socket
import os.path
import logging

from threading import Condition, Lock

from AccessGrid.hosting.pyGlobus import ServiceBase

from AccessGrid.hosting import AccessControl

from AccessGrid import AppService
from AccessGrid.Types import Capability
from AccessGrid.Descriptions import StreamDescription, CreateStreamDescription
from AccessGrid.Descriptions import ConnectionDescription, VenueDescription
from AccessGrid.Descriptions import ApplicationDescription, ServiceDescription
from AccessGrid.Descriptions import CreateDataDescription, DataDescription
from AccessGrid.Descriptions import BadDataDescription, BadServiceDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.GUID import GUID
from AccessGrid import DataStore
from AccessGrid.scheduler import Scheduler
from AccessGrid.Events import Event, HeartbeatEvent, DisconnectEvent, ClientExitingEvent
from AccessGrid.Utilities import formatExceptionInfo, AllocateEncryptionKey
from AccessGrid.Utilities import GetHostname, ServerLock

# these imports are for dealing with SOAP structs, which we won't have to 
# do when we have WSDL; at that time, these imports and the corresponding calls
# should be removed
from AccessGrid.ClientProfile import CreateClientProfile
from AccessGrid.Descriptions import CreateServiceDescription

log = logging.getLogger("AG.VenueServer")

class VenueException(Exception):
    """
    A generic exception type to be raised by the Venue code.
    """
    pass

class BadDataDescription(Exception):
    """
    The exception raised when a data description struct is not
    successfully converted to a real data description.
    """
    pass

class BadServiceDescription(Exception):
    """
    The exception raised when a service description struct is not
    succesfully converted to a real service description.
    """
    pass

class BadConnectionDescription(Exception):
    """
    The exception raised when a connection description struct is not
    succesfully converted to a real connection description.
    """
    pass

class BadStreamDescription(Exception):
    """
    The exception raised when a stream description struct is not
    successfully converted to a real stream description.
    """
    pass

class InvalidClientProfileException(Exception):
    """
    The exception raised when a client profile struct is not
    successfully converted to a client profile.
    """
    pass

class InvalidVenueState(Exception):
    """
    The exception raised when the venue state cannot be retrieved.
    """
    pass

class AdministratorAlreadyPresent(Exception):
    """
    The exception raised when an administrator is added, but is
    already an administrator.
    """
    pass

class AdministratorNotFound(Exception):
    """
    The exception raised when an administrator is not found in the
    venues list of administrators.
    """
    pass

class ConnectionNotFound(Exception):
    """
    The exception raised when a connection is not found in the venues
    list of connections.
    """
    pass

class ApplicationNotFound(Exception):
    """
    The exception raised when an application is not found in the
    venues list of applications.
    """
    pass

class ApplicationUnbindError(Exception):
    """
    The exception raised when the server can't unbind an application
    web service.
    """
    pass

class NotAuthorized(Exception):
    """
    The exception raised when the caller is not authorized to invoke the
    method.
    """
    pass

class DataAlreadyPresent(Exception):
    """
    The exception raised when a data description is already present in
    the venue.
    """
    pass

class DataNotFound(Exception):
    """
    The exception raised when a data description is not found in
    the venue.
    """
    pass

class StreamAlreadyPresent(Exception):
    """
    The exception raised when a stream is already present in the venue.
    """
    pass

class StreamNotFound(Exception):
    """
    The exception raised when a stream is not found in the venue.
    """
    pass

class ServiceAlreadyPresent(Exception):
    """
    The exception raised when a service is already present in the venue.
    """
    pass

class ServiceNotFound(Exception):
    """
    The exception raised when a service is not found in the venue.
    """
    pass

class ClientNotFound(Exception):
    """
    The exception raised when a client is not found in the venues list
    of active clients.
    """
    pass

class Venue(ServiceBase.ServiceBase):
    """
    A Virtual Venue is a virtual space for collaboration on the Access Grid.
    """
    def __init__(self, server, name, description, administrators,
                 dataStoreLocation, id=None):
        """
        Venue constructor.
        """
        log.debug("------------ STARTING VENUE")
        self.server = server
        self.name = name
        self.description = description
        self.administrators = administrators
        self.encryptMedia = server.GetEncryptAllMedia()
        if self.encryptMedia:
            self.encryptionKey = AllocateEncryptionKey()
        else:
            self.encryptionKey = None
        self.simpleLock = ServerLock("venue")
        self.heartbeatLock = ServerLock("heartbeat")
        self.clientDisconnectOK = {}
        
        if id == None:
            self.uniqueId = str(GUID())
        else:
            self.uniqueId = id
            
        self.cleanupTime = 30

        self.connections = dict()
        self.applications = dict()
        self.data = dict()
        self.services = dict()
        self.streamList = StreamDescriptionList()
        self.clients = dict()

        #
        # Dictionary keyed on client private id; value
        # true if a remove is in process on this client.
        #
        self.clientsBeingRemoved = {}
        self.clientsBeingRemovedLock = ServerLock("clientRemove")

        self.dataStore = None
        self.producerCapabilities = []
        self.consumerCapabilities = []

        self.uri = self.server.MakeVenueURL(self.uniqueId)

        log.info("Venue URI %s", self.uri)

        self.server.eventService.AddChannel(self.uniqueId)
        self.server.textService.AddChannel(self.uniqueId)
        log.debug("Registering heartbeat for %s", self.uniqueId)
        self.server.eventService.RegisterCallback(self.uniqueId,
                                           HeartbeatEvent.HEARTBEAT,
                                           self.ClientHeartbeat)

        self.server.eventService.RegisterCallback(self.uniqueId,
                                                  DisconnectEvent.DISCONNECT,
                                                  self.EventServiceDisconnect)
        self.server.eventService.RegisterCallback(self.uniqueId,
                                                  ClientExitingEvent.CLIENT_EXITING,
                                                  self.EventServiceClientExits)

        #
        # Create the directory to hold the venue's data.
        #

        log.debug("data store location: %s" % dataStoreLocation)
        
        if dataStoreLocation is None or not os.path.exists(dataStoreLocation):
            log.warn("Creating venue: Data storage path %s not valid",
                     dataStoreLocation)
            self.dataStorePath = None
        else:
            self.dataStorePath = os.path.join(dataStoreLocation, self.uniqueId)
            if not os.path.exists(self.dataStorePath):
                try:
                    os.mkdir(self.dataStorePath)
                except OSError:
                    log.exception("Could not create venueStoragePath.")
                    self.dataStorePath = None


        # Start the data store
        if self.dataStorePath is None or not os.path.isdir(self.dataStorePath):
            log.warn("Not starting datastore for venue: %s does not exist %s",
                      self.uniqueId, self.dataStorePath)

        self.server.dataTransferServer.RegisterPrefix(str(self.uniqueId), self)

        self.dataStore = DataStore.DataStore(self, self.dataStorePath,
                                             str(self.uniqueId))
        self.dataStore.SetTransferEngine(self.server.dataTransferServer)

        log.info("Have upload url: %s", self.dataStore.GetUploadDescriptor())
        
        #self.StartApplications()

        #self.AllowedEntryRole = AccessControl.Role("Venue.AllowedEntry", self)
        #self.VenueUsersRole = AccessControl.Role("Venue.VenueUsers", self)

    def __repr__(self):
        """
        A standard repr method to make a string that can be print'd.

        **Returns:**

            *string* Simple string representation of the Venue.
        """
        return "Venue: name=%s id=%s" % (self.name, id(self))

    def _Authorize(self):
        """

        This is a simplistic authorization that only checks to see if
        the caller is in the list of administrators of this venue, or
        the venue server. if they are they are authorized, if they
        aren't they are not authorized.

        **Returns:**

            *0* If authorization fails.

            *1* If authorization succeeds.
        """
        sm = AccessControl.GetSecurityManager()
        if sm == None:
            return 1
        elif sm.GetSubject().GetName() in self.administrators:
            return 1
        # call back up to the server
        elif self.server._Authorize():
            return 1
        else:
            return 0

    def AsINIBlock(self):
        """
        This serializes the data in this venue as a INI formatted
        block of text.
        """
        # The Venue Block
        sclass = str(self.__class__).split('.')
        string = "\n[%s]\n" % self.uniqueId
        string += "type : %s\n" % sclass[-1]
        string += "name : %s\n" % self.name
        string += "description : %s\n" % self.description
        if len(self.administrators):
            string += "administrators : %s\n" % ":".join(self.administrators)
        string += "encryptMedia : %d\n" % self.encryptMedia
        string += "cleanupTime : %d\n" % self.cleanupTime
        if self.encryptMedia:
            string += "encryptionKey : %s\n" % self.encryptionKey

        # Get the list of connections
        clist = ":".join(map( lambda conn: conn.GetId(),
                              self.connections.values() ))
        if len(clist):
            string += "connections : %s\n" % clist

        # Get the list of streams
        slist = ":".join(map( lambda stream: stream.GetId(),
                              self.streamList.GetStaticStreams() ))
        if len(slist):
            string += "streams : %s\n" % slist

        # Get the list of data
        # For now we have to sort out the data so we only
        # store venue data in the persistence file
        vdata = []
        for d in self.data.values():
            if d.GetType() == None:
                vdata.append(d)
        dlist = ":".join(map( lambda data: data.GetId(), vdata ))

        if len(dlist):
            string += "data : %s\n" % dlist

        # List of applications
        alist = ":".join(map(lambda app: app.GetId(),
                             self.applications.values()))

        if len(alist):
            string += "applications : %s\n" % alist

        # List of services
        servlist = ":".join(map(lambda service: service.GetId(),
                                self.services.values()))

        if len(servlist):
            string += "services: %s\n" % servlist
            
        # The blocks for other data
        if len(clist):
            string += "".join(map(lambda conn: conn.AsINIBlock(),
                                    self.connections.values() ))
        if len(dlist):
            string += "".join(map(lambda data: data.AsINIBlock(), vdata ))

        if len(slist):
            string += "".join(map(lambda stream: stream.AsINIBlock(),
                                    self.streamList.GetStaticStreams()))

        if len(alist):
            string += "".join(map(lambda app: app.AsINIBlock(),
                                  self.applications.values()))

        if len(servlist):
            string += "".join(map(lambda service: service.AsINIBlock(),
                                  self.services.values()))
            
        return string

    def AsVenueDescription(self):
        """
        This creates a Venue Description filled in with the data from
        this venue.
        """
        desc = VenueDescription(self.name, self.description,
                                self.administrators, 
                                (self.encryptMedia, self.encryptionKey),
                                self.connections.values(),
                                self.GetStaticStreams())
        desc.SetURI(self.uri)
        
        return desc

    def AsVenueState(self):
        """
        This creates a Venue State filled in with the data from this
        venue.
        """
        venueState = {
            'uniqueId' : self.uniqueId,
            'name' : self.name,
            'description' : self.description,
            'uri' : self.uri,
            'connections' : self.connections.values(),
            'applications': map(lambda x: x.AsApplicationDescription(),
                                self.applications.values()),
            'clients' : map(lambda c: c[0], self.clients.values()),
            'services' : self.services.values(),
            'data' : self.data.values(),
            'eventLocation' : self.server.eventService.GetLocation(),
            'textLocation' : self.server.textService.GetLocation()
            }

        return venueState
    
    def StartApplications(self):
        """
        Restart the application services after a server restart.

        For each app impl, awaken the app, and create a new
        web service binding for it.
        """

        for appImpl in self.applications.values():
            appImpl.Awaken(self.server.eventService)
            app = AppService.AppObject(appImpl)
            hostObj = self.server.hostingEnvironment.BindService(app)
            appHandle = hostObj.GetHandle()
            appImpl.SetHandle(appHandle)
            log.debug("Restarted app id=%s handle=%s",
                      appImpl.GetId(), appHandle)


    def SetDataStore(self, dataStore):
        """
        Set the Data Store for the Venue. This is usually set to the data
        store the venue server uses.

        **Arguments:**

            *dataStore* Path to the data store.

        """
        self.dataStore = dataStore

    def CleanupClients(self):
        """
        CleanupClients is called by a regularly scheduled task to
        cleanup stale client connections.
        """
        now_sec = time.time()

        users_to_remove = []
        
        self.heartbeatLock.acquire()
        for privateId in self.clients.keys():
            (client, then_sec) = self.clients[privateId]
            
            if abs(now_sec - then_sec) > self.cleanupTime:
                users_to_remove.append(privateId)

        self.heartbeatLock.release()

        for privateId in users_to_remove:
            log.debug("Removing user %s with expired heartbeat time",
                      client.name)

            self.RemoveUser(privateId)

    def ClientHeartbeat(self, event):
        """
        This is an Event handler for heartbeat events. When a
        heartbeat is received from a client we keep track of the
        recieve time. This is important because there is an active
        thread that is cleaning up inactive connections (ones who's
        heartbeats haven't been seen for some time).

        **Arguments:**

            *privateId* The privateId of the client who sent the heartbeat.
            
        **Raises:**

            *ClientNotFound* This is raised when we get a heartbeat
            for a client that we don't know about.
        """
        now = time.time()
        privateId = event.data
        
        # log.debug("Got Client Heartbeat for %s at %s." % (privateId, now))

        if event.venue != self.uniqueId:
            log.info("ClientHeartbeat: Received heartbeat for a different venue %s", event.venue)
       
        if self.clients.has_key(privateId):
            self.heartbeatLock.acquire()

            (profile, heartbeatTime) = self.clients[privateId]
            self.clients[privateId] = (profile, now)

            self.heartbeatLock.release()
        else:
            log.debug("ClientHeartbeat: Got heartbeat for missing client")
    
    def EventServiceDisconnect(self, event):
        """
        This is an Event handler for Disconnect events. This keeps the
        Venue cleaned up by removing users that disconnect.
        
        **Arguments:**

            *privateId* The private id of the user disconnecting.
        """
        privateId = event.data
        log.debug("VenueServer: Got Client disconnect for %s venue=%s", privateId, event.venue)
        if event.venue != self.uniqueId:
            log.info("ClientHeartbeat: Received client disconnect for a different venue %s", event.venue)

        #
        # We don't lock here; RemoveUser handles the locking.
        #

        if privateId in self.clientDisconnectOK and self.clientDisconnectOK[privateId]:
            log.debug("Got disconnect, but I'm okay")
            del self.clientDisconnectOK[privateId]
        else:
            self.RemoveUser(privateId)
        
    def EventServiceClientExits(self, event):
        """
        This is an Event handler for normal client exits.
        
        **Arguments:**

            *privateId* The private id of the user disconnecting.
        """
        privateId = event.data
        if event.venue != self.uniqueId:
            log.info("ClientHeartbeat: Received client exits for a different venue %s", event.venue)
        log.debug("VenueServer: Got Client exiting for %s", privateId)

        self.clientDisconnectOK[privateId] = 1
        
    def Shutdown(self):
        """
        This method cleanly shuts down all active threads associated with the
        Virtual Venue. Currently there are a few threads in the Event
        Service.
        """

    def NegotiateCapabilities(self, clientProfile, privateId):
        """
        This method takes a client profile and matching privateId, then it
        finds a set of streams that matches the client profile. Later this
        method could use network services to find The Best Match of all the
        network services, the existing streams, and all the client
        capabilities.

        **Arguments:**

            *clientProfile* The profile of the client that needs to
            have capabilities negotiated.

            *privateId* The privateId of the client associated with
            the client profile passed in.

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

                # add user as producer of new stream
                if not matchesExistingStream:
                    capability = Capability( clientCapability.role,
                                             clientCapability.type )
                    capability.parms = clientCapability.parms

                    addr = self.AllocateMulticastLocation()
                    streamDesc = StreamDescription( self.name,
                                                    addr,
                                                    capability, 
                                                    self.encryptMedia, 
                                                    self.encryptionKey,
                                                    0)
                    log.debug("added user as producer of non-existent stream")
                    self.streamList.AddStreamProducer( privateId,
                                                       streamDesc )

                    # Distribute event announcing new stream
                    self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.ADD_STREAM,
                                                    self.uniqueId,
                                                    streamDesc ) )



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

        **Returns:**

            *location* A new multicast network location object.
        """
        defaultTtl = 127
        location = MulticastNetworkLocation(
            self.server.multicastAddressAllocator.AllocateAddress(),
            self.server.multicastAddressAllocator.AllocatePort(),
            defaultTtl )

        return location

    def GetNextPrivateId( self ):
        """
        This method creates the next Private Id.

        **Returns:**

            *privateId* A unique private id.
        """

        privateId = str(GUID())

        return privateId

    def FindUserByProfile(self, profile):
        """
        Find out if a given client is in the venue from their client profile.
        If they are, return their private id, if not, return None.

        **Arguments:**

            *profile* The client profile of the user being searched for.

        **Returns:**

            *privateId* if the user is found

            *None* if the user is not found

        """
        for privateId in self.clients.keys():
            (client, heartbeatTime) = self.clients[privateId]
            
            if client.publicId == profile.publicId:
                return privateId

        return None

    def RemoveUser(self, privateId):
        """
        This method removes a user from the venue, cleaning up all the
        state associated with that user.

        **Arguments:**

            *privateId* The private Id of the user being removed.

        """

        self.clientsBeingRemovedLock.acquire()

        if privateId in self.clientsBeingRemoved and self.clientsBeingRemoved[privateId]:
            log.debug("RemoveUser: private id %s already being removed", privateId)
            self.clientsBeingRemovedLock.release()
            return

        self.clientsBeingRemoved[privateId] = 1
        self.clientsBeingRemovedLock.release()

        self.simpleLock.acquire()
        
        try:
            # Remove user as stream producer
            log.debug("Called RemoveUser on %s", privateId)
            self.streamList.RemoveProducer(privateId)

            # Remove clients from venue
            if not self.clients.has_key(privateId):
                log.warn("RemoveUser: Tried to remove a client that doesn't exist")
                self.simpleLock.release()
                return

            self.heartbeatLock.acquire()
            client, heartbeatTime = self.clients[privateId]
            self.heartbeatLock.release()
            
            # Remove clients private data
            for description in self.data.values():
                
                if description.type == client.publicId:
                    log.debug("RemoveUser: Remove private data %s"
                              % description.name)

                    # Send the event
                    self.server.eventService.Distribute( self.uniqueId,
                                                         Event( Event.REMOVE_DATA,
                                                                self.uniqueId,
                                                                description) )
                    
                    del self.data[description.name]
                   
            # Distribute event
            clientProfile, heartbeatTime = self.clients[privateId]
            
            log.debug("RemoveUser: Distribute EXIT event")
            
            self.server.eventService.Distribute( self.uniqueId,
                                                 Event( Event.EXIT,
                                                        self.uniqueId,
                                                        clientProfile ) )
            del self.clients[privateId]
        except:
            log.exception("Venue.RemoveUser: Body of method threw exception")

        self.clientsBeingRemovedLock.acquire()
        del self.clientsBeingRemoved[privateId]
        self.clientsBeingRemovedLock.release()

        self.simpleLock.release()

    def SetConnections(self, connectionDict):
        """
        SetConnections is a convenient aggregate accessor for the list of
        connections for this venue. Alternatively the user could iterate over
        a list of connections adding them one by one, but this is more
        desirable.

        **Arguments:**

            *connectionDict* A dictionary of connections.
        """
        log.debug("Calling SetConnections.")
        
        self.connections = connectionDict
            
        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.SET_CONNECTIONS,
                                                    self.uniqueId,
                                                    connectionDict.values() ) )

    def Enter(self, clientProfile):
        """
        The Enter method is used by a VenueClient to gain access to the
        services, clients, and content found within a Virtual Venue.

        **Arguments:**

            *clientProfile* The profile of the client entering the venue.
            
        **Returns:**

            *(state, privateId, streamDescriptions)* This tuple is
            returned upon success. The state is a snapshot of the
            current venuestate. The privateId is a private, unique id
            assigned by the venue for this client session, the
            streamDescriptions are the stream descriptions the venue
            has found best match this clients capabilities.
        """
        log.debug("Enter called.")
        
        privateId = None
        
        # First we search for this user
        # privateId = self.FindUserByProfile(clientProfile)

        # If we don't find them, we assign a new id
        if privateId == None:
            privateId = self.GetNextPrivateId()
            log.debug("Enter: Assigning private id: %s", privateId)
        else:
            log.debug("Enter: Client already in venue: %s", privateId)
            # raise ClientAlreadyPresent

        # reset connection information
        self.clients[privateId] = (clientProfile, time.time())
        
        # negotiate to get stream descriptions to return
        streamDescriptions = self.NegotiateCapabilities(clientProfile,
                                                            privateId)

        log.debug("Current users:")
        for prof, tm in self.clients.values():
            log.debug("  name=%s time=%s pubId=%s", prof.name, tm, prof.publicId)
        log.debug("Enter: Distribute enter event ")

        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.ENTER,
                                                    self.uniqueId,
                                                    clientProfile ) )

        try:
            state = self.AsVenueState()
            log.debug("state: %s", state)
        except:
            log.exception("Enter: Can't get state.")
            raise InvalidVenueState
        
        return ( state, privateId, streamDescriptions )

    def AddData(self, dataDescription ):
        """
        The AddData method enables VenuesClients to put data in the Virtual
        Venue. Data put in the Virtual Venue through AddData is persistently
        stored.

        **Arguments:**

            *dataDescription* A real data description.
            
        **Raises:**

            *DataAlreadyPresent* Raised when data is added with the
            same name as data already in the venue.
            
        **Returns:**

            *dataDescription* upon successfully adding the data.
        """
        name = dataDescription.name
              
        log.debug("AddData with name %s " %name)
             
        if self.data.has_key(name):
            log.exception("AddData: data already present: %s", name)
            raise DataAlreadyPresent

        self.data[name] = dataDescription
        
        log.debug("AddData: Distribute ADD_DATA event %s", dataDescription)
        
        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.ADD_DATA,
                                                    self.uniqueId,
                                                    dataDescription ) )
        return dataDescription
        
    def RemoveData(self, dataDescription):
        """
        RemoveData removes persistent data from the Virtual Venue.

        **Arguments:**

            *dataDescription* A real data description.
            
        **Raises:**

            *DataNotFound* Raised when the data is not found in the Venue.

        **Returns:**

            *dataDescription* Upon successfully removing the data.
        """
        name = dataDescription.name
        
        if not name in self.data:
            self.simpleLock.release()
            log.exception("RemoveData: Data not found.")
            raise DataNotFound

        del self.data[ dataDescription.name ]
            
        # This is venue resident so delete the file
        if(dataDescription.type is None or dataDescription.type == "None"):
            self.dataStore.DeleteFile(dataDescription.name)
                
        # Send the event
        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.REMOVE_DATA,
                                                    self.uniqueId,
                                                    dataDescription ) )
        return dataDescription
    
    def UpdateData(self, dataDescription):
        """
        Replace the current description for dataDescription.name with
        this one.

        **Arguments:**

            *dataDescription* A real data description.
            
        **Raises:**

            *DataNotFound* Raised when the data is not found in the Venue.

        **Returns:**

            *dataDescription* Upon successfully updating the data.
        """

        name = dataDescription.name

        if not self.data.has_key(name):
            log.exception("UpdateData: data not already present: %s", name)
            raise DataNotFound

        log.debug("Checking file %s for validity", name)
        url = self.dataStore.GetDownloadDescriptor(name)
        if url is None:
            log.warn("File %s has vanished", name)
            del self.data[name]
        else:
            dataDescription.SetURI(url)
            self.data[dataDescription.name] = dataDescription

        log.debug("Distribute UPDATE_DATA event %s", dataDescription)

        self.server.eventService.Distribute( self.uniqueId,
                                      Event( Event.UPDATE_DATA,
                                             self.uniqueId,
                                             dataDescription ) )

    def GetData(self, name):
        """
        GetData is the method called by a VenueClient to retrieve information
        about the data. This might also be the operation that the VenueClient
        uses to actually retrieve the real data.

        If there's not a running datastore we have to return a null
        string, because SOAP doesn't serialize None correctly.

        **Arguments:**

            *name* The name of the data to be retrieved.
            
        **Returns:**

            *dataDescription* A real data description that corresponds
            to the name passed in.

            *empty string* When the data is not found, or there is no
            data store running.

        """
        if self.dataStore is None:
            return ''

        if self.data.has_key(name):
            return self.data[name]
        else:
            return ''

    def AddService(self, serviceDescription):
        """
        The AddService method enables VenuesClients to put services in
        the Virtual Venue. Service put in the Virtual Venue through
        AddService is persistently stored.

        **Arguments:**

            *serviceDescription* A real service description.
            
        **Raises:**

            *ServiceAlreadyPresent* Raised when a service is added twice.
            
        **Returns:**

            *serviceDescription* Upon successfully adding the service.
        """

        name = serviceDescription.name

        if self.services.has_key(name):
            self.simpleLock.release()
            log.exception("AddService: service already present: %s", name)
            raise ServiceAlreadyPresent

        self.services[serviceDescription.name] = serviceDescription

        log.debug("Distribute ADD_SERVICE event %s", serviceDescription)

        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.ADD_SERVICE,
                                                    self.uniqueId,
                                                    serviceDescription ) )

        return serviceDescription

    def RemoveService(self, serviceDescription):
        """
        RemoveService removes persistent service from the Virtual Venue.

        **Arguments:**

            *serviceDescription* A real service description.
            
        **Raises:**

            *ServiceNotFound* When a service not present is removed.
        
        **Returns:**

            *serviceDescription* Upon successfully removing the service.
        """
        if not serviceDescription.name in self.services:
            self.simpleLock.release()
            log.exception("Service not found!")
            raise ServiceNotFound

        del self.services[serviceDescription.name ]

        log.debug("Distribute REMOVE_SERVICE event %s", serviceDescription)

        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.REMOVE_SERVICE,
                                                    self.uniqueId,
                                                    serviceDescription ) )

        return serviceDescription
    #
    # Interface methods
    #

    def wsAddData(self, dataDescriptionStruct ):
        """
        Interface to Add data to the Venue.
        
        **Arguments:**

            *dataDescriptionStruct* The Data Description that's now an
            anonymous struct that is being added to the venue.

        **Raises:**

            *BadDataDescription* This is raised if the data
            description struct cannot be converted to a real data
            description.
            
        **Returns:**

            *dataDescription* A data description is returned on success.
        """        
        log.debug("wsAddData")

        # if not self._Authorize():
        #    raise NotAuthorized

        try:
            dataDescription = CreateDataDescription(dataDescriptionStruct)
        except:
            log.exception("wsAddData: Bad Data Description.")
            raise BadDataDescription

        try:
            self.simpleLock.acquire()

            returnValue = self.AddData(dataDescription)

            self.simpleLock.release()
        
            return returnValue
        except:
            self.simpleLock.release()
            log.exception("wsAddData: exception")
            raise

    wsAddData.soap_export_as = "AddData"

    def wsRemoveData(self, dataDescriptionStruct ):
        """
        Interface for removing data.
        
        **Arguments:**

            *dataDescriptionStruct* The Data Description that's now an
            anonymous struct that is being added to the venue.

        **Raises:**

            *BadDataDescription* This is raised if the data
            description struct cannot be converted to a real data
            description.

        **Returns:**

            *dataDescription* A data description is returned on success.
        """
        log.debug("wsRemoveData")
        
        # if not self._Authorize():
        #     raise NotAuthorized
        
        try:
            dataDescription = CreateDataDescription(dataDescriptionStruct)
        except:
            log.exception("wsRemoveData: Bad Data Description.")
            raise BadDataDescription

        try:
            self.simpleLock.acquire()
        
            returnValue = self.RemoveData(dataDescription)

            self.simpleLock.release()
        
            return returnValue
        except:
            self.simpleLock.release()
            log.exception("wsRemoveData: exception")
            raise

    wsRemoveData.soap_export_as = "RemoveData"

    def wsUpdateData(self, dataDescriptionStruct):
        """
        Interface to update data that's in the venue with new data
        (and/or description?)

        **Arguments:**

            *dataDescriptionStruct* The Data Description that's now an
            anonymous struct that is being added to the venue.

        **Raises:**

            *BadDataDescription* This is raised if the data
            description struct cannot be converted to a real data
            description.

        **Returns:**

            *dataDescription* A data description is returned on success.
        """
        log.debug("wsUpdateData")

        # if not self._Authorize():
        #    raise NotAuthorized

        try:
            dataDescription = CreateDataDescription(dataDescriptionStruct)
        except:
            log.exception("wsUpdateData: Bad data description.")
            raise BadDataDescription

        try:
            self.simpleLock.acquire()
        
            returnValue = self.UpdateData(dataDescription)

            self.simpleLock.release()
        
            return returnValue
        except:
            self.simpleLock.release()
            log.exception("wsUpdateData: exception")
            raise

    wsUpdateData.soap_export_as = "UpdateData"

    def wsGetData(self, name):
        """
        Interface to retrieve data from the data store.
        
        **Arguments:**

            *name* The name of the data to be retrieved.
            
        **Returns:**

            *dataDescription* A data description is returned on success.

            - or -
            
            *empty string* If the data is not found or there is no
            data store, then an empty string is returned, because SOAP
            doesn't serialize None correctly.

        """
        log.debug("wsGetData")

        try:
            self.simpleLock.acquire()
        
            returnValue = self.GetData(name)

            self.simpleLock.release()

            return returnValue
        except:
            self.simpleLock.release()
            log.exception("wsGetData: exception")
            raise

    wsGetData.soap_export_as = "GetData"

    def wsAddService(self, servDescStruct ):
        """
        Interface to add a service to the venue.
        
        **Arguments:**

            *servDescStruct* an anonymous struct that contains a
            service description.

        **Raises:**

            *BadServiceDescription* This is raised if the anonymous
            struct can't be converted to a real service description.

        **Returns:**

            *serviceDescription* A service description is returned on success.
            
        """
        log.debug("wsAddService")
        
        # if not self._Authorize():
        #     raise NotAuthorized

        try:
            serviceDescription = CreateServiceDescription(servDescStruct)
        except:
            log.exception("wsAddService: Bad service description.")
            raise BadServiceDescription

        try:
            self.simpleLock.acquire()
         
            returnValue = self.AddService(serviceDescription)

            self.simpleLock.release()
         
            return returnValue
        except:
            self.simpleLock.release()
            log.exception("wsAddService: exception")
            raise
     
    wsAddService.soap_export_as = "AddService"

    def wsRemoveService(self, servDescStruct ):
        """
        Interface to remove a service from the venue.
        
        **Arguments:**

            *servDescStruct* an anonymous struct that contains a
            service description.

        **Raises:**

            *BadServiceDescription* This is raised if the anonymous
            struct can't be converted to a real service description.

        **Returns:**

            *serviceDescription* A service description is returned on success.
            
        """
        log.debug("wsRemoveService")
        
        # if not self._Authorize():
        #     raise NotAuthorized

        try:
            serviceDescription = CreateServiceDescription(servDescStruct)
        except:
            log.exception("wsRemoveService: Bad service description.")
            raise BadServiceDescription

        try:
            self.simpleLock.acquire()
            
            returnValue = self.RemoveService(serviceDescription)
            
            self.simpleLock.release()
        
            return returnValue
        except:
            self.simpleLock.release()
            log.exception("wsRemoveService: exception")
            raise
            
    wsRemoveService.soap_export_as = "RemoveService"

    def wsSetConnections(self, connectionList):
        """
        Interface for setting all the connections in a venue in a single call.
        
        **Arguments:**

            *connectionList* a list of connection descriptions that
            have been converted to anonymous structs by the SOAP
            module.
            
        **Raises:**
            
            *BadConnectionDescription* This is raised when an
            anonymous struct is not converted to a real connection
            description.
        """
        if not self._Authorize():
            raise NotAuthorized

        for connection in connectionList:
            c = ConnectionDescription(connection.name,
                                      connection.description,
                                      connection.uri)

            if c == None:
                log.exception("wsSetConnections: Bad connection description.")
                raise BadConnectionDescription
                
            try:
                self.simpleLock.acquire()
                
                self.AddConnection(c)       
                
                self.simpleLock.release()
            except:
                self.simpleLock.release()
                log.exception("wsSetConnections: exception")
                raise
        
    wsSetConnections.soap_export_as = "SetConnections"

    def wsAddConnection(self, connectionDescStruct):
        """
        AddConnection allows an administrator to add a connection to a
        virtual venue to this virtual venue.

        **Arguments:**

            *ConnectionDescriptionStruct* An anonymous struct
            containing a connection description.

        **Raises:**

            *NotAuthorized* Raised when the caller is not an administrator.

            *BadConnectionDescription* Raised when the connection
            description struct is not successfully converted to a
            connection description.
        """
        if not self._Authorize():
            raise NotAuthorized

        c = ConnectionDescription(connectionDescStruct.name,
                                  connectionDescStruct.description,
                                  connectionDescStruct.uri)
        
        if c == None:
            log.exception("AddConnection: Bad connection description.")
            raise BadConnectionDescription

        try:
            self.simpleLock.acquire()

            self.AddConnection(c)
        
            self.simpleLock.release()
        except:
            self.simpleLock.release()
            log.exception("wsAddConnection: exception")
            raise
        
    wsAddConnection.soap_export_as = "AddConnection"
    
    def wsEnter(self, clientProfileStruct):
        """
        Interface used to enter a Virtual Venue.
        
        **Arguments:**

            *clientProfileStruct* An anonymous struct containing a
            client profile.

        **Raises:**

            *InvalidClientProfileException* This is raised when the client
            profile is not successfully converted to a real client
            profile.
            
        **Returns:**

            *(state, privateId, streamDescriptions)* This tuple is
            returned to the client on success. The state is the
            current state of the Virtual Venue and includes locations
            for the text and event services. The private Id is a venue
            assigned private id for the lifetime of this client
            session. The stream descriptions are the result of the
            venue negotiating the client capabilities.

        """        
        # Authorization management.
        #
        # Get the security manager for this invocation. This will tell
        # us how the user was authenticated for this call.
        #
        # To check to see whether this user can even enter, see if
        # he is in the AllowedEntry role
        #

        # sm = AccessControl.GetSecurityManager()
        # if  sm.ValidateRole(self.AllowedEntryRole):
        #     subject = sm.GetSubject()
        
        #     if self.VenueUsersRole.HasSubject(subject):
        #         log.info("User %s validated for entry to %s", subject, self)
        #         self.VenueUsersRole.AddSubject(subject)
        #     else:
        #         log.info("User %s rejected for entry to %s",
        #                   sm.GetSubject(), self)
        #         raise VenueException("Entry denied")

        log.debug("wsEnter: Called.")
        
        clientProfile = CreateClientProfile(clientProfileStruct)

        if clientProfile == None:
            raise InvalidClientProfileException

        clientProfile.distinguishedName = AccessControl.GetSecurityManager().GetSubject().GetName()

        try:
            self.simpleLock.acquire()
        
            returnValue = self.Enter(clientProfile)

            self.simpleLock.release()

            return returnValue
        except:
            self.simpleLock.release()
            log.exception("wsEnter: exception")
            raise
    
    wsEnter.soap_export_as = "Enter"

    # 
    # Management methods
    # Need to make these interface methods, for mgmt
    #
    
    def AddAdministrator(self, string):
        """
        Interface to add an administrator to this venue.
        
        **Arguments:**

            *string* The Distinguished Name (DN) of the new administrator.
            
        **Raises:**

            *NotAuthorized* This is raised when the caller is not an
            administrator.

            *AdministratorAlreadyPresent* This is raised when an
            administrator is added a second time.
            
        **Returns:**

            *string* the Distinguished Name (DN) of the administrator added.

        """
        if not self._Authorize():
            raise NotAuthorized
        
        if string not in self.administrators:
            self.simpleLock.acquire()
            
            self.administrators.append(string)

            self.simpleLock.release()
            
            return string
        else:
            log.exception("AddAdministrator: Administrator already present")
            raise AdministratorAlreadyPresent

    AddAdministrator.soap_export_as = "AddAdministrator"

    def RemoveAdministrator(self, string):
        """
        Interface for removing an administrator from the venue.
        
        **Arguments:**

            *string* The Dinstinguished Name (DN) of the administrator
            to be removed.

        **Raises:**

            *NotAuthorized* This is raised when the caller is not an
            administrator.

            *AdministratorNotFound* This is raised when the
            administrator specified is not an administrator on this
            venue.

        **Returns:**

            *string* The Distinguished Name (DN) of the administrator removed.

        """
        if not self._Authorize():
            raise NotAuthorized

        if not string in self.administrators:
            log.exception("RemoveAdministrator: Administrator not found")
            raise AdministratorNotFound

        self.simpleLock.acquire()
            
        self.administrators.remove(string)

        self.simpleLock.release()
            
        return string

    RemoveAdministrator.soap_export_as = "RemoveAdministrator"

    def SetAdministrators(self, administratorList):
        """
        Interface to add a list of administrators.

        **Arguments:**

            *administratorList* This is a list of Distinguished Names (DNs).
            
        **Raises:**

            *NotAuthorized* This is raised if the caller is not an
            administrator.
        """
        if not self._Authorize():
            raise NotAuthorized

        self.simpleLock.acquire()
        
        self.administrators = self.administrators + administratorList

        self.simpleLock.release()

    SetAdministrators.soap_export_as = "SetAdministrators"

    def GetAdministrators(self):
        """
        Interface to get the list of administrators for the venue.
        """
        self.simpleLock.acquire()
        
        returnValue = self.administrators

        self.simpleLock.release()

        return returnValue

    GetAdministrators.soap_export_as = "GetAdministrators"

    def SetEncryptMedia(self, value, key=None):
        """
        Turn media encryption on or off.

        **Arguments:**

            *value* Flag indicating whether encryption should be on or off.

            *key=None* An optional key for encryption, if not
            provided, and the value is 1, then one is created.

        **Raises:**

            *NotAuthorized* Raised when the caller is not an administrator.

        **Returns:**

            *value* The value of the EncryptMedia flag.
        """
        if not self._Authorize():
            raise NotAuthorized

        self.simpleLock.acquire()
        
        self.encryptMedia = value

        if not self.encryptMedia:
            self.encryptionKey = None
        else:
            if key == None or len(key.strip()) == 0:
                key = AllocateEncryptionKey()
            self.encryptionKey = key

        self.simpleLock.release()
        
        return self.encryptMedia

    SetEncryptMedia.soap_export_as = "SetEncryptMedia"

    def GetEncryptMedia(self):
        """
        Return whether we are encrypting streams or not.
        """
        self.simpleLock.acquire()

        returnValue = self.encryptionKey

        self.simpleLock.release()

        return returnValue

    GetEncryptMedia.soap_export_as = "GetEncryptMedia"

    def AddConnection(self, connectionDescription):
        """
        AddConnection allows an administrator to add a connection to a
        virtual venue to this virtual venue.

        **Arguments:**

            *ConnectionDescription* A real connection description to
            be added to this venue.
            
        """
        self.connections[connectionDescription.uri] = connectionDescription
        
        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.ADD_CONNECTION,
                                                    self.uniqueId,
                                                    connectionDescription ) )
        
    def RemoveConnection(self, connectionDescription):
        """
        RemoveConnection removes a connection to another virtual venue
        from this virtual venue. This is an administrative operation.

        **Arguments:**

            *connectionDescriptionStruct* An anonymous struct
            containing a connection description.

        **Raises:**

            *NotAuthorized* Raised when the caller is not an administrator.

            *ConnectionNotFound* Raised when a connection isn't found
            to be rmeoved.

            *BadConnectionDescription* Raised when the connection
            description struct is not successfully converted to a
            connection description.
        """
        if not self._Authorize():
            raise NotAuthorized

        c = ConnectionDescription(connectionDescription.name,
                                  connectionDescription.description,
                                  connectionDescription.uri)
        
        if c == None:
            log.exception("RemoveConnection: Bad connection description.")
            raise BadConnectionDescription
        
        if not self.connections.has_key(connectionDescription.uri):
            log.exception("RemoveConnection: Connection not found.")
            raise ConnectionNotFound
        else:
            self.simpleLock.acquire()
            
            del self.connections[connectionDescription.uri]

            self.simpleLock.release()
            
            self.server.eventService.Distribute( self.uniqueId,
                                                 Event( Event.REMOVE_CONNECTION,
                                                        self.uniqueId,
                                                        connectionDescription ) )

    RemoveConnection.soap_export_as = "RemoveConnection"

    def GetConnections(self):
        """
        GetConnections returns a list of all the connections to other venues
        that are found within this venue.

        **Returns:**

            *ConnectionList* A list of connection descriptions.
        """
        log.debug("Calling GetConnections.")

        self.simpleLock.acquire()
        
        returnValue = self.connections.values()

        self.simpleLock.release()

        return returnValue

    GetConnections.soap_export_as = "GetConnections"

    def SetDescription(self, description):
        """
        SetDescription allows an administrator to set the venues description
        to something new.

        **Arguments:**

            *description* New description for this venue.
        """
        if not self._Authorize():
            raise NotAuthorized

        self.simpleLock.acquire()
        
        self.description = description

        self.simpleLock.release()
        
    SetDescription.soap_export_as = "SetDescription"

    def GetDescription(self):
        """
        GetDescription returns the description for the virtual venue.
        **Arguments:**
        """
        return self.description
    
    GetDescription.soap_export_as = "GetDescription"

    def SetName(self, name):
        """
        SetName allows an administrator to set the venues name
        to something new.

        **Arguments:**

            *name* New name for this venue.
        """
        if not self._Authorize():
            raise NotAuthorized

        self.simpleLock.acquire()
        
        self.name = name

        self.simpleLock.release()
        
    SetName.soap_export_as = "SetName"

    def GetName(self):
        """
        GetName returns the name for the virtual venue.
        """
        return self.name
    
    GetName.soap_export_as = "GetName"

    def AddStream(self, inStreamDescription ):
        """
        Add a stream to the list of streams for this venue.
        
        **Arguments:**

            *inStreamDescription* An anonymous struct containing a
            stream description.

        **Raises:**

            *NotAuthorized* This is raised when the caller is not an
            administrator.
            
            *BadStreamDescription* This is raised when the struct
            passed in cannot be successfully converted to a real
            Stream Description.
        """
        if not self._Authorize():
            raise NotAuthorized

        log.debug("%s - Adding Stream: ", self.uniqueId)

        streamDescription = CreateStreamDescription( inStreamDescription )

        if streamDescription == None:
            log.exception("AddStream: Bad stream description.")
            raise BadStreamDescription
        
        self.simpleLock.acquire()
        
        self.streamList.AddStream( streamDescription )

        self.simpleLock.release()
        
    AddStream.soap_export_as = "AddStream"

    def RemoveStream(self, inStreamDescription):
        """
        Remove the given stream from the venue

        **Arguments:**

            *inStreamDescription* An anonymous struct containing a
            stream description to be removed.
            
        **Raises:**

            *NotAuthorized* This is raised when the caller is not an
            administrator.
            
            *BadStreamDescription* This is raised when the struct
            passed in cannot be successfully converted to a real
            Stream Description.
        """
        if not self._Authorize():
            raise NotAuthorized
        
        streamDescription = CreateStreamDescription( inStreamDescription )

        if streamDescription == None:
            log.exception("RemoveStream: Bad stream description.")
            raise BadStreamDescription

        self.simpleLock.acquire()
        
        self.streamList.RemoveStream( streamDescription )

        self.simpleLock.release()

    RemoveStream.soap_export_as = "RemoveStream"

    def GetStreams(self):
        """
        GetStreams returns a list of stream descriptions to the caller.
        """
        self.simpleLock.acquire()
        
        returnValue = self.streamList.GetStreams()

        self.simpleLock.release()

        return returnValue
    
    GetStreams.soap_export_as = "GetStreams"

    def GetStaticStreams(self):
        """
        GetStaticStreams returns a list of static stream descriptions
        to the caller.
        """
        self.simpleLock.acquire()
        
        returnValue = self.streamList.GetStaticStreams()

        self.simpleLock.release()

        return returnValue
    
    GetStaticStreams.soap_export_as = "GetStaticStreams"

    # Client Methods
    def Exit(self, privateId ):
        """
        The Exit method is used by a VenueClient to cleanly leave a Virtual
        Venue. Cleanly leaving a Virtual Venue allows the Venue to cleanup
        any state associated (or caused by) the VenueClients presence.

        **Arguments:**

            *privateId* The privateId of the client to be removed from
            the venue.

        **Raises:**

            *ClientNotFound* Raised when a privateId is not found in
            the venues list of clients.
        """
        log.debug("Called Venue Exit on %s", privateId)
            
        if not self.clients.has_key( privateId ):
            log.exception("Exit: User not found!")
            raise ClientNotFound
        
        self.RemoveUser(privateId)

    Exit.soap_export_as = "Exit"

    def UpdateClientProfile(self, clientProfileStruct ):
        """
        UpdateClientProfile allows a VenueClient to update/modify the client
        profile that is stored by the Virtual Venue that they gave to the Venue
        when they called the Enter method.

        **Arguments:**

            *clientProfileStruct* An anonymous struct containing a
            client profile.

        **Raises:**

            *InvalidClientProfileException* Raised when the client
            profile struct cannot be converted to a real client
            profile.
        """

        clientProfile = CreateClientProfile( clientProfileStruct )

        if clientProfile == None:
            log.exception("UpdatelClientProfile: Invalid client profile.")
            raise InvalidClientProfileException
        
        log.debug("Called UpdateClientProfile on %s " %clientProfile.name)

        for privateId in self.clients.keys():
            client, heartbeatTime = self.clients[privateId]

            if client.publicId == clientProfile.publicId:
                self.clients[privateId] = (clientProfile, time.time())

        log.debug("Distribute MODIFY_USER event")

        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.MODIFY_USER,
                                                    self.uniqueId,
                                                    clientProfile ) )
        
    UpdateClientProfile.soap_export_as = "UpdateClientProfile"

    def GetUploadDescriptor(self):
        """
        Retrieve the upload descriptor from the Venue's datastore.

        **Arguments:**

        **Raises:**
        
        **Returns:**

            *upload description* the upload descriptor for the data store.

            *''* If there is not data store we return an empty string,
            because None doesn't serialize right with our SOAP
            implementation.
        """
        if self.dataStore is None:
            returnValue = ''
        else:
            returnValue = self.dataStore.GetUploadDescriptor()

        return returnValue
    
    GetUploadDescriptor.soap_export_as = "GetUploadDescriptor"

    def GetApplication(self, id):
        """
        Return the application state for the given application object.

        **Arguments:**

            *id* The id of the application being retrieved.
            
        **Raises:**

            *ApplicationNotFound* Raised when the application is not
            found in the venue.

        **Returns:**

            *appState* The state of the application object.
        """
        if not self.applications.has_key(id):
            log.exception("GetApplication: Application not found.")
            raise ApplicationNotFound

        app = self.applications[id]
        returnValue = app.GetState()

        return returnValue
    
    GetApplication.soap_export_as = "GetApplication"

    def CreateApplication(self, name, description, mimeType, id = None ):
        """
        Create a new application object.  Initialize the
        implementation, and create a web service interface for it.

        **Arguments:**

            *name* A name for the application instance.

            *description* A description for the new application instance.

            *mimeType* A mime-type for the new application, used to
            match applications with clients.
        
        **Returns:**

            *appHandle* A url to the new application object/service.
        """
        
        log.debug("CreateApplication: name=%s description=%s",
                  name, description)

        appImpl = AppService.CreateApplication(name, description, mimeType, 
                                           self.server.eventService, id)
        app = AppService.AppObject(appImpl)

        hostObj = self.server.hostingEnvironment.BindService(app)
        appHandle = hostObj.GetHandle()
        appImpl.SetHandle(appHandle)

        self.applications[appImpl.GetId()] = appImpl

        appDesc = appImpl.AsApplicationDescription()
        
        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.ADD_APPLICATION,
                                                    self.uniqueId,
                                                    appDesc ) )
        
        log.debug("CreateApplication: Created id=%s handle=%s",
                  appDesc.id, appDesc.uri)

        return appDesc

    CreateApplication.soap_export_as = "CreateApplication"

    def DestroyApplication(self, appId):
        """
        Destroy an application object.

        **Arguments:**

            *appId* The id of the application object to be destroyed.
            
        **Raises:**

            *ApplicationNotFound* Raised when an application is not
            found for the application id specified.

            *ApplicationUnbindError* Raised when the hosting
            environment can't unbind the application from the web
            service layer.
        """
        # Get the application object
        try:
            app = self.applications[appId]
        except KeyError:
            log.exception("DestroyApp: Application not found.")
            raise ApplicationNotFound

        # Stop the web service interface
        try:
            self.server.hostingEnvironment.UnbindService(app)
        except:
            log.exception("DestroyApp: Unbind failed for application.")
            raise ApplicationUnbindError

        # Shut down the application
        app.Shutdown()

        # Create the application description
        appImpl = self.applications[appId]
        ad = ApplicationDescription(appImpl.GetId(), appImpl.name,
                                    appImpl.description,
                                    appImpl.handle, appImpl.mimeType)

        # Send the remove application event
        self.server.eventService.Distribute(self.uniqueId,
                                            Event(Event.REMOVE_APPLICATION,
                                                  self.uniqueId,
                                                  ad))

        # Get rid of it for good
        del self.applications[appId]

    DestroyApplication.soap_export_as = "DestroyApplication"

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
        """
        Constructor for Stream Description List.
        """
        self.streams = []

    def __RemoveProducer( self, producingUser, inStream ):
        """
        Internal : Remove producer from stream with given index
        """
        streamListItem = self.FindStreamByDescription(inStream)

        if streamListItem != None:
            (stream, producerList) = streamListItem

            if producingUser in producerList:
                producerList.remove( producingUser )

    def AddStream( self, stream ):
        """
        Add a stream to the list, only if it doesn't already exist

        **Arguments:**

           *stream*  A stream description.
           
        **Raises:**

           *StreamAlreadyPresent* This is raised if the stream is
           already present in the Venue.
           
        """
        if not self.FindStreamByDescription(stream):
            self.streams.append( ( stream, [] ) )
        else:
            log.exception("AddStream: Stream already present.")
            raise StreamAlreadyPresent
        
    def RemoveStream( self, stream ):
        """
        Remove a stream from the list

        **Arguments:**

            *stream* A stream description to be removed from the venue.
            
        **Raises:**

            *StreamNotFound* This is raised if the stream description
            is not found in this venue.
            
        """
        streamListItem = self.FindStreamByDescription(stream)

        if streamListItem != None:
            self.streams.remove(streamListItem)
        else:
            log.exception("RemoveStream: Stream not found.")
            raise StreamNotFound

    def AddStreamProducer( self, producingUser, inStream ):
        """
        Add a stream to the list, with the given producer

        **Arguments:**

            *producingUser* A user who is producing media for this
            stream description.

            *inStream* The stream description of the media the user is
            producing.

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

        **Arguments:**

            *producingUser* The user producing the stream.

            *inStream* the Stream descriptino the producing user is
            producing.
        """

        self.__RemoveProducer( producingUser, inStream )
        
        streamListItem = self.FindStreamByDescription(inStream)
        
        if streamListItem != None:
            (streamDesc, producerList) = streamListItem

            if len(producerList) == 0:
                self.streams.remove((streamDesc, producerList))

    def RemoveProducer( self, producingUser ):
        """
        Remove producer from all streams. Then cleanup streams to get
        rid of unused streams.
        
        **Arguments:**

            *producingUser* The user to be removed from all existing
            streams.
        """
        for stream, producerList in self.streams:
            self.__RemoveProducer( producingUser, stream )

        self.CleanupStreams()

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

        **Returns:**

            *streamList* The list of stream descriptions.
        """
        # The magic map/lambda combination
        return map( lambda streamTuple: streamTuple[0], self.streams )

    def GetStaticStreams(self):
        """
        GetStaticStreams returns a list of static stream descriptions
        to the caller.

        **Returns:**
        
            *staticStreams* The list of stream descriptions for the
            static streams in this Venue.
        """
        staticStreams = []

        for stream, producerList in self.streams:
            if stream.static:
                staticStreams.append( stream )

        return staticStreams

    def FindStreamByDescription( self, inStream ):
        """
        This method finds a stream, producerlist tuple by searching for the
        stream description.
        
        **Arguments:**

            *inStream* A stream description to look for.
            
        **Returns:**

            *(stream, producerList)* If found, the stream,
            producerlist tuple is returned.

            *None* If not found.
        """
        # Loop over all the streams
        for stream, producerList in self.streams:

            log.debug("StreamDescriptionList.index Address %s %s",
                      inStream.location.host,
                      stream.location.host)
            log.debug("StreamDescriptionList.index Port %d %d",
                      inStream.location.port,
                      stream.location.port)

            # If the host and port match, this is the stream
            if inStream.location.host == stream.location.host and \
                   inStream.location.port == stream.location.port:
                # So return the (stream, producerList) tuple
                return (stream, producerList)

        # If we got through all the streams and didn't find anything,
        # return None
        return None

