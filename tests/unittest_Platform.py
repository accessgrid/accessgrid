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
import os, sys, shutil
import os.path
import tempfile
from AccessGrid import Platform
from AccessGrid.Platform import Config
from AccessGrid.Platform.Config import UserConfig, SystemConfig, GlobusConfig, AGTkConfig, MimeConfig

class DefaultPaths(unittest.TestCase):

    def setUp(self):
        if os.environ.has_key(Platform.AGTK_LOCATION):
            del os.environ[Platform.AGTK_LOCATION]
        if os.environ.has_key(Platform.AGTK_USER):
            del os.environ[Platform.AGTK_USER]

    def testIsLinux(self):
        Platform.isLinux()

    def testIsOSX(self):
        Platform.isOSX()

    def testIWindows(self):
        Platform.isWindows()

class AGTkConfigTests(unittest.TestCase):

    def setUp(self):
        reload(Config) # reload before each test to clear global instances of configs.
        self.userdir = tempfile.mktemp()
        self.sysdir = tempfile.mktemp()
        self.foodir = os.path.join(self.sysdir, "foo")
        os.mkdir(self.userdir)
        os.mkdir(self.sysdir)
        os.mkdir(self.foodir)
        os.environ[Platform.AGTK_LOCATION] = self.sysdir
        os.environ[Platform.AGTK_USER] = self.userdir
        # initialize AGTk config.
        AGTkConfig.instance(initIfNeeded=1)

    def tearDown(self):
        os.rmdir(self.foodir)
        shutil.rmtree(self.userdir, ignore_errors=1)
        shutil.rmtree(self.sysdir, ignore_errors=1)

    def testVersion(self):
        version = AGTkConfig.instance().GetVersion()

    def testGetBaseDir(self):
        baseDir = AGTkConfig.instance().GetBaseDir()
        assert baseDir == self.sysdir , 'incorrect install dir'
        assert os.path.isdir(baseDir)

    def testGetConfigDir(self):
        configDir = AGTkConfig.instance().GetConfigDir()
        assert configDir != "" and configDir is not None, 'invalid user config dir'
        expectedDir = os.path.join(self.sysdir, "Config")
        assert configDir == expectedDir, 'AGTkConfig config dir %s != AGTkConfig...GetConfigDir() %s' % (configDir, expectedDir)
        assert os.path.isdir(configDir)

    def testGetInstallDir(self):
        instDir = AGTkConfig.instance().GetInstallDir()
        assert instDir != "" and instDir is not None, 'invalid install dir'
        assert os.path.isdir(instDir)

    def testGetBinDir(self):
        binDir = AGTkConfig.instance().GetBinDir()
        assert binDir != "" and binDir is not None, 'invalid bin dir'

    def testGetDocDir(self):
        docDir = AGTkConfig.instance().GetDocDir()
        assert docDir != "" and docDir is not None, 'invalid shared doc dir'
        assert os.path.isdir(docDir)

    def testGetLogDir(self):
        logDir = AGTkConfig.instance().GetLogDir()
        assert logDir != "" and logDir is not None, 'invalid log dir'
        assert os.path.isdir(logDir)

    def testGetSharedAppDir(self):
        appDir = AGTkConfig.instance().GetSharedAppDir()
        assert appDir != "" and appDir is not None, 'invalid app dir'
        assert os.path.isdir(appDir)

    def testGetNodeServicesDir(self):
        nsDir = AGTkConfig.instance().GetNodeServicesDir()
        assert nsDir != "" and nsDir is not None, 'invalid node services dir'
        assert os.path.isdir(nsDir)

    def testGetServicesDir(self):
        servicesDir = AGTkConfig.instance().GetServicesDir()
        assert servicesDir != "" and servicesDir is not None, 'invalid services dir'
        assert os.path.isdir(servicesDir)

class GlobusConfigTests(unittest.TestCase):

    def setUp(self):
        reload(Config) # reload before each test to clear global instances of configs.
        self.userdir = tempfile.mktemp()
        self.sysdir = tempfile.mktemp()
        self.foodir = os.path.join(self.sysdir, "foo")
        os.mkdir(self.userdir)
        os.mkdir(self.sysdir)
        os.mkdir(self.foodir)
        os.environ[Platform.AGTK_LOCATION] = self.sysdir
        os.environ[Platform.AGTK_USER] = self.userdir
        AGTkConfig.instance(initIfNeeded=1)

    def tearDown(self):
        os.rmdir(self.foodir)
        shutil.rmtree(self.userdir, ignore_errors=1)
        shutil.rmtree(self.sysdir, ignore_errors=1)

    def testInit(self):
        GlobusConfig.instance(initIfNeeded=1)

    def testInit2(self):
        GlobusConfig.instance(initIfNeeded=0)


