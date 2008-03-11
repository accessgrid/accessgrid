#-----------------------------------------------------------------------------
# Name:        Descriptions.py
# Purpose:     Classes for Access Grid Object Descriptions
#
# Author:      Ivan R. Judson
#
# Created:     2002/11/12
# RCS-ID:      $Id: Descriptions.py,v 1.108 2007/12/20 16:37:23 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Descriptions.py,v 1.108 2007/12/20 16:37:23 turam Exp $"
__docformat__ = "restructuredtext en"

import string

from AccessGrid.GUID import GUID
from AccessGrid import Log
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.NetworkLocation import UnicastNetworkLocation
from AccessGrid.NetworkLocation import ProviderProfile
from AccessGrid.ClientProfile import ClientProfile

log = Log.GetLogger(Log.DataStore)

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
        
    def __str__(self):
        return self.name

    def __cmp__(self,other):
        if other == None:
            return 1
        if self.name < other.name:
            return -1
        elif self.name == other.name:
            return 0
        else:
            return 1
        
    def Copy(obj):
        """
        Copy constructor.  Creates a new instance of the input type, copying 
        attributes defined in that class.  By so doing, it skips any additional
        attributes that have been added to the input instance.  For example, ZSI
        adds attributes to describe data present in the incoming XML instance 
        but not present in the XMLSchema.
        
        Note:  For now, this is being applied to DataDescriptions only.  Issues not
        addressed include:  nested descriptions, deep copies, and integration with
        the standard copy module (__copy__).
        """
        objCopy = obj.__class__()
        
        attrs = objCopy.__dict__.keys()
        for attr in attrs:
            try:
                setattr(objCopy,attr,getattr(obj,attr))
            except:
                log.exception('Exception copying attribute %s of class %s', attr, obj.__class__)
        return objCopy
    Copy = staticmethod(Copy)
      



class BadDataDescription(Exception):
    pass


#Modified by NA2-HPCE
class DataDescription(ObjectDescription):
    """
    A Data Description represents data within a venue.

    With the introdcution of DirectoryDescription and FileDescription
    this class changed to an abstract class, which is not instantiated
    itself.
    
    For the introduction of the new classes and the establishing of the 
    hierarchy new member variables hav ebenn added:
        
        objetType: distinguishes between files and directories
        parentID:  contains the GUID of the description the current
                   description is attached to.
        hierarchyLevel: denotes the level of the data object within the hierarchy
                   root level starts with 0
    
    Thereby directory hierarchies are supported.
    
    DataDescriptions can still be used for personal data stores, the same way
    the were used before, as now methods or members have been removed from 
    DataDescription.
    """

    #
    # Status values
    #

    STATUS_INVALID = "invalid"
    STATUS_REFERENCE = "reference"
    STATUS_PRESENT = "present"
    STATUS_PENDING = "pending"
    STATUS_UPLOADING = "uploading"
    
    TYPE_DIR = "Directory"
    TYPE_FILE = "File"
    TYPE_COMMON = "Common undefined"
   
    valid_status = [STATUS_INVALID, STATUS_REFERENCE, STATUS_PRESENT,
                    STATUS_PENDING, STATUS_UPLOADING]

    class InvalidStatus(Exception):
        pass
    
    #Modified by NA2-HPCE
    def __init__(self, name=None):
        ObjectDescription.__init__(self, name)

        self.status = self.STATUS_INVALID
        self.size = 0
        self.checksum = None
        self.owner = None
        self.type = None # this is venue data
        self.lastModified = None
        self.objectType = None # identifies the type of data; see also the constants
        self.parentId = "-1" # parent id of parent of this data object; uninitialized is -1
        self.hierarchyLevel = -1 # level in the data hierarchy; first level is 0; uninitialized is -1

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

    #Modified by NA2-HPCE
    def AsINIBlock(self):
        string = ObjectDescription.AsINIBlock(self)
        string += "status : %s\n" % self.GetStatus()
        string += "size : %d\n" % self.GetSize()
        string += "checksum : %s\n" % self.GetChecksum()
        string += "owner: %s\n" % self.GetOwner()
        string += "type: %s\n" % self.GetType()
        string += 'lastModified: %s\n' % self.GetLastModified()
        string += 'objType: %s\n' % self.GetObjectType()
        string += 'parent: %s\n' % self.GetParentId()
        string += 'hierarchyLevel: %s\n' % self.GetLevel()

        return string
    
    #Added by NA2-HPCE
    def SetObjectType(self, type):
        self.objectType = type
        
    #Added by NA2-HPCE
    def GetObjectType(self):
        try:
            return self.objectType
        except:
            return None
    
    #Added by NA2-HPCE
    def IsOfType(self, type):
        
        try:
            if type == self.objectType:
                return True
            else:
                return False
        except:
            return False    
    
    #Added by NA2-HPCE
    def GetParentId(self):
        if self.parentId == None:        
            return -1
        else:
            return self.parentId
    
    #Added by NA2-HPCE
    def SetParentId(self, parent):
        self.parentId = str(parent)
    
    #Added by NA2-HPCE
    def SetLevel(self, level):
        self.hierarchyLevel = int(level)
    
    #Added by NA2-HPCE
    def GetLevel(self):
        return self.hierarchyLevel
        
        

