#-----------------------------------------------------------------------------
# Name:        Descriptions.py
# Purpose:     Classes for Access Grid Object Descriptions
#
# Author:      Ivan R. Judson
#
# Created:     2002/11/12
# RCS-ID:      $Id: Descriptions.py,v 1.2 2003-01-06 20:49:45 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

class ObjectDescription:
    """
    An object description has four parts:
        name : string
        description : string
        uri : uri (string)
        icon : IconType
    """
    name = ""
    description = ""
    uri = ""
    icon = None
    
    def __init__(self, name, description, uri, icon):
        self.name = name
        self.description = description
        self.uri = uri
        self.icon = icon
    
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
    __doc__ = """
        The Service Description is the Virtual Venue resident information about
        services users can interact with. This is an extension of the Object
        Description that adds a mimeType which should be a standard mime-type.
        """
    mimeType = ""
    
    def __init__(self, name, description, uri, icon, mimetype):
        ObjectDescription(self, name, description, uri, icon)
        self.mimeType = mimetype

    def SetMimeType(self, mimetype):
        self.mimeType = mimetype
    
    def GetMimeType(self):
        return self.mimeType    
      
class VenueDescription(ObjectDescription):
    __doc__ = """
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
    coherenceLocation = None
    extendedDescription = ""
    
    def __init__(self, name, description, icon, extendeddescription):
        ObjectDescription.__init__(self, name, description, "", icon)
        self.extendedDescription = extendeddescription
        
    def SetExtendedDescription(self, extendeddescription):
        self.extendedDescription = extendeddescription
        
    def GetExtendedDescription(self):
        return self.extendedDescription
    
    def SetCoherenceLocation(self, coherenceLocation):
        self.coherenceLocation = coherenceLocation
        
    def GetCoherenceLocation(self):
        return self.coherenceLocation        
   
class DataDescription(ObjectDescription):
    __doc__ = """A Data Description represents data within a venue."""
    storageType = ''
    
    def __init__(self, name, description, uri, icon, storageType):
        ObjectDescription(self, name, description, uri, icon)
        self.storageType = storageType
        
    def SetStorageType(self, storage_type):
        self.storageType = storageType
        
    def GetStorageType(self):
        return self.storageType
    
class ConnectionDescription(ObjectDescription):
    __doc__ = """
    A Connection Description is used to represent the 
    connection from the current venue to another venue.
    """
    pass    