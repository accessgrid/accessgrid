#-----------------------------------------------------------------------------
# Name:        ClientProfile.py
# Purpose:     The ClientProfile is the data that is used on the server side
#               to represent connected clients (both users and shared nodes).
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: ClientProfile.py,v 1.1.1.1 2002-12-16 22:25:37 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

class ClientProfile:
    __doc__ = """
    The client profile is used to represent the clients throughout the AG.
    The client profile is all public data, however only the author of the
    profile is allowed to modify it.
    """
    technicalSupportInformation = ''
    profileType = ''
    location = ''
    email = ''
    name = ''
    phoneNumber = ''
    icon = None
    venueClientURL = ''
    publicID = ''
    
    def __init__(self, technicalSupportInformation, profileType, location, email, 
                 name, phone, icon, venueClientURL, publicID):
        self.technicalSupportInformation = technicalSupportInformation
        self.profileType = profileType
        self.location = location
        self.email = email
        self.name = name
        self.phoneNumber = phone
        self.icon = icon
        self.venueClientURI = venueClientURL
        self.publicID = publicid
        
    def SetTechnicalSupportInformation(self, technicalSupportInformation):
        self.technicalSupportInformation = technicalSupportInformation
        
    def GetTechnicalSupportInformation(self):
        return self.technicalSupportInformation
    
    def SetProfileType(self, profileType):
        self.profileType = profileType
        
    def GetProfileType(self):
        return self.profileType
    
    def SetLocation(self, location):
        self.location = location
    
    def GetLocation(self):
        return location
    
    def SetEmail(self, email):
        self.email = email
    
    def GetEmail(self):
        return self.email
    
    def SetName(self, name):
        self.name = name
        
    def GetName(self):
        return self.name
    
    def SetPhoneNumber(self, phoneNumber):
        self.phoneNumber = phoneNumber
        
    def GetPhoneNumber(self):
        return self.phoneNumber
    
    def SetIcon(self, icon):
        self.icon = icon
        
    def GetIcon(self):
        return self.icon
    
    def SetVenuClientURL(self, venueClientURL):
        self.venueClientURL = venueClientURL
    
    def GetVenueClientURL(self):
        return self.venueClientURL
    
    def SetPublicID(self, publicID):
        self.publicID = publicID
        
    def GetPublicID(self):
        return self.publicID