#-----------------------------------------------------------------------------
# Name:        ClientProfile.py
# Purpose:     The ClientProfile is the data that is used on the server side
#               to represent connected clients (both users and shared nodes).
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: ClientProfile.py,v 1.6 2003-01-21 19:27:35 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import ConfigParser
import string

class ClientProfile:
    """
    The client profile is used to represent the clients throughout the AG.
    The client profile is all public data, however only the author of the
    profile is allowed to modify it.
    """

    _defaultProfile = {
        'VenueClient.profileType' : 'user',
        'VenueClient.name' : 'John Doe',
        'VenueClient.email' : 'john@mail.com',
        'VenueClient.phoneNumber' : '+1 888 959 5555',
        'VenueClient.icon' : '',
        'VenueClient.publicId' : 'do-de-do',
        'VenueClient.location' : 'Fargo, North Dakota',
        'VenueClient.venueClientURL' : '',
        'VenueClient.technicalSupportInformation' : '',
        'VenueClient.homeVenue' : 'http://test.com/Venues/default'
        }

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
        self.venueClientUri = ''
        self.technicalSupportInformation = ''
        self.homeVenue = ''
        self.privateId = None
        self.distinguishedName = None
        self.capabilities = []

        if profileFile != None:
            self._LoadFromFile(self.profileFile)



    def _LoadFromFile(self, fileName):
	"""
	Returns a dictionary with keys of the form <section>.<option>
	and the corresponding values.
	This is from the python cookbook credit: Dirk Holtwick.
	"""
        profile = {}
        self.cp = ConfigParser.ConfigParser()
        self.cp.read(fileName)
        for sec in self.cp.sections():
            for opt in self.cp.options(sec):
                        val = string.strip(self.cp.get(sec, opt))
                        profile[sec + "." + opt] = string.strip(self.cp.get(sec, opt))
        self.profileType = profile['VenueClient.profiletype']
        self.name = profile['VenueClient.name']
        self.email = profile['VenueClient.email']
        self.phoneNumber = profile['VenueClient.phonenumber']
        self.icon = profile['VenueClient.icon']
        self.publicId = profile['VenueClient.publicid']
        self.location = profile['VenueClient.location']
        self.technicalSupportInformation = profile['VenueClient.technicalsupportinformation']
        self.homeVenue = profile['VenueClient.homevenue']

        return profile

    def Dump(self):
        """
        """
        print "Profile Type: " + self.profileType
        print "Name: " + self.name
        print "Email: " + self.email
        print "Phone Number: " + self.phoneNumber
        print "Location: " + self.location
        print "Venue Client URL: " + self.venueClientURL
        print "Technical Support Information: " + self.technicalSupportInformation
        print "Icon: " + str(self.icon)
        print "Public ID: " + self. publicId
        
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
        return location
    
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
    
    def SetTechnicalSupportInformation(self, technicalSupportInformation):
        """ """
        self.technicalSupportInformation = technicalSupportInformation
        
    def GetTechnicalSupportInformation(self):
        """ """
        return self.technicalSupportInformation
    
    def SetPublicID(self, publicId):
        """ """
        self.publicId = publicId
        
    def GetPublicID(self):
        """ """
        return self.publicId

if __name__ == "__main__":
    profile = ClientProfile('userProfileExample')
    print "\nProfile from File:"
    profile.Dump()

    profile2 = ClientProfile()
    print "\nEmpty Profile:"
    profile2.Dump()
