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
import os, sys
import os.path
import tempfile
from AccessGrid import Platform

class DefaultPaths(unittest.TestCase):

    def setUp(self):
        if os.environ.has_key(Platform.AGTK_LOCATION):
            del os.environ[Platform.AGTK_LOCATION]
        if os.environ.has_key(Platform.AGTK_USER):
            del os.environ[Platform.AGTK_USER]

    def testIsOSX(self):
        Platform.isOSX()
    
    def testSystem(self):
        configDir = Platform.GetSystemConfigDir()
        print "System config dir: ", configDir
        assert configDir != "" and configDir is not None, 'empty system config dir'
    
    def testUser(self):
        configDir = Platform.GetUserConfigDir()
        print "User config dir: ", configDir
        assert configDir != "" and configDir is not None, 'empty user config dir'

    def testUserAppPath(self):
        appDir = Platform.GetUserAppPath()
        print "User app dir: ", appDir
        assert appDir != "" and appDir is not None, 'empty user app path'

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

    def testSharedDocDir(self):
        docDir = Platform.GetSharedDocDir()
        print "shared doc dir: ", docDir
        assert docDir != "" and docDir is not None, 'empty shared doc dir'

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

    def testGetMimeCommands(self):
        if sys.platform == Platform.WIN:
            commands = Platform.Win32GetMimeCommands(mimeType=None, ext="txt")
        else:
            commands = Platform.LinuxGetMimeCommands(mimeType=None, ext="txt")

    def testGetMimeType(self):
        if sys.platform == Platform.WIN:
            commands = Platform.Win32GetMimeType("txt")
        else:
            commands = Platform.LinuxGetMimeType("txt")

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
        print "System config dir (using temp name): ", configDir
        assert configDir != "" and configDir is not None, 'empty config dir'
        assert configDir == self.sysdir
    
    def testUser(self):
        configDir = Platform.GetUserConfigDir()
        print "User config dir (using temp name): ", configDir
        assert configDir != "" and configDir is not None, 'empty config dir'
        assert configDir == self.userdir

    def testConfigFile(self):
        #
        # Test for a config directory that's probably not there
        #
        configDir = Platform.GetConfigFilePath("foo")
        print "Got foo dir (using temp name): ", configDir
        assert configDir == self.foodir

def suite():
    """Returns a suite containing all the test cases in this module."""

    suites = []
    for testClass in [DefaultPaths, Environ]:
        suites.append(unittest.makeSuite(testClass))

    return unittest.TestSuite(suites)

if __name__ == '__main__':
    # When this module is executed from the command-line, run all its tests
    unittest.main()

