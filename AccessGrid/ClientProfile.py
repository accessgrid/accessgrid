#-----------------------------------------------------------------------------
# Name:        ClientProfile.py
# Purpose:     The ClientProfile is the data that is used on the server side
#               to represent connected clients (both users and shared nodes).
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: ClientProfile.py,v 1.10 2003-01-28 04:12:15 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import ConfigParser
import string

from AccessGrid.Utilities import LoadConfig, SaveConfig
class ClientProfile:
    """
    The client profile is used to represent the clients throughout the AG.
    The client profile is all public data, however only the author of the
    profile is allowed to modify it.
    """

    defaultProfile = {
        'ClientProfile.type' : "user",
        'ClientProfile.name' : 'John Doe',
        'ClientProfile.email' : 'john@mail.com',
        'ClientProfile.phone' : '+1 888 959 5555',
        'ClientProfile.icon' : '',
        'ClientProfile.id' : 'do-de-do',
        'ClientProfile.location' : 'Nowhere, Fast',
        'ClientProfile.venueclienturl' : '',
        'ClientProfile.techsupportinfo' : '',
        'ClientProfile.home' : 'http://test.com/Venues/default'
        }

    USER = "user"
    NODE = "node"
    
    def __init__(self, profileFile = None):
        """ """
        self.profileFile = profileFile
        self.profileType = ''
        self.name = ''
        self.email = ''
        self.phoneNumber = ''
        self.icon = None
        self.publicId = ''
        self.location = ''
        self.venueClientURL = ''
        self.techSupportInfo = ''
        self.homeVenue = ''
        self.privateId = None
        self.distinguishedName = None
        self.capabilities = []

        if profileFile != None:
            self.Load(self.profileFile)

    def Load(self, fileName):
	"""
	"""
        self.profile = LoadConfig(fileName, ClientProfile.defaultProfile)
        
        self.profileType = self.profile['ClientProfile.type']
        self.name = self.profile['ClientProfile.name']
        self.email = self.profile['ClientProfile.email']
        self.phoneNumber = self.profile['ClientProfile.phone']
        self.icon = self.profile['ClientProfile.icon']
        self.publicId = self.profile['ClientProfile.id']
        self.location = self.profile['ClientProfile.location']
        self.venueClientURL = self.profile['ClientProfile.venueclienturl']
        self.techSupportInfo = self.profile['ClientProfile.techsupportinfo']
        self.homeVenue = self.profile['ClientProfile.home']

        self.Dump()
        
    def Dump(self):
        """
        """
        print "Profile Type: " + self.profileType
        print "Name: " + self.name
        print "Email: " + self.email
        print "Phone Number: " + self.phoneNumber
        print "Icon: " + self.icon
        print "Location: " + self.location
        print "Venue Client URL: " + self.venueClientURL
        print "Technical Support Information: " + self.techSupportInfo
        print "Public ID: " + self. publicId
        print "Home Venue: " + self.homeVenue
        
    def Save(self, fileName):
        """ """
        config = {}
        config['ClientProfile.type'] = self.GetProfileType()
        config['ClientProfile.name'] = self.GetName()
        config['ClientProfile.email'] = self.GetEmail()
        config['ClientProfile.phone'] = self.GetPhoneNumber()
        config['ClientProfile.icon'] = self.GetIcon()
        config['ClientProfile.location'] = self.GetLocation()
        config['ClientProfile.venueclienturl'] = self.GetVenueClientURL()
        config['ClientProfile.techsupportinfo'] = self.GetTechSupportInfo()
        config['ClientProfile.id'] = self.GetPublicId()
        config['ClientProfile.home'] = self.GetHomeVenue()
        
        SaveConfig(fileName, config)
        
    def SetProfileType(self, profileType):
        """ """
        self.profileType = profileType
        
    def GetProfileType(self):
        """ """
        return self.profileType
    
    def SetLocation(self, location):
        """ """
        self.location = location
    
    def GetLocation(self):
        """ """
        return self.location
    
    def SetEmail(self, email):
        """ """
        self.email = email
    
    def GetEmail(self):
        """ """
        return self.email
    
    def SetName(self, name):
        """ """
        self.name = name
        
    def GetName(self):
        """ """
        return self.name
    
    def SetPhoneNumber(self, phoneNumber):
        """ """
        self.phoneNumber = phoneNumber
        
    def GetPhoneNumber(self):
        """ """
        return self.phoneNumber
    
    def SetIcon(self, icon):
        """ """
        self.icon = icon
        
    def GetIcon(self):
        """ """
        return self.icon
    
    def SetVenuClientURL(self, venueClientURL):
        """ """
        self.venueClientURL = venueClientURL
    
    def GetVenueClientURL(self):
        """ """
        return self.venueClientURL
    
    def SetTechSupportInfo(self, techSupportInfo):
        """ """
        self.techSupportInfo = techSupportInfo
        
    def GetTechSupportInfo(self):
        """ """
        return self.techSupportInfo
    
    def SetPublicId(self, publicId):
        """ """
        self.publicId = publicId
        
    def GetPublicId(self):
        """ """
        return self.publicId

    def GetHomeVenue(self):
        return self.homeVenue

    def SetHomeVenue(self, venue):
        self.homeVenue = venue
