#-----------------------------------------------------------------------------
# Name:        unittest_ClientProfile.py
# Purpose:     
#
# Author:      Eric C. Olson
#   
# Created:     2003/05/07
# RCS-ID:    
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
Unittest for ClientProfile

"""

import signal, time, os
import unittest
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid.ClientProfile import ClientProfile, InvalidProfileException

class ClientProfileTestCase(unittest.TestCase):
    """A test case for ClientProfile."""

    def testSaveLoad(self):
       c = ClientProfile()
       filename = os.path.join( SystemConfig.instance().GetTempDir(),".testProfile") 
       c.Save(filename)

       d = ClientProfile()
       d.Load(filename)
       assert d.CheckProfile()

    def testIsDefault(self):
       c = ClientProfile() 
       assert c.IsDefault()

    def testCheckProfile(self): 
       c = ClientProfile()
       assert c.CheckProfile()

    def testSetGetProfileType(self): 
       c = ClientProfile()
       c.SetProfileType("user")
       assert "user" == c.GetProfileType()

    def testSetGetLocation(self): 
       c = ClientProfile()
       c.SetLocation("somelocation")
       assert "somelocation" == c.GetLocation()

    def testSetGetEmail(self): 
       c = ClientProfile()
       c.SetEmail("test@email.com")
       assert "test@email.com" == c.GetEmail()

    def testSetGetName(self): 
       c = ClientProfile()
       c.SetName("test name")
       assert "test name" == c.GetName()

    def testGetDistinguishedName(self): 
       c = ClientProfile()
       dname = c.GetDistinguishedName()

    def testSetGetPhoneNumber(self): 
       c = ClientProfile()
       c.SetPhoneNumber("867-5309")
       assert "867-5309" == c.GetPhoneNumber()

    def testSetGetVenueClientURL(self): 
       c = ClientProfile()
       c.SetVenueClientURL("https://vv2.mcs.anl.gov:9000/Venues/default")
       assert "https://vv2.mcs.anl.gov:9000/Venues/default" == c.GetVenueClientURL()

    def testSetGetTechSupportInfo(self): 
       c = ClientProfile()
       c.SetTechSupportInfo("Some Tech Support Info")
       assert "Some Tech Support Info" == c.GetTechSupportInfo()

    def testSetGetPublicId(self): 
       c = ClientProfile()
       c.SetPublicId("myPublicId")
       assert "myPublicId" == c.GetPublicId()

    def testSetGetHomeVenue(self): 
       c = ClientProfile()
       c.SetHomeVenue("https://vv2.mcs.anl.gov:9000/Venues/default")
       assert "https://vv2.mcs.anl.gov:9000/Venues/default" == c.GetHomeVenue()


def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(ClientProfileTestCase)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')

