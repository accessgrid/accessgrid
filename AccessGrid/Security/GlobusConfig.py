#-----------------------------------------------------------------------------
# Name:        GlobusConfig.py
# Purpose:     Configuration objects for Globus-ey Goop using the toolkit.
#              there are config objects for various sub-parts of the system.
# Created:     2003/05/06
# RCS-ID:      $Id: GlobusConfig.py,v 1.1 2004-12-23 18:14:35 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: GlobusConfig.py,v 1.1 2004-12-23 18:14:35 judson Exp $"

import os
import sys
import re
import struct
import time
import select
import socket
import shutil

if sys.platform == 'win32':
    try:
        from pyGlobus import utilc, gsic, ioc
        import _winreg, win32api
        from win32com.shell import shell, shellcon
        import Utilities as SecurityUtilities
        utilc.globus_module_activate(gsic.get_module())
        utilc.globus_module_activate(ioc.get_module())
        SecurityUtilities.CreateTCPAttrAlwaysAuth()
    except:
        pass
elif sys.platform == 'linux2' or sys.platform == 'darwin':
    try:
        from pyGlobus import security
    except:
        pass
    
from AccessGrid import Log
log = Log.GetLogger(Log.Toolkit)

pyGlobusSetenv = None
pyGlobusGetenv = None
pyGlobusUnsetenv = None

try:
    import pyGlobus.utilc
    pyGlobusSetenv = pyGlobus.utilc.setenv
    pyGlobusUnsetenv = pyGlobus.utilc.unsetenv
    pyGlobusGetenv = pyGlobus.utilc.getenv
except:
    pass

