#-----------------------------------------------------------------------------
# Name:        Descriptions.py
# Purpose:     Classes for Access Grid Object Descriptions
#
# Author:      Ivan R. Judson
#
# Created:     2002/11/12
# RCS-ID:      $Id: Descriptions.py,v 1.37 2003-08-22 23:15:01 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import string
from AccessGrid.GUID import GUID
from AccessGrid.NetworkLocation import MulticastNetworkLocation, UnicastNetworkLocation
from AccessGrid.Types import Capability
from AccessGrid.Utilities import PathFromURL
from AccessGrid.hosting.AccessControl import RoleManager

class ObjectDescription:
    """
    An object description has four parts:
        id : string
        name : string
        description : string
        uri : uri (string)
    """
    def __init__(self, name, description = None, uri = None):
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
#            string += "uri : %s\n" % PathFromURL(self.uri)

        return string

    def SetId(self, id):
        self.id = id
        
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
    
    def __init__(self, name):
        ObjectDescription.__init__(self, name)

        self.status = self.STATUS_INVALID
        self.size = 0
        self.checksum = None
        self.owner = None
        self.type = None # this is venue data

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
        if type(size) != int:
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

        return string

def CreateDataDescription(dataDescStruct):
    """
    """
    dd = DataDescription(dataDescStruct.name)
    dd.SetId(dataDescStruct.id)
    dd.SetName(dataDescStruct.name)
    dd.SetDescription(dataDescStruct.description)
    dd.SetURI(dataDescStruct.uri)
    if dataDescStruct.type == '':
        dd.SetType(None)
    else:
        dd.SetType(dataDescStruct.type)
    dd.SetStatus(dataDescStruct.status)
    dd.SetSize(dataDescStruct.size)
    dd.SetChecksum(dataDescStruct.checksum)
    dd.SetOwner(dataDescStruct.owner)

    return dd

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
    def __init__(self, name=None, description=None, roleManager=None,
                 encryptionInfo=(0,''), connectionList=[], staticStreams=[]):
        ObjectDescription.__init__(self, name, description, None)

        self.streams = []
        self.connections = {}
        self.encryptMedia = 0
        self.encryptionKey = None
        #self.administrators = []
        # Exclude roleManager.  Roles and admins handled separately.
        self.roleManager = roleManager
        #if roleManager:
            #self.roleManager = roleManager
        #else:
            #self.roleManager = RoleManager()

        #print "VenueDesc.__init__ : admins:"
        #if "Venue.Administrators" in self.roleManager.GetRoleList():
            #print self.roleManager.GetRole("Venue.Administrators").GetSubjectListAsStrings()
        
        self.encryptMedia = encryptionInfo[0]
        
        if self.encryptMedia:
            self.encryptionKey = encryptionInfo[1]
        else:
            self.encryptionKey = None
           
        self.connections = {}
        for c in connectionList:
            self.connections[c.uri] = c

        self.streams = staticStreams
    
    def AsINIBlock(self):
        string = ObjectDescription.AsINIBlock(self)
        
        # Usually the roleManager in the description is None
        if self.roleManager:
            rm = self.roleManager
            if len(rm.validRoles):
                # Write a list of roles names to the config file.
                string += "roles : %s\n" % ":".join(rm.GetRoleList())
                for r in rm.validRoles.keys():
                    # Still include Venue.VenueUsers. 
                    #if not r == "Venue.VenueUsers": # VenueUsers are not persisted
                    string += r + " : %s\n" % ":".join(rm.validRoles[r].GetSubjectListAsStrings()) 
        string += "encryptMedia: %d\n" % self.encryptMedia
        if self.encryptMedia:
            string += "encryptionKey : %s\n" % self.encryptionKey
        clist = ":".join(map(lambda conn: conn.GetId(),
                             self.connections.values()))
        string += "connections : %s\n" % clist
        slist = ":".join(map(lambda stream: stream.GetId(),
                             self.streams))
        string += "streams : %s\n" % slist
        string += "\n".join(map(lambda conn: conn.AsINIBlock(),
                                self.connections.values()))
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
    about services users can interact with. This is an extension of
    the Object Description that adds a mimeType which should be a
    standard mime-type.
    """
    def __init__(self, name, description, uri, mimetype):   
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
    
class ApplicationDescription(ObjectDescription):
    """
    The Service Description is the Virtual Venue resident information
    about services users can interact with. This is an extension of
    the Object Description that adds a mimeType which should be a
    standard mime-type.
    """
    def __init__(self, id, name, description, uri, mimetype):   
        ObjectDescription.__init__(self, name, description, uri)
        # We override the generated id
        self.id = id
        self.mimeType = mimetype   
    
    def SetMimeType(self, mimetype):   
        self.mimeType = mimetype   
            
    def GetMimeType(self):   
        return self.mimeType   

    def AsINIBlock(self):
        string = ObjectDescription.AsINIBlock(self)
        string += "mimeType : %s\n" % self.mimeType
        
        return string
        
class StreamDescription( ObjectDescription ):
   """A Stream Description represents a stream within a venue"""
   def __init__( self, name=None, 
                 location=MulticastNetworkLocation(), 
                 capability=Capability(),
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
       id = str(GUID())
       networkLocation.id = id
       self.networkLocations.append(networkLocation)
       return id
       
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
#       string += "static : %d\n" % self.static
       string += "location : %s\n" % self.location
       string += "capability : %s\n" % self.capability

       return string
   
class AGServiceManagerDescription:
    def __init__( self, name, uri ):
        self.name = name
        self.uri = uri

class AGServiceDescription:
    def __init__( self, name, description, uri, capabilities,
                  resource, executable, serviceManagerUri,
                  servicePackageUri ):
        self.name = name
        self.description = description

        self.uri = uri

        self.capabilities = capabilities
        self.resource = resource
        self.executable = executable
        self.serviceManagerUri = serviceManagerUri
        self.servicePackageUri = servicePackageUri
    
def CreateStreamDescription( streamDescStruct ):
    if streamDescStruct.location.type == MulticastNetworkLocation.TYPE:
        networkLocation = MulticastNetworkLocation( streamDescStruct.location.host,
                                                    streamDescStruct.location.port,
                                                    streamDescStruct.location.ttl )
    else:
        networkLocation = UnicastNetworkLocation( streamDescStruct.location.host,
                                                    streamDescStruct.location.port)
    cap = Capability( streamDescStruct.capability.role, 
                      streamDescStruct.capability.type )
    streamDescription = StreamDescription( streamDescStruct.name, 
                                           networkLocation,
                                           cap,
                                           streamDescStruct.encryptionFlag,
                                           streamDescStruct.encryptionKey,
                                           streamDescStruct.static)
    return streamDescription

def CreateServiceDescription(serviceDescStruct):
    serviceDescription = ServiceDescription( serviceDescStruct.name,    
                                             serviceDescStruct.description,
                                             serviceDescStruct.uri,
                                             serviceDescStruct.mimeType )
    return serviceDescription

def CreateVenueDescription(venueDescStruct):
    clist = []
    for c in venueDescStruct.connections:
        # THIS IS ICKY TOO
        if c != '\n':
            clist.append(ConnectionDescription(c.name, c.description, c.uri))

    slist = []
    for s in venueDescStruct.streams:
        slist.append(CreateStreamDescription(s))

    # If a roleManager was sent with venueDescriptions, it would use
    #   code like this, but we'll set admins and roles separately.
    #if venueDescStruct.roleManager:
        #roleManager = RoleManager()
        #for role_struct in venueDescStruct.roleManager.validRoles:
           #print "role_struct", role_struct
           #roleManager.RegisterRole(role_struct.name)
           #registered_role = roleManager.GetRole(role_struct.name)
           #for subj in role_struct.subjects:
               #registered_role.AddSubject(subj)
    
        #print "CreateVenueDesc: admins:"
        #if "Venue.Administrators" in roleManager.GetRoleList():
            #print roleManager.GetRole("Venue.Administrators").GetSubjectListAsStrings()
   
       
    vdesc = VenueDescription(venueDescStruct.name, venueDescStruct.description,
                             None,
                             (venueDescStruct.encryptMedia,
                              venueDescStruct.encryptionKey), clist, slist)
    vdesc.uri = venueDescStruct.uri
    
    return vdesc

