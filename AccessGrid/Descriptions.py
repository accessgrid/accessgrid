#-----------------------------------------------------------------------------
# Name:        Descriptions.py
# Purpose:     Classes for Access Grid Object Descriptions
#
# Author:      Ivan R. Judson
#
# Created:     2002/11/12
# RCS-ID:      $Id: Descriptions.py,v 1.94 2006-02-24 23:15:43 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Descriptions.py,v 1.94 2006-02-24 23:15:43 turam Exp $"
__docformat__ = "restructuredtext en"

import string

from AccessGrid.GUID import GUID
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.NetworkLocation import UnicastNetworkLocation
from AccessGrid.NetworkLocation import ProviderProfile
from AccessGrid.ClientProfile import ClientProfile

class ObjectDescription:
    """
    An object description has four parts:
        id : string
        name : string
        description : string
        uri : uri (string)
    """
    def __init__(self, name=None, description = None, uri = None,
                 oid = None):

        # Catch annoying None case
        if oid != None:
            self.id = oid
        else:
            self.id = str(GUID())

        self.name = name
        self.description = description
        self.uri = uri
        
    def __repr__(self):
        classpath = string.split(str(self.__class__), '.')
        classname = classpath[-1]
        return "%s: %s" % (classname, str(self.__dict__))

    def AsINIBlock(self):
        string = "\n[%s]\n" % self.id
        string += "name : %s\n" % self.name
        if self.description != None:
            string += "description : %s\n" % self.description
        if self.uri != None:
            string += "uri : %s\n" % self.uri

        return string

    def SetId(self, oid):
        self.id = oid
        
    def GetId(self):
        return self.id
    
    def SetName(self, name):
        self.name = name
        
    def GetName(self):
        return self.name
    
    def SetDescription(self, description):
        self.description = description
        
    def GetDescription(self):
        return self.description
    
    def SetURI(self, uri):
        self.uri = uri
        
    def GetURI(self):
        return self.uri

class BadDataDescription(Exception):
    pass

class DataDescription(ObjectDescription):
    """
    A Data Description represents data within a venue.

    Each description object represents a single file. (We assume that
    the venue-resident data server does not support directory hierarchies).

    """

    #
    # Status values
    #

    STATUS_INVALID = "invalid"
    STATUS_REFERENCE = "reference"
    STATUS_PRESENT = "present"
    STATUS_PENDING = "pending"
    STATUS_UPLOADING = "uploading"
   
    valid_status = [STATUS_INVALID, STATUS_REFERENCE, STATUS_PRESENT,
                    STATUS_PENDING, STATUS_UPLOADING]

    class InvalidStatus(Exception):
        pass
    
    def __init__(self, name=None):
        ObjectDescription.__init__(self, name)

        self.status = self.STATUS_INVALID
        self.size = 0
        self.checksum = None
        self.owner = None
        self.type = None # this is venue data
        self.lastModified = None

    def SetLastModified(self, date):
        self.lastModified = date

    def GetLastModified(self):
        return self.lastModified

    def SetType(self, type):
        self.type = type

    def GetType(self):
        return self.type

    def SetStatus(self, status):
        if status not in self.valid_status:
            raise self.InvalidStatus(status)
        self.status = status

    def GetStatus(self):
        return self.status

    def SetSize(self, size):
        if type(size) != int and type(size) != long:
            raise TypeError("Size must be an int.")
        self.size = size

    def GetSize(self):
        return self.size

    def SetChecksum(self, checksum):
        self.checksum = checksum

    def GetChecksum(self):
        return self.checksum

    def SetOwner(self, owner):
        self.owner = owner

    def GetOwner(self):
        return self.owner

    def AsINIBlock(self):
        string = ObjectDescription.AsINIBlock(self)
        string += "status : %s\n" % self.GetStatus()
        string += "size : %d\n" % self.GetSize()
        string += "checksum : %s\n" % self.GetChecksum()
        string += "owner: %s\n" % self.GetOwner()
        string += "type: %s\n" % self.GetType()
        string += 'lastModified: %s\n' % self.GetLastModified()

        return string

class ConnectionDescription(ObjectDescription):
    """
    A Connection Description is used to represent the 
    connection from the current venue to another venue.
    """
    pass    

