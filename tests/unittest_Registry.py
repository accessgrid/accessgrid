#-----------------------------------------------------------------------------
# Name:        unittest_VenueServer.py
# Purpose:     
#
# Author:      Eric C. Olson
#   
# Created:     2005/12/20
# RCS-ID:    
# Copyright:   (c) 2005,2006
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
Unittest for Registry

"""
import sys
import logging, logging.handlers
import unittest
import threading
import time

class RegistryTestCase(unittest.TestCase):
    """A test case for the Registry."""

    # Called before each testCase
    def setUp(self):
        self._startRegistry()

    # Called after each testCase
    def tearDown(self):
        self._stopRegistry()

    def _startRegistry(self):
        from AccessGrid.Registry.RegistryPeer import RegistryPeer
        port = 8030
        peerListUrl = "file://localhost_registry_nodes.txt"
        global gRegistryPeer
        gRegistryPeer = RegistryPeer(peerListUrl=peerListUrl, port=port)
        threading.Thread(target=gRegistryPeer.Run).start()

    def _stopRegistry(self):
        global gRegistryPeer
        gRegistryPeer.Stop()
        time.sleep(2) # assumes AGXMLRPC timeout interval is 1 second

    def testStartRegistry(self):
        pass # tested during setup and teardown functions

    def _bridgeDescriptionsMatch(self, bridge1, bridge2):
        keys = set(bridge1.__dict__.keys() + bridge2.__dict__.keys())
        for key in keys:
            if not (bridge1.__dict__[key] == bridge2.__dict__[key]):
                return False
        return True

    def testRegisterAndLookupBridges(self):
        from AccessGrid.Registry.RegistryClient import RegistryClient
        from AccessGrid.Descriptions import BridgeDescription, QUICKBRIDGE_TYPE, UMTP_TYPE
        from AccessGrid.GUID import GUID
        peerListUrl = "file://localhost_registry_nodes.txt"
        rc = RegistryClient(url=peerListUrl)

        guid1 = GUID()
        name1 = "name1"
        host1 = "host1"
        listenPort1 = 20001
        serverType1 = QUICKBRIDGE_TYPE
        desc1 = "description1"
        bridgeDesc1 = BridgeDescription(guid=guid1, name=name1, host=host1, port=listenPort1, serverType=serverType1, description=desc1)
        validSecs1 = rc.RegisterBridge(bridgeDesc1)

        guid2 = GUID()
        name2 = "name2"
        host2 = "host2"
        listenPort2 = 20002
        serverType2 = UMTP_TYPE
        desc2 = "description2"
        bridgeDesc2 = BridgeDescription(guid=guid2, name=name2, host=host2, port=listenPort2, serverType=serverType2, description=desc2)
        validSecs2 = rc.RegisterBridge(bridgeDesc2)

        results = rc.LookupBridge(5)
        found1 = False
        found2 = False
        for result in results:
            if self._bridgeDescriptionsMatch(result, bridgeDesc1):
                found1 = True
            if self._bridgeDescriptionsMatch(result, bridgeDesc2):
                found2 = True
        assert found1
        assert found2
         

    # def testRegistryPeer(self):


def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(RegistryTestCase)
    return unittest.TestSuite( [suite1] )

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

