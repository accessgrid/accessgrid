#-----------------------------------------------------------------------------
# Name:        Descriptions.py
# Purpose:     Classes for Access Grid Object Descriptions
#
# Author:      Ivan R. Judson
#
# Created:     2002/11/12
# RCS-ID:      $Id: Descriptions.py,v 1.17 2003-03-25 16:06:33 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import string
from AccessGrid.GUID import GUID

class ObjectDescription:
    """
    An object description has four parts:
        id : string
        name : string
        description : string
        uri : uri (string)
        icon : IconType
    """
    def __init__(self, name, description = "", uri = ""):
        self.id = str(GUID())
        self.name = name
        self.description = description
        self.uri = uri
        
    def __repr__(self):
        classpath = string.split(str(self.__class__), '.')
        classname = classpath[-1]
        return "%s: %s" % (classname, str(self.__dict__))

    def AsINIBlock(self):
        string = "[%s]\n" % self.id
        string += "name : %s\n" % self.name
        string += "description : %s\n" % self.description
        string += "uri : %s\n" % self.uri

        return string

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
        self.size = None
        self.checksum = None
        self.owner = None

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
        string = ObjectDescription.AsINIFile(self)
        string += "status : %s\n" % self.status
        string += "size : %d\n" % self.size
        string += "checksum : %d\n" % self.checksum
        string += "owner: %s\n" % self.owner

        return string
        
class ConnectionDescription(ObjectDescription):
    """
    A Connection Description is used to represent the 
    connection from the current venue to another venue.
    """
    pass    


from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.Types import Capability

class StreamDescription( ObjectDescription ):
   """A Stream Description represents a stream within a venue"""
   def __init__( self, name=None, description=None,
                 location=MulticastNetworkLocation(), 
                 capability=Capability(),
                 encryptionKey=0 ):
      ObjectDescription.__init__( self, name, description, None)
      self.location = location
      self.capability = capability
      self.encryptionKey = encryptionKey
      self.static = 0

   def AsINIBlock(self):
       string = ObjectDescription.AsINIBlock(self)
       string += "encryptionKey : %s\n" % self.encryptionKey
       string += "static : %d\n" % self.static
       string += "location : %s\n" % self.location
       string += "capability : %s\n" % self.capability

       return string
   
def CreateStreamDescription( streamDescriptionStruct ):
    networkLocation = MulticastNetworkLocation( streamDescriptionStruct.location.host,
                                                streamDescriptionStruct.location.port,
                                                streamDescriptionStruct.location.ttl )
    cap = Capability( streamDescriptionStruct.capability.role, 
                      streamDescriptionStruct.capability.type )
    streamDescription = StreamDescription( streamDescriptionStruct.name, 
                                           streamDescriptionStruct.description,
                                           networkLocation,
                                           cap,
                                           streamDescriptionStruct.encryptionKey )
    streamDescription.static = streamDescriptionStruct.static
    return streamDescription



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
    
