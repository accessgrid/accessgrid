#-----------------------------------------------------------------------------
# Name:        unittest_VenueServer.py
# Purpose:     
#
# Author:      Eric C. Olson
#   
# Created:     2003/04/04
# RCS-ID:    
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
Unittest for VenueServer

No external connections are made for this level of test.
Temporarily requires a kill (unix: cntrl-Z, "kill %") to stop the server and the test.

Note that PyUnit (and JUnit as well) execute setUp() and tearDown() once for
EACH test and make it difficult to setUp and tearDown something across multiple
tests.  This is not ideal for our server tests, but we work around it to keep a
server running for multiple tests.

Testing:
   AddVenue, RemoveVenue, Checkpoint, AddAdministrator, RemoveAdministrator, GetAdministrator, GetSetStorageLocaion, GetSetEncryptAllMedia
Not Testing yet:
   Persistence, SetDefaultVenueServer

"""

import logging, logging.handlers
import unittest
from AccessGrid.Descriptions import VenueDescription
from AccessGrid.VenueServer import VenueServer
from AccessGrid.Venue import Venue
from AccessGrid.hosting.pyGlobus.Server import Server

class VenueServerTestSuite(unittest.TestSuite):
    """A TestSuite that creates a server for use by VenueServerTestCase."""

    def __init__(self, tests=()):
        global venueServer  # so TestCases can access it
        global venue1       # so TestCases can access it
        unittest.TestSuite.__init__(self, tests) # Important to call base class constructor
        logFile = "VenueServer.log"
        log = logging.getLogger("AG")
        log.setLevel(logging.DEBUG)
        hdlr = logging.handlers.RotatingFileHandler(logFile, "a", 10000000, 0)
        fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
        hdlr.setFormatter(fmt)
        log.addHandler(hdlr)
        # server
        venueServer = VenueServer()
        venueServer.SetStorageLocation("testData")
        # A venue for testing
        venue1 = VenueDescription("unittestVenue1", "venue for unittest")
        venue1.uri = "LocalVenueServer/default1"
        venueServer.AddVenue(venue1)


class VenueServerTestCase(unittest.TestCase):
    """A test case for VenueServers."""

    def testAddVenue(self):
        venueServer.AddVenue(VenueDescription("unittestVenue2", "venue for unittest"));

    def testRemoveVenue(self):
        rvenue = VenueDescription("unittestVenue3", "venue for unittest")
        rvenue.uri = "LocalVenueServer/default2"

        venueServer.AddVenue(rvenue)

        venueRemoved = 0
        venueDescList = venueServer.GetVenues()
        for v in venueDescList:
            if v.name == "unittestVenue3":
                venueServer.RemoveVenue(v.uri)    
                venueRemoved = 1
        assert venueRemoved

    def testGetSetStorageLocation(self):
        venueServer.SetStorageLocation("testData")
        assert "testData" == venueServer.GetStorageLocation()

    def testCheckpoint(self):
        venueServer.Checkpoint()

    def testGetSetEncryptAllMedia(self):
        original = venueServer.GetEncryptAllMedia()
        venueServer.SetEncryptAllMedia(1)
        assert 1 == venueServer.GetEncryptAllMedia()
        venueServer.SetEncryptAllMedia(0)
        assert 0 == venueServer.GetEncryptAllMedia()
        venueServer.SetEncryptAllMedia(original)

    def testAddRemoveAdministrator(self):
        venueServer.AddAdministrator("testAdmin")
        assert "testAdmin" in venueServer.GetAdministrators()
        venueServer.RemoveAdministrator("testAdmin")
        assert "testAdmin" not in venueServer.GetAdministrators()

    # Test not finished yet
    # def testGetSetDefaultVenue(self):
        #original = venueServer.GetDefaultVenue()
        #venueServer.SetDefaultVenue(venue1.uri)
        #assert venueServer.GetDefaultVenue() == venue1.uri
        #venueServer.SetDefaultVenue(original)

    # def testAddData(self):

    # VenueServer.ModifyVenue not finished yet.
    # def testModifyVenue(self):

    # This shutdown is not the most elegant solution, but the writers of PyUnit and JUnit 
    #   want to make it as hard as possible to allow a single teardown (or setup) that
    #   will affect multiple testCases.  We don't want to shutdown and restart the 
    #   server for each test -- and besides, at the time of this writing it's not supported 
    #   by the server.   This should be the last test case in the default function list 
    #   and also last when the list is sorted alphabetically.
  # Commented out for now because it takes a long time to shutdown, and we still have to kill
  #   the server for now anyway.
    #def testZEnd(self):
        #venueServer.Shutdown(0)

    # Would be called after each testCase
    # def tearDown(self):
        #

    # Would be called before each testCase
    # def setUp(self):
        #

def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(VenueServerTestCase, suiteClass=VenueServerTestSuite)
    return unittest.TestSuite( [suite1] )

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

