#-----------------------------------------------------------------------------
# Name:        unittest_Platform.py
# Purpose:     
#
# Author:      Robert Olson
#   
# Created:     2003/04/03
# RCS-ID:    
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import unittest
import signal, time, os
from AccessGrid import Platform

class DefaultPaths(unittest.TestCase):

    def setUp(self):
        pass
    
    def testSystem(self):
        configDir = Platform.GetSystemConfigDir()
        print "System config dir: ", configDir
        assert configDir != "" and configDir is not None, 'empty config dir'
    
    def testUser(self):
        configDir = Platform.GetUserConfigDir()
        print "User config dir: ", configDir
        assert configDir != "" and configDir is not None, 'empty config dir'

    def testConfigFile(self):
        #
        # Test for a config directory that's probably not there
        #
        configDir = Platform.GetConfigFilePath("foo")
        print "Got foo dir ", configDir
        assert configDir is None

    def testInstallDir(self):
        instDir = Platform.GetInstallDir()
        print "Install dir: ", instDir
        assert instDir != "" and instDir is not None, 'empty install dir'

    def testTempDir(self):
        tempDir = Platform.GetTempDir()
        print "Temp dir: ", tempDir
        assert tempDir != "" and tempDir is not None, 'empty temp dir'
        assert os.path.isdir(tempDir), 'temp dir does not exist'

    def testSystemTempDir(self):
        tempDir = Platform.GetSystemTempDir()
        print "System Temp dir: ", tempDir
        assert tempDir != "" and tempDir is not None, 'empty temp dir'
        assert os.path.isdir(tempDir), 'temp dir does not exist'

    def testUsername(self):
        user = Platform.GetUsername()
        print "Username: ", user
        assert type(user) == type(""), 'username not a string'
        assert user != "", 'username empty'

    def testFreeSpace(self):
        free = Platform.GetFilesystemFreeSpace("/")
        print "Free space: ", free

def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(DefaultPaths)
    return unittest.TestSuite((suite1,))

if __name__ == '__main__':
    # When this module is executed from the command-line, run all its tests
    unittest.main()

