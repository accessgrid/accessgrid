#-----------------------------------------------------------------------------
# Name:        ClientProfile.py
# Purpose:     The ClientProfile is the data that is used on the server side
#               to represent connected clients (both users and shared nodes).
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: ClientProfile.py,v 1.22 2003-05-09 22:59:58 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import ConfigParser
import string

from AccessGrid.Utilities import LoadConfig, SaveConfig
from AccessGrid.GUID import GUID

class InvalidProfileException(Exception):
    """
    This is a bad profile.
    """
    pass

class ClientProfile:
    """
    The client profile is used to represent the clients throughout the AG.
    The client profile is all public data, however only the author of the
    profile is allowed to modify it.
    """

    configSection = 'ClientProfile'
    
    validOptions = [
        'type',
        'name',
        'email',
        'phone',
        'icon',
        'id',
        'location',
        'venueclienturl',
        'techsupportinfo',
        'home']
        
    defaultProfile = {
        'ClientProfile.type' : "user",
        'ClientProfile.name' : '<Insert Name Here>',
        'ClientProfile.email' : '<Insert Email Address Here>',
        'ClientProfile.phone' : '<Insert Phone Number Here>',
        'ClientProfile.icon' : '<Leave blank for now>',
        'ClientProfile.id' : '',
        'ClientProfile.location' : '<Insert Postal Address Here>',
        'ClientProfile.venueclienturl' : '',
        'ClientProfile.techsupportinfo' : '<Insert Technical Support Contact Information Here>',
        'ClientProfile.home' : 'https://vv2.mcs.anl.gov:9000/Venues/default'
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
        else:
            self.profile = ClientProfile.defaultProfile.copy()
            self.profile['ClientProfile.id'] = GUID()

    def Load(self, fileName):
	"""
	"""
        profile = ClientProfile.defaultProfile.copy()
        profile['ClientProfile.id'] = GUID()
        self.profile = LoadConfig(fileName, profile)

        if self.CheckProfile():
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
        else:
            raise InvalidProfileException
        
    def Dump(self):
        """
        """
        print "Profile: "
        for k in self.profile.keys():
            print "Key: %s Value: %s" % (k, self.profile[k])
        print "Profile Type: " + self.profileType
        print "Name: " + self.name
        print "Email: " + self.email
        print "Phone Number: " + self.phoneNumber
        print "Location: " + self.location
        print "Venue Client URL: " + self.venueClientURL
        print "Technical Support Information: " + self.techSupportInfo
        print "Public ID: " + str(self.publicId)
        print "Home Venue: " + self.homeVenue
        
    def Save(self, fileName):
        """ """
        config = {}
        config['ClientProfile.type'] = self.GetProfileType()
        config['ClientProfile.name'] = self.GetName()
        config['ClientProfile.email'] = self.GetEmail()
        config['ClientProfile.phone'] = self.GetPhoneNumber()
        config['ClientProfile.location'] = self.GetLocation()
        config['ClientProfile.venueclienturl'] = self.GetVenueClientURL()
        config['ClientProfile.techsupportinfo'] = self.GetTechSupportInfo()
        config['ClientProfile.id'] = self.GetPublicId()
        config['ClientProfile.home'] = self.GetHomeVenue()
        
        SaveConfig(fileName, config)

    def IsDefault(self):
        sc = self.profile.copy()
        sc['ClientProfile.id'] = ''
        
        if sc == ClientProfile.defaultProfile:
            return 1
        else:
            return 0

    def CheckProfile(self):
        for x in self.profile.keys():
            (section, option) = string.split(x, '.')
            if (section != ClientProfile.configSection and
                section != string.lower(ClientProfile.configSection)
                or option not in ClientProfile.validOptions):
                return 0
        return 1
    
    def SetProfileType(self, profileType):
        """ """
        self.profileType = profileType
        self.profile[ClientProfile.configSection + '.type'] = profileType
        
    def GetProfileType(self):
        """ """
        return self.profileType
    
    def SetLocation(self, location):
        """ """
        self.location = location
        self.profile[ClientProfile.configSection + '.location'] = location
    
    def GetLocation(self):
        """ """
        return self.location
    
    def SetEmail(self, email):
        """ """
        self.email = email
        self.profile[ClientProfile.configSection + '.email'] = email
    
    def GetEmail(self):
        """ """
        return self.email
    
    def SetName(self, name):
        """ """
        self.name = name
        self.profile[ClientProfile.configSection + '.name'] = name
        
    def GetName(self):
        """ """
        return self.name
    
    def GetDistinguishedName(self):
        """ """
        return self.distinguishedName

    def SetPhoneNumber(self, phoneNumber):
        """ """
        self.phoneNumber = phoneNumber
        self.profile[ClientProfile.configSection + '.phone'] = phoneNumber
        
    def GetPhoneNumber(self):
        """ """
        return self.phoneNumber
    
    def SetVenueClientURL(self, venueClientURL):
        """ """
        self.venueClientURL = venueClientURL
        self.profile[ClientProfile.configSection + '.venueclienturl'] = venueClientURL
    
    def GetVenueClientURL(self):
        """ """
        return self.venueClientURL
    
    def SetTechSupportInfo(self, techSupportInfo):
        """ """
        self.techSupportInfo = techSupportInfo
        self.profile[ClientProfile.configSection + '.techsupportinfo'] = techSupportInfo
        
    def GetTechSupportInfo(self):
        """ """
        return self.techSupportInfo
    
    def SetPublicId(self, publicId):
        """ """
        self.publicId = publicId
        self.profile[ClientProfile.configSection + '.id'] = publicId
        
    def GetPublicId(self):
        """ """
        return self.publicId

    def SetHomeVenue(self, venue):
        self.homeVenue = venue
        self.profile[ClientProfile.configSection + '.home'] = venue

    def GetHomeVenue(self):
        return self.homeVenue



def CreateClientProfile( clientProfileStruct ):
    """
    Create a client profile from a SOAP struct
    (this function should be removed when we have 
    WSDL support)
    """
    from AccessGrid.Types import Capability

    clientProfile = ClientProfile()

    clientProfile.distinguishedName = clientProfileStruct.distinguishedName
    clientProfile.email = clientProfileStruct.email
    clientProfile.homeVenue = clientProfileStruct.homeVenue
    clientProfile.icon = clientProfileStruct.icon
    clientProfile.location = clientProfileStruct.location
    clientProfile.name = clientProfileStruct.name
    clientProfile.phoneNumber = clientProfileStruct.phoneNumber
    clientProfile.privateId = clientProfileStruct.privateId
    clientProfile.profileFile = clientProfileStruct.profileFile
    clientProfile.profileType = clientProfileStruct.profileType
    clientProfile.publicId = clientProfileStruct.publicId
    clientProfile.techSupportInfo = clientProfileStruct.techSupportInfo
    clientProfile.venueClientURL = clientProfileStruct.venueClientURL

    # should be converting capabilities here
    clientProfile.capabilities = clientProfileStruct.capabilities


    return clientProfile
