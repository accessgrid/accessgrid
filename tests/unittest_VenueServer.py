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
import threading
from AccessGrid.Descriptions import VenueDescription
from AccessGrid.VenueServer import VenueServer
from AccessGrid.Venue import Venue
from AccessGrid import Toolkit
from AccessGrid.Security import X509Subject

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
        # initialize toolkit and environment
        app = Toolkit.CmdlineApplication()
        app.Initialize()
        # server
        venueServer = VenueServer()
        venueServer.SetStorageLocation("testData")
        # A venue for testing
        venue1 = VenueDescription("unittestVenue1", "venue for unittest")
        venue1.uri = "LocalVenueServer/default1"
        venueServer.AddVenue(venue1)


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

    # Authorization callback for globus
    def AuthCallback(server, g_handle, remote_user, context):
        return 1

    def testAddVenue(self):
        venueServer.AddVenue(VenueDescription("unittestVenue2", "venue for unittest"));

    def testRemoveVenue(self):
        rvenue = VenueDescription("unittestVenue3", "venue for unittest")
        rvenue.uri = "LocalVenueServer/default2"

        venueServer.AddVenue(rvenue)

        venueRemoved = 0
        venueDescList = venueServer.GetVenues()
        for v in venueDescList:
            print "venue:", v.name, ", ", v.uri
            if v.name == "unittestVenue3":
                id = venueServer.IdFromURL(v.uri)
                venueServer.RemoveVenue(id)
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
        venueServer.authManager.FindRole("Administrators").AddSubject(X509Subject.CreateSubjectFromString("testAdmin"))
        assert "testAdmin" in venueServer.authManager.FindRole("Administrators").GetSubjectListAsStrings()
        venueServer.authManager.FindRole("Administrators").RemoveSubject("testAdmin")
        assert "testAdmin" not in venueServer.authManager.FindRole("Administrators").GetSubjectListAsStrings()

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
    def testZEnd(self):
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
    suite1 = unittest.makeSuite(VenueServerTestCase, suiteClass=VenueServerTestSuite)
    return unittest.TestSuite( [suite1] )

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