class VenueDescription(ObjectDescription):
    """
    A Venue Description is used to represent a Venue.
    """
    def __init__(self, name=None, description=None, encryptionInfo=(0,''),
                 connectionList=None, staticStreams=None, oid = None,
                 uri=None):

        ObjectDescription.__init__(self, name, description, uri, oid)
        self.streams = list()
        self.encryptMedia = 0
        self.encryptionKey = None
        self.encryptMedia = encryptionInfo[0]
        
        if self.encryptMedia:
            self.encryptionKey = encryptionInfo[1]
        else:
            self.encryptionKey = None
           
        if connectionList == None:
            self.connections = []
        else:
            self.connections = connectionList
        if staticStreams == None:
            self.streams = []
        else:
            self.streams = staticStreams
    
    def AsINIBlock(self):
        string = ObjectDescription.AsINIBlock(self)
        if self.encryptMedia:
            string += "encryptionKey : %s\n" % self.encryptionKey
        clist = ":".join(map(lambda conn: conn.GetId(),
                             self.connections))
        string += "connections : %s\n" % clist
        slist = ":".join(map(lambda stream: stream.GetId(),
                             self.streams))
        string += "streams : %s\n" % slist
        string += "\n".join(map(lambda conn: conn.AsINIBlock(),
                                self.connections))
        string += "\n".join(map(lambda stream: stream.AsINIBlock(),
                                self.streams))
        return string

    def __repr__(self):
        return self.AsINIBlock()

class BadServiceDescription(Exception):
    pass


class ServiceDescription(ObjectDescription):
    """
    The Service Description is the Virtual Venue resident information
    about services users can interact with.

    Extends ObjectDescription with one more attribute:

        mimetype : string
    """
    def __init__(self, name=None, description="", uri=None, mimetype=""):   
        ObjectDescription.__init__(self, name, description, uri)   
        self.mimeType = mimetype   
          
    def SetMimeType(self, mimetype):   
        self.mimeType = mimetype   
            
    def GetMimeType(self):   
        return self.mimeType   

    def AsINIBlock(self):
        string = ObjectDescription.AsINIBlock(self)
        string += "mimeType: %s" % self.mimeType

        return string

class ApplicationCmdDescription:
    def __init__(self, appDesc, verb, cmd, senderProfile):   
        self.appDesc = appDesc
        self.verb = verb
        self.command = cmd
        self.profile = senderProfile
    
class ApplicationDescription(ObjectDescription):
    """
    The Service Description is the Virtual Venue resident information
    about services users can interact with. This is an extension of
    the Object Description that adds a mimeType which should be a
    standard mime-type.
    """
    def __init__(self, oid=None, name=None, description="", uri="", mimetype="", startable=1):   
        ObjectDescription.__init__(self, name, description, uri, oid = oid)
        self.mimeType = mimetype   
        self.startable = startable
    
    def SetMimeType(self, mimetype):   
        self.mimeType = mimetype   
            
    def GetMimeType(self):   
        return self.mimeType   

    def AsINIBlock(self):
        string = ObjectDescription.AsINIBlock(self)
        string += "mimeType : %s\n" % self.mimeType
        string += "startable : %s\n" % self.startable
        
        return string

class BadApplicationDescription(Exception):
    pass
        
class Capability:

    PRODUCER = "producer"
    CONSUMER = "consumer"

    AUDIO = "audio"
    VIDEO = "video"
    TEXT  = "text"

    def __init__( self, role=None, type=None, codec=None, rate=None, serviceId = None, channels = 1):
        self.role = role # consumer/producer
        self.type = type # audio/video/other
        self.codec = codec # according to mime type
        self.rate = rate # RTP clock rate
        self.channels = channels
        self.serviceId = serviceId 
        
    def __repr__(self):
        string = "%s, %s, %s, %s, %s, %s" % (self.role, self.type, self.serviceId, self.codec, str(self.rate), str(self.channels))
        return string

    def matches( self, capability ):
        if (str(self.type) != str(capability.type) or
            str(self.codec) != str(capability.codec) or
            int(self.channels) != int(capability.channels) or
            int(self.rate) != int(capability.rate)):
            # type mismatch
            return 0

        # capability match
        return 1

