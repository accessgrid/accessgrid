#-----------------------------------------------------------------------------
# Name:        unittest_AGNodeService.py
# Purpose:     
#
# Author:      Eric C. Olson
#   
# Created:     2003/04/07
# RCS-ID:    
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
Unittest for AGNodeService

No external connections are made for this level of test.

Note that PyUnit (and JUnit as well) execute setUp() and tearDown() once for
EACH test and make it difficult to setUp and tearDown something across multiple
tests.  This is not ideal for our server tests, but we work around it to keep a
server running for multiple tests.

Testing:
   AddVenue, RemoveVenue, Checkpoint, AddAdministrator, RemoveAdministrator, GetAdministrator, GetSetStorageLocaion, GetSetEncryptAllMedia
Not Testing yet:
   Persistence, SetDefaultVenueServer

"""

import signal, time, sys
import unittest
import logging, logging.handlers

from AccessGrid.AGNodeService import AGNodeService, AGNodeServiceI
from AccessGrid.AGServiceManager import AGServiceManager, AGServiceManagerI
from AccessGrid.Descriptions import AGServiceManagerDescription
from AccessGrid.hosting import SecureServer as Server
from AccessGrid import Toolkit

nodeService = None
server = None
log = None

class AGNodeServiceTestCase(unittest.TestCase):
    """A test case for AGNodeServices."""

    # Signal handler to catch signals and shutdown
    def SignalHandler(self, signum, frame):
        """
        SignalHandler catches signals and shuts down the VenueServer (and
        all of it's Venues. Then it stops the hostingEnvironment.
        """
        print "SignalHandler"
        global running, server

        server.Stop()
        # shut down the node service, saving config or whatever
        running = 0

    def testAAABegin(self):
        global nodeService, server, log

        # initialize toolkit and environment
        app = Toolkit.Service.instance()
        app.Initialize("NodeService_test", sys.argv[:1])
        log = app.GetLog()
        
        # Create a Node Service
        nodeService = AGNodeService()

        # Create a hosting environment
        server = Server(('localhost', 4000))

        # get url and print it
        url = server.GetURLBase()
        print "Server URL: %s" % url

        # Create the Node Service Service
        nsurl = server.RegisterObject(AGNodeServiceI(nodeService),
                                      path="/NodeService")

        print "NS URL: %s" % nsurl
        
        # Tell the world where to find the service
        log.info("Starting service; URI: %s", nsurl)

        # Register a signal handler so we can shut down cleanly
        signal.signal(signal.SIGINT, self.SignalHandler)

        # Run the service
        server.RunInThread()


    # Authorization Methods

    def testAddRemoveAuthorizedUser(self):
        global nodeService
        pass

    # Service Manager Methods

    def testAddRemoveServiceManager(self):
        global nodeService, server
        # Create the Service Manager
        serviceManager = AGServiceManager(server)
        smurl = server.RegisterObject(AGServiceManagerI(serviceManager),
                              path="/ServiceManager")
        serviceManagerDesc = AGServiceManagerDescription("testServiceManager",
                                                smurl)
        nodeService.AddServiceManager(serviceManagerDesc)

        assert serviceManagerDesc in nodeService.GetServiceManagers()
        nodeService.RemoveServiceManager(serviceManagerDesc) 
        assert serviceManagerDesc not in nodeService.GetServiceManagers()

    # Service Methods

    def testGetServices(self):
        global nodeService
        nodeService.GetServices()

    # Configuration Methods

    def testGetConfigurations(self):
        global nodeService
        nodeService.GetConfigurations()

    def testStoreConfiguration(self):
        global nodeService
        nodeService.StoreConfiguration(".testStore_agns.cfg")

    def testLoadConfiguration(self):
        global nodeService
        nodeService.StoreConfiguration(".testLoad_agns.cfg")
        nodeService.LoadConfiguration(".testLoad_agns.cfg")

    #def testConfigureStreams(self):

    # Other Methods

    def testGetCapabilites(self):
        global nodeService
        nodeService.GetCapabilities()

    # Cleanup things set up in the test suite init above.
    #   Unittest suites don't have a proper way to cleanup things used 
    #   in the entire suite.
    def testZEnd(self):
        global nodeService
        nodeService.Stop()
        server.Stop() 

def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(AGNodeServiceTestCase)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')

