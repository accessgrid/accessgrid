#-----------------------------------------------------------------------------
# Name:        ClientProfile.py
# Purpose:     The ClientProfile is the data that is used on the server side
#               to represent connected clients (both users and shared nodes).
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: ClientProfile.py,v 1.28 2003-09-11 20:43:41 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import os
import ConfigParser
import string
import md5

from AccessGrid.Utilities import LoadConfig, SaveConfig
from AccessGrid.GUID import GUID
from AccessGrid.Platform import GetUserConfigDir

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
        'home',
        'distinguishedname']
        
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

    def Load(self, fileName, loadDnDetails=0):
	"""
        loadDnDetails is used by the cache to include the reading
          of a DN when reading from the stored profile.
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
            if loadDnDetails:
                if 'ClientProfile.distinguishedname' in self.profile:
                    self.distinguishedName = self.profile['ClientProfile.distinguishedname']
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

    def __str__(self):
        returnVal =  " Profile Type: " + self.profileType \
                    + "\n Name: " + self.name \
                    + "\n Email: " + self.email\
                    + "\n Phone Number: " + self.phoneNumber\
                    + "\n Location: " + self.location\
                    + "\n Venue Client URL: " + self.venueClientURL\
                    + "\n Technical Support Information: " + self.techSupportInfo\
                    + "\n Public ID: " + str(self.publicId)\
                    + "\n Home Venue: " + self.homeVenue

        return returnVal
        
    def Save(self, fileName, saveDnDetails=0):
        """
        saveDnDetails is used by the cache to include the DN
          in the stored profile.
        """
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
        if saveDnDetails:
            config['ClientProfile.distinguishedname'] = self.GetDistinguishedName()
        
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

    def InformationMatches(self, obj):
        """
        return true (1) if profile information is equivalent
          return false (0) otherwise.
        This was written mostly for the ClientProfileCache to use, so
          if modifying this function keep that purpose in mind.
          Specifically, a profile should be equivalent to its cached 
          profile if the user hasn't changed his/her profile.  This means
          things such as VenueClientURL are not tested below since it can
          change after the venue client reconnects.
        """
        if not isinstance(obj, ClientProfile):
            return 0
        isSame = 0
        try:
            # members not tested for equality 
            #  self.fileType == obj.fileType
            #  self.publicId == obj.publicId
            #  self.privateId == obj.privateId
            #  self.capabilities == obj.capabilites 
            #  self.distinguishedName == obj.distinguishedName 
            #  self.venueClientURL == obj.venueClientURL and \
            if self.profileType == obj.profileType and \
               self.name == obj.name and \
               self.email == obj.email and \
               self.phoneNumber == obj.phoneNumber and \
               self.icon == obj.icon and \
               self.location == obj.location and \
               self.techSupportInfo == obj.techSupportInfo and \
               self.homeVenue == obj.homeVenue :
                isSame = 1
        except:
            pass
        return isSame

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

class ClientProfileCache:
    """
    Class for caching profiles.
    """
    def __init__(self, cachePath=""):
        if len(cachePath):
            self.cachePath = cachePath
        else:
            self.cachePath = os.path.join(GetUserConfigDir(), "profileCache")
        if not os.path.exists( self.cachePath ):
            os.mkdir (self.cachePath)

    def updateProfile(self, profile):
        if not profile.GetDistinguishedName():
            raise InvalidProfileException
            return

        # Create a filename to store profile in the cache.
        # Hash is almost always unique.  If there ever is 
        #   a filename collision, it's not the end of the 
        #   world, only the most recent profile gets cached.
        hash = md5.new(profile.GetDistinguishedName())
        short_filename = hash.hexdigest()
        filename = os.path.join(self.cachePath, short_filename)

        # If profile in cache, load it and see if it's different
        if os.path.exists( filename ):
            old_profile = ClientProfile(filename)
            if not profile.InformationMatches(old_profile):
                # Save profile if it is different than cached profile.
                profile.Save(filename, saveDnDetails=1)
        else:
            profile.Save(filename, saveDnDetails=1)

    def loadProfileFromDN(self, distinguished_name):
        hash = md5.new(distinguished_name)
        short_filename = hash.hexdigest()
        filename = os.path.join(self.cachePath, short_filename)
        profile = ClientProfile()
        profile.Load(filename, loadDnDetails=1)
        return profile

    def loadAllProfiles(self):
        profiles = []
        files = os.listdir(self.cachePath)
        for file in files:
            long_filename = os.path.join(self.cachePath, file)
            profile = ClientProfile()
            profile.Load(long_filename, loadDnDetails=1)
            if profile:
                profiles.append(profile)
        return profiles