class GlobusConfig:
    """
    This object encapsulates the information required to correctly configure
    Globus and pyGlobus for use with the Access Grid Toolkit.

    @ivar location: the location of the globus installation
    @ivar caCertDir: the directory of Certificate Authority Certificates
    @ivar hostname: the Hostname for the globus configuration
    @ivar proxyFile: THe filename for the globus proxy
    @ivar certFile: The filename of the X509 certificate.
    @ivar keyFile: The filename of the X509 key.
    """
    theGlobusConfigInstance = None
    
    def instance(initIfNeeded=1):
        if GlobusConfig.theGlobusConfigInstance == None:
            GlobusConfig(initIfNeeded)

        return GlobusConfig.theGlobusConfigInstance

    instance = staticmethod(instance)
    
    def __init__(self, configDir, initIfNeeded=0):
        """
        This is the constructor, the only argument is used to indicate
        a desire to intialize the existing environment if it is discovered
        to be uninitialized.

        @param initIfNeeded: a flag indicating if this object should
        initialize the system if it is not.

        @type initIfNeeded: integer
        """
        if GlobusConfig.theGlobusConfigInstance is not None:
            raise Exception, "Only one instance of Globus Config is allowed."

        self.initIfNeeded = initIfNeeded

        self.userConfigDir = configDir

        self.location = None
        self.hostname = None
        self.serverFlag = None
        self.distCACertDir = None
        self.distCertFileName = None
        self.distKeyFileName = None
        self.proxyFileName = None

    def __str__(self):
        return self._repr_()

    def _repr_(self):
        tmpstr = "Globus Configuration:\n"
        tmpstr += "Location: %s\n" % self.GetLocation()
        tmpstr += "Hostname: %s\n" % self.GetHostname()
        tmpstr += "Proxy Filename: %s\n" % self.GetProxyFileName()
        
        return tmpstr
        
    def _SetHostnameToLocalIP(self):
        """
        Set the hostname to the IP address
        """
        raise Exception, "This should not be called directly, but through a subclass."

    # We define our own setenv/unsetenv to prod both the pyGlobus
    # environment and the standard python environment.
    def Setenv(self, name, val):
        global pyGlobusSetenv

        os.environ[name] = val
        
        if pyGlobusSetenv:
            pyGlobusSetenv(name, val)
            
    def Unsetenv(self, name):
        global pyGlobusUnsetenv

        if name in os.environ:
            del os.environ[name]

        if pyGlobusUnsetenv:
            pyGlobusUnsetenv(name)

    def Getenv(self, name):
        global pyGlobusGetenv

        if pyGlobusGetenv:
            return pyGlobusGetenv(name)
        else:
            return os.getenv(name)

    def SetHostname(self):
        """
        Ensure that we have a valid Globus hostname.

        If GLOBUS_HOSTNAME is set, we will do nothing further.

        Otherwise, we will inspect the hostname as returned by the
        socket.getfqdn() call. If it appears to be valid (where valid
        means that it maps to an IP address and we can locally bind to
        that address), we needn't do anythign, since the globus
        hostname calls will return the right thing.

        Otherwise, we need to get our IP address using
        SystemConfig.GetLocalIPAddress()
        """

        ghn = os.getenv("GLOBUS_HOSTNAME")
            
        if ghn is not None:
            self.hostname = ghn
            log.debug("Using GLOBUS_HOSTNAME=%s as set in the environment",
                      self.hostname)
            return
        else:
            hostname = socket.getfqdn()
            # It has to really be a fqdn.
            if hostname.find(".") < 0:
                return self._SetHostnameToLocalIP()

            # And one has to be able to bind to it.
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind((hostname, 0))
                # This worked, so we are okay.
                log.debug("System hostname of %s is valid", hostname)
                self.hostname = hostname
                self.Setenv("GLOBUS_HOSTNAME", hostname)
                return
            except socket.error:
                log.exception("Error setting globus hostname.")

            # Binding to our hostname didn't work. Retrieve our IP address
            # and use that.

            return self._SetHostnameToLocalIP()

    def GetHostname(self):
        if self.hostname is None:
            self.SetHostname()

        return self.hostname

    def RemoveHostname(self):
        self.Unsetenv("GLOBUS_HOSTNAME")
        self.hostname = None
        
    def GetLocation(self):
        if self.location is not None and not os.path.exists(self.location):
            raise Exception, "GlobusConfig: Globus directory does not exist."

        return self.location

    def SetLocation(self, location):
        self.location = location
        self.Setenv("GLOBUS_LOCATION", location)
        
    def RemoveLocation(self):

        self.location = None
        self.Unsetenv("GLOBUS_LOCATION")

    def SetActiveCACertDir(self, dir):
        self.Setenv("X509_CERT_DIR", dir)

    def SetProxyCert(self, proxyFile):
        """
        Configure globus runtime for using a proxy cert.

        """
        self.Unsetenv("X509_USER_CERT")
        self.Unsetenv("X509_USER_KEY")
        self.Unsetenv("X509_RUN_AS_SERVER")
        self.Setenv("X509_USER_PROXY", proxyFile)

    def SetUserCert(self, cert, key):
        """
        Configure globus runtime for using a cert and key pair.
        """

        self.Setenv("X509_USER_CERT", cert)
        self.Setenv("X509_USER_KEY", key)
        self.Setenv("X509_RUN_AS_SERVER", "1")
        self.Unsetenv("X509_USER_PROXY")

    def GetDistCACertDir(self):
        return self.distCACertDir
    
    def GetDistCertFileName(self):
        return self.distCertFileName

    def GetDistKeyFileName(self):
        return self.distKeyFileName
    
    def GetProxyFileName(self):
        return self.proxyFileName
        
