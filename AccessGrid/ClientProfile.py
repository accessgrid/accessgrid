#-----------------------------------------------------------------------------
# Name:        ClientProfile.py
# Purpose:     The ClientProfile is the data that is used on the server side
#               to represent connected clients (both users and shared nodes).
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: ClientProfile.py,v 1.42 2004-12-06 19:52:03 lefvert Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: ClientProfile.py,v 1.42 2004-12-06 19:52:03 lefvert Exp $"
__docformat__ = "restructuredtext en"

import os
import ConfigParser
import string
import md5

from AccessGrid.Utilities import LoadConfig, SaveConfig
from AccessGrid.GUID import GUID
from AccessGrid.Platform.Config import UserConfig
from AccessGrid import Log

log = Log.GetLogger(Log.VenueClient)

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
        'ClientProfile.techsupportinfo':'',
        'ClientProfile.venueclienturl' : '',
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
        self.publicId = str(GUID())
        self.location = ''
        self.venueClientURL = ''
        self.homeVenue = ''
        self.privateId = None
        self.distinguishedName = None
        self.techSupportInfo = ''
        self.connectionId = None

        if profileFile != None and os.path.exists(profileFile):
            self.Load(self.profileFile)
        else:
            self.profile = ClientProfile.defaultProfile.copy()
            self.profile['ClientProfile.id'] = self.publicId
            self._SetFromConfig() # Get the values from the config

    def Load(self, fileName, loadDnDetails=0):
	"""
        loadDnDetails is used by the cache to include the reading
          of a DN when reading from the stored profile.
	"""
        profile = ClientProfile.defaultProfile.copy()
        self.profile = LoadConfig(fileName, profile)

        self._SetFromConfig() # Get the values from the config

        if loadDnDetails: # DN used with profileCache, not in standard profile.
            if 'ClientProfile.distinguishedname' in self.profile:
                self.distinguishedName = self.profile['ClientProfile.distinguishedname']

    def _SetFromConfig(self):
        if self.CheckProfile():
            self.profileType = self.profile['ClientProfile.type']
            self.name = self.profile['ClientProfile.name']
            self.email = self.profile['ClientProfile.email']
            self.phoneNumber = self.profile['ClientProfile.phone']
            self.icon = self.profile['ClientProfile.icon']
            self.publicId = self.profile['ClientProfile.id']
            self.location = self.profile['ClientProfile.location']
            self.venueClientURL = self.profile['ClientProfile.venueclienturl']
            self.homeVenue = self.profile['ClientProfile.home']
            self.techSupportInfo = self.profile['ClientProfile.techsupportinfo']
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
        print "Public ID: " + str(self.publicId)
        print "Home Venue: " + self.homeVenue

    def __str__(self):
        returnVal =  " Profile Type: " + self.profileType \
                    + "\n Name: " + self.name \
                    + "\n Email: " + self.email\
                    + "\n Phone Number: " + self.phoneNumber\
                    + "\n Location: " + self.location\
                    + "\n Venue Client URL: " + self.venueClientURL\
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
                log.error('ClientProfile.CheckProfile: Check profile failed for section: %s option: %s'%(section, option))
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
               self.homeVenue == obj.homeVenue :
                isSame = 1
        except:
            pass
        return isSame

class ClientProfileCache:
    """
    Class for caching profiles.
    """
    def __init__(self, cachePath=""):
        if len(cachePath):
            self.cachePath = cachePath
        else:
            userConfig = UserConfig.instance()
            self.cachePath = os.path.join(userConfig.GetConfigDir(),
                                          "profileCache")
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
        hsh = md5.new(profile.GetDistinguishedName())
        short_filename = hsh.hexdigest()
        filename = os.path.join(self.cachePath, short_filename)

        # If profile in cache, load it and see if it's different
        if os.path.exists( filename ):
            old_profile = ClientProfile(filename)
            if not profile.InformationMatches(old_profile):
                # Save profile if it is different than cached profile.
                profile.Save(filename, saveDnDetails=1)
        else:
            # create directory in case it was removed while app was running.
            if not os.path.exists(self.cachePath):
                os.mkdir(self.cachePath)
            profile.Save(filename, saveDnDetails=1)

    def loadProfileFromDN(self, distinguished_name):
        hsh = md5.new(distinguished_name)
        short_filename = hsh.hexdigest()
        filename = os.path.join(self.cachePath, short_filename)
        profile = ClientProfile()
        profile.Load(filename, loadDnDetails=1)
        return profile

    def loadAllProfiles(self):
        profiles = []
        files = os.listdir(self.cachePath)
        for f in files:
            long_filename = os.path.join(self.cachePath, f)
            profile = ClientProfile()
            profile.Load(long_filename, loadDnDetails=1)
            if profile:
                profiles.append(profile)
        return profiles


