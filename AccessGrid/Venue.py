#-----------------------------------------------------------------------------
# Name:        Venue.py
# Purpose:     The Virtual Venue is the object that provides the collaboration
#               scopes in the Access Grid.
#
# Author:      Ivan R. Judson, Thomas D. Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: Venue.py,v 1.209 2004-07-08 19:13:41 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
The Venue provides the interaction scoping in the Access Grid. This module
defines what the venue is.
"""

__revision__ = "$Id: Venue.py,v 1.209 2004-07-08 19:13:41 turam Exp $"
__docformat__ = "restructuredtext en"

import sys
import time
import re
import string
import socket
import os.path

from threading import Condition, Lock

from AccessGrid import Log
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.Toolkit import Service

from AccessGrid.Security.AuthorizationManager import AuthorizationManager
from AccessGrid.Security.AuthorizationManager import AuthorizationManagerI
from AccessGrid.Security.AuthorizationManager import AuthorizationIMixIn
from AccessGrid.Security.AuthorizationManager import AuthorizationIWMixIn
from AccessGrid.Security.AuthorizationManager import AuthorizationMixIn
from AccessGrid.Security import X509Subject, Role, Subject
from AccessGrid.Security.Subject import SubjectAlreadyPresent

from AccessGrid import DataStore
from AccessGrid import NetService
from AccessGrid.Types import Capability
from AccessGrid.SharedApplication import SharedApplication, SharedApplicationI
from AccessGrid.Descriptions import CreateClientProfile
from AccessGrid.Descriptions import CreateStreamDescription
from AccessGrid.Descriptions import CreateConnectionDescription
from AccessGrid.Descriptions import CreateDataDescription
from AccessGrid.Descriptions import CreateServiceDescription
from AccessGrid.Descriptions import CreateApplicationDescription
from AccessGrid.Descriptions import StreamDescription
from AccessGrid.Descriptions import CreateNetworkLocation
from AccessGrid.Descriptions import ConnectionDescription, VenueDescription
from AccessGrid.Descriptions import ApplicationDescription, ServiceDescription
from AccessGrid.Descriptions import DataDescription, VenueState
from AccessGrid.Descriptions import BadDataDescription, BadServiceDescription
from AccessGrid.Descriptions import BadApplicationDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.GUID import GUID
from AccessGrid.scheduler import Scheduler
from AccessGrid.Events import Event, HeartbeatEvent, DisconnectEvent
from AccessGrid.Events import ClientExitingEvent
from AccessGrid.Events import MarshalledEvent
from AccessGrid.Utilities import AllocateEncryptionKey, ServerLock
from AccessGrid.hosting import PathFromURL
from AccessGrid.Platform.Config import UserConfig, SystemConfig
from AccessGrid.ClientProfile import ClientProfileCache, InvalidProfileException

log = Log.GetLogger(Log.VenueServer)

# Initialize usage log, but set flag so handlers don't include it by default.
usage_log = Log.GetLogger(Log.Usage, defaultHandled=0)

class VenueException(Exception):
    """
    A generic exception type to be raised by the Venue code.
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

class AdministratorRemovingSelf(Exception):
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

