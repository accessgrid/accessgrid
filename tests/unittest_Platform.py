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
import os
import os.path
import tempfile
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

class EnvPaths(unittest.TestCase):

    def setUp(self):
        self.userdir = tempfile.mktemp()
        self.sysdir = tempfile.mktemp()
        self.foodir = os.path.join(self.sysdir, "foo")
        os.mkdir(self.userdir)
        os.mkdir(self.sysdir)
        os.mkdir(self.foodir)
        os.environ[Platform.AGTK_LOCATION] = self.sysdir
        os.environ[Platform.AGTK_USER] = self.userdir

    def tearDown(self):
        os.rmdir(self.foodir)
        os.rmdir(self.userdir)
        os.rmdir(self.sysdir)
    
    def testSystem(self):
        configDir = Platform.GetSystemConfigDir()
        print "System config dir: ", configDir
        assert configDir != "" and configDir is not None, 'empty config dir'
        assert configDir == self.sysdir
    
    def testUser(self):
        configDir = Platform.GetUserConfigDir()
        print "User config dir: ", configDir
        assert configDir != "" and configDir is not None, 'empty config dir'
        assert configDir == self.userdir

    def testConfigFile(self):
        #
        # Test for a config directory that's probably not there
        #
        configDir = Platform.GetConfigFilePath("foo")
        print "Got foo dir ", configDir
        assert configDir == self.foodir

class GPI(unittest.TestCase):
    def testGPI(self):
        Platform.GPI()

def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(DefaultPaths)
    suite2 = unittest.makeSuite(EnvPaths)
    suite3 = unittest.makeSuite(GPI)
    return unittest.TestSuite((suite1, suite2, suite3))

if __name__ == '__main__':
    # When this module is executed from the command-line, run all its tests
    unittest.main()

