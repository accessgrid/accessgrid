#-----------------------------------------------------------------------------
# Name:        unittest_Descriptions.py
# Purpose:     
#
# Author:      Eric C. Olson
#   
# Created:     2003/05/14
# RCS-ID:    
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
Unittest for Descriptions

"""

import signal, time, os
import unittest
from AccessGrid import Platform
from AccessGrid.Descriptions import *

class ObjectDescriptionTestCase(unittest.TestCase):
    """A test case for ObjectDescription."""

    def testObjectDescriptionDefaultConstructor(self):
       o = ObjectDescription("name") 

    def testObjectDescriptionConstructor(self):
       o = ObjectDescription("object name", "object description", "http://someuri") 
       assert o.GetName() == "object name"
       assert o.GetDescription() == "object description"
       assert o.GetURI() == "http://someuri"

    def testSetGetId(self):
       o = ObjectDescription("name")
       o.SetId(5)
       assert 5 == o.GetId()

    def testSetGetName(self):
       o = ObjectDescription("name")
       o.SetName("object name")
       assert "object name" == o.GetName()

    def testSetGetDescription(self):
       o = ObjectDescription("name")
       o.SetDescription("a description")
       assert "a description" == o.GetDescription()

    def testSetGetUri(self):
       o = ObjectDescription("name")
       o.SetURI("http://someuri")
       assert "http://someuri" == o.GetURI()

class DataDescriptionTestCase(unittest.TestCase):
    """A test case for DataDescription."""

    def testDataDescriptionDefaultConstructor(self):
       d = DataDescription("name")

    def testDataDescriptionConstructor(self):
       d = DataDescription("name")
       assert "name" == d.GetName()

    def testSetGetType(self):
       d = DataDescription("name")
       d.SetType("someType")
       assert "someType" == d.GetType()

    def testSetGetStatus(self):
       d = DataDescription("name")
       d.SetStatus(d.STATUS_PENDING)
       assert d.STATUS_PENDING == d.GetStatus()

    def testSetGetSize(self):
       d = DataDescription("name")
       d.SetSize(5)
       assert 5 == d.GetSize()

    def testSetGetChecksum(self):
       d = DataDescription("name")
       d.SetChecksum(16)
       assert 16 == d.GetChecksum()

    def testSetGetOwner(self):
       d = DataDescription("name")
       d.SetOwner("john doe")
       assert "john doe" == d.GetOwner()

    def testAsINIBlock(self):
       d = DataDescription("name")
       str = d.AsINIBlock()

class ConnectionDescriptionTestCase(unittest.TestCase):
    """A test case for ConnectionDescription.
       This is basically an ObjectDescription so there are very few tests."""

    def testConnectionDescriptionDefaultConstructor(self):
       c = ConnectionDescription("name")
       assert "name" == c.GetName()

    def testConnectionDescriptionConstructor(self):
       c = ConnectionDescription("name", "description", "http://someuri")
       assert c.GetName() == "name"
       assert c.GetDescription() == "description"
       assert c.GetURI() == "http://someuri"

class VenueDescriptionTestCase(unittest.TestCase):
    """A test case for VenueDescription."""

    def testVenueDescriptionDefaultConstructor(self):
       v = VenueDescription()

    def testVenueDescriptionConstructor(self):
       v = VenueDescription("name", "description", ["admin1","admin2"],(0,''), [], [])
       assert v.GetName() == "name"
       assert v.GetDescription() == "description"

    def testAsINIBlock(self):
       v = VenueDescription()
       str = v.AsINIBlock() 

class ServiceDescriptionTestCase(unittest.TestCase):
    """A test case for ServiceDescription."""

    def testServiceDescriptionConstructor(self):
       s = ServiceDescription("name", "description", "http://someuri", "x-ag-testmimetype")
       assert s.GetName() == "name"
       assert s.GetDescription() == "description"
       assert s.GetMimeType() == "x-ag-testmimetype"

    def testSetGetMimeType(self):
       s = ServiceDescription("name", "description", "http://someuri", "x-ag-testmimetype")
       s.SetMimeType("x-ag-testmimetype2")
       assert s.GetMimeType() == "x-ag-testmimetype2"

class ApplicationDescriptionTestCase(unittest.TestCase):
    """A test case for ApplicationDescription."""

    def testApplicationescriptionConstructor(self):
       s = ApplicationDescription("my_id", "name", "description", "http://someuri", "x-ag-testmimetype")
       assert s.id == "my_id"
       assert s.GetName() == "name"
       assert s.GetDescription() == "description"
       assert s.GetMimeType() == "x-ag-testmimetype"

    def testSetGetMimeType(self):
       s = ApplicationDescription("my_id", "name", "description", "http://someuri", "x-ag-testmimetype")
       s.SetMimeType("x-ag-testmimetype2")
       assert s.GetMimeType() == "x-ag-testmimetype2"

class StreamDescriptionTestCase(unittest.TestCase):
    """A test case for StreamDescription."""

    def testStreamDescriptionDefaultConstructor(self):
       v = StreamDescription()

    def testStreamDescriptionConstructor(self):
       location = MulticastNetworkLocation()
       capability = Capability()
       encryptionFlag = 1
       encryptionKey = "abcdefg"
       static = 0
       v = StreamDescription("name", location, capability, encryptionFlag, encryptionKey, static )
       assert "name" == v.GetName()
       assert capability == v.capability
       assert encryptionFlag == v.encryptionFlag
       assert encryptionKey == v.encryptionKey
       assert static == v.static

    def testAsINIBlock(self):
       v = StreamDescription()
       str = v.AsINIBlock() 

class AGServiceManagerDescriptionTestCase(unittest.TestCase):
    """A test case for ServiceManagerDescription."""

    def testAGServiceManagerDescriptionConstructor(self):
       s = AGServiceManagerDescription("name", "http://someuri")
       assert s.name == "name"
       assert s.uri == "http://someuri"

class AGServiceDescriptionTestCase(unittest.TestCase):
    """A test case for ServiceDescription."""

    def testAGServiceDescriptionConstructor(self):
       s = AGServiceDescription("name", "description", "http://someuri", "some capabilities", "some resource", "some executable", "http://some_servicemanageruri", "http://some_servicepackageuri", "version")
       assert s.name == "name"
       assert s.description == "description"
       assert s.uri == "http://someuri"
       assert s.resource == "some resource"
       assert s.capabilities == "some capabilities"
       assert s.executable == "some executable"
       assert s.serviceManagerUri == "http://some_servicemanageruri"
       assert s.servicePackageFile == "http://some_servicepackageuri"
       assert s.version == "version"
       
def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(ObjectDescriptionTestCase)
    suite2 = unittest.makeSuite(DataDescriptionTestCase)
    suite3 = unittest.makeSuite(ConnectionDescriptionTestCase)
    suite4 = unittest.makeSuite(VenueDescriptionTestCase)
    suite5 = unittest.makeSuite(ServiceDescriptionTestCase)
    suite6 = unittest.makeSuite(ApplicationDescriptionTestCase)
    suite7 = unittest.makeSuite(StreamDescriptionTestCase)
    suite8 = unittest.makeSuite(AGServiceManagerDescriptionTestCase)
    suite9 = unittest.makeSuite(AGServiceDescriptionTestCase)
    return unittest.TestSuite([suite1,suite2,suite3,suite4,suite5,suite6,suite7,suite8,suite9])

if __name__ == '__main__':
    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')