class GlobusConfigUnix(GlobusConfig):
    """
    This object encapsulates the information required to correctly configure
    Globus and pyGlobus for use with the Access Grid Toolkit.

    @ivar location: the location of the globus installation
    @ivar caCertDir: the directory of Certificate Authority Certificates
    @ivar hostname: the Hostname for the globus configuration
    @ivar proxyFile: THe filename for the globus proxy
    @ivar certFile: The filename of the X509 certificate.
    @ivar keyFile: The filename of the X509 key.
    """
    def __init__(self, initIfNeeded):
        """
        This is the constructor, the only argument is used to indicate
        a desire to intialize the existing environment if it is discovered
        to be uninitialized.

        @param initIfNeeded: a flag indicating if this object should
        initialize the system if it is not.

        @type initIfNeeded: integer
        """
        GlobusConfig.__init__(self, initIfNeeded)

        GlobusConfig.theGlobusConfigInstance = self
        
        self._StandardConfig()

        self._EnvironmentConfig()

    def _StandardConfig(self):
        """
        This tries to setup to initial configuration from the the
        specification of what a "standard globus" configuration should
        be.
        """
        try:
            self.userConfigDir = os.path.join(os.environ['HOME'], ".globus")
        except KeyError:
            raise NameError, "HOME not defined."

        if not os.path.exists(self.userConfigDir):
            os.mkdir(self.userConfigDir)
            
        self.distKeyFileName = os.path.join(self.userConfigDir, "userkey.pem")
        self.distCertFileName = os.path.join(self.userConfigDir,
                                             "usercert.pem")
        self.proxyFileName = os.path.join(self.userConfigDir,
                                          "x509up_u%s" %(os.getuid()))
        try:
            self.location = os.environ['GLOBUS_LOCATION']
        except KeyError:
            self.location = None
            self.distCACertDir = None
            raise KeyError, "GLOBUS_LOCATION not found"

        if self.location:
            self.distCACertDir = os.path.join(self.location, "CAcertificates")

    def _EnvironmentConfig(self):
        """
        This overrides the basic configuration with envrionmental
        modifications.
        """
        if os.environ.has_key('GLOBUS_HOSTNAME'):
            self.hostname = os.environ['GLOBUS_HOSTNAME']
        else:
            if self.initIfNeeded:
                self.SetHostname()
                
        if os.environ.has_key('X509_RUN_AS_SERVER'):
            self.serverFlag = os.environ['X509_RUN_AS_SERVER']
        else:
            self.serverFlag = None

        if os.environ.has_key('X509_CERT_DIR'):
            self.distCACertDir = os.environ['X509_CERT_DIR']
                
        if os.environ.has_key('X509_USER_PROXY'):
            self.proxyFileName = os.environ['X509_USER_PROXY']
                
        if os.environ.has_key('X509_USER_CERT'):
            self.distCertFileName = os.environ['X509_USER_CERT']
                
        if os.environ.has_key('X509_USER_KEY'):
            self.distKeyFileName = os.environ['X509_USER_KEY']
    
    def _SetHostnameToLocalIP(self):
        try:
            self.hostname = SystemConfig.instance().GetLocalIPAddress()
            log.debug("retrieved local IP address %s", self.hostname)
        except:
            self.hostname = "127.0.0.1"
            
            log.exception("Failed to determine local IP address, using %s",
                          self.hostname)

        self.Setenv("GLOBUS_HOSTNAME", self.hostname)


