#-----------------------------------------------------------------------------
# Name:        unittest_AGServiceManager.py
# Purpose:     
#
# Author:      Eric C. Olson
#   
# Created:     2003/04/01
# RCS-ID:    
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
Unittest for AGServiceManager
No external connections are made for this level of test.

Testing:
   SetAuthorizedUsers, GetResources, DiscoverResources
Not Testing yet:
   Persistence, SetDefaultVenueServer

Note that PyUnit (and JUnit as well) execute setUp() and tearDown() once
for each test.

"""

import unittest
import signal, time, os, sys
import logging, logging.handlers
from AccessGrid.AGServiceManager import AGServiceManager, AGServiceManagerI
from AccessGrid.AGNodeService import AGNodeService, AGNodeServiceI
from AccessGrid.hosting import SecureServer as Server
from AccessGrid.Platform import AGTK_LOCATION 
from AccessGrid import Toolkit

serviceManager = None
nodeService = None
server = None
log = None
smURL = None

# AGServiceManager unittests below assume a basic initialization works 
#   in their setup so we'll just confirm it works in a separate test.
class AGServiceManagerBasicTest(unittest.TestCase):
    """Basic test case for AGServiceManager."""
    def testInit(self):
        """Test initialization"""
        app = Toolkit.Service.instance()
        app.Initialize("unittest_AGServiceManager", sys.argv[:1])
        self.serviceManager = AGServiceManager(Server(('localhost',5000)))
        self.serviceManager.Shutdown()
        time.sleep(1)

class AGServiceManagerTestCase(unittest.TestCase):

    def testAAABegin(self):
        global server, serviceManager, nodeService, log, smURL

        # initialize toolkit and environment
        app = Toolkit.Service.instance()
        app.Initialize("ServiceManager_test", sys.argv[:1])
        log = app.GetLog()

        # Startup serviceManager to test
        server = Server(('localhost', 5000))
        serviceManager = AGServiceManager(server)
        smURL = server.RegisterObject(AGServiceManagerI(serviceManager),
                                         path="/ServiceManager")

        # Start a node service to help test some of ServiceManager's
        #  functions like AddService()
        nodeService = AGNodeService()
        nsurl = server.RegisterObject(AGNodeServiceI(nodeService),
                                      path="/NodeService")

    def testValidInitialization(self):
        global serviceManager
        assert None != serviceManager.processManager

    # Authorization methods

    def testSetAuthorizedUsers(self):
        global serviceManager
        pass

    # Resource methods
    def testGetResources(self):
        global serviceManager
        serviceManager.GetResources()

    # Service methods

    def testAddService(self):
        global serviceManager, nodeService
        services = serviceManager.GetAvailableServices()

        # Verify there are services to add.
        assert services is not None and len(services) > 0 

        # Add all services to make sure they work
        for service in services:
            if service.name != "" and service.name != "DisplayService":
                serviceManager.AddService(service, None, None)

        time.sleep(2)

    def testRemoveService(self):
        global serviceManager, nodeService
        # First add a service to make sure we can remove one.
        possible_services = serviceManager.GetAvailableServices()

        # Verify there are services to add.
        assert possible_services is not None and len(possible_services) > 0

        index = len(possible_services) - 1   # try adding and removing the last one
        service = possible_services[index]
        serviceManager.AddService(service, None, None)
        time.sleep(2) 

        # Should have at least one service to remove now.
        services = serviceManager.GetServices()
        assert len(services) > 0
        service_to_remove = services[ len(services) - 1 ]  # remove the last one (could be any)
        serviceManager.RemoveService(service_to_remove)

    def testRemoveServices(self):
        global serviceManager
        serviceManager.RemoveServices()

    def testGetServices(self):
        global serviceManager
        serviceManager.GetServices()

    # StopServices
    def testStopServices(self):
        global serviceManager
        serviceManager.StopServices()

    # The last test cleans up the suite.
    def testZEnd(self):
        global serviceManager, nodeService
        time.sleep(2)
        serviceManager.Shutdown()
        nodeService.Stop()

def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(AGServiceManagerBasicTest)
    suite2 = unittest.makeSuite(AGServiceManagerTestCase)
    return unittest.TestSuite([suite1, suite2])

if __name__ == '__main__':
    # When this module is executed from the command-line, run all its tests
    unittest.main(defaultTest='suite')

