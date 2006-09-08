#-----------------------------------------------------------------------------
# Name:        Venue.py
# Purpose:     The Virtual Venue is the object that provides the collaboration
#               scopes in the Access Grid.
# Created:     2002/12/12
# RCS-ID:      $Id: Venue.py,v 1.277 2006-09-08 21:29:22 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
The Venue provides the interaction scoping in the Access Grid. This module
defines what the venue is.
"""

__revision__ = "$Id: Venue.py,v 1.277 2006-09-08 21:29:22 turam Exp $"

import sys
import time
import re
import string
import socket
import os.path

from AccessGrid import Log
from AccessGrid.Toolkit import Service

from AccessGrid.Security.AuthorizationManager import AuthorizationManager
from AccessGrid.interfaces.AuthorizationManager_interface import AuthorizationManager as AuthorizationManagerI
from AccessGrid.Security import X509Subject, Role, Subject, Action
from AccessGrid.Security.Subject import SubjectAlreadyPresent

from AccessGrid import DataStore
from AccessGrid import NetService
from AccessGrid.Descriptions import Capability, Capability3
from AccessGrid.SharedApplication import SharedApplication
from AccessGrid.Descriptions import StreamDescription, StreamDescription3
from AccessGrid.Descriptions import DirectoryDescription
from AccessGrid.Descriptions import FileDescription
from AccessGrid.Descriptions import ConnectionDescription, VenueDescription, VenueDescription3
from AccessGrid.Descriptions import ApplicationDescription, ServiceDescription
from AccessGrid.Descriptions import DataDescription, VenueState, DataDescription3, VenueState3
from AccessGrid.Descriptions import BadDataDescription, BadServiceDescription
from AccessGrid.Descriptions import BadApplicationDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation, UnicastNetworkLocation
from AccessGrid.GUID import GUID
from AccessGrid.scheduler import Scheduler
from AccessGrid.Events import Event, DisconnectEvent
from AccessGrid.Events import ClientExitingEvent
from AccessGrid.Utilities import AllocateEncryptionKey, ServerLock
from AccessGrid.hosting import PathFromURL
from AccessGrid.Platform.Config import UserConfig, SystemConfig
from AccessGrid.ClientProfile import ClientProfileCache, InvalidProfileException
from AccessGrid.NetworkServicesManager import NetworkServicesManager
from AccessGrid.interfaces.AccessGrid_Types import www_accessgrid_org_v3_0 as AGTypes
from AccessGrid.interfaces.Venue_interface import Venue as VenueI
from AccessGrid.interfaces.Venue_client import VenueIW
from AccessGrid.interfaces.SharedApplication_interface import SharedApplication as SharedApplicationI
from AccessGrid.InProcessVenueEventClient import InProcessVenueEventClient
from AccessGrid import Version

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
    
class CertificateRequired(Exception): pass


class VenueClientState:
    """
    Instances of the VenueClientState class hold the per-client state that the
    venue cares about. This includes the client's profile, the last time
    a heartbeat was received from the client, the client's connections
    to the text and event services, and any queues of events waiting to be
    delivered to those services (after the client connects, before the
    client's event client connects to the service).

    One thing to add in here is to put a status variable, this is
    where a method call can be used to change the status of client connections.

    """
    def __init__(self, venue, timeout, connectionId, profile):
        self.profile = profile
        self.venue = venue
        self.connectionId = connectionId
        self.timeout = time.time() + timeout
        self.status = None
        
    def __repr__(self):
        s = "VenueClientState(name=%s connectionId=%s)" % (
            self.profile.name, self.connectionId)
        return s

    def GetClientProfile(self):
        return self.profile

    def UpdateClientProfile(self, profile):
        self.profile = profile

    def SetTimeout(self, t_next):
        #log.debug("SET TIMEOUT TO: %d now = %d", t_next, time.time())
        self.timeout = t_next

    def GetTimeout(self):
        return self.timeout
    
    def CheckTimeout(self, timeout):
        log.debug("Client Timeout Check: %d vs %d", self.timeout, timeout)
        if self.timeout < timeout:
            return 1
        else:
            return 0
        
    def GetConnectionId(self):
        return self.profile.GetConnectionId()
    
    def GetPublicId(self):
        return self.profile.GetPublicId()

    def GetStatus(self):
        return self.status

    def SetStatus(self, status):
        self.status = status
        
class Venue:
    """
    A Virtual Venue is a virtual space for collaboration on the Access Grid.
    """
    
    
    def authorize(self, auth_info, post, action):
        from ZSI.ServiceContainer import GetSOAPContext
        ctx = GetSOAPContext()
#         print dir(ctx)
#         print "Container: ", ctx.connection
#         print "Parsed SOAP: ", ctx.parsedsoap
#         print "Container: ", ctx.container
#         print "HTTP Headers:\n", ctx.httpheaders
#         print "----"
#         print "XML Data:\n", ctx.xmldata
        try:
            if hasattr(ctx.connection,'get_peer_cert'):
                cert = ctx.connection.get_peer_cert()
                if cert:
                    subject = cert.get_subject().as_text()
                    subject = X509Subject.X509Subject(subject)
                else:
                    if self.authManager.IsIdentificationRequired():
                        raise CertificateRequired
                        
                    subject = None
                    
                # Check whether user is authorized to perform this action
                action = action.split('#')[-1]
                isAuth = self.authManager.IsAuthorized(subject, action) 
                if isAuth:
                    return 1
                
                # If user is a venueserver admin, allow them to do whatever they 
                # want to a venue
                adminRole = self.server.authManager.FindRole('Administrators')
                admins = self.server.authManager.GetSubjects(adminRole)
                if subject in admins:
                    return 1
                    
                return 0
        except CertificateRequired:
            raise
        except:
            log.exception("Exception in Venue.authorize; rejecting authorization")
            return 0
    
    def __init__(self, server, name, description, dataStoreLocation,
                 oid=None):
        """
        Venue constructor.
        """
        self.authManager = AuthorizationManager()
        
        # pointer to outside world
        self.servicePtr = Service.instance()
        
        if oid:
            self.uniqueId = oid
        else:
            self.uniqueId = str(GUID())

        # Initialize Authorization Stuff
        self.authManager.AddRequiredRole(Role.Role("AllowedEntry"))
        self.authManager.AddRequiredRole(Role.Role("VenueUsers"))
        self.authManager.AddRequiredRole(Role.Administrators)
        self.authManager.AddRequiredRole(Role.Everybody)

        rl = self.authManager.GetRequiredRoles()
        self.authManager.AddRoles(rl)

        # Default actions for Entry Roles.
        self.defaultEntryActionNames = ["Enter", "Exit", "GetStreams",
                                        "UpdateLifetime",
                                        "NegotiateCapabilities",
					"NegotiateCapabilities3",
                                        "GetStaticStreams",
                                        "GetUploadDescriptor",
                                        "AsVenueDescription",
                                        "GetRolesForSubject",
                                        "CreateApplication",
                                        "UpdateApplication",
                                        "DestroyApplication",
                                        "UpdateClientProfile",
                                        "AddService", "RemoveService",
					"AddService3", "RemoveService3",
                                        "UpdateService", "GetServices",
					"UpdateService3", "GetServices3",
                                        "AddData", "UpdateData", "RemoveData",
					"AddData3", "UpdateData3", "RemoveData3",
                                        "GetDataStoreInformation",
                                        "GetDataDescriptions",
                                        "AddNetworkService",
                                        "RemoveNetworkService",
                                        "GetNetworkServices", "GetClients",
                                        "GetCachedProfiles", "AddConnection",
                                        "RemoveConnection", "GetConnections",
                                        "SetConnections", "GetEncryptMedia",
                                        "GetDescription", "GetDescription3", "GetName",
                                        "GetApplication", "GetApplications",
                                        "AddNetworkLocationToStream",
                                        "RemoveNetworkLocationFromStream",
                                        "GetEventServiceLocation",
                                        "DetermineSubjectRoles",
                                        "AddNetService", "RemoveNetService",
                                        "IsAuthorized", "IsValid",
                                        "AllocateMulticastLocation",
                                        "RecycleMulticastLocation",
                                        "GetState",
					"GetState3",
                                        "AddDir",
					"GetDescById",
                                        "RemoveDir",
                                        "HDDump",
                                        "GetVersion",
					"GetDataSize",
                                        ]
        # Methods in Venue IW that are not default to everybody:
        #   "Shutdown", "SetEncryptMedia", "RegenerateEncryptionKeys",
        #   "SetDescription", "SetName", "AddStream", "RemoveStream",
        #   "ImportAuthorizationPolicy", 
        #   "AddSubjectToRole", "RemoveSubjectFromRole", "SetSubjectsInRole",
        #   "FlushRoles", "GetUsersInRole", "GetRoleNames"

        # Default actions for VenueUsers Roles.
        self.defaultVenueUserActionNames = ["AddDir"]

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
        self.clientDisconnectOK = {}
        self.maxTimeout = 120.0
        
        self.connections = list()
        self.applications = dict()
        self.services = dict()
        self.streamList = StreamDescriptionList()
        self.clients = dict()
        self.netServices = dict()
        self.networkServicesManager = NetworkServicesManager()
        
        # Dictionary keyed on client private id; value
        # true if a remove is in process on this client.
        self.clientsBeingRemoved = {}
        self.clientsBeingRemovedLock = ServerLock("clientRemove")

        self.dataStore = None
        self.producerCapabilities = []
        self.consumerCapabilities = []

        if self.server != None:
            self.uri = self.server.MakeVenueURL(self.uniqueId)

            log.info("Venue URI %s", self.uri)

            # Send an Add Venue Event to the services
            # Then they can create create channels

            # or

            # make a call to create channels in the services
            
        # Create the directory to hold the venue's data.
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

        # Start the event client.
        self.eventClient = InProcessVenueEventClient(self.server.eventService, 
                                       self.GetId(),
                                       self.GetId())
        self.eventClient.Start()
        
            
    

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
        log.info("Building auth policy.")
        
        # Add default entry roles to entry actions.
        for actionName in self.defaultEntryActionNames:
            self.authManager.AddRoleToAction(Action.Action(actionName), 
                                             Role.Role("AllowedEntry"))
            self.authManager.AddRoleToAction(Action.Action(actionName),
                                             Role.Everybody)

        # Add default entry roles to venueusers actions.
        # Currently no actions include VenueUsers
        for actionName in self.defaultVenueUserActionNames:
            self.authManager.AddRoleToAction(Action.Action(actionName), 
                                             Role.Role("VenueUsers"))

    def _UpdateProfileCache(self, profile):
        try:
            self.cache.updateProfile(profile)
        except InvalidProfileException:
            log.warn("UpdateProfileCache: InvalidProfile when storing a venue user's profile in the cache.")
        except:
            log.exception("UpdateProfileCache: Unable to write venue user's profile in the cache.")

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

        # Venue Authorization Policy
        policy = self.authManager.ExportPolicy()
        # Don't store these control characters, but lets make sure we
        # bring them back
        policy = re.sub("\r\n", "<CRLF>", policy)
        policy = re.sub("\r", "<CR>", policy)
        policy = re.sub("\n", "<LF>", policy)
        string += 'authorizationPolicy : %s\n' % policy

        #
        ##  END OF VENUE SECTION

        
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
	Method for legacy support for AG 3.0.2. clients
        """
        desc = VenueDescription(self.name, self.description,
                                (self.encryptMedia, self.encryptionKey),
                                self.connections,
                                self.GetStaticStreams(),
                                self.uniqueId)
        uri = self.server.MakeVenueURL(self.uniqueId)
        desc.SetURI(uri)

        return desc
    
    def AsVenueDescription3(self):
        """
        This creates a Venue Description filled in with the data from
        this venue.
        """
        desc = VenueDescription3(self.name, self.description,
                                (self.encryptMedia, self.encryptionKey),
                                self.connections,
                                self.GetStaticStreams(),
                                self.uniqueId)
        uri = self.server.MakeVenueURL(self.uniqueId)
        desc.SetURI(uri)

        return desc

    def AsVenueState(self):
        """
        This creates a Venue State filled in with the data from this
        venue.
	Method for legacy support for AG 3.0.2. clients
        """

        try:
            dList = self.dataStore.GetDataDescriptions()
	    log.debug("List of DataDescriptions")
	    for item in dList:
		log.debug("%s: %s", item.GetObjectType(), item.GetName())
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
                                dList, None, None, None, applist,
                                self.services.values())
        return venueState

    def AsVenueState3(self):
        """
        This creates a Venue State filled in with the data from this
        venue.
        """

        try:
            dList = self.dataStore.GetDataDescriptions3()
	    log.debug("List of DataDescriptions")
	    for item in dList:
		log.debug("%s: %s", item.GetObjectType(), item.GetName())
        except:
            log.exception("Venue::AsVenueState3: Failed to get data descrs.")
            dList = []

        try:
            applist = map(lambda x: x.AsApplicationDescription(),
                          self.applications.values())
        except:
            log.exception("Venue::AsVenueState3: Failed to get applications.")
            applist = []
            
        try:
            clientlist = map(lambda c: c.GetClientProfile(),
                             self.clients.values())
        except:
            log.exception("Venue::AsVenueState3: Failed to get profiles.")
            clientlist = []

        venueState = VenueState3(self.uniqueId, self.name, self.description,
                                self.uri, self.connections, clientlist,
                                dList, None, None, None, applist,
                                self.services.values())
        return venueState


    def GetState(self):
	"""
	Method for legacy support for AG 3.0.2. clients
	"""
        venueState = self.AsVenueState()
        # change to lists until zsi can handle dictionaries.
        venueState.clients = venueState.clients.values()
        venueState.data = venueState.data.values()
        venueState.services = venueState.services.values()
        venueState.applications = venueState.applications.values()
        venueState.connections = venueState.connections.values()
        venueState.dataLocation = self.GetUploadDescriptor()

        # tuple of different types can't be serialized
        venueState.eventLocation=  ":".join(map(lambda x : str(x), self.GetEventServiceLocation() ))
        venueState.textLocation = ":".join(map(lambda x : str(x), self.GetTextServiceLocation() ))
	
	                
        return venueState

    def GetState3(self):
        venueState = self.AsVenueState3()
        # change to lists until zsi can handle dictionaries.
        venueState.clients = venueState.clients.values()
        venueState.data = venueState.data.values()
        venueState.services = venueState.services.values()
        venueState.applications = venueState.applications.values()
        venueState.connections = venueState.connections.values()
        venueState.dataLocation = self.GetUploadDescriptor()

        # tuple of different types can't be serialized
        venueState.eventLocation=  ":".join(map(lambda x : str(x), self.GetEventServiceLocation() ))
        venueState.textLocation = ":".join(map(lambda x : str(x), self.GetTextServiceLocation() ))
	
	                
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
#            appImpl.Awaken(self.server.eventService)
            app = SharedApplicationI(impl=appImpl, auth_method_name="authorize")
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
        now_sec = time.time()

        log.debug("CleanupClients: now=%d", now_sec)
        
        self.clientsBeingRemovedLock.acquire()

        # Look for users to remove
        clientsToRemove = []
        for connId in self.clients.keys():
            try:
                log.debug("CleanupClients: client %s %s timeout=%d", connId, self.clients[connId].GetClientProfile().name,
                            self.clients[connId].GetTimeout())
                if self.clients[connId].CheckTimeout(now_sec):
                    log.info("  User %s %s will be removed (Timed Out)", connId, self.clients[connId].GetClientProfile().name)
                    clientsToRemove.append(connId)
            except:
                log.exception('Error removing client with connId=%s', connId)

        self.clientsBeingRemovedLock.release()
        
        # Actually remove users
        for connId in clientsToRemove:
            try:
                self.RemoveUser(connId)
            except:
                log.exception("Error removing user; connId=%s", connId)
                
                
        for connId in self.netServices.keys():
            try:
                if self.netServices[connId][1] > now_sec:
                    log.info("Removing network service %s at %d (Timed Out)",
                              connId, now_sec)
                    self.RemoveNetworkService(connId)
            except:
                log.exception('Error removing netService with connId=%s', connId)
                
    def __GetMatchingStream(self, capabilities):
        '''
        Get streams that matches the capabilities of a service
        '''
        serviceProducerCaps = filter(lambda x: x.role == Capability.PRODUCER, capabilities)
        serviceConsumerCaps = filter(lambda x: x.role == Capability.CONSUMER, capabilities)
        streams = self.streamList.GetStreams()
        streams = filter(lambda x: x.capability[0].type == capabilities[0].type, streams)
        matchingStreams = []

        for s in streams:
            streamProducerCaps = filter(lambda x: x.role == Capability.PRODUCER, s.capability)
            streamConsumerCaps = filter(lambda x: x.role == Capability.CONSUMER, s.capability)
          
            streamConsumerMatch = 0
            serviceConsumerMatch = 0

            # Compare stream producer capabilities to
            # service consumer capabilities
            for cap in streamProducerCaps:
                for ccap in serviceConsumerCaps:
                    if ccap.matches(cap):
                        # found matching service consumer
                        serviceConsumerMatch = 1

            if len(streamProducerCaps)==0 or len(serviceConsumerCaps) == 0:
                serviceConsumerMatch = 1

            # Compare service producer capabilities
            # to stream consumer capabilities
            for cap in serviceProducerCaps:
                for ccap in streamConsumerCaps:
                    if ccap.matches(cap):
                        streamConsumerMatch = 1

            if len(serviceProducerCaps)==0 or len(streamConsumerCaps) == 0:
                streamConsumerMatch = 1

            # If all producers found a matching consumer,
            # the stream matches
            if serviceConsumerMatch and streamConsumerMatch:
                matchingStreams.append(s)

        # Just return the first stream that matches
        if len(matchingStreams)>0:
            return matchingStreams[0]
        else:
            return None

    def __AddCapabilitiesToStream(self, stream, capabilities):
        match = 0
        for cap in capabilities:
            for c in stream.capability:
                if c.matches(cap):
                    match = 1
            if not match:
                caps = stream.capability
                caps.append(cap)
                stream.capability = caps
            
    def NegotiateCapabilities3(self, privateId, capabilities):
        """
        This method takes node capabilitis and finds a set of streams that
        matches those capabilities.  This method uses the network services
        manager to find The Best Match of all the network services, the
        existing streams, and all the client capabilities.
        
        **Arguments:**
        
        *privateId* Private id for the node
        *capabilities* Node capabilities
        """
        log.debug("negotiate capabilities")
	

        if not self.clients.has_key(privateId):
            raise InvalidVenueState
               
        streamDescriptions = []

        # group service capabilities together
        services = {}
        for c in capabilities:
	    log.debug("Capability to be processed: %s", c)
            if services.has_key(c.serviceId):
                caps = services[c.serviceId]
                caps.append(c)
                services[c.serviceId] = caps
            else:
                services[c.serviceId] = [c]

        # For each service, find a stream that matches
        streams = None
        matchesExistingStream = 0
        mismatchedServices = []
        
        for serviceId in services.keys():
            stream = self.__GetMatchingStream(services[serviceId])
            nrOfProducers = filter(lambda x: x.role == Capability3.PRODUCER, capabilities)
            
            # If matching stream is found, add capabilities to the stream
            if stream:
                self.__AddCapabilitiesToStream(stream, services[serviceId])
                
                # If the service has producer capabilities, add user as producer
                if len(nrOfProducers)>0:
                    self.streamList.AddStreamProducer(privateId,
                                                      stream)
                
                log.debug("added user as producer of existent stream")
            else:
                # Check if network service can resolve mismatch
                matchingStreams = []
                streams = self.streamList.GetStreams()
                if streams:
                    matchingStreams = self.networkServicesManager.ResolveMismatch(
                        streams , services[serviceId])

                for streamList, producer in matchingStreams:
                    for s in streamList:
                        if not self.streamList.FindStreamByDescription(s):
                            # Make new stream available for other clients.
                            self.streamList.AddStream3(s)
                            # Also add a new producer of the stream.
                            self.streamList.AddStreamProducer( producer, s)
                      
                # Create new stream
                if not matchingStreams:
		    log.debug("Stream doesn't exist create new one!")
		    locCap = services[serviceId]
		    log.debug("Stream type: %s!", locCap[0].type)
			
		    #Proposed change for determining the correct capability for IP creation
		    #for item in locCap
		    #    if item.type == "COVISE":
		    #        correctCap = item
		    		    
		    
		    #AG3.0.2 exception block
		    try:
			for entry in locCap:
			    log.debug(" Caps: %s", entry)
			    
		    	if locCap[0].locationType == Capability3.PREFERRED_UNICAST:
			    log.debug("Stream prefers unicast!")
			    addr = self.AllocateUnicastLocation(locCap[0])
		    	else:
			    log.debug("Stream prefers multicast!")
			    addr = self.AllocateMulticastLocation()
                    
                        log.debug("Stream address: %s : %s", addr.GetHost(), addr.GetPort())
		    except:
			log.debug("AG3.0.2 client! Only multicast address!")
			addr = self.AllocateMulticastLocation()
		    
		    streamDesc = StreamDescription3(self.name,
                                                   addr, services[serviceId], 
                                                   self.encryptMedia, 
                                                   self.encryptionKey,0)
                    log.debug("added user as producer of non-existent stream")
                    self.streamList.AddStreamProducer( privateId,
                                                       streamDesc )

        # return all available streams
        return  self.streamList.GetStreams()    
       
    def NegotiateCapabilities(self, privateId, capabilities):
        """
        This method takes node capabilitis and finds a set of streams that
        matches those capabilities.  This method uses the network services
        manager to find The Best Match of all the network services, the
        existing streams, and all the client capabilities.

	Method for legacy support for AG 3.0.2. clients
        
        **Arguments:**
        
        *privateId* Private id for the node
        *capabilities* Node capabilities
        """
        log.debug("negotiate capabilities")

        if not self.clients.has_key(privateId):
            raise InvalidVenueState
               
        streamDescriptions = []

        # group service capabilities together
        services = {}
        for c in capabilities:
            if services.has_key(c.serviceId):
                caps = services[c.serviceId]
                caps.append(c)
                services[c.serviceId] = caps
            else:
                services[c.serviceId] = [c]

        # For each service, find a stream that matches
        streams = None
        matchesExistingStream = 0
        mismatchedServices = []
        
        for serviceId in services.keys():
            stream = self.__GetMatchingStream(services[serviceId])
            nrOfProducers = filter(lambda x: x.role == Capability.PRODUCER, capabilities)
            
            # If matching stream is found, add capabilities to the stream
            if stream:
                self.__AddCapabilitiesToStream(stream, services[serviceId])
                
                # If the service has producer capabilities, add user as producer
                if len(nrOfProducers)>0:
                    self.streamList.AddStreamProducer(privateId,
                                                      stream)
                
                log.debug("added user as producer of existent stream")
            else:
                # Check if network service can resolve mismatch
                matchingStreams = []
                streams = self.streamList.GetStreams()
                if streams:
                    matchingStreams = self.networkServicesManager.ResolveMismatch(
                        streams , services[serviceId])

                for streamList, producer in matchingStreams:
                    for s in streamList:
                        if not self.streamList.FindStreamByDescription(s):
                            # Make new stream available for other clients.
                            self.streamList.AddStream(s)
                            # Also add a new producer of the stream.
                            self.streamList.AddStreamProducer( producer, s)
                      
                # Create new stream
                if not matchingStreams:
                    addr = self.AllocateMulticastLocation()
                    streamDesc = StreamDescription( self.name,
                                                    addr, services[serviceId], 
                                                    self.encryptMedia, 
                                                    self.encryptionKey,0)
                    log.debug("added user as producer of non-existent stream")
                    self.streamList.AddStreamProducer( privateId,
                                                       streamDesc )

        # return all available streams
        return  self.streamList.GetStreams()

    def FindConnection(self, cid):
        if self.clients.has_key(cid):
            return self.clients[cid]
        
        if self.netServices.has_key(cid):
            return self.netServices[cid]

        return None

    def UpdateLifetime(self, cid, requestedTimeout=0):
        """
        """
        conn = self.FindConnection(cid)
        if conn is not None:
        
            # Require the client to send another message before the timeout
            conn.SetTimeout(time.time() + self.maxTimeout)
            
            # Tell the client to send a message well before the timeout
            clientNextHeartbeat = .3*self.maxTimeout;
            log.debug("UpdateLifetime: %s %s ; next heartbeat by %d", 
                      conn.profile.connectionId, conn.profile.name,
                      clientNextHeartbeat)
            return clientNextHeartbeat
        else:
            log.debug("UpdateLifetime: connection not found: cid=%s", cid)
            return -1

    #Added by NA2-HPCE
    def AllocateUnicastLocation(self, capability):
	"""
        This method creates a new Unicast Network Location based
	on the service preferred IP in the capability

        **Returns:**

        *location* A new unicast network location object.
        """
        location = UnicastNetworkLocation(capability.host, capability.port)

        return location

    def AllocateMulticastLocation(self):
        """
        This method creates a new Multicast Network Location.

        **Returns:**

        *location* A new multicast network location object.
        """
        defaultTtl = 127
        evenPortFlag = 1
        location = MulticastNetworkLocation(
                        self.server.multicastAddressAllocator.AllocateAddress(),
                        self.server.multicastAddressAllocator.AllocatePort(evenPortFlag),
                        defaultTtl )

        return location

    def RecycleMulticastLocation(self, location):
        """
        This method creates a new Multicast Network Location.

        **Returns:**

        *location* A new multicast network location object.
        """
        try:
            self.server.multicastAddressAllocator.RecycleAddress(location.host)
        except:
            log.exception("Failed to recycle multicast address %s", location.host)
        
        try:
            self.server.multicastAddressAllocator.RecyclePort(location.port)
        except:
            log.exception("Failed to recycle port %d", location.port) 

    def GetNextPrivateId( self ):
        """
        This method creates the next Private Id.

        **Returns:**

        *privateId* A unique private id.
        """

        privateId = str(GUID())

        return privateId

    def RemoveUser(self, privateId):
        """
        This method removes a user from the venue, cleaning up all the
        state associated with that user.

        **Arguments:**

        *privateId* The private Id of the user being removed.

        """

        self.clientsBeingRemovedLock.acquire()

        try:
            if privateId in self.clientsBeingRemoved and self.clientsBeingRemoved[privateId]:
                log.debug("RemoveUser: private id %s already being removed", privateId)
                self.clientsBeingRemovedLock.release()
                return
            
            self.clientsBeingRemoved[privateId] = 1
           
        except:
            log.exception("Venue.RemoveUser: Failed")
            
        self.clientsBeingRemovedLock.release()

        self.simpleLock.acquire()

        try:
            try:
                # Remove user as stream producer
                log.debug("Called RemoveUser on %s", privateId)
                self.streamList.RemoveProducer(privateId)
            except:
                log.exception("Error removing Producers")
                
            try:
                # Remove clients from venue
                if not self.clients.has_key(privateId):
                    log.warn("RemoveUser: Tried to remove a client that doesn't exist")
                    usage_log.info("\"RemoveUser\",\"%s\",\"%s\",\"%s\"", "DN Unavailable", self.name, self.uniqueId)
                    self.simpleLock.release()
                    return
                else:
                    usage_log.info("\"RemoveUser\",\"%s\",\"%s\",\"%s\"", 
                               self.clients[privateId].GetClientProfile().GetDistinguishedName(), 
                               self.name, self.uniqueId)
            except:
                log.exception("Error starting to remove client from venue")

            try:
                # Remove the user from the venue users role
                # - get the subject of the user to remove
                cp =self.clients[privateId].GetClientProfile()
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

            except:
                log.exception("Error removing client from venue users role")
                
            try:
                vclient = self.clients[privateId]
                clientProfile = vclient.GetClientProfile()
            except:
                log.exception("Error getting VenueClientState and profile to remove")

            try:
                if privateId in self.clients:
                    del self.clients[privateId]
            except:
                log.exception("Venue.RemoveUser: Error deleting client.")

            log.debug("RemoveUser: Distribute EXIT event")
            self.eventClient.Send(Event.EXIT, clientProfile)
          
        except:
            log.exception("Venue.RemoveUser: Body of method threw exception")

       
        self.clientsBeingRemovedLock.acquire()
        try:
            del self.clientsBeingRemoved[privateId]
        except:
            log.exception("Venue.RemoveUser: Failed")
            
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
        #self.eventClient.Send(Event.SET_CONNECTIONS, connectionList)

    def Enter(self, clientProfile):
        """
        The Enter method is used by a VenueClient to gain access to the
        services, clients, and content found within a Virtual Venue.

        **Arguments:**

        *clientProfile* The profile of the client entering the venue.

        **Returns:**

        *(state, privateId)* This tuple is
        returned upon success. The state is a snapshot of the
        current venuestate. The privateId is a private, unique id
        assigned by the venue for this client session.
        """
        log.debug("Enter called.")
        # allocate connection-specific id;
        # this is passed back to 2.3+ clients in the private id, 
        # which unfortunately lengthens the private id generally
        clientProfile.connectionId = str(GUID())
        log.debug("Enter: Assigning connection id: %s", clientProfile.connectionId)
        # Send this before we set up client state, so that
        # we don't end up getting our own enter event enqueued.

        self.eventClient.Send(Event.ENTER, clientProfile)
        # Create venue client state object
        vcstate = self.clients[clientProfile.connectionId] = VenueClientState(self,
                                                             self.maxTimeout,
                                                   clientProfile.connectionId,
                                                             clientProfile)
        self._UpdateProfileCache(clientProfile)
        usage_log.info("\"Enter\",\"%s\",\"%s\",\"%s\"",
                       clientProfile.GetDistinguishedName(),
                       self.name, self.uniqueId)
        log.debug("Current users:")
        for c in self.clients.values():
            log.debug("   " + str(c))
        log.debug("Enter: Distribute enter event ")

        try:
            if self.servicePtr.GetOption("secure"):
                dn = clientProfile.GetDistinguishedName()
                self.authManager.FindRole("VenueUsers").AddSubject(X509Subject.CreateSubjectFromString(dn))
        except SubjectAlreadyPresent:
            log.info("User already in venue users list: %s", dn)

        try:
            state = self.AsVenueState3()
            log.debug("state: %s", state)
        except:
            log.exception("Enter: Can't get state.")
            raise InvalidVenueState

        return clientProfile.connectionId



    def RegisterNetworkService(self, nsd):
        """
        Registers a network service with the venue.
        
        @Param networkServiceDescription: A network service description.
        """
        log.debug('register network service %s'%nsd.name)
        try:
            self.networkServicesManager.RegisterService(nsd)
            #self.eventClient.Send(Event.ADD_SERVICE, nsd)
          
        except:
            log.exception('Venue.RegisterNetworkService: Failed')
            raise Exception, 'Venue.RegisterNetworkService: Failed'
           
    def UnRegisterNetworkService(self, nsd):
        """
        Removes a network service from the venue
        
        @Param networkServiceDescription: A network service description.*
        """
        try:
            self.networkServicesManager.UnRegisterService(nsd)
            self.streamList.RemoveProducer(nsd.uri)
            #self.eventClient.Send(Event.REMOVE_SERVICE, nsd)
          
        except:
            log.exception('Venue.UnRegisterNetworkService: Failed')
            raise Exception, 'Venue.UnRegisterNetworkService: Failed'

    def GetNetworkServices(self):
        """
        GetNetworkServices returns a list of all the network services
        in this venue.
        
        @returns: A list of NetworkServiceDescriptions.
        """
        try:
            s = self.networkServicesManager.GetServices()
        except:
            log.exception('Venue.GetNetworkServices: Failed')
            raise Exception, 'Venue.GetNetworkServices: Failed.'
        return s
        
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
            #self.server.eventService.CloseConnection(netService.connObj)
            netService.connObj = None

        # Remove the netservice from the netservice list
        del self.netServices[privateId]

   

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

        try:
            # Shut down event client
            self.eventClient.Stop()
        except:
            log.exception("Venue.ShutDown could not stop event client")

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

        self.eventClient.Send(Event.ADD_SERVICE, serviceDescription)

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

        self.eventClient.Send(Event.UPDATE_SERVICE, serviceDescription)
    
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
        self.eventClient.Send(Event.REMOVE_SERVICE, serviceDescription)
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
        self.eventClient.Send(Event.ADD_CONNECTION, connectionDesc)
                 
    def RemoveConnection(self, connectionDesc):
        """
        """
        
        found = 0
            
        for c in self.connections:
            if c.GetURI() == connectionDesc.GetURI():
                found = 1
                self.connections.remove(c)
                self.eventClient.Send(Event.REMOVE_CONNECTION, connectionDesc)
         
        if not found:
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
                    self.eventClient.Send(Event.MODIFY_STREAM, stream)
               
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
        
    #ZSI:HO
    def GetDataSize(self):
	retVal = self.dataStore.GetDataSize()
	log.debug("Value in Venue: %s", retVal)
	return retVal
	
    
    # Added by NA2-HPCE
    def GetCurDataDesc(self):
	return self.dataStore.GetCurDataDesc()
    
    def GetDescById(self, id):
	return self.dataStore.GetDescById(id)

    def GetName(self):
        """
        GetName returns the name for the virtual venue.
        """
        return self.name

    def GetClients(self):
        """
        Return a list of the clients in this venue.
        """
        clientlist = map(lambda c: c.GetClientProfile(),
                             self.clients.values())
        return clientlist
    
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
        self.eventClient.Send(Event.ADD_STREAM, inStreamDescription)
	     
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
        self.eventClient.Send(Event.REMOVE_STREAM, inStreamDescription)
	
      
    def GetStreams(self):
        """
        GetStreams returns a list of stream descriptions to the caller.
	Method for legacy support for AG 3.0.2. clients
        """
        return self.streamList.GetStreams()

    def GetStreams3(self):
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

        self.clientsBeingRemovedLock.acquire()
        try:
            if not self.clients.has_key( privateId ):
                log.exception("Exit: User not found!")
                usage_log.info("\"Exit\",\"%s\",\"%s\",\"%s\"", 0, self.name, self.uniqueId)
                raise ClientNotFound
            else:
                usage_log.info("\"Exit\",\"%s\",\"%s\",\"%s\"", self.clients[privateId].GetClientProfile().GetDistinguishedName(), self.name, self.uniqueId)
        except:
            log.exception("Error in usage logging")
            
        self.clientsBeingRemovedLock.release()

        try:
            self.RemoveUser(privateId)
        except:
            log.exception('Error in Venue.Exit; privateId=%s', privateId)


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

        self.clientsBeingRemovedLock.acquire()
        try:
            for connectionId in self.clients.keys():
                vclient = self.clients[connectionId]
                if vclient.GetPublicId() == clientProfile.publicId:
                    vclient.UpdateClientProfile(clientProfile)
                    #vclient.UpdateAccessTime()

            self.eventClient.Send(Event.MODIFY_USER, clientProfile)
        except:
            log.exception('Error updating client profile')
        
        self.clientsBeingRemovedLock.release()
              
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
                self.eventClient.Send(Event.MODIFY_STREAM, stream)
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
                self.eventClient.Send(Event.MODIFY_STREAM, stream)
              
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
                self.eventClient.Send(Event.MODIFY_STREAM, stream)
                pass
             
    def GetEventServiceLocation(self):
        # return (self.server.GetEventServiceLocation(), self.uniqueId)

        serverServices = self.server.GetServices()
        location = None
        
        for s in serverServices:
            if s.GetType() == "AsyncoreEvent":
                location = s.GetLocation()
        return location

    def GetTextServiceLocation(self):
        serverServices = self.server.GetServices()
        location = None
        
        for s in serverServices:
            if s.GetType() == "JabberText":
                location = s.GetLocation()
      
        return location

    def AddData(self, dataDescription ):
        """
        LEGACY: This is just left here not to change the interface for
        AG2.0 clients. (personal data)
        """
        legacyObject = self.CreateLegacyDataDescription(dataDescription)
        self.eventClient.Send( Event.ADD_DATA, legacyObject)
	
	
    	
    # Added by NA2-HPCE
    def AddRootDir(self, dataDesc):
        locDataDesc=self.dataStore.AddRootDir(dataDesc)
	
        self.server.eventService.Distribute(self.uniqueId,
                                             Event(Event.ADD_DATA,
                                                    self.uniqueId,
                                                    locDataDesc))
	
    def AddEntryPoint(self, directory, parent):
        server.AddEntryPoint(directory,parent,self.uniqueId)
	    
    
    # Added by NA2-HPCE for debugging
    def HDDump(self):
        self.dataStore.Dump()
	   
    #Added by NA2-HPCE
    def AddDir(self, name, desc, level, puid):
        log.debug("CreateDir %s at level %s", name, level)
        locDataDesc=self.dataStore.AddDir(name, desc, level, puid)
	
        #self.server.eventService.Distribute(self.uniqueId,
                                             #Event(Event.ADD_DATA,
                                                    #self.uniqueId,
                                                    #locDataDesc))
	
        #Converting to list to work around non-functioning dictionaries
        #locDataDesc.dataContainer.data = locDataDesc.dataContainer.values()

        #Send event to clients
        log.debug("Sending update event for added directory!")
        self.eventClient.Send(Event.ADD_DIR,locDataDesc.id)

    def RemoveData(self, dataDescription):
        """
        RemoveData removes persistent data from the Virtual Venue.
        **Arguments:**

        *dataDescription* A real data description.

        **Raises:**

        *DataNotFound* Raised when the data is not found in the Venue.

        **Returns:**

        *dataDescription* Upon successfully removing the data.

	Method for legacy support for AG 3.0.2. clients
	
        """

        name = dataDescription.name

        # This is venue resident so delete the file
        if(dataDescription.type is None or dataDescription.type == "None"):
	    log.debug("Entered Event activiation!")
	    if self.dataStore.RemoveFiles([dataDescription]):
		return dataDescription
	    legacyObject = self.CreateLegacyDataDescription(dataDescription)
            self.eventClient.Send( Event.REMOVE_DATA, legacyObject)
        else:
            log.info("Venue.RemoveData tried to remove non venue data.")

        return dataDescription

    def RemoveData3(self, dataDescription):
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
	    log.debug("Entered Event activiation!")
	    self.dataStore.DumpDataStack()
            self.dataStore.RemoveFiles3([dataDescription])
	    legacyObject = self.CreateLegacyDataDescription(dataDescription)
            self.eventClient.Send(Event.REMOVE_DATA, legacyObject)
	    self.dataStore.DumpDataStack()
        else:
            log.info("Venue.RemoveData tried to remove non venue data.")

        return dataDescription
    
    #Added by NA2-HPCE
    def RemoveDir(self, data):
        """
        RemoveData removes persistent data from the Virtual Venue.
        **Arguments:**

        *dataDescription* A real data description.

        **Raises:**

        *DataNotFound* Raised when the data is not found in the Venue.

        **Returns:**

        *dataDescription* Upon successfully removing the data.
        """

        #ame = dataDescription.name

        # This is venue resident so delete the file
	if isinstance(data, DataDescription3):
	    self.dataStore.RemoveDir(data.id)
	    log.debug("Send Event - Data: %s", data.id)
	else:
	    return 0
        
	#Send event to clients
	
	self.eventClient.Send(Event.REMOVE_DIR,data)

	    
            
        return id

    def UpdateData(self, dataDescription, dataStoreCall = 0):
        """
        Replace the current description for dataDescription.name with
        this one.

	Method for legacy support for AG 3.0.2. clients
        """
        #
        # This method is called both from the data store and from clients.
        # The data store only wants to distribute an event, while clients
        # need to modify the actual data store.
        #
        
        if dataStoreCall:
	    legacyObject = self.CreateLegacyDataDescription(dataDescription)
            self.eventClient.Send( Event.UPDATE_DATA, legacyObject)
            return

        # This is venue resident so modify the file
        if(dataDescription.type is None or dataDescription.type == "None"):
            self.dataStore.ModifyData(dataDescription)
	    legacyObject = self.CreateLegacyDataDescription(dataDescription)
            self.eventClient.Send( Event.UPDATE_DATA, legacyObject)

        else:
            log.info("Venue.UpdateData tried to modify non venue data. That should not happen")
            
        return dataDescription

    def UpdateData3(self, dataDescription, dataStoreCall = 0):
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
	    legacyObject = self.CreateLegacyDataDescription(dataDescription)
            self.eventClient.Send( Event.UPDATE_DATA, dataDescription)
            return

        # This is venue resident so modify the file
        if(dataDescription.type is None or dataDescription.type == "None"):
            self.dataStore.ModifyData3(dataDescription)
	    legacyObject = self.CreateLegacyDataDescription(dataDescription)
            self.eventClient.Send( Event.UPDATE_DATA, legacyObject)

        else:
            log.info("Venue.UpdateData tried to modify non venue data. That should not happen")
            
        return dataDescription

    def DistributeEvent(self, type, data):
        self.eventClient.Send(type, data)
                    
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
	Method for legacy support for AG 3.0.2. clients
        """
        try:
            dList = self.dataStore.GetDataDescriptions()
            return dList
        except:
            log.exception("Venue.GetDataDescriptions.")
            dList = []
            raise
    def GetDataDescriptions3(self):
        """
        """
        try:
            dList = self.dataStore.GetDataDescriptions3()
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
        appI = SharedApplicationI(impl=app, auth_method_name="authorize")
        # pull out the venue path, so these can be a subspace
        path = self.server.hostingEnvironment.FindPathForObject(self)
        path = path + "/apps/%s" % appId
        # register the app with the hosting environment
       
        try:
            self.server.hostingEnvironment.RegisterObject(appI, path=path)
        except Exception, e:
            import traceback
            traceback.print_exc()
        # register the authorization interface and serve it.
        self.server.hostingEnvironment.RegisterObject(
                                 AuthorizationManagerI(impl=app.authManager),
                                 path=path+'/Authorization')
        # pull the url back out and put it in the app object
        appURL = self.server.hostingEnvironment.FindURLForObject(app)
        app.SetHandle(appURL)

        # grab the description, and update the universe with it
        appDesc = app.AsApplicationDescription()

        try:
            self.eventClient.Send( Event.ADD_APPLICATION, appDesc)
        except Exception, e:
            log.exception("Failed to send app creation event")
        log.debug("CreateApplication: Created id=%s handle=%s",
                  appDesc.id, appDesc.uri)
        return appDesc

    def UpdateApplication(self, applicationDesc):
        """
        Update application.

        **Arguments:**

        *applicationDesc* Object describing the application.

        **Raises:**

        *ApplicationNotFound* Raised when an application is not
        found for the application id specified.
        """
        if not self.applications.has_key(applicationDesc.id):
            raise ApplicationNotFound

        appImpl = self.applications[applicationDesc.id]
        appImpl.name = applicationDesc.name
        appImpl.description = applicationDesc.description
        
        self.applications[applicationDesc.id] = appImpl
        
        self.eventClient.Send( Event.UPDATE_APPLICATION, applicationDesc)

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
        self.eventClient.Send( Event.REMOVE_APPLICATION, appDesc)

        # Get rid of it for good
        del self.applications[appId]
        
    def GetProperty(self, propertyList):
        pname = (AGTypes, "Dictionary")
        ret_dict = AGTypes.Dictionary_(pname=pname).pyclass ; ret_dict.entries = []
        for prop in propertyList:
            if prop == "state" or prop == "venueid": 
                pname = (AGTypes, "DictionaryEntry")
                entry = AGTypes.DictionaryEntry_(pname=pname).pyclass
                entry.key = "venueid"          # entry.SetKey("venueid")
                entry.value = self.uniqueId    # entry.SetValue(self.uniqueId)
                ret_dict.entries.append(entry) # ret_dict.GetEntries().append(entry)
            if prop == "state" or prop == "name": 
                pname = (AGTypes, "DictionaryEntry")
                entry = AGTypes.DictionaryEntry_(pname=pname)
                entry.key = "name"              # entry.SetKey("name")
                entry.value = self.name         # entry.SetValue(self.name)
                ret_dict.entries.append(entry)  # ret_dict.GetEntries().append(entry)
            if prop == "state" or prop == "description": 
                pname = (AGTypes, "DictionaryEntry")
                entry = AGTypes.DictionaryEntry_(pname=pname)
                entry.key = "description"       # entry.SetKey("description")
                entry.value = self.description  # entry.SetValue(self.description)
                ret_dict.entries.append(entry)  # ret_dict.GetEntries().append(entry)
            if prop == "state" or prop == "eventLocationStr": 
                pname = (AGTypes, "DictionaryEntry")
                entry = AGTypes.DictionaryEntry_(pname=pname).pyclass
                entry.key = "eventLocationStr"         
                location = self.GetEventServiceLocation()
                # since lists won't work here yet, convert to a string
                entry.value =  ":".join(map(lambda x : str(x), location))
                ret_dict.entries.append(entry)
            if prop == "state" or prop == "textLocationStr": 
                pname = (AGTypes, "DictionaryEntry")
                entry = AGTypes.DictionaryEntry_(pname=pname).pyclass
                entry.key = "textLocationStr"         
                location = self.GetTextServiceLocation()
                # since lists won't work here yet, convert to a string
                entry.value =  ":".join(map(lambda x : str(x), location))
                ret_dict.entries.append(entry)
                     
            if prop == "state" or prop == "connections": 
                pass
            if prop == "state" or prop == "data": 
                pass
            if prop == "state" or prop == "clients": 
                pass
                """
                try:
                    clientlist = map(lambda c: c.GetClientProfile(),
                                             self.clients.values())
                except:
                    log.exception("Venue::AsVenueState: Failed to get profiles.")
                    clientlist = []
                pname = (AGTypes, "DictionaryEntry")
                entry = AGTypes.DictionaryEntry_(pname=pname)
                entry.key = "clients"
                entry.value = clientlist
                ret_dict.entries.append(entry)
                """
            if prop == "state" or prop == "applications": 
                pass
            if prop == "state" or prop == "services": 
                pass

        return ret_dict
        
        
    def GetVersion(self):
        return Version.GetVersion()
    
    def CreateLegacyDataDescription(self, data):
	legacyObject = DataDescription()
	legacyObject.SetDescription(data.GetDescription())
	legacyObject.SetLastModified(data.GetLastModified())
	legacyObject.SetChecksum(data.GetChecksum())
	legacyObject.SetId(data.GetId())
	legacyObject.SetName(data.GetName())
	legacyObject.SetOwner(data.GetOwner())
	legacyObject.SetSize(data.GetSize())
	legacyObject.SetStatus(data.GetStatus())
	legacyObject.SetType(data.GetType())
	legacyObject.SetURI(data.GetURI())
	return legacyObject
	

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