#Added by NA2-HPCE    
class DirectoryDescription(DataDescription):
    """
    Data object that describes the directorie properties of 
    directories of the FTP data storage. Its unique DataContainer
    can be determined with the appropriate method to attach
    new data objects, namely files or directories.
    
    The physical, relative path  starting from the root of the FTP
    data store is stored in self.location . This is done to ease 
    directory retrieval for uploads.
    
    To store the location to the physical path over Venue server downtimes
    a AsINIBlock method has to be added.
    
    """

    def __init__(self, name=""):
        DataDescription.__init__(self, name)
        
        self.dataContainer = None
        self.objectType = DataDescription.TYPE_DIR
        self.location = ""
        self.dataContainer = list()
        #if not dataDescContainer == None:
        #    self.dataContainer = dataDescContainer
    
    def GetChildren(self):
        return self.dataContainer
    
    def AddChild(self, id):
        self.dataContainer.append(id)
        
    def RemoveChild(self, id):
        for item in self.dataContainer:
            if item == id:
                self.dataContainer.remove(item)
    
    def SetDataContainer(self, dataContainer):
        self.dataContainer = dataContainer
    
    def GetDataContainer(self):
        return self.dataContainer
    
    def SetLocation(self, location):
        self.location = location
        self.uri = location
    
    def GetLocation(self):
        return self.location
    
    def AsINIBlock(self):
        string = DataDescription.AsINIBlock()
        string += "status : %s\n" % self.GetLocation()
        
        return string
    def Search(self, directoryDict, pathList):
        log.debug("Search: Size of pathList: %s", len(pathList))
        log.debug("Search: Examining path part: %s", pathList[0])


        nextDD = None

        for item in directoryDict.values():
            if item.name == pathList[len(pathList)-2]:
                nextDD = item
                break
                
        pathList = pathList[1:len(pathList)]
        if len(pathList) == 0:
            log.debug("Search: Found end of path. ID is: %s", nextDD.GetId())
            return nextDD.GetId()
        else:
            log.debug("Search: continue on next recursive path level!")
            return nextDD.Search(directoryDict, pathList)

#Added by NA2-HPCE
class FileDescription(DataDescription):
    """
    This class basically is the replacement for the previous DataDescription
    class. It encapsulates properties of files and maintains the mode of 
    the object.
    
    """
    
    def __init__(self,name):
        DataDescription.__init__(self,name)
        self.objectType = DataDescription.TYPE_FILE

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
    def __init__(self, appDesc=None, verb=None, cmd=None, senderProfile=None):   
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

class PluginDescription(ObjectDescription):
    def __init__(self, oid=None, name=None, description="", uri="",
                 command = "", module="", icon=""):
        ObjectDescription.__init__(self, name, description, uri, oid = oid)
        self.command = command
        self.module = module
        self.icon = icon

    def AsINIBlock(self):
        string = ObjectDescription.AsINIBlock(self)
        string += "command : %s\n" % self.command
        string += "module : %s\n" % self.module
        string += "icon : %s\n" % self.icon

        return string