class StreamDescription( ObjectDescription ):
   """A Stream Description represents a stream within a venue"""
   def __init__( self, name=None, 
                 location=0, 
                 capability=0,
                 encryptionFlag=0, encryptionKey=None,
                 static=0):
      ObjectDescription.__init__( self, name, None, None)
      self.location = location
      self.capability = capability
      self.encryptionFlag = encryptionFlag
      self.encryptionKey = encryptionKey
      self.static = static
      self.networkLocations = []
      
      if location:
          self.AddNetworkLocation(location)
          
   def AddNetworkLocation(self,networkLocation):
       """
       Add the specified network location to the list
       
       Note: This method overwrites the network location id 
             in the incoming network location
       """
       networkLocation.id = str(GUID())
       self.networkLocations.append(networkLocation)
       return networkLocation.id
       
   def RemoveNetworkLocation(self, networkLocationId):
       """
       Remove the network location with specified id
       """
       for networkLocation in self.networkLocations:
           if networkLocation.id == networkLocationId:
               self.networkLocations.remove(networkLocation)

   def AsINIBlock(self):
       string = ObjectDescription.AsINIBlock(self)
       string += "encryptionFlag : %s\n" % self.encryptionFlag
       if self.encryptionFlag:
           string += "encryptionKey : %s\n" % self.encryptionKey
       string += "location : %s\n" % self.location
       string += "capability : %s\n" % self.capability[0].type

       return string
   
class AGServiceManagerDescription:
    def __init__( self, name="", uri="" ):
        self.name = name
        self.uri = uri
        self.builtin = 0

class AGServiceDescription:
    def __init__( self, name="", uri="", capabilities=[], resource="", packageFile=""):
        self.name = name
        self.uri = uri
        self.capabilities = capabilities
        self.resource = resource
        self.packageFile = packageFile

class AGServicePackageDescription:
    def __init__(self,name="",description="",packageFile="",resourceNeeded=0):
        self.name = name
        self.description = description
        self.packageFile = packageFile
        self.resourceNeeded = resourceNeeded
        
    def GetName(self):
        return self.name
        
    def GetDescription(self):
        return self.description
        
    def GetPackageFile(self):
        return self.packageFile
        
    def GetResourceNeeded(self):
        return self.resourceNeeded

class AGNetworkServiceDescription(ObjectDescription):
    def __init__(self, name, description, uri,
                 capabilities, version):
        ObjectDescription.__init__(self, name)
        self.name = name
        self.description = description
        self.uri = uri
        self.version = version
        self.capabilities = capabilities
               
class AppParticipantDescription:
    def __init__(self, appId='', clientProfile=None, status=''):
        self.appId = appId
        self.clientProfile = clientProfile
        self.status = status
        
class AppDataDescription:
    def __init__(self, appId=None, key=None, value=None):
        self.appId = appId
        self.key = key
        self.value = value

class SharedAppState:
    def __init__( self, name=None, description=None, id=None, mimeType=None, uri=None, data=None):
        self.name = name
        self.id = id
        self.description = description
        self.mimeType = mimeType
        self.uri = uri
        if data == None:
            self.data = []
        else:
            self.data = data
    