class ConnectionAlreadyPresent(Exception):
    """
    This exception is raised when a connection is added the second time.
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

class VenueClientState:
    """
    Instances of the VenueClientState class hold the per-client state that the
    venue cares about. This includes the client's profile, the last time
    a heartbeat was received from the client, the client's connections
    to the text and event services, and any queues of events waiting to be
    delivered to those services (after the client connects, before the
    client's event client connects to the service).
    """

    def __init__(self, venue, privateId, profile):
        self.venue = venue
        self.privateId = privateId
        self.clientProfile = profile
        self.lastHeartbeat = None

        #
        # messageQueue is the queue of events to be delivered
        # to the client's event client when it connects.
        #
        self.messageQueue = []

        #
        # connObj is the event service connection object
        # for this client.
        #
        self.eventConnObj = None
	self.textConnObj = None

    def __repr__(self):
        s = "VenueClientState(name=%s privateID=%s lastHeartbeat=%s)" % (
            self.clientProfile.name, self.privateId, self.lastHeartbeat)
        return s

    def SendEvent(self, marshalledEvent):
        if self.eventConnObj is None:
            log.debug("Enqueue event of type %s for %s",
	            marshalledEvent.GetEvent().eventType,
	            self.clientProfile.GetName())
            self.messageQueue.append(marshalledEvent)
        else:
            log.debug("Send event of type %s for %s",
	            marshalledEvent.GetEvent().eventType,
	            self.clientProfile.GetName())
            self.eventConnObj.writeMarshalledEvent(marshalledEvent)

    def SetConnection(self, connObj):
        """
        We've gotten a connection from the event client.

        Send the accumulated events, if any.
        """

        log.debug("Set connection for %s", self.clientProfile.GetName())


        while len(self.messageQueue) > 0:
            mEvent = self.messageQueue.pop(0)
            log.debug("Send queued event of type %s for %s",
            mEvent.GetEvent().eventType,
            self.clientProfile.GetName())
            log.debug("writing marshalled event %s", mEvent.GetEvent())
            connObj.writeMarshalledEvent(mEvent)

        self.eventConnObj = connObj

    def SetTextConnection(self, conn):
	self.textConnObj = conn

    def CloseEventChannel(self):
        """
        Close down our connection to the event service.
        """

        if self.eventConnObj is not None:
            self.venue.server.eventService.CloseConnection(self.eventConnObj)
        self.eventConnObj = None

    def CloseTextChannel(self):

	if self.textConnObj is not None:
	    self.venue.server.textService.CloseConnection(self.textConnObj)

	self.textConnObj = None

    def UpdateAccessTime(self):
        self.lastHeartbeat = time.time()

    def UpdateClientProfile(self, profile):
        self.clientProfile = profile

    def GetLastHeartbeat(self):
        return self.lastHeartbeat

    def GetTimeSinceLastHeartbeat(self, now):
        return now - self.lastHeartbeat

    def GetPrivateId(self):
        return self.privateId

    def GetPublicId(self):
        return self.clientProfile.GetPublicId()

    def GetClientProfile(self):
        return self.clientProfile

class Venue(AuthorizationMixIn):
    """
    A Virtual Venue is a virtual space for collaboration on the Access Grid.
    """
    def __init__(self, server, name, description, dataStoreLocation,
                 oid=None):
        """
        Venue constructor.
        """
        # pointer to outside world
        self.servicePtr = Service.instance()
        
        if oid:
            self.uniqueId = oid
        else:
            self.uniqueId = str(GUID())

        AuthorizationMixIn.__init__(self)
        allowedEntryRole = Role.Role("AllowedEntry")
        self.AddRequiredRole(allowedEntryRole)
        venueUsersRole = Role.Role("VenueUsers")
        self.AddRequiredRole(venueUsersRole)
        admin = Role.Role("Administrators")
        admin.SetRequireDefault(1)
        self.AddRequiredRole(admin)
        self.AddRequiredRole(Role.Everybody)
        # Default actions for Entry Roles.
        self.defaultEntryActionNames = ["Enter", "Exit", "GetStreams", "GetStaticStreams", "GetUploadDescriptor", "GetRolesForSubject", "CreateApplication", "UpdateApplication", "DestroyApplication", "UpdateClientProfile", "AddService", "RemoveService", "UpdateService", "GetServices", "AddData", "UpdateData", "RemoveData", "GetDataStoreInformation", "GetDataDescriptions", "AddNetworkService", "RemoveNetworkService", "GetNetworkServices", "GetClients", "GetCachedProfiles", "AddConnection", "RemoveConnection", "GetConnections", "SetConnections", "GetEncryptMedia", "GetDescription", "GetName", "GetApplication", "GetApplications", "AddNetworkLocationToStream", "RemoveNetworkLocationFromStream", "GetEventServiceLocation", "DetermineSubjectRoles", "AddNetService", "RemoveNetService", "IsAuthorized", "IsValid"]
        # Methods in Venue IW that are not default to everybody:
        #   "Shutdown", "SetEncryptMedia", "RegenerateEncryptionKeys", "SetDescription", "SetName", "AddStream", "RemoveStream", "ImportAuthorizationPolicy", "AllocateMulticastLocation", "AddSubjectToRole", "RemoveSubjectFromRole", "SetSubjectsInRole", "FlushRoles", "GetUsersInRole", "GetRoleNames"

        # Default actions for VenueUsers Roles.
        self.defaultVenueUserActionNames = []

        admin.AddSubject(self.servicePtr.GetDefaultSubject())
        
        # Set parent auth mgr to server so administrators cascades?

        log.debug("------------ STARTING VENUE")
        self.server = server
        self.name = name
        self.description = description

        if server != None:
            self.encryptMedia = server.GetEncryptAllMedia()
        else:
            self.encryptMedia = 1
            
        if self.encryptMedia:
            self.encryptionKey = AllocateEncryptionKey()
        else:
            self.encryptionKey = None
        self.simpleLock = ServerLock("venue")
        self.heartbeatLock = ServerLock("heartbeat")
        self.clientDisconnectOK = {}
        
        self.cleanupTime = 30

        self.connections = list()
        self.applications = dict()
        self.services = dict()
        self.streamList = StreamDescriptionList()
        self.clients = dict()
        self.netServices = dict()

        #
        # Dictionary keyed on client private id; value
        # true if a remove is in process on this client.
        #
        self.clientsBeingRemoved = {}
        self.clientsBeingRemovedLock = ServerLock("clientRemove")

        self.dataStore = None
        self.producerCapabilities = []
        self.consumerCapabilities = []

        if self.server != None:
            self.uri = self.server.MakeVenueURL(self.uniqueId)

            log.info("Venue URI %s", self.uri)

            self.server.eventService.AddChannel(self.uniqueId,
                                                self.channelAuthCallback)
            self.server.textService.AddChannel(self.uniqueId,
					       self.textChannelAuthCallback)
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

        self.dataStore = DataStore.DataStore(self, self.dataStorePath,
                                             str(self.uniqueId),
                                             self.server.dataTransferServer)
        log.info("Have upload url: %s", self.dataStore.GetUploadDescriptor())

        # Cache server profiles.
        # Store in a server wide location.  You could make this different for
        # each venue if you wanted to track who entered certain venues (secure
        # venues or conference venues for example).
        self.profileCachePrefix = "serverProfileCache"
        userConfig = UserConfig.instance()
        self.profileCachePath = os.path.join(userConfig.GetConfigDir(),
                                             self.profileCachePrefix)

        self.cache = ClientProfileCache(self.profileCachePath)

    #self.StartApplications()

    def __repr__(self):
        """
        A standard repr method to make a string that can be print'd.

        **Returns:**

        *string* Simple string representation of the Venue.
        """
        retStr = "Venue: name=%s id=%s url=%s" % (self.name, id(self),
                                                  self.uri)
        return retStr

    def _AddDefaultRolesToActions(self):
        # Initialize actions with the roles they contain by default.

        # Add default entry roles to entry actions.
        allowedEntryRole = self.authManager.FindRole("AllowedEntry")
        everybodyRole = Role.Everybody
        for actionName in self.defaultEntryActionNames:
            action = self.authManager.FindAction(actionName)
            if action != None:
                if not action.HasRole(allowedEntryRole):
                    action.AddRole(allowedEntryRole)
                if not action.HasRole(everybodyRole):
                    action.AddRole(everybodyRole)
            else:
                raise "DefaultActionNotFound " + actionName

        # Add default entry roles to venueusers actions.
        # Currently no actions include VenueUsers
        venueUsersRole = self.authManager.FindRole("VenueUsers")
        for actionName in self.defaultVenueUserActionNames:
            action = self.authManager.FindAction(actionName)
            if action != None:
                if not action.HasRole(venueUsersRole):
                    action.AddRole(venueUsersRole)
            else:
                raise "DefaultActionNotFound " + actionName

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
        string += "uri  : %s\n" % self.uniqueId
        # Don't store these control characters, but lets make sure we
        # bring them back
        desc = re.sub("\r\n", "<CRLF>", self.description)
        desc = re.sub("\r", "<CR>", desc)
        desc = re.sub("\n", "<LF>", desc)

        string += "description : %s\n" % desc
        string += "encryptMedia : %d\n" % self.encryptMedia
        string += "cleanupTime : %d\n" % self.cleanupTime
        if self.encryptMedia:
            string += "encryptionKey : %s\n" % self.encryptionKey

        # Get the list of connections
        clist = ":".join(map( lambda conn: conn.GetId(), self.connections))
        if len(clist):
            string += "connections : %s\n" % clist

        # Get the list of streams
        slist = ":".join(map( lambda stream: stream.GetId(),
        self.streamList.GetStaticStreams() ))
        if len(slist):
            string += "streams : %s\n" % slist

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
                                  self.connections))

        if len(slist):
            string += "".join(map(lambda stream: stream.AsINIBlock(),
                                  self.streamList.GetStaticStreams()))

        if len(alist):
            string += "".join(map(lambda app: app.AsINIBlock(),
                                  self.applications.values()))

        if len(servlist):
            string += "".join(map(lambda service: service.AsINIBlock(),
                                  self.services.values()))

        policy = self.authManager.ExportPolicy()
        # Don't store these control characters, but lets make sure we
        # bring them back
        policy = re.sub("\r\n", "<CRLF>", policy)
        policy = re.sub("\r", "<CR>", policy)
        policy = re.sub("\n", "<LF>", policy)
        string += 'authorizationPolicy : %s' %policy
        
        return string

    def ImportAuthorizationPolicy(self, policy):
        """
        This method takes a string that is an XML representation of an
        authorization policy. This policy is parsed and this object is
        configured to enforce the specified policy.

        @param policy: the policy as a string
        @type policy: an XML formatted string
        """
        self.authManager.ImportPolicy(policy)

    def AsVenueDescription(self):
        """
        This creates a Venue Description filled in with the data from
        this venue.
        """
        desc = VenueDescription(self.name, self.description,
                                (self.encryptMedia, self.encryptionKey),
                                self.connections,
                                self.GetStaticStreams())
        uri = self.server.MakeVenueURL(self.uniqueId)
        desc.SetURI(uri)

        return desc

    def AsVenueState(self):
        """
        This creates a Venue State filled in with the data from this
        venue.
        """

        try:
            dList = self.dataStore.GetDataDescriptions()
        except:
            log.exception("Venue::AsVenueState: Failed to get data descrs.")
            dList = []

        try:
            applist = map(lambda x: x.AsApplicationDescription(),
                          self.applications.values())
        except:
            log.exception("Venue::AsVenueState: Failed to get applications.")
            applist = []
            
        try:
            clientlist = map(lambda c: c.GetClientProfile(),
                             self.clients.values())
        except:
            log.exception("Venue::AsVenueState: Failed to get profiles.")
            clientlist = []

        venueState = VenueState(self.uniqueId, self.name, self.description,
                                self.uri, self.connections, clientlist,
                                dList, self.server.eventService.GetLocation(),
                                self.server.textService.GetLocation(),
                                applist, self.services.values(),
                                self.server.backupServer)
        return venueState

    def GetId(self):
        """
        @returns: the id of this object.
        """
        return self.uniqueId
    
    def StartApplications(self):
        """
        Restart the application services after a server restart.

        For each app impl, awaken the app, and create a new
        web service binding for it.
        """

        for appImpl in self.applications.values():
            appImpl.Awaken(self.server.eventService)
            app = SharedApplicationI(appImpl)
            hostObj = self.server.hostingEnvironment.BindService(app)
            appHandle = hostObj.GetHandle()
            appImpl.SetHandle(appHandle)
            log.debug("Restarted app id=%s handle=%s",
                      appImpl.GetId(), appHandle)

    def CleanupClients(self):
        """
        CleanupClients is called by a regularly scheduled task to
        cleanup stale client connections.
        """
        users_to_remove = []
        netservices_to_remove = []
        now_sec = time.time()

        self.heartbeatLock.acquire()
        for privateId in self.clients.keys():

            vclient = self.clients[privateId]

            if vclient.GetTimeSinceLastHeartbeat(now_sec) > self.cleanupTime:
                users_to_remove.append(privateId)

        for privateId in self.netServices.keys():
            (netService,then_sec) = self.netServices[privateId]

            if abs(now_sec - then_sec) > self.cleanupTime:
                netservices_to_remove.append(privateId)

        self.heartbeatLock.release()

        # Actually remove user
        for privateId in users_to_remove:
            log.debug("Removing user %s with expired heartbeat time",
            self.clients[privateId].GetClientProfile().GetName())

            self.RemoveUser(privateId)

        # Actually remove net services
        for privateId in netservices_to_remove:
            log.info("Removing netservice %s with expired heartbeat time",
            privateId)
            self.RemoveNetworkService(privateId)

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

        if str(event.venue) != str(self.uniqueId):
            log.info("ClientHeartbeat: %s received heartbeat for a different venue %s", self.uniqueId, event.venue)

        if self.clients.has_key(privateId):
            self.heartbeatLock.acquire()

            self.clients[privateId].UpdateAccessTime()

            self.heartbeatLock.release()
        elif self.netServices.has_key(privateId):
            (netService, heartbeatTime) = self.netServices[privateId]
            self.netServices[privateId] = (netService,now)
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
            log.info("EventServiceDisconnect: Received client disconnect for a different venue %s", event.venue)

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
            log.info("EventServiceClientExits: Received client exits for a different venue %s", event.venue)
        log.debug("VenueServer: Got Client exiting for %s", privateId)

        self.clientDisconnectOK[privateId] = 1

    def NegotiateCapabilities(self, vcstate):
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

        clientProfile = vcstate.GetClientProfile()
        privateId = vcstate.GetPrivateId()

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
            vclient = self.clients[privateId]

            if vclient.GetPublicId() == profile.publicId:
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
                usage_log.info("\"RemoveUser\",\"%s\",\"%s\",\"%s\"", "DN Unavailable", self.name, self.uniqueId)
                return
            else:
                usage_log.info("\"RemoveUser\",\"%s\",\"%s\",\"%s\"", 
                               self.clients[privateId].GetClientProfile().GetDistinguishedName(), 
                               self.name, self.uniqueId)

            # Remove the user from the venue users role
            # - get the subject of the user to remove
            dn = self.clients[privateId].GetClientProfile().GetDistinguishedName()
            subject = X509Subject.CreateSubjectFromString(dn)
            
            # - check for other occurrences of this subject
            foundSubj = 0
            for cl in self.clients.values():
                tmp_dn = cl.GetClientProfile().GetDistinguishedName()
                if subject == X509Subject.CreateSubjectFromString(tmp_dn):
                    foundSubj += 1
                    
                    # early out
                    if foundSubj > 1:
                        break

            # - remove the subject only if it occurs singly
            if foundSubj == 1:
                log.debug("Removing single instance of user")
                role = self.authManager.FindRole("VenueUsers")
                if subject in role.GetSubjects():
                    role.RemoveSubject(subject)
            else:
                log.debug("Multiple instances, not removing %s", foundSubj)
                    

            vclient = self.clients[privateId]
            clientProfile = vclient.GetClientProfile()

            #
            # Shut down the client's connection to the event service.
            #

            vclient.CloseEventChannel()
	    vclient.CloseTextChannel()

            log.debug("RemoveUser: Distribute EXIT event")

            self.DistributeEvent(Event( Event.EXIT,
                                        self.uniqueId,
                                        clientProfile ) )
        except:
            log.exception("Venue.RemoveUser: Body of method threw exception")

        try:
            if privateId in self.clients:
                del self.clients[privateId]
        except:
            log.exception("Venue.RemoveUser: Error deleting client.")

        self.clientsBeingRemovedLock.acquire()
        del self.clientsBeingRemoved[privateId]
        self.clientsBeingRemovedLock.release()

        self.simpleLock.release()

    def SetConnections(self, connectionList):
        """
        SetConnections is a convenient aggregate accessor for the list of
        connections for this venue. Alternatively the user could iterate over
        a list of connections adding them one by one, but this is more
        desirable.

        **Arguments:**

        *connectionDict* A dictionary of connections.
        """
        log.debug("Calling SetConnections.")

        self.connections = list(connectionList)

        self.server.eventService.Distribute( self.uniqueId,
        Event( Event.SET_CONNECTIONS,
        self.uniqueId,
        connectionList ) )

    def DistributeEvent(self, event):
        """
        Distribute this event to our clients.

        We can't just invoke the event channel distribute because
        we need to enqueue the event for venue clients that haven't
        yet connected.

        Create a marshalled event object from the event and invoke
        SendEvent on each of our client objects.
        """

        mEvent = MarshalledEvent()
        mEvent.SetEvent(event)
        
        for c in self.clients.values():
            c.SendEvent(mEvent)
        
    def channelAuthCallback(self, event, connObj):
        """
        Authorization callback to gate the connection of new clients
        to the venue's event channel.

        event is the incoming event that triggered the authorization request.
        connObj is the event service connection handler object for the request.
        """

        priv = event.data
        log.debug("Venue gets channelAuthCallback, privateID=%s", priv)

        authorized = 0
        if priv in self.clients:
            log.debug("Private id is in client list, authorizing")
            authorized = 1

            #
            # Snag the lock and set up the client for event service
            #

            self.simpleLock.acquire()
            try:
                self.clients[priv].SetConnection(connObj)
            except:
                log.exception("Exception setting connection (id=%s)", priv)
                
            self.simpleLock.release()

        elif self.netServices.has_key(priv):
            log.debug("Private id is in netservices list, authorizing")
            netService = self.netServices[priv][0]
            netService.SetConnection(connObj)
            authorized = 1
        else:
            log.debug("Private id is not client list, denying")
            authorized = 0

        return authorized

    def textChannelAuthCallback(self, event, connObj):
        """
        Authorization callback to gate the connection of new clients
        to the venue's text channel.

        event is the incoming event that triggered the authorization request.
        connObj is the event service connection handler object for the request.
        """

        priv = event.data
        log.debug("Venue gets channelAuthCallback, privateID=%s", priv)

        authorized = 0
        if priv in self.clients:
            log.debug("Private id is in client list, authorizing")
            authorized = 1

            self.simpleLock.acquire()
            try:
                self.clients[priv].SetTextConnection(connObj)
            except:
                log.exception("Exception setting text connection (id=%s)", 
			      priv)
            self.simpleLock.release()

        else:
            log.debug("Private id is not client list, denying")
            authorized = 0

        return authorized

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

        # If we don't find them, we assign a new id
        if privateId == None:
            privateId = self.GetNextPrivateId()
            log.debug("Enter: Assigning private id: %s", privateId)
        else:
            log.debug("Enter: Client already in venue: %s", privateId)

        # Send this before we set up client state, so that
        # we don't end up getting our own enter event enqueued.
        self.DistributeEvent(Event(Event.ENTER, self.uniqueId, clientProfile))

        # Create venue client state object
        vcstate = self.clients[privateId] = VenueClientState(self,
                                                             privateId,
                                                             clientProfile)
        vcstate.UpdateAccessTime()
        self._UpdateProfileCache(clientProfile)
        usage_log.info("\"Enter\",\"%s\",\"%s\",\"%s\"", clientProfile.GetDistinguishedName(), self.name, self.uniqueId)

        # negotiate to get stream descriptions to return
        streamDescriptions = self.NegotiateCapabilities(vcstate)

        log.debug("Current users:")
        for c in self.clients.values():
            log.debug("   " + str(c))
        log.debug("Enter: Distribute enter event ")

        try:
            if not self.servicePtr.GetOption("insecure"):
                dn = clientProfile.GetDistinguishedName()
                self.authManager.FindRole("VenueUsers").AddSubject(X509Subject.CreateSubjectFromString(dn))
        except SubjectAlreadyPresent:
            log.info("User already in venue users list: %s", dn)

        try:
            state = self.AsVenueState()
            log.debug("state: %s", state)
        except:
            log.exception("Enter: Can't get state.")
            raise InvalidVenueState

        return ( state, privateId, streamDescriptions )

    def _UpdateProfileCache(self, profile):
        try:
            self.cache.updateProfile(profile)
        except InvalidProfileException:
            log.warn("UpdateProfileCache: InvalidProfile when storing a venue user's profile in the cache.")

    def AddNetworkService(self, clientType, privateId):
        """
        AddNetworkService adds a net service to those in the venue
        """

        # Remove the net service if it's already registered
        if self.netServices.has_key(privateId):
            log.info("AddNetworkService: id already registered")
            log.info("removing old state: id %s", privateId)
            self.RemoveNetworkService(privateId)

        log.info("AddNetworkService: type=%s", clientType)

        netService = NetService.CreateNetService(clientType,self,privateId)

        self.netServices[privateId] = (netService, time.time())

        return privateId

    def RemoveNetworkService(self, privateId):
        """
        RemoveNetworkService removes a netservice from those in the venue
        """

        # Stop the net service
        netService = self.netServices[privateId][0]
        log.info("RemoveNetworkService: type=%s privateId=%s", netService.type,
                 privateId)
        netService.Stop()

        # Close the connection to the net service
        if netService.connObj is not None:
            self.server.eventService.CloseConnection(netService.connObj)
        netService.connObj = None

        # Remove the netservice from the netservice list
        del self.netServices[privateId]

    def GetNetworkServices(self):
        """
        GetNetworkServices returns a list of all the network services
        in this venue.

        *self.netServices* A list of connection descriptions.
        """
        #This can't really do anything until we have something to give back
        pass

    def GetCachedProfiles(self):
        """
        This method returns a list of client profiles that have been registered
        for this venue.

        **Returns:**

        *cachedProfiles* A list of ClientProfiles.
        """
        
        cachedProfiles = self.cache.loadAllProfiles()

        return cachedProfiles
    
    def Shutdown(self):
        """
        This method cleanly shuts down all active threads associated with the
        Virtual Venue. Currently there are a few threads in the Event
        Service.
        """

        try:
            # Shut down data store
            self.dataStore.Shutdown()
        except:
            log.exception("Venue.ShutDown Could not shut down data store")

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

        if self.services.has_key(serviceDescription.id):
            log.exception("AddService: service already present: %s",
                          serviceDescription.name)
            raise ServiceAlreadyPresent

        self.services[serviceDescription.id] = serviceDescription

        log.debug("Distribute ADD_SERVICE event %s", serviceDescription)

        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.ADD_SERVICE,
                                                    self.uniqueId,
                                                    serviceDescription ) )

        return serviceDescription

    def UpdateService(self, serviceDescription):
        """
        The UpdateService method enables VenuesClients to modify
        a service description.

        **Arguments:**

        *serviceDescription* A real service description.

        **Raises:**

        *ServiceNotFound* Raised when service is not found.

        **Returns:**

        *serviceDescription* Upon successfully adding the service.
        """
        if not self.services.has_key(serviceDescription.id):
            log.exception("Service not found!")
            raise ServiceNotFound

        self.services[serviceDescription.id] = serviceDescription

        log.debug("Distribute UPDATE_SERVICE event %s", serviceDescription)

        self.server.eventService.Distribute( self.uniqueId,
        Event( Event.UPDATE_SERVICE,
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
              
        if not self.services.has_key(serviceDescription.id):
            log.exception("Service not found!")
            raise ServiceNotFound

        del self.services[serviceDescription.id]

        log.debug("Distribute REMOVE_SERVICE event %s", serviceDescription)
        
        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.REMOVE_SERVICE,
                                                    self.uniqueId,
                                                    serviceDescription ) )
        return serviceDescription

    def GetServices(self):
        """
        GetServices returns a list of all the services in this venue.

        *self.services* A list of connection descriptions.
        """
        return self.services.values()

    def AddConnection(self, connectionDesc):
        """
        AddConnection allows an administrator to add a connection to a
        virtual venue to this virtual venue.

        **Arguments:**

        *ConnectionDescription* A connection description.

        **Raises:**
        """
        for c in self.connections:
            if c.GetURI() == connectionDesc.GetURI():
                raise ConnectionAlreadyPresent

        self.connections.append(connectionDesc)
        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.ADD_CONNECTION,
                                                    self.uniqueId,
                                                    connectionDesc ) )
            
    def RemoveConnection(self, connectionDesc):
        """
        """
        for c in self.connections:
            if c.GetURI() == connectionDesc.GetURI():
                self.connections.remove(c)
                self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.REMOVE_CONNECTION,
                                                    self.uniqueId,
                                                    connectionDesc ) )
            else:
                raise ConnectionNotFound
            
    def GetConnections(self):
        """
        GetConnections returns a list of all the connections to other venues
        that are found within this venue.

        **Returns:**

        *self.connections* A list of connection descriptions.
        """
        return self.connections

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
        self.encryptMedia = value

        if not self.encryptMedia:
            self.encryptionKey = None
        else:
            if key == None or len(key.strip()) == 0:
                key = AllocateEncryptionKey()
            self.encryptionKey = key

        # Make sure streams' encryption is the same as the venue's.
        for stream in self.streamList.GetStreams():
            stream.encryptionFlag = self.encryptMedia
            stream.encryptionKey = self.encryptionKey

        return self.encryptMedia

    def GetEncryptMedia(self):
        """
        Return whether we are encrypting streams or not.
        """
        return self.encryptionKey

    def RegenerateEncryptionKeys(self):
        log.debug("Regenerating Encryption Key")
            
        self.encryptionKey = AllocateEncryptionKey()

        if self.encryptMedia:
            # Make sure streams' encryption is the same as the venue's.
            for stream in self.streamList.GetStreams():
                if stream.encryptionKey != self.encryptionKey:
                    stream.encryptionKey = self.encryptionKey

                    # Send a ModifyStream event
                    self.server.eventService.Distribute( self.uniqueId,
                                                  Event( Event.MODIFY_STREAM,
                                                         self.uniqueId,
                                                         stream ) )
        return self.encryptionKey

        
    def SetDescription(self, description):
        """
        SetDescription allows an administrator to set the venues description
        to something new.

        **Arguments:**

        *description* New description for this venue.
        """
        self.description = description

    def GetDescription(self):
        """
        GetDescription returns the description for the virtual venue.
        **Arguments:**
        """
        return self.description

    def SetName(self, name):
        """
        SetName allows an administrator to set the venues name
        to something new.

        **Arguments:**

        *name* New name for this venue.
        """
        self.name = name

    def GetName(self):
        """
        GetName returns the name for the virtual venue.
        """
        return self.name

    def GetClients(self):
        """
        Return a list of the clients in this venue.
        """
        return self.clients.values()
    
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
        log.debug("%s - Venue.AddStream: %s %d %d", self.uniqueId,
                  inStreamDescription.location.host,
                  inStreamDescription.location.port,
                  inStreamDescription.location.ttl )
        
        self.streamList.AddStream(inStreamDescription)

        # Distribute event announcing new stream
        self.server.eventService.Distribute(self.uniqueId,
                                            Event(Event.ADD_STREAM,
                                                   self.uniqueId,
                                                   inStreamDescription))

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
        log.debug("%s - Venue.RemoveStream: %s %d %d", self.uniqueId,
                  inStreamDescription.location.host,
                  inStreamDescription.location.port,
                  inStreamDescription.location.ttl )

        self.streamList.RemoveStream(inStreamDescription)
        
        # Distribute event announcing removal of stream
        self.server.eventService.Distribute(self.uniqueId,
                                             Event(Event.REMOVE_STREAM,
                                                    self.uniqueId,
                                                    inStreamDescription))

    def GetStreams(self):
        """
        GetStreams returns a list of stream descriptions to the caller.
        """
        return self.streamList.GetStreams()

    def GetStaticStreams(self):
        """
        GetStaticStreams returns a list of static stream descriptions
        to the caller.
        """
        return self.streamList.GetStaticStreams()

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
            usage_log.info("\"Exit\",\"%s\",\"%s\",\"%s\"", 0, self.name, self.uniqueId)
            raise ClientNotFound
        else:
            usage_log.info("\"Exit\",\"%s\",\"%s\",\"%s\"", self.clients[privateId].GetClientProfile().GetDistinguishedName(), self.name, self.uniqueId)

        self.RemoveUser(privateId)

    def UpdateClientProfile(self, clientProfile):
        """
        UpdateClientProfile allows a VenueClient to update/modify the client
        profile that is stored by the Virtual Venue that they gave to the Venue
        when they called the Enter method.

        **Arguments:**

        *clientProfile* A client profile.

        **Raises:**
        """
               
        log.debug("Called UpdateClientProfile on %s " %clientProfile.name)

        for privateId in self.clients.keys():
            vclient = self.clients[privateId]
            if vclient.GetPublicId() == clientProfile.publicId:
                vclient.UpdateClientProfile(clientProfile)
                vclient.UpdateAccessTime()

        log.debug("Distribute MODIFY_USER event")

        self.DistributeEvent(Event(Event.MODIFY_USER, self.uniqueId,
                                   clientProfile))
      
    def AddData(self, dataDescription ):
        """
        LEGACY: This is just left here not to change the interface for
        AG2.0 clients. (personal data)
        """
        self.server.eventService.Distribute(self.uniqueId,
                                             Event(Event.ADD_DATA,
                                                    self.uniqueId,
                                                    dataDescription))
        

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

        # This is venue resident so delete the file
        if(dataDescription.type is None or dataDescription.type == "None"):
            list = []
            list.append(dataDescription)
            self.dataStore.RemoveFiles(list)
            self.server.eventService.Distribute( self.uniqueId,
                                                 Event( Event.REMOVE_DATA,
                                                        self.uniqueId,
                                                        dataDescription ) )
            
        else:
            log.info("Venue.RemoveData tried to remove non venue data.")

        return dataDescription

    def UpdateData(self, dataDescription, dataStoreCall = 0):
        """
        Replace the current description for dataDescription.name with
        this one.
        """
        #
        # This method is called both from the data store and from clients.
        # The data store only wants to distribute an event, while clients
        # need to modify the actual data store.
        #
        
        if dataStoreCall:
            self.server.eventService.Distribute( self.uniqueId,
                                                 Event( Event.UPDATE_DATA,
                                                        self.uniqueId,
                                                        dataDescription ) )
            return


        name = dataDescription.name
        
        # This is venue resident so modify the file
        if(dataDescription.type is None or dataDescription.type == "None"):
            self.dataStore.ModifyData(dataDescription)
            self.server.eventService.Distribute( self.uniqueId,
                                                 Event( Event.UPDATE_DATA,
                                                        self.uniqueId,
                                                        dataDescription ) )

        else:
            log.info("Venue.UpdateData tried to modify non venue data. That should not happen")
            
        return dataDescription
            
    def GetDataStoreInformation(self):
        """
        Retrieve an upload descriptor and a URL to the Venue's DataStore 

        **Arguments:**

        **Raises:**

        **Returns:**

        *(upload description, url)* the upload descriptor to the
        Venue's DataStore and the url to the DataStore SOAP service.

        """

        descriptor = ""
        location = ""

        if self.dataStore is not None:
            try:
                descriptor = self.dataStore.GetUploadDescriptor()
                location = str(self.uri)
                return descriptor, location
            except:
                log.exception("Venue.GetDataStoreInformation.")
                raise

    def GetDataDescriptions(self):
        """
        """
        try:
            dList = self.dataStore.GetDataDescriptions()
            return dList
        except:
            log.exception("Venue.GetDataDescriptions.")
            dList = []
            raise

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
        returnValue = ''

        if self.dataStore is not None:
            try:
                returnValue = self.dataStore.GetUploadDescriptor()
                return returnValue
            except:
                log.exception("Venue.GetUploadDescriptor.")
                raise

    def GetApplication(self, aid):
        """
        Return the application state for the given application object.

        **Arguments:**

        *aid* The id of the application being retrieved.

        **Raises:**

        *ApplicationNotFound* Raised when the application is not
        found in the venue.

        **Returns:**

        *appState* The state of the application object.
        """
        if not self.applications.has_key(aid):
            log.exception("GetApplication: Application not found.")
            raise ApplicationNotFound

        app = self.applications[aid]
        returnValue = app.GetState()

        return returnValue

    def GetApplications(self):
        """
        return a list of the applications in this venue.
        """
        
        # Create a list of application descriptions to return
        adl = map( lambda a: a.AsApplicationDescription(), self.applications.values() )
        return adl
        
    def CreateApplication(self, name, description, mimeType, aid = None ):
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

        # Create the shared application object
        app = SharedApplication(name, description, mimeType, 
                                  self.server.eventService, aid)
        app.SetVenueURL(self.uri)
        appId = app.GetId()
        self.applications[appId] = app

        # Create the interface object
        appI = SharedApplicationI(app)

        # pull out the venue path, so these can be a subspace
        path = self.server.hostingEnvironment.FindPathForObject(self)
        path = path + "/apps/%s" % appId

        # register the app with the hosting environment
        self.server.hostingEnvironment.RegisterObject(appI, path=path)

        # register the authorization interface and serve it.
        self.server.hostingEnvironment.RegisterObject(
                                  AuthorizationManagerI(app.authManager),
                                  path=path+'/Authorization')
        
        # pull the url back out and put it in the app object
        appURL = self.server.hostingEnvironment.FindURLForObject(app)
        app.SetHandle(appURL)

        # grab the description, and update the universe with it
        appDesc = app.AsApplicationDescription()

        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.ADD_APPLICATION,
                                                    self.uniqueId,
                                                    appDesc ) )

        log.debug("CreateApplication: Created id=%s handle=%s",
                  appDesc.id, appDesc.uri)

        return appDesc

    def UpdateApplication(self, appDescStruct):
        """
        Update application.

        **Arguments:**

        *applicationDesc* Object describing the application.

        **Raises:**

        *ApplicationNotFound* Raised when an application is not
        found for the application id specified.
        """
             
        if not self.applications.has_key(appDescStruct.id):
            raise ApplicationNotFound

        try:
            applicationDesc = CreateApplicationDescription(appDescStruct)
        except:
            log.exception("UpdateApplication: Bad application description.")
            raise BadApplicationDescription

        appImpl = self.applications[applicationDesc.id]
        appImpl.name = applicationDesc.name
        appImpl.description = applicationDesc.description
        
        self.applications[applicationDesc.id] = appImpl
        
        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.UPDATE_APPLICATION,
                                                    self.uniqueId,
                                                    applicationDesc ) )

        log.debug("Update Application: id=%s handle=%s",
                  applicationDesc.id, applicationDesc.uri)

        return applicationDesc

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

        # Shut down the application
        
        app.Shutdown()

        # Remove the interface
        try:
            self.server.hostingEnvironment.UnregisterObject(app)
        except KeyError:
            log.exception ("DestroyApp: SOAPpy.UnregisterObject returned a key error.")
                
        # Create the application description
        appDesc = app.AsApplicationDescription()

        # Send the remove application event
        self.server.eventService.Distribute(self.uniqueId,
                                            Event(Event.REMOVE_APPLICATION,
                                                  self.uniqueId,
                                                  appDesc))

        # Get rid of it for good
        del self.applications[appId]

    def AddNetworkLocationToStream(self, privateId, streamId, networkLocation):
        """
        Add a transport to an existing stream

        **Arguments:**

        *streamId* The id of the stream to which to add the transport
        *networkLocation* The network location (transport) to add

        **Raises:**

        Note:  This method overwrites the private id in the incoming
        network location

        """
        # Validate private id before allowing call
        if privateId not in self.netServices.keys():
            # Raise location not found?
            log.info("AddNetworkLocationToStream: unrecognized private id %s; skipping", 
                     privateId)
            return None
        
        # Add the network location to the specified stream
        nid = 0
        streamList = self.streamList.GetStreams()
        for stream in streamList:
            if stream.id == streamId:
                
            
                # Set the private id as passed in
                networkLocation.privateId = privateId
                
                # Add the network location to the stream
                nid = stream.AddNetworkLocation(networkLocation)
                log.info("Added network location %s to stream %s for private id %s",
                         nid, streamId, privateId)
                
                # Send a ModifyStream event
                self.server.eventService.Distribute( self.uniqueId,
                                                     Event( Event.MODIFY_STREAM,
                                                            self.uniqueId,
                                                            stream ) )
                break
                                                            
        if not nid:
            log.info("AddNetworkLocationToStream: stream id=%s not found",
                     streamId)
                     
        return nid

    def RemoveNetworkLocationFromStream(self, privateId, streamId,
                                        networkLocationId):

        # Validate private id before allowing call
        if privateId not in self.netServices.keys():
            return None

        # Remove the network location from the specified stream
        streamList = self.streamList.GetStreams()
        for stream in streamList:
            if stream.id == streamId:
                # Remove network location from stream
                log.info("Removing network location %s from stream %s",
                         networkLocationId, streamId)
                stream.RemoveNetworkLocation(networkLocationId)

                # Send a ModifyStream event
                self.server.eventService.Distribute( self.uniqueId,
                                                     Event( Event.MODIFY_STREAM,
                                                            self.uniqueId,
                                                            stream ) )


    def RemoveNetworkLocationsByPrivateId(self, privateId):
        log.info("Removing network locations for private id %s", privateId)

        # Make local copy of net service private id list,
        # with incoming private id removed
        netServicePrivateIds = self.netServices.keys()
        if privateId in netServicePrivateIds:
            netServicePrivateIds.remove(privateId)


        # Remove network locations tagged with specified private id
        streamList = self.streamList.GetStreams()
        for stream in streamList:
            streamModified = 0
            for netloc in stream.networkLocations:
                # Clean up the network locations generally,
                # removing any that don't correspond to a 
                # known net service
                #
                # This brute-force cleanup of the network locations list
                # in a stream is being done to resolve multiple network
                # locations being registered for a single bridge server.
                #
                # This is a bug that should be fixed in the bridge server
                # or the supporting venueserver-side code.  Once the bug
                # is fixed, this brute-force code should be removed.
                # - turam
                if netloc.privateId and netloc.privateId not in netServicePrivateIds:

                    # Remove network location from stream
                    log.info("Removing network location %s from stream %s; privateId=%s",
                              netloc.id, stream.id, netloc.privateId)
                    stream.RemoveNetworkLocation(netloc.id)
                    streamModified = 1

            if streamModified:
                # Send a ModifyStream event
                self.server.eventService.Distribute( self.uniqueId,
                          Event( Event.MODIFY_STREAM,
                          self.uniqueId,
                          stream ) )


    def GetEventServiceLocation(self):
        return (self.server.eventService.GetLocation(), self.uniqueId)


# Legacy calls
    def AddSubjectToRole(self, subject, role_string):
        """
        Adds user to list of users authorized for a specific role.
        """
        subj = X509.CreateSubjectFromString(subject)
        role = self.authManager.FindRole(role_string)
        role.AddSubject(subj)
        
    def RemoveSubjectFromRole(self, subject, role):
        """
        Removes a user from list of those authorized for a specific
        role.
        """
        subj = X509.CreateSubjectFromString(subject)
        role = self.authManager.FindRole(role_string)
        role.RemoveSubject(subj)

    def SetSubjectsInRole(self, subject_list, role_string):
        """
        Sets the users in a role.  Be extra careful so we don't
        wipe out all the subjects in this role if there's an error.
        """
        sl = map(lambda x: X509.CreateSubjectFromString(x), subject_list)
        role = self.authManager.FindRole(role_string)
        
    def GetUsersInRole(self, role_string):
        """
        Returns a list of strings of users' names.
        """
        role = self.authManager.FindRole(role_string)
        sls = role.GetSubjectListAsStrings()
        return sls
    
    def GetRoleNames(self):
        """
        Returns a list of role names.
        """
        rl = self.authManager.GetRoles()
        rnl = map(lambda x: x.GetName(), rl)
        return rnl

    def DetermineSubjectRoles(self, subject):
        """
        Return a list of roles for the calling subject
        """
        if self.servicePtr.GetOption("insecure"):
            return ['Administrators']
        roleList = self.authManager.GetRolesForSubject(subject)
        roleNameList = map( lambda r: r.GetName(), roleList )
        return roleNameList
        


class VenueI(SOAPInterface, AuthorizationIMixIn):
    """
    A Virtual Venue is a virtual space for collaboration on the Access Grid.
    """
    def __init__(self, impl):
        SOAPInterface.__init__(self, impl)

    def _authorize(self, *args, **kw):
        """
        The authorization callback. We should be able to implement this
        just once and remove a bunch of the older code.
        """
        if self.impl.servicePtr.GetOption("insecure"):
            return 1

        subject, action = self._GetContext()
        
        log.info("Authorizing action: %s for subject %s", action.name,
                 subject.name)

        authManager = self.impl.authManager
        
        return authManager.IsAuthorized(subject, action)

    def Enter(self, clientProfileStruct):
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
        log.debug("Interface Enter: Called.")

        # Rebuild the profile
        clientProfile = CreateClientProfile(clientProfileStruct)

        if self.impl.servicePtr.GetOption("insecure"):
            subject = Subject.Subject("", auth_type=None)
            clientProfile.distinguishedName = ""
        else:
            subject = self._GetCaller()
            clientProfile.distinguishedName = subject.name

        # Call Enter
        try:
            r = self.impl.Enter(clientProfile)
        except:
            log.exception("VenueI.Enter: exception")
            raise

        return r

    def GetClients(self):
        """
        retrieve the list of clients in the venue.
        """
        try:
            retval = self.impl.GetClients()
            return retval
        except:
            log.exception("VenueI.GetClients: exception")
            raise

    def AddNetworkService(self, clientType, privateId=None):
        """
        AddNetworkService adds a net service to those in the venue
        """
        if privateId == None:
            privateId = str(GUID())

        # Lock and do the call
        try:
            retval = self.impl.AddNetworkService(clientType, privateId)
            return retval
        except:
            log.exception("VenueI.AddNetworkService: exception")
            raise
            
    AddNetService = AddNetworkService

    def RemoveNetworkService(self, privateId):
        """
        RemoveNetworkService removes a netservice from those in the venue
        """

        # Lock and do the call
        try:
            self.impl.RemoveNetworkService(privateId)
        except:
            log.exception("VenueI.RemoveNetworkService: exception")
            raise
    
    RemoveNetService = RemoveNetworkService
    
    def GetNetworkServices(self):
        """
        Return data on the existing network services.
        """
        # This can't do anything until we have something to return
        return None

    def GetCachedProfiles(self):
        """
        This method returns a list of client profiles that have been registered
        for this venue.
        
        **Returns:**
        
        *cachedProfiles* A list of ClientProfiles.
        """

        try:
            return self.impl.GetCachedProfiles()

        except:
            log.exception("VenueI.GetCachedProfiles: exception")
            raise
            
    def Shutdown(self):
        """
        This method cleanly shuts down all active threads associated with the
        Virtual Venue. Currently there are a few threads in the Event
        Service.
        """

        # Lock and do the call
        try:
            self.impl.Shutdown()
        except:
            log.exception("VenueI.Shutdown: exception")
            raise

    def AddService(self, servDescStruct ):
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
        log.debug("VenueI.AddService")            


        serviceDescription = CreateServiceDescription(servDescStruct)

        try:
            returnValue = self.impl.AddService(serviceDescription)
        except:
            log.exception("VenueI.AddService: exception")
            raise

        return returnValue

    def RemoveService(self, servDescStruct ):
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
        log.debug("VenueI.RemoveService")

        serviceDescription = CreateServiceDescription(servDescStruct)

        try:
            returnValue = self.impl.RemoveService(serviceDescription)
        except:
            log.exception("VenueI.RemoveService: exception")
            raise

        return returnValue

    def UpdateService(self, servDescStruct ):
        """
        Interface to update a service from the venue.

        **Arguments:**

        *servDescStruct* an anonymous struct that contains a
        service description.

        **Raises:**

        *BadServiceDescription* This is raised if the anonymous
        struct can't be converted to a real service description.

        **Returns:**

        *serviceDescription* A service description is returned on success.

        """
        log.debug("VenueI.UpdateService")

        serviceDescription = CreateServiceDescription(servDescStruct)

        try:
            returnValue = self.impl.UpdateService(serviceDescription)
        except:
            log.exception("VenueI.UpdateService: exception")
            raise

        return returnValue

    def GetServices(self):
        """
        Interface to remove a service from the venue.

        **Arguments:**

        **Raises:**

        **Returns:**

        *serviceDescriptionList* A service description is returned on success.

        """
        log.debug("VenueI.GetServices")

        try:
            returnValue = self.impl.GetServices()
            return returnValue
        except:
            log.exception("VenueI.GetServices: exception")
            raise

    def SetConnections(self, connDescStructList):
        """
        Interface for setting all the connections in a venue in a single call.

        **Arguments:**

        *connDescStructList* a list of connection descriptions that
        have been converted to anonymous structs by the SOAP
        module.

        **Raises:**

        *BadConnectionDescription* This is raised when an
        anonymous struct is not converted to a real connection
        description.
        """
        try:
            connectionList = []
            for c in connDescStructList:
                connectionList.append(CreateConnectionDescription(c))
            self.impl.SetConnections(connectionList)
        except:
            log.exception("VenueI.SetConnections: exception")
            raise

    def AddConnection(self, connectionDescStruct):
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
        c = CreateConnectionDescription(connectionDescStruct)

        try:
            self.impl.AddConnection(c)
        except:
            log.exception("AddConnection: exception")
            raise

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
        c = CreateConnectionDescription(connectionDescription)
        try:
            self.impl.RemoveConnection(c)
        except:
            log.exception("VenueI.RemoveConnection.")
            raise
        
    def GetConnections(self):
        """
        GetConnections returns a list of all the connections to other venues
        that are found within this venue.

        **Returns:**

        *ConnectionList* A list of connection descriptions.
        """
        log.debug("Calling GetConnections.")

        try:
            cls = self.impl.GetConnections()
            return cls
        except:
            log.exception("VenueI.GetConnections.")
            raise
        
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

        try:
            retval = self.impl.SetEncryptMedia(value, key)
        except:
            log.exception("VenueI.SetEncryptMedia.")
            raise

        return retval
    
    def GetEncryptMedia(self):
        """
        Return whether we are encrypting streams or not.
        """
        try:
            returnValue = self.impl.GetEncryptMedia()
        except:
            log.exception("VenueI.GetEncryptMedia.")
            raise
        
        return returnValue

    def RegenerateEncryptionKeys(self):
        """
        RegenerateKeys allows one to regenerate the encryption keys on
        the venue. THis should only be done with extreme care, as the
        regeneration of encryption keys will interrupt existing
        collaborations by restarting simple media tools.
        """
        try:
            return self.impl.RegenerateEncryptionKeys()
        except:
            log.exception("Failed to regenerate encryption keys.", e)
            raise
        
    def SetDescription(self, description):
        """
        SetDescription allows an administrator to set the venues description
        to something new.

        **Arguments:**

        *description* New description for this venue.
        """
        try:
            self.impl.SetDescription(description)
        except:
            log.exception("VenueI.SetDescription.")
            raise

    def GetDescription(self):
        """
        GetDescription returns the description for the virtual venue.
        **Arguments:**
        """
        try:
            retval = self.impl.GetName()
        except:
            log.exception("VenueI.GetName.")
            raise

        return retval
    
    def SetName(self, name):
        """
        SetName allows an administrator to set the venues name
        to something new.

        **Arguments:**

        *name* New name for this venue.
        """
        try:
            self.impl.SetName(name)
        except:
            log.exception("VenueI.SetName.")
            raise

    def GetName(self):
        """
        GetName returns the name for the virtual venue.
        """
        try:
            retval = self.impl.GetName()
        except:
            log.exception("VenueI.GetName.")
            raise

        return retval

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
        streamDescription = CreateStreamDescription(inStreamDescription)
        
        try:
            self.impl.AddStream(streamDescription)
        except:
            log.exception("VenueI.AddStream.")
            raise

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
        streamDescription = CreateStreamDescription(inStreamDescription)
        try:
            self.impl.RemoveStream(streamDescription)
        except:
            log.exception("VenueI.RemoveStream.")
            raise

    def GetStreams(self):
        """
        GetStreams returns a list of stream descriptions to the caller.
        """
        try:
            sl = self.impl.GetStreams()
            return sl
        except:
            log.exception("VenueI.GetStreams")
            raise

    def GetStaticStreams(self):
        """
        GetStaticStreams returns a list of static stream descriptions
        to the caller.
        """
        try:
            sl = self.impl.GetStaticStreams()
            return sl
        except:
            log.exception("VenueI.GetStaticStreams")
            raise

    def Exit(self, privateId):
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
        try:
            self.impl.Exit(privateId)
        except:
            log.exception("VenueI.Exit.")
            raise
        
    def UpdateClientProfile(self, clientProfileStruct):
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
        clientProfile = CreateClientProfile(clientProfileStruct)

        try:
            self.impl.UpdateClientProfile(clientProfile)
        except:
            log.exception("VenueI.UpdateClientProfile.")
            raise

    def AddData(self, dataDescriptionStruct):
        """
        LEGACY: The implementation call is only present to support AG2.0 clients.
        
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
        dataDescription = CreateDataDescription(dataDescriptionStruct)

        try:
           self.impl.AddData(dataDescription)
        except:
            log.exception("VenueI.AddData: exception")
            raise

    def RemoveData(self, dataDescriptionStruct):
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
        dataDescription = CreateDataDescription(dataDescriptionStruct)
        
        try:
            returnValue = self.impl.RemoveData(dataDescription)
        except:
            log.exception("VenueI.RemoveData: exception")
            raise

        return returnValue

    def UpdateData(self, dataDescriptionStruct):
        """
        Replace the current description for dataDescription.name with
        this one.
        """
        dataDescription = CreateDataDescription(dataDescriptionStruct)

        try:
            returnValue = self.impl.UpdateData(dataDescription)
        except:
            log.exception("VenueI.UpdateData: exception")
            raise

    def GetDataStoreInformation(self):
        """
        Retrieve an upload descriptor and a URL to the Venue's DataStore 

        **Arguments:**

        **Raises:**

        **Returns:**

            *(upload description, url)* the upload descriptor to the Venue's DataStore
            and the url to the DataStore SOAP service.

        """

        try:
            return self.impl.GetDataStoreInformation()
        except:
            log.exception("VenueI.GetDataStoreInformation.")
            raise


    def GetDataDescriptions(self):
        """
        """
        try:
            ddl = self.impl.GetDataDescriptions()
            return ddl
        except:
            log.exception("VenueI.GetDataDescriptions.")
            raise

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
        try:
            retval = self.impl.GetUploadDescriptor()
            return retval
        except:
            log.exception("VenueI.GetUploadDescriptor.")
            raise

    def GetApplication(self, aid):
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
        try:
            as = self.impl.GetApplication(aid)
            return as
        except:
            log.exception("VenueI.GetApplication.")
            raise

    def GetApplications(self):
        """
        return the list of application descriptions for this venue.
        """
        try:
            adl = self.impl.GetApplications()
            return adl
        except:
            log.exception("VenueI.GetApplications.")
            raise
        
    def CreateApplication(self, name, description, mimeType, aid = None ):
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
        try:
            retval = self.impl.CreateApplication(name, description, mimeType,
                                                 aid)
            return retval
        except:
            log.exception("VenueI.CreateApplication.")
            raise

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
        try:
            self.impl.DestroyApplication(appId)
        except:
            log.exception("VenueI.DestroyApplication.")
            raise

    def UpdateApplication(self, appDescStruct ):
        """
        Interface to update a service from the venue.

        **Arguments:**

        *appDescStruct* an anonymous struct that contains an
        application description.

        **Raises:**

        *BadApplicationDescription* This is raised if the anonymous
        struct can't be converted to a real application description.

        **Returns:**

        *applicationDescription* An app description is returned on success.

        """
        log.debug("VenueI.UpdateApplication")

        applicationDescription = CreateApplicationDescription(appDescStruct)

        try:
            returnValue = self.impl.UpdateApplication(applicationDescription)
        except:
            log.exception("VenueI.UpdateApplication: exception")
            raise

        return returnValue
        
    def AddNetworkLocationToStream(self, privateId, streamId, networkLocationStruct):
        """
        Add a transport to an existing stream

        **Arguments:**

        *streamId* The id of the stream to which to add the transport
        *networkLocation* The network location (transport) to add

        **Raises:**


        Note:  This method overwrites the private id in the incoming
        network location

        """
        try:
            # Create a NetworkLocation object from the
            # network location struct
            networkLocation = CreateNetworkLocation(networkLocationStruct)
                
            retval = self.impl.AddNetworkLocationToStream(privateId, streamId,
                                                          networkLocation)
            return retval
        except:
            log.exception("VenueI.AddNetworkLocationToStream.")
            raise

    def RemoveNetworkLocationFromStream(self, privateId, streamId,
                                        networkLocationId):

        try:
            self.impl.RemoveNetworkLocationFromStream(privateId,
                                                      streamId,
                                                      networkLocationId)
        except:
            log.exception("VenueI.RemoveNetworkLocationFromStream.")
            raise

    def GetEventServiceLocation(self):
        try:
            esl = self.impl.GetEventServiceLocation()
            return esl
        except:
            log.exception("VenueI.GetEventServiceLocation.")
            raise

    def ImportAuthorizationPolicy(self, policy):
        """
        This method takes a string that is an XML representation of an
        authorization policy. This policy is parsed and this object is
        configured to enforce the specified policy.

        @param policy: the policy as a string
        @type policy: an XML formatted string
        """
        self.impl.ImportAuthorizationPolicy(policy)

    def AllocateMulticastLocation(self):
        try:
            return self.impl.AllocateMulticastLocation()
        except:
            log.exception("AllocateMulticastLocation: exception")
            raise


# Legacy calls
    def AddSubjectToRole(self, subject, role_string):
        """
        Adds user to list of users authorized for a specific role.
        """
        self.impl.AddSubjectToRole(subject,role_string)
        
    def RemoveSubjectFromRole(self, subject, role):
        """
        Removes a user from list of those authorized for a specific
        role.
        """
        self.impl.RemoveSubjectFromRole(subject,role)

    def SetSubjectsInRole(self, subject_list, role_string):
        """
        Sets the users in a role.  Be extra careful so we don't
        wipe out all the subjects in this role if there's an error.
        """
        self.impl.SetSubjectsInRole(subject_list,role_string)
        
    def FlushRoles(self):
        """
        Enforce roles that may have just changed.
        Not needed for administrator roles, just allowed entry.
        Since "VenueUsers" is not fully enforced yet, we'll
        check the connections.
        """
        pass
    
    def GetUsersInRole(self, role_string):
        """
        Returns a list of strings of users' names.
        """
        return self.impl.GetUsersInRole(role_string)
    
    def GetRoleNames(self):
        """
        Returns a list of role names.
        """
        return self.impl.GetRoleNames()

    def DetermineSubjectRoles(self):
        """
        Return a list of roles for the calling subject
        """
        subject = self._GetCaller()
        return self.impl.DetermineSubjectRoles(subject)
        

class VenueIW(SOAPIWrapper, AuthorizationIWMixIn):
    def __init__(self, url, faultHandler = None):
        SOAPIWrapper.__init__(self, url, faultHandler)

    def SetEncryptMedia(self, value, key):
        return self.proxy.SetEncryptMedia(value, key)

    def GetEncryptMedia(self):
        return self.proxy.GetEncryptMedia()

    def RegenerateEncryptionKeys(self):
        return self.proxy.RegenerateEncryptionKeys()
    
    def SetDescription(self, description):
        return self.proxy.SetDescription(description)

    def GetDescription(self):
        return self.proxy.GetDescription()

    def SetName(self, name):
        return self.proxy.SetName(name)

    def GetName(self):
        return self.proxy.GetName()

    def SetConnections(self, connectionList):
        return self.proxy.SetConnections(connectionList)

    def AddConnection(self, connection):
        return self.proxy.AddConnection(connection)

    def RemoveConnection(self, cid):
        return self.proxy.RemoveConnection(cid)

    def GetConnections(self):
        return self.proxy.GetConnections()

    def AddStream(self, streamDesc):
        return self.proxy.AddStream(streamDesc)

    def RemoveStream(self, sid):
        return self.proxy.RemoveStream(sid)

    def GetStreams(self):
        streamDescList = []
        streamDescStructList = self.proxy.GetStreams()
        for streamDescStruct in streamDescStructList:
            streamDescList.append( CreateStreamDescription(streamDescStruct) )
        return streamDescList

    def GetStaticStreams(self):
        streamDescList = []
        streamDescStructList = self.proxy.GetStaticStreams()
        for streamDescStruct in streamDescStructList:
            streamDescList.append( CreateStreamDescription(streamDescStruct) )
        return streamDescList

    def Shutdown(self):
        return self.proxy.Shutdown()

    def Enter(self, profile):
        (r1, r2, r3) = self.proxy.Enter(profile)
        return (r1, r2, r3)

    def Exit(self, pid):
        return self.proxy.Exit(pid)

    def GetClients(self):
        cl = self.proxy.GetClients()
        rcl = list()
        for c in cl:
            rcl.append(CreateClientProfile(c))

        return rcl
    
    def UpdateClientProfile(self, profile):
        return self.proxy.UpdateClientProfile(profile)

    def AddNetworkService(self, type, privateID):
        return self.proxy.AddNetworkService(type, privateID)

    def RemoveNetworkService(self, nid):
        return self.proxy.RemoveNetworkService(nid)

    def GetNetworkServices(self):
        return None
    
    def AddService(self, serviceDesc):
        return self.proxy.AddService(serviceDesc)

    def RemoveService(self, sid):
        return self.proxy.RemoveService(sid)

    def UpdateService(self, serviceDesc):
        return self.proxy.UpdateService(serviceDesc)

    def GetServices(self):
        sl = self.proxy.GetServices()
        rsl = list()
        for s in sl:
            rsl.append(CreateServiceDescription(s))
        return rsl

    def AddData(self, dataDescription):
        return self.proxy.AddData(dataDescription)

    def RemoveData(self, did):
        return self.proxy.RemoveData(did)

    def UpdateData(self, dataDescription):
        return self.proxy.UpdateData(dataDescription)

    def GetDataDescriptions(self):
        return self.proxy.GetDataDescriptions()

    def GetDataStoreInformation(self):
        return self.proxy.GetDataStoreInformation()
    
    def GetUploadDescriptor(self):
        return self.proxy.GetUploadDescriptor()

    def GetApplication(self, aid):
        return self.proxy.GetApplication(aid)

    def GetApplications(self):
        adl = self.proxy.GetApplications()
        al = list()
        for a in adl:
            al.append(CreateApplicationDescription(a))
        return al
        
    def CreateApplication(self, name, description, mimeType):
        return self.proxy.CreateApplication(name, description, mimeType)

    def DestroyApplication(self, aid):
        return self.proxy.DestroyApplication(aid)
        
    def UpdateApplication(self, applicationDesc):
        return self.proxy.UpdateApplication(applicationDesc)

    def AddNetworkLocationToStream(self, privId, streamId, networkLocation):
        return self.proxy.AddNetworkLocationToStream(privId, streamId,
                                                     networkLocation)

    def RemoveNetworkLocationFromStream(self, privId, streamId, networkId):
        return self.proxy.RemoveNetworkLocationFromStream(privId, streamId,
                                                            networkId)

    def GetEventServiceLocation(self):
        return self.proxy.GetEventServiceLocation()
    
    def AllocateMulticastLocation(self):
        return self.proxy.AllocateMulticastLocation()

    def GetCachedProfiles(self):
        return self.proxy.GetCachedProfiles()
    
    # -----------------------------------------------------
    # This allows old clients to connect to new servers.
    #
    def IsValid(self):
        return 1
    
    # -----------------------------------------------------


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