class BadApplicationDescription(Exception):
    pass
        
class Capability:

    #role
    PRODUCER = "producer"
    CONSUMER = "consumer"

    #type
    AUDIO = "audio"
    VIDEO = "video"
    TEXT  = "text"
    
    #LocationType
    PREFERRED_UNICAST = "UC"
    MULTICAST = "MC"

    def __init__( self, role=None, type=None, codec=None, rate=0, serviceId = None, channels = 1):
        self.role = role # consumer/producer
        self.type = type # audio/video/other
        self.codec = codec # according to mime type
        self.rate = rate # RTP clock rate
        self.channels = channels
        self.serviceId = serviceId 
        self.locationType = None  # Secpifies whether to use multicast assigned by Venue or Unicast as specified by service
        self.port = 0           # only applicable if used PREFERRED_UNICAST: port of service to use
        self.host = None          # only applicable if used PFEFERRED_UNICAST: ip of service to use
        if self.codec == None:
            self.codec=None
            
        if rate == None:
            self.rate = 0
        
    def SetLocationType(self, type):
        self.locationType = type

    def SetHost(self, host):
        self.host = host
    
    def SetPort(self, port):
        self.port = port
        
    
        
    def __repr__(self):
        string = "%s, %s, %s, %s, %s, %s, %s, %s" % (self.role, self.type, self.serviceId, self.codec, str(self.rate), str(self.channels), str(self.host), str(self.locationType))
        return string

    def matches( self, capability ):
        try:
            if (str(self.type) != str(capability.type) or
                str(self.codec) != str(capability.codec) or
                int(self.channels) != int(capability.channels) or
                int(self.rate) != int(capability.rate)):
                # type mismatch
                return 0
        except:
            log.exception('Exception in capability compare')

        # capability match
        return 1

class StreamDescription(ObjectDescription):
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

from AccessGrid.DispatchMixIn import DispatchMixIn
class AGServiceManagerDescription(DispatchMixIn):

    def __init__( self, name="", uri="" ):
        from AccessGrid.interfaces.AGServiceManager_client import AGServiceManagerIW

        self.name = name
        self.uri = uri
        self.builtin = 0
        
        self.serviceIWClass = AGServiceManagerIW
        DispatchMixIn.__init__(self)
        


class AGServiceDescription(DispatchMixIn):
    def __init__( self, name="", uri="", capabilities=[], resource="", packageFile=""):
        from AccessGrid.interfaces.AGService_client import AGServiceIW

        self.name = name
        self.uri = uri
        self.capabilities = capabilities
        self.resource = resource
        self.packageFile = packageFile
        self.startPriority = 0
        self.inlineClass = None
        
        self.serviceIWClass = AGServiceIW
        DispatchMixIn.__init__(self)
        
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

    #Changed interface to accpet dataDescription Id instead of description
    def RemoveData( self, dataDescription ):
        try:
            del self.data[dataDescription.id]
        except:
            log.exception("Failed to remove data")

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
    UNREACHABLE = 100000
    UNRANKED = 100000
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
        self.rank = BridgeDescription.UNREACHABLE
        self.userRank = BridgeDescription.UNRANKED
    
    def GetKey(self):
        return "%s:%s:%s" % (self.name, self.host, self.port)
        
    def sort(x, y, orderBridgesByPing=0):
        if orderBridgesByPing:
            return cmp(x.rank, y.rank)
        rank = cmp(x.userRank, y.userRank)
        if rank == 0:
            return cmp(x.rank, y.rank)
        else:
            return rank
        
        
class BeaconSource:
    def __init__(self,cname=None,ssrc=None):
        self.cname = cname
        self.ssrc = ssrc
        
class BeaconSourceData:
    def __init__(self,ssrc,total_lost,fract_lost,jitter):
        self.ssrc = ssrc
        self.total_lost = total_lost
        self.fract_lost = fract_lost
        self.jitter = jitter
        