class UserConfigTests(unittest.TestCase):

    def setUp(self):
        reload(Config) # reload before each test to clear global instances of configs.
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
        shutil.rmtree(self.userdir, ignore_errors=1)
        shutil.rmtree(self.sysdir, ignore_errors=1)

    def testGetProfile(self):
        profile = UserConfig.instance().GetProfile()
        assert profile != None

    def testGetBaseDir(self):
        baseDir = UserConfig.instance().GetBaseDir()
        assert baseDir == self.userdir , 'incorrect base dir'
        assert os.path.isdir(baseDir)

    def testGetConfigDir(self):
        configDir = UserConfig.instance().GetConfigDir()
        assert configDir != "" and configDir is not None, 'empty user config dir'
        expectedDir = os.path.join(self.userdir, "Config")
        assert configDir == expectedDir, 'AGTkConfig config dir %s != AGTkConfig...GetConfigDir() %s' % (configDir, expectedDir)

    def testGetTempDir(self):
        tempDir = UserConfig.instance().GetTempDir()
        assert tempDir != "" and tempDir is not None, 'empty temp dir'
        assert os.path.isdir(tempDir), 'temp dir does not exist'

    def testGetLogDir(self):
        logDir = UserConfig.instance().GetLogDir()
        assert logDir != "" and logDir is not None, 'invalid log dir'
        assert os.path.isdir(logDir)

    def testGetSharedAppDir(self):
        appDir = UserConfig.instance().GetSharedAppDir()
        assert appDir != "" and appDir is not None, 'empty user app dir'
        assert os.path.isdir(appDir)

    def testGetNodeServicesDir(self):
        nsDir = UserConfig.instance().GetNodeServicesDir()
        assert nsDir != "" and nsDir is not None, 'invalid node services dir'
        assert os.path.isdir(nsDir)

    def testGetServicesDir(self):
        servicesDir = UserConfig.instance().GetServicesDir()
        assert servicesDir != "" and servicesDir is not None, 'invalid services dir'
        assert os.path.isdir(servicesDir)


class SystemConfigTests(unittest.TestCase):

    def setUp(self):
        reload(Config) # reload before each test to clear global instances of configs.
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
        shutil.rmtree(self.userdir, ignore_errors=1)
        shutil.rmtree(self.sysdir, ignore_errors=1)

    def testGetTempDir(self):
        tempDir = SystemConfig.instance().GetTempDir()
        assert tempDir != "" and tempDir is not None, 'empty temp dir'
        assert os.path.isdir(tempDir), 'temp dir does not exist'

    def testGetHostname(self):
        SystemConfig.instance().GetHostname()

    def testGetProxySettings(self):
        SystemConfig.instance().GetProxySettings()

    def testFreeSpace(self):
        free = SystemConfig.instance().GetFileSystemFreeSpace("/")
        assert free > 0

    def testUsername(self):
        username = SystemConfig.instance().GetUsername()
        assert len(username) > 0

    def testGetDefaultRouteIP(self):
        SystemConfig.instance().GetDefaultRouteIP()

    def testGetResources(self):
        resources = SystemConfig.instance().GetResources()
        assert type(resources) == type([])

    def testPerformanceSnapshot(self):
        perf = SystemConfig.instance().PerformanceSnapshot()


class MimeConfigTests(unittest.TestCase):

    def setUp(self):
        reload(Config) # reload before each test to clear global instances of configs.
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
        shutil.rmtree(self.userdir, ignore_errors=1)
        shutil.rmtree(self.sysdir, ignore_errors=1)

    def testGetMimeCommands(self):
        commands = MimeConfig.instance().GetMimeCommands(mimeType=None, ext="txt")

    def testGetMimeType(self):
        commands = MimeConfig.instance().GetMimeType("txt")

class EnvPaths(unittest.TestCase):

    def setUp(self):
        reload(Config) # reload before each test to clear global instances of configs.
        self.userdir = tempfile.mktemp()
        self.sysdir = tempfile.mktemp()
        self.foodir = os.path.join(self.sysdir, "foo")
        os.mkdir(self.userdir)
        os.mkdir(self.sysdir)
        os.mkdir(self.foodir)
        os.environ[Platform.AGTK_LOCATION] = self.sysdir
        os.environ[Platform.AGTK_USER] = self.userdir
        # Create a default AGTk configuration
        AGTkConfig.instance(initIfNeeded=1)

    def tearDown(self):
        os.rmdir(self.foodir)
        shutil.rmtree(self.userdir, ignore_errors=1)
        shutil.rmtree(self.sysdir, ignore_errors=1)
    
    def testAGTkConfigConfigDir(self):
        #print "BASEDIR:", AGTkConfig.instance().installBase, self.userdir, self.sysdir
        configDir = AGTkConfig.instance().GetConfigDir()
        #print "AGTk config dir (using temp name): ", configDir
        assert configDir != "" and configDir is not None, 'empty config dir'
        expectedDir = os.path.join(self.sysdir, "Config")
        assert configDir == expectedDir, 'AGTkConfig config dir %s != AGTkConfig...GetConfigDir() %s' % (configDir, expectedDir)
    
    def testUserConfigDir(self):
        configDir = UserConfig.instance().GetConfigDir()
        #print "User config dir (using temp name): ", configDir
        assert configDir != "" and configDir is not None, 'empty config dir'
        expectedDir = os.path.join(self.userdir, "Config")
        assert configDir == expectedDir, 'User config dir %s != UserConfig...GetConfigDir() %s' % (configDir, expectedDir)

def suite():
    """Returns a suite containing all the test cases in this module."""

    suites = []
    for testClass in [DefaultPaths, Environ]:
        suites.append(unittest.makeSuite(testClass))

    return unittest.TestSuite(suites)

if __name__ == '__main__':
    # When this module is executed from the command-line, run all its tests
    unittest.main()