class GlobusConfigWin32(GlobusConfig):
    """
    This object encapsulates the information required to correctly configure
    Globus and pyGlobus for use with the Access Grid Toolkit.

    HKCU\Software\Globus
    HKCU\Software\Globus\GSI
    HKCU\Software\Globus\GSI\x509_user_proxy = {userappdata}\globus\u509up_uxxx
    HKCU\Software\Globus\GSI\x509_user_key={userappdata}\globus\userkey.pem
    HKCU\Software\Globus\GSI\x509_user_cert={userappdata}\globus\usercert.pem
    HKCU\Software\Globus\GSI\x509_cert_dir={app}\config\certificates
    HKCU\Environment\GLOBUS_LOCATION = {app}

    @ivar location: the location of the globus installation

    @ivar hostname: the Hostname for the globus configuration

    @ivar distCACertDir: the directory of Certificate Authority Certificates as shipped
    with the toolkit
    @ivar distCertFileName: The filename of the X509 certificate as used by a system
    installation of Globus
    @ivar distKeyFileName: The filename of the X509 private key as used by a system
    installation of Globus

    """
    def __init__(self, initIfNeeded):
        """
        This is the constructor, the only argument is used to indicate
        a desire to intialize the existing environment if it is discovered
        to be uninitialized.

        @param initIfNeeded: a flag indicating if this object should
        initialize the system if it is not.

        @type initIfNeeded: integer
        """
        GlobusConfig.__init__(self, initIfNeeded)

        GlobusConfig.theGlobusConfigInstance = self

        self._StandardConfig()

        self._EnvironmentConfig()
        
        
    def _SetHostnameToLocalIP(self):
        try:
            self.hostname = SystemConfig.instance().GetLocalIPAddress()
            log.debug("retrieved local IP address %s", self.hostname)
        except:
            self.hostname = "127.0.0.1"
            
            log.exception("Failed to determine local IP address, using %s",
                          self.hostname)

        self.Setenv("GLOBUS_HOSTNAME", self.hostname)

    def GetGlobusKey(self):
        gkey = None

        try:
            gkey = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                                   "Software\Globus", 0, _winreg.KEY_SET_VALUE)
        except:
            log.exception("Couldn't retrieve globus key from registry.")
            # third, Create the keys
            try:
                gkey = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER,
                                         "Software\Globus")
            except:
                log.exception("Couldn't initialize the globus registry key.")
            return None

        if gkey is None:
            log.error("Can't do any more initialization, Globus looks misconfigured.")
            return None
        
        try:
            gsikey = _winreg.OpenKey(gkey, "GSI", 0, _winreg.KEY_SET_VALUE)
            return gsikey
        except:
            log.exception("Couldn't retrieve gsi key from registry.")
            # third, Create the keys
            try:
                gsikey = _winreg.CreateKey(gkey, "GSI")
                return gsikey
            except:
                log.exception("Couldn't initialize the gsi registry key.")
            return None

    def _StandardConfig(self):
        """
        """
        # First, get the paths to stuff we need
        try:
            self.userConfigDir = os.path.join(shell.SHGetFolderPath(0,
                                                       shellcon.CSIDL_APPDATA,
                                                       0, 0),
                                    "globus")
        except WindowsError:
            raise WindowsError, "Home not found."

        self.distKeyFileName = os.path.join(self.userConfigDir, "userkey.pem")
        self.distCertFileName = os.path.join(self.userConfigDir,
                                             "usercert.pem")
        self.proxyFileName = os.path.join(self.userConfigDir, "x509up_u%s"
                                                    % win32api.GetUserName())

        try:
            self.location = os.environ['GLOBUS_LOCATION']
        except KeyError:
            self.location = None
            self.distCACertDir = None
            raise KeyError, "GLOBUS_LOCATION not found"

        if self.location:
            self.distCACertDir = os.path.join(self.location, "CAcertificates")

    def _EnvironmentConfig(self):
        """
        """
        """
        right now we just want to check and see if registry settings
        are in place for the various parts.
        """
        # Zero, get keys we need
        gsikey = self.GetGlobusKey()
        
        # Check GLOBUS_HOSTNAME
        self.SetHostname()

        # Check for values out of the registry.
        # It doesn't matter if they're not there; we're going to completely
        # configure our environment later on.
        try:
            (self.distKeyFileName, val_type) = _winreg.QueryValueEx(gsikey,
                                                             "x509_user_key")
        except WindowsError:
            pass

        try:
            (self.distCertFileName, val_type) = _winreg.QueryValueEx(gsikey,
                                                                 "x509_user_cert")
        except WindowsError:
            pass

        try:
            (self.distCACertDir, val_type) = _winreg.QueryValueEx(gsikey,
                                                             "x509_cert_dir")
        except WindowsError:
            pass
        
        try:
            _winreg.CloseKey(gsikey)
        except WindowsError:
            log.exception("Error trying to close globus registry key.")
            
    def SetUserCert(self, cert, key):
        """
        Configure globus runtime for using a cert and key pair.
        """

        Config.GlobusConfig.SetUserCert(self, cert, key)

        #
        # On windows, if there's a proxy setting in the registry,
        # it trumps the run_as_server setting.
        #

        gkey = self.GetGlobusKey()
        try:
            _winreg.DeleteValue(gkey, "x509_user_proxy")
            _winreg.CloseKey(gkey)
        except WindowsError:
            pass
        
def GetConfig(initIfNeeded=0):
    import sys
    if sys.platform == 'win32':
        gc = GlobusConfigWin32(initIfNeeded)
        print "1"
        print gc
        print "2"
        return gc
    elif sys.platform == 'linux2' or sys.platform == 'darwin':
        return GlobusConfigUnix(initIfNeeded)
