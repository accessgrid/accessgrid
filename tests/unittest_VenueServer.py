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
import sys
import logging, logging.handlers
import unittest
import threading
from AccessGrid.Descriptions import VenueDescription
from AccessGrid.VenueServer import VenueServer
from AccessGrid.hosting import IdFromURL
from AccessGrid.Venue import Venue
from AccessGrid import Toolkit
from AccessGrid.Security import X509Subject

class VenueServerTestCase(unittest.TestCase):
    """A test case for VenueServers."""

    def SignalHandler(self, signum, frame):
        """
        SignalHandler catches signals and shuts down the VenueServer (and
        all of it's Venues. Then it stops the hostingEnvironment.
        """
        print "SignalHandler"
        global running
        global server
        server.Stop()
        # shut down the node service, saving config or whatever
        running = 0

    def testAddVenue(self):
        global venueServer
        venueServer.AddVenue(VenueDescription("unittestVenue2", "venue for unittest"));

    def testRemoveVenue(self):
        global venueServer
        rvenue = VenueDescription("unittestVenue3", "venue for unittest")
        rvenue.uri = venueServer.AddVenue(rvenue)
        venueRemoved = 0
        venueDescList = venueServer.GetVenues()
        for v in venueDescList:
            print "venue:", v.name, ", ", v.uri
            if v.name == rvenue.name:
                venueServer.RemoveVenue(v.uri)
                venueRemoved = 1
        assert venueRemoved

    def testGetSetStorageLocation(self):
        global venueServer
        venueServer.SetStorageLocation("testData")
        assert "testData" == venueServer.GetStorageLocation()

    def testCheckpoint(self):
        global venueServer
        venueServer.Checkpoint()

    def testGetSetEncryptAllMedia(self):
        global venueServer
        original = venueServer.GetEncryptAllMedia()
        venueServer.SetEncryptAllMedia(1)
        assert 1 == venueServer.GetEncryptAllMedia()
        venueServer.SetEncryptAllMedia(0)
        assert 0 == venueServer.GetEncryptAllMedia()
        venueServer.SetEncryptAllMedia(original)

    def testAddRemoveAdministrator(self):
        global venueServer
        venueServer.authManager.FindRole("Administrators").AddSubject(X509Subject.CreateSubjectFromString("testAdmin"))

        assert venueServer.authManager.FindRole("Administrators").HasSubject(X509Subject.CreateSubjectFromString("testAdmin"))
        venueServer.authManager.FindRole("Administrators").RemoveSubject(X509Subject.CreateSubjectFromString("testAdmin"))
        assert not venueServer.authManager.FindRole("Administrators").HasSubject(X509Subject.CreateSubjectFromString("testAdmin"))

    def testAAABegin(self):
        global venueServer  # so TestCases can access it
        global venue1       # so TestCases can access it
        # initialize toolkit and environment
        app = Toolkit.Service()
        #
        app.Initialize("VenueServer_test", sys.argv[:1])
        # server
        venueServer = VenueServer()
        venueServer.SetStorageLocation("testData")
        # A venue for testing
        venue1 = VenueDescription("unittestVenue1", "venue for unittest")
        venue1.uri = "LocalVenueServer/default1"
        venueServer.AddVenue(venue1)

    # Test not finished yet
    # def testGetSetDefaultVenue(self):
        #original = venueServer.GetDefaultVenue()
        #venueServer.SetDefaultVenue(venue1.uri)
        #assert venueServer.GetDefaultVenue() == venue1.uri
        #venueServer.SetDefaultVenue(original)

    # def testAddData(self):

    # VenueServer.ModifyVenue not finished yet.
    # def testModifyVenue(self):

    # Cleanup things we set up in the test suite init above.
    #   Unittest suites don't have a proper way to cleanup things used in
    #   the entire suite.  The writers of PyUnit and JUnit do this so
    #   tests don't interfere with each other.
    # But we don't want to shutdown and restart the server for each test.
    #   This should be the last test case in the default function list 
    #   and also last when the list is sorted alphabetically.

    def testZZZEnd(self):
        venueServer.Shutdown()
        # In case tests leave threads open, print them out so we
        # know why the program isn't exiting.
        for t in threading.enumerate():
            if "MainThread" != t.getName() and t.getName().find("Dummy") == -1:
                print "Thread ", t

    # Would be called after each testCase
    # def tearDown(self):
        #

    # Would be called before each testCase
    # def setUp(self):
        #

def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(VenueServerTestCase)
    return unittest.TestSuite( [suite1] )

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

