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

import unittest
import signal, time, os
from AccessGrid.AGServiceManager import AGServiceManager
from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.Platform import GetConfigFilePath, AGTK_LOCATION 
from AccessGrid.Platform import *

class AGServiceManagerBasicTestCase(unittest.TestCase):
    """Basic test case for AGServiceManager."""

    def testInit(self):
        """Test initialization"""
        # For testing we'll change to a local test config path.
        os.environ[AGTK_LOCATION] = "testInstall"
        self.serviceManager = AGServiceManager(Server(0))
        self.serviceManager.Shutdown()
        del self.serviceManager

class AGServiceManagerBasicCase(unittest.TestCase):

    def setUp(self):
        """Test initialization"""
        # For testing we'll change to a local test config path.
        os.environ[AGTK_LOCATION] = "testInstall"
        self.serviceManager = AGServiceManager(Server(0))

    def testValidInitialization(self):
        assert None != self.serviceManager.authManager
        assert None != self.serviceManager.processManager

  # def testOtherTestsHere

    def tearDown(self):
        self.serviceManager.Shutdown()
        del self.serviceManager


def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(AGServiceManagerBasicTestCase)
    suite2 = unittest.makeSuite(AGServiceManagerTestCase)
    return unittest.TestSuite((suite1, suite2))

if __name__ == '__main__':
    # When this module is executed from the command-line, run all its tests
    unittest.main()

