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
import signal, time, os
import logging, logging.handlers
from AccessGrid.AGServiceManager import AGServiceManager
from AccessGrid.AGNodeService import AGNodeService
from AccessGrid.hosting import Server
from AccessGrid.Platform import AGTK_LOCATION 

# AGServiceManager unittests below assume a basic initialization works 
#   in their setup so we'll just confirm it works in a separate test.
class AGServiceManagerBasicTest(unittest.TestCase):
    """Basic test case for AGServiceManager."""

    def testInit(self):
        """Test initialization"""
        self.serviceManager = AGServiceManager(Server(('',0)))
        self.serviceManager.Shutdown()
        time.sleep(1)

global serviceManager
#global serviceManagerDesc
global nodeService
global server

def AuthCallback(server, g_handle, remote_user, context):
    return 1

class AGServiceManagerTestSuite(unittest.TestSuite):
    """Test suite for AGServiceManager"""

    def __init__(self, tests=()):
        unittest.TestSuite.__init__(self, tests)  # call parent's __init__

        # Startup logging
        self.logFile = ".agsm.log"
        self.debugMode = 0
        self.log = logging.getLogger("AG")
        self.log.setLevel(logging.DEBUG)
        self.hdlr = logging.handlers.RotatingFileHandler(self.logFile, "a", 10000000, 0)
        fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
        self.hdlr.setFormatter(fmt)
        self.log.addHandler(self.hdlr)
        if self.debugMode:
            self.log.addHandler(logging.StreamHandler())

        # Startup serviceManager to test
        global serviceManager
        global sm_server
        sm_port = 12000
        sm_server = Server( sm_port, auth_callback=AuthCallback)
        serviceManager = AGServiceManager(sm_server)
        sm_server.BindService(serviceManager, "ServiceManager")

        #global serviceManagerDesc
        #serviceManagerDesc = AGServiceManagerDescription("localhost:12000","https://localhost:12000/ServiceManager")

        # Start a node service to help test some of ServiceManager's
        #  functions like AddService()
        global nodeService
        ns_port = 11000
        global ns_server
        ns_server = Server( ns_port, auth_callback=AuthCallback)
        nodeService = AGNodeService()
        ns_server.BindService(nodeService, "NodeService")

class AGServiceManagerTestCase(unittest.TestCase):

    def testValidInitialization(self):
        assert None != serviceManager.authManager
        assert None != serviceManager.processManager

    # Authorization methods

    def testSetAuthorizedUsers(self):
        serviceManager.SetAuthorizedUsers(["jdoe"])
        assert "jdoe" in serviceManager.authManager.GetAuthorizedUsers()

    # Resource methods

    def testDiscoverResources(self):
        serviceManager.DiscoverResources()

    def testGetResources(self):
        serviceManager.GetResources()

    # Service methods

    def testAddService(self):
        services = nodeService.GetAvailableServices()

        # Verify there are services to add.
        assert len(services) > 0 

        # Add all services to make sure they work
        for service in services:
            if service.name != "":
                #serviceManager.AddService(nodeService.servicePackageRepository.GetPackageUrl(services[0].name + ".zip"), None, None)
                serviceManager.AddService(nodeService.servicePackageRepository.GetPackageUrl(service.name + ".zip"), None, None)

        time.sleep(2)

    def testRemoveService(self):
        # First add a service to make sure we can remove one.
        possible_services = nodeService.GetAvailableServices()

        # Verify there are services to add.
        assert len(possible_services) > 0

        index = len(possible_services) - 1   # try adding and removing the last one
        service = possible_services[index]
        serviceManager.AddService(nodeService.servicePackageRepository.GetPackageUrl(service.name + ".zip"), None, None)
        time.sleep(2) 

        # Should have at least one service to remove now.
        services = serviceManager.GetServices()
        assert len(services) > 0
        service_to_remove = services[ len(services) - 1 ]  # remove the last one (could be any)
        serviceManager.RemoveService(service_to_remove)

    def testRemoveServices(self):
       serviceManager.RemoveServices()

    def testGetServices(self):
        serviceManager.GetServices()

    # StopServices
    def testStopServices(self):
        serviceManager.StopServices()

    # The last test cleans up the suite.
    def testZEnd(self):
        time.sleep(2)
        serviceManager.Shutdown()
        nodeService.Stop()

def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(AGServiceManagerBasicTest)
    suite2 = unittest.makeSuite(AGServiceManagerTestCase, suiteClass=AGServiceManagerTestSuite)
    return unittest.TestSuite([suite1, suite2])

if __name__ == '__main__':
    # When this module is executed from the command-line, run all its tests
    unittest.main(defaultTest='suite')

