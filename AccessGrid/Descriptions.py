#-----------------------------------------------------------------------------
# Name:        Descriptions.py
# Purpose:     Classes for Access Grid Object Descriptions
#
# Author:      Ivan R. Judson
#
# Created:     2002/11/12
# RCS-ID:      $Id: Descriptions.py,v 1.15 2003-02-28 17:20:43 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import string

class ObjectDescription:
    """
    An object description has four parts:
        name : string
        description : string
        uri : uri (string)
        icon : IconType
    """
    def __init__(self, name, description = "", icon = None, uri = ""):
        self.name = name
        self.description = description
        self.uri = uri
        self.icon = icon
    
    def __repr__(self):
        classpath = string.split(str(self.__class__), '.')
        classname = classpath[-1]
        return "%s: %s" % (classname, str(self.__dict__))


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
    
    def SetIcon(self, icon):
        self.icon = icon
        
    def GetIcon(self):
        return self.icon 
    
class ServiceDescription(ObjectDescription):
    """
        The Service Description is the Virtual Venue resident information about
        services users can interact with. This is an extension of the Object
        Description that adds a mimeType which should be a standard mime-type.
        """
    
    def __init__(self, name, description, uri, icon, mimetype):
        ObjectDescription.__init__(self, name, description, uri, icon)
        self.mimeType = mimetype

    def SetMimeType(self, mimetype):
        self.mimeType = mimetype
    
    def GetMimeType(self):
        return self.mimeType    
      
class VenueDescription(ObjectDescription):
    """
    This is a Venue Description. The Venue Description is used by Venue Clients
    to present the appearance of a space to the users.
    """
    
    """
    The extendedDescription attribute is for arbitrary customization of the
    VenueDescription. Venues clients are not required to process this data
    but if they can, venues clients can present a richer spatial experience.
    It is suggested that this be simply XML so that clients require no
    additional software for processing it.
    """
    def __init__(self, name, description, icon = None, extendeddescription = ""):
        ObjectDescription.__init__(self, name, description, icon)
        self.extendedDescription = extendeddescription
        self.eventLocation = None
        self.textLocation = None
        
    def SetExtendedDescription(self, extendeddescription):
        self.extendedDescription = extendeddescription
        
    def GetExtendedDescription(self):
        return self.extendedDescription
    
    def SetEventLocation(self, eventLocation):
        self.eventLocation = eventLocation
        
    def GetEventLocation(self):
        return self.eventLocation        

    def SetTextLocation(self, textLocation):
        self.textLocation = textLocation
        
    def GetTextLocation(self):
        return self.textLocation        
   
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
      ObjectDescription.__init__( self, name, description, None, None )
      self.location = location
      self.capability = capability
      self.encryptionKey = encryptionKey
      self.static = 0

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
    