class VenueState:
    def __init__( self, uniqueId=None, name=None, description=None, uri=None, connections=[],
                  clients=[], data=[], eventLocation=None, textLocation=None, dataLocation=None,
                  applications=[], services=[]):
        self.uniqueId = uniqueId
        self.name = name
        self.description = description
        self.uri = uri
        self.eventLocation = eventLocation
        self.textLocation = textLocation
        self.dataLocation = dataLocation
        self.services = services
        
        self.connections = dict()
        self.clients = dict()
        self.data = dict()
        self.applications = dict()
        self.services = dict()
        
        if connections != None:
            for connection in connections:
                self.connections[connection.uri] = connection
        if clients != None:
            for client in clients:
                # Pre-2.3 server compatability code
                if not client.connectionId:
                    client.connectionId = client.venueClientURL

                self.clients[client.connectionId] = client
        if data != None:
            for datum in data:
                self.data[datum.id] = datum
        if applications != None:
            for app in applications:
                self.applications[app.uri] = app
        if services != None:
            for service in services:
                self.services[service.id] = service
    def SetUniqueId(self, uniqueId):
        self.uniqueId = uniqueId
    def GetUniqueId(self):
        return self.uniqueId
    def SetDescription( self, description ):
        self.description = description
    def GetDescription( self ):
        return self.description
    def SetName( self, name ):
        self.name = name
    def GetName( self ):
        return self.name
    def SetUri( self, uri ):
        self.uri = uri
    def GetUri( self ):
        return self.uri
    def AddUser( self, userProfile ):
        self.clients[userProfile.connectionId] = userProfile
    def RemoveUser( self, userProfile ):
        if userProfile.connectionId in self.clients.keys():
            del self.clients[userProfile.connectionId]
    def ModifyUser( self, userProfile ):
        if userProfile.connectionId in self.clients.keys():
            self.clients[userProfile.connectionId] = userProfile
    def GetUsers( self ):
        return self.clients.values()
    def AddConnection( self, connectionDescription ):
        self.connections[connectionDescription.uri] = connectionDescription
    def RemoveConnection( self, connectionDescription ):
        del self.connections[connectionDescription.uri]
    def SetConnections( self, connectionList ):
        for connection in connectionList:
            self.connections[connection.uri] = connection
    def GetConnections(self):
        return self.connections.values()
    def AddData( self, dataDescription ):
        self.data[dataDescription.id] = dataDescription
    def UpdateData( self, dataDescription ):
        self.data[dataDescription.id] = dataDescription
    def RemoveData( self, dataDescription ):
        del self.data[dataDescription.id]
    def GetData(self):
        return self.data.values()
    def AddService( self, serviceDescription ):
        self.services[serviceDescription.id] = serviceDescription
    def UpdateService(self, serviceDescription):
        self.services[serviceDescription.id] = serviceDescription            
    def RemoveService( self, serviceDescription ):
        if self.services.has_key(serviceDescription.id):
            del self.services[serviceDescription.id]  
        else:
            # Legacy code: Accomodate old (2.1.2 and before) servers,
            # which allocate a new id when the service description goes
            # through them.
            for sid,service in self.services.items():
                if service.name == serviceDescription.name:
                    del self.services[sid]
    def GetServices(self):
        return self.services.values()
    def AddApplication( self, applicationDescription ):
        self.applications[applicationDescription.uri] = applicationDescription
    def UpdateApplication(self, applicationDescription):
        self.applications[applicationDescription.uri] = applicationDescription
    def RemoveApplication( self, applicationDescription ):
        self.applications[applicationDescription.uri] = applicationDescription
    def GetApplications(self):
        return self.applications.values()
    def SetEventLocation( self, eventLocation ):
        self.eventLocation = eventLocation
    def GetEventLocation( self ):
        return self.eventLocation
    def SetTextLocation( self, textLocation ):
        self.textLocation = textLocation
    def GetTextLocation( self ):
        return self.textLocation
    def SetDataLocation( self, dataLocation ):
        self.dataLocation = dataLocation
    def GetDataLocation( self ):
        return self.dataLocation

class ResourceDescription: 
    def __init__(self,name=""):
        self.name = name

class NodeConfigDescription:
    SYSTEM = 'system'
    USER = 'user'
    def __init__(self,name="",type=""):
        self.name = name
        self.type = type

class EventDescription:
    '''
    Event class.
    '''
    def __init__(self, type=None, channelId=None, senderId=None, data=None):
        '''
        channelId - which channel this event should be sent on
        senderId - unique id of sender
        data - event data
        '''
        self.channelId = str(channelId)
        self.senderId = str(senderId)
        self.data = data
        self.eventType = str(type)

    def GetChannelId(self):
        return self.channelId

    def GetSenderId(self):
        return self.senderId

    def GetData(self):
        return self.data

    def GetEventType(self):
        return self.eventType 


QUICKBRIDGE_TYPE = "QuickBridge"
UMTP_TYPE = "UMTP"
STATUS_ENABLED = "Enabled"
STATUS_DISABLED = "Disabled"

class BridgeDescription:
    def __init__(self, guid, name, host, port, serverType, description="",
                 portMin=None, portMax=None):
        self.guid = guid
        self.name = name
        self.host = host
        self.port = port
        self.serverType = serverType
        self.description = description
        self.portMin = portMin
        self.portMax = portMax
        self.status = STATUS_ENABLED
        self.rank = 10 
