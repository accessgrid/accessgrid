#-----------------------------------------------------------------------------
# Name:        Config.py
# Purpose:     Configuration objects for applications using the toolkit.
#              there are config objects for various sub-parts of the system.
# Created:     2003/05/06
# RCS-ID:      $Id: Config.py,v 1.12 2004-04-09 14:05:26 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Config.py,v 1.12 2004-04-09 14:05:26 judson Exp $"

import os
import sys
import socket
import re

from pyGlobus import utilc

import AccessGrid.Config
from AccessGrid import Log
from AccessGrid.Platform import AGTK_USER, AGTK_LOCATION
from AccessGrid.Version import GetVersion

log = Log.GetLogger(Log.Toolkit)

# To speed things up on windows
from pyGlobus import utilc, gsic, ioc
from AccessGrid.Security import Utilities as SecurityUtilities
utilc.globus_module_activate(gsic.get_module())
utilc.globus_module_activate(ioc.get_module())
SecurityUtilities.CreateTCPAttrAlwaysAuth()

# Windows Defaults
try:
    import _winreg
    import win32api
    from win32com.shell import shell, shellcon
except:
    log.exception("Python windows extensions are missing, but required!")
    pass

class AGTkConfig(AccessGrid.Config.AGTkConfig):
    """
    This class encapsulates a system configuration for the Access Grid
    Toolkit. This object provides primarily read-only access to configuration
    data that is created when the toolkit is installed.

    @ivar version: The version of this installation.
    @ivar installDir: The directory this toolkit is installed in.
    @ivar docDir: The directory for documentation for the toolkit.
    @ivar appDir: The directory for system installed shared applications
    @ivar nodeServicesDir: the directory for system installed node services
    @ivar servicesDir: the directory for system installed services
    @ivar pkgCacheDir: The directory of shared application and node
    service packages for all users of this installation.
    @ivar configDir: The directory for installation configuration.

    @type appDir: string
    @type nodeServicesDir: string
    @type servicesDir: string
    @type configDir: string
    @type pkgCacheDir: string
    @type version: string
    @type installDir: string
    @type docDir: string
    """
    theAGTkConfigInstance = None
    AGTkRegBaseKey = "SOFTWARE\Access Grid Toolkit\%s" % GetVersion()

    def instance(initIfNeeded=0):
        if AGTkConfig.theAGTkConfigInstance == None:
            AGTkConfig(initIfNeeded)

        return AGTkConfig.theAGTkConfigInstance

    instance = staticmethod(instance)
    
    def __init__(self, initIfNeeded):

        if AGTkConfig.theAGTkConfigInstance is not None:
            raise Exception, "Only one instance of AGTkConfig is allowed."

        # Create the singleton
        AGTkConfig.theAGTkConfigInstance = self

        # Set the flag to initialize if needed
        self.initIfNeeded = initIfNeeded
        
        # Initialize state
        self.version = GetVersion()
        self.installBase = None
        self.installDir = None
        self.configDir = None
        
        self.pkgCacheDir = None
        self.servicesDir = None
        self.nodeServicesDir = None
        self.appDir = None
        self.docDir = None
        
        # Now fill in data
        self._Initialize()
        
    def _Initialize(self):
        self.GetConfigDir()
        self.GetInstallDir()
        self.GetDocDir()
        self.GetPkgCacheDir()
        self.GetSharedAppDir()
        self.GetNodeServicesDir()
        self.GetServicesDir()
        
    def GetVersion(self):
        return self.version

    def _GetInstallBase(self):
        global AGTK_LOCATION
        
        if self.installBase == None:
            try:
                self.installBase = os.environ[AGTK_LOCATION]
            except:
                try:
                    AGTK = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                                           self.AGTkRegBaseKey)
                    self.installBase, valuetype = _winreg.QueryValueEx(AGTK,
                                                                 "InstallPath")
                except:
                    raise Exception, "AGTk installation corrupt: Cannot find installation base."

        # remove trailing "\bin" if it's there
        if self.installBase.endswith("bin"):
            self.installBase = os.path.join(os.path.split(self.installBase)[:-1])[0]
            
        # Check the installation
        if not os.path.exists(self.installBase):
            raise Exception, "AGTkConfig: installation base does not exist."
        
        return self.installBase
        
    def GetConfigDir(self):
        if self.installBase == None:
            self._GetInstallBase()

        self.configDir = os.path.join(self.installBase, "config")

        if self.configDir is not None and not os.path.exists(self.configDir):
            raise Exception, "AGTkConfig: config dir does not exist."

        return self.configDir

    GetInstallDir = _GetInstallBase
    
    def GetBinDir(self):
        if self.installBase == None:
            self._GetInstallBase()

        self.installDir = os.path.join(self.installBase, "bin")

        # Check the installation
        if self.installDir is not None and not os.path.exists(self.installDir):
            raise Exception, "AGTkConfig: install dir does not exist."

        return self.installDir

    def GetDocDir(self):
        if self.installBase == None:
            self._GetInstallBase()

        self.docDir = os.path.join(self.installBase, "doc")

        # Check the installation
        if self.docDir is not None and not os.path.exists(self.docDir):
            raise Exception, "AGTkConfig: doc dir does not exist."

        return self.docDir

    def GetPkgCacheDir(self):
        if self.pkgCacheDir == None:
            ucd = self.GetConfigDir()
            self.pkgCacheDir = os.path.join(ucd, "PackageCache")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if self.pkgCacheDir is not None and \
                   not os.path.exists(self.pkgCacheDir):
                os.mkdir(self.pkgCacheDir)

        # Check the installation
        if self.pkgCacheDir is not None and \
               not os.path.exists(self.pkgCacheDir):
            raise Exception, "AGTkConfig: pkg cache dir does not exist."            
        return self.pkgCacheDir

    def GetSharedAppDir(self):
        if self.appDir == None:
            ucd = self.GetConfigDir()
            self.appDir = os.path.join(ucd, "SharedApplications")

        # Check dir and create it if needed.
        if self.initIfNeeded:
            if self.appDir is not None and not os.path.exists(self.appDir):
                os.mkdir(self.appDir)

        # Check the installation
        if self.appDir is not None and not os.path.exists(self.appDir):
            raise Exception, "AGTkConfig: app dir does not exist."

        return self.appDir

    def GetNodeServicesDir(self):
        if self.nodeServicesDir == None:
            ucd = self.GetConfigDir()
            self.nodeServicesDir = os.path.join(ucd, "NodeServices")

        # Check dir and create it if needed.
        if self.initIfNeeded:
            if self.nodeServicesDir is not None and not os.path.exists(self.nodeServicesDir):
                os.mkdir(self.nodeServicesDir)

        # Check the installation
        if self.nodeServicesDir is not None and not os.path.exists(self.nodeServicesDir):
            raise Exception, "AGTkConfig: node service dir does not exist."

        return self.nodeServicesDir

    def GetServicesDir(self):
        if self.servicesDir == None:
            ucd = self.GetConfigDir()
            self.servicesDir = os.path.join(ucd, "Services")

        # Check dir and create it if needed.
        if self.initIfNeeded:
            if self.servicesDir is not None and not os.path.exists(self.servicesDir):
                os.mkdir(self.servicesDir)

        # Check the installation
        if self.servicesDir is not None and not os.path.exists(self.servicesDir):
            raise Exception, "AGTkConfig: services dir does not exist."

        return self.servicesDir

class GlobusConfig(AccessGrid.Config.GlobusConfig):
    """
    This object encapsulates the information required to correctly configure
    Globus and pyGlobus for use with the Access Grid Toolkit.

    HKCU\Software\Globus
    HKCU\Software\Globus\GSI
    HKCU\Software\Globus\GSI\x509_user_proxy = {%TEMP%|{win}\temp}\proxy
    HKCU\Software\Globus\GSI\x509_user_key =
                                        {userappdata}\globus\userkey.pem
    HKCU\Software\Globus\GSI\x509_user_cert =
                                       {userappdata}\globus\usercert.pem
    HKCU\Software\Globus\GSI\x509_cert_dir =
                                 {app}\config\certificates
    HKCU\Environment\GLOBUS_LOCATION = {app}

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
    
    def __init__(self, initIfNeeded):
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

        GlobusConfig.theGlobusConfigInstance = self

        self.initIfNeeded = initIfNeeded
        self.location = None
        self.proxyFileName = None
        self.caCertDir = None
        self.certFileName = None
        self.keyFileName = None
        self.hostname = None

        self._Initialize()
        
#     def _Initialize(self):
#         """
#         This does globus environment initialization.
#         """
#         self._InitializeRegistry()

#         self._InitializeHostname()

#     def _InitializeHostname(self):
#         """
#         Ensure that we have a valid Globus hostname.

#         If GLOBUS_HOSTNAME is set, we will do nothing further.

#         Otherwise, we will inspect the hostname as returned by the
#         socket.getfqdn() call. If it appears to be valid (where valid
#         means that it maps to an IP address and we can locally bind to
#         that address), we needn't do anythign, since the globus
#         hostname calls will return the right thing.

#         Otherwise, we need to get our IP address using
#         SystemConfig.GetLocalIPAddress()
#         """
#         self.hostname = os.getenv("GLOBUS_HOSTNAME")
#         if self.hostname is not None:
#             log.debug("Using GLOBUS_HOSTNAME=%s as set in the environment",
#                       self.hostname)
#             return

#         hostname = socket.getfqdn()

#         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         try:
#             sock.bind((hostname, 0))

#             #
#             # This worked, so we are okay.
#             #

#             log.debug("System hostname of %s is valid", hostname) 
#             return
        
#         except socket.error:
#             pass

#         #
#         # Binding to our hostname didn't work. Retrieve our IP address
#         # and use that.
#         #

#         try:
#             myip = SystemConfig.instance().GetLocalIPAddress()
#             log.debug("retrieved local IP address %s", myip)
#         except:
#             myip = "127.0.0.1"
#             log.exception("Failed to determine local IP address, using %s",
#                           myip)

#         import AccessGrid.Utilities
#         AccessGrid.Utilities.setenv("GLOBUS_HOSTNAME", myip)

    def _GetGlobusKey(self):
        try:
            gkey = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                                   "Software\Globus")
            gsikey = _winreg.OpenKey(gkey, "GSI")
            return gsikey
        except:
            log.exception("Couldn't retrieve globus key from registry.")
            # third, Create the keys
            try:
                gkey = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER,
                                         "Software\Globus")
                gsikey = _winreg.CreateKey(gkey, "GSI")
                return gsikey
            except:
                log.exception("Couldn't initialize the globus registry keys.")
            return None

#    def _InitializeRegistry(self):
    def _Initialize(self):
        """
        right now we just want to check and see if registry settings
        are in place for the various parts.
        """
        # First, get the paths to stuff we need
        uappdata = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
        agtkdata = AGTkConfig.instance().GetConfigDir()
        gloc = AGTkConfig.instance().GetInstallDir()
        
        # second, create the values
        self.keyFileName = os.path.join(uappdata, "globus", "userkey.pem")
        self.certFileName = os.path.join(uappdata, "globus", "usercert.pem")
        self.proxyFileName = os.path.join(win32api.GetTempPath(), "proxy")
        self.caCertDir = os.path.join(agtkdata, "config", "CAcertificates")
        
        # Third try to setup GLOBUS_LOCATION, if it's not already set
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Environment")
            (self.location, type) = _winreg.QueryValueEx(key,
                                                         "GLOBUS_LOCATION")
        except WindowsError:
            if self.initIfNeeded:
                log.info("GLOBUS_LOCATION not set, setting...")
                # Set Globus Location
                self.SetLocation(loc)

        # Check GLOBUS_HOSTNAME
        self.SetHostname()
        
        # After globus location comes the all important x509_*

        try:
            (self.keyFileName, type) = _winreg.QueryValueEx(gsikey,
                                                             "x509_user_key")
        except WindowsError:
            if self.initIfNeeded:
                log.info("Globus user key registry entry not initialized.")
                self.SetKeyFileName(self.keyFileName)

        try:
            (self.certFileName, type) = _winreg.QueryValueEx(gsikey,
                                                             "x509_user_cert")
        except WindowsError:
            if self.initIfNeeded:
                log.info("Globus user cert registry entry not initialized.")
                self.SetCertFileName(self.certFileName)

        try:
            (self.caCertDir, type) = _winreg.QueryValueEx(gsikey,
                                                             "x509_cert_dir")
        except WindowsError:
            if self.initIfNeeded:
                log.info("Globus proxy registry entry not initialized.")
                self.SetCACertDir(cacertdir)

    def SetHostname(self, hn=None):
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
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Environment")
            (self.hostname, type) = _winreg.QueryValueEx(key,
                                                         "GLOBUS_HOSTNAME")
        except WindowsError:
            log.info("GLOBUS_HOSTNAME not set, setting...")

        if self.hostname is not None and hn == self.hostname:
            log.debug("Using GLOBUS_HOSTNAME=%s as set in the environment",
                      self.hostname)
            return

        elif hn is not None:
            self.hostname = hn
        else:
            hostname = socket.getfqdn()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind((hostname, 0))
                # This worked, so we are okay.
                log.debug("System hostname of %s is valid", hostname) 
                return
            except socket.error:
                log.exception("Error setting globus hostname.")

            # Binding to our hostname didn't work. Retrieve our IP address
            # and use that.
            try:
                self.hostname = SystemConfig.instance().GetLocalIPAddress()
                log.debug("retrieved local IP address %s", myip)
            except:
                self.hostname = "127.0.0.1"
                log.exception("Failed to determine local IP address, using %s",
                              self.hostname)

        # Do the actual setting
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Environment", 0,
                                  _winreg.KEY_ALL_ACCESS)
            _winreg.SetValueEx(key, "GLOBUS_HOSTNAME", 0,
                               _winreg.REG_EXPAND_SZ, self.hostname)
        except WindowsError:
            log.exception("Couldn't setup GLOBUS_LOCATION.")
            return 0

        # This propogates the change to all running apps
        self.SendSettingChange()
        
    def GetHostname(self):
        if self.hostname is None:
            self.SetHostname()

        return self.hostname
    
    def GetLocation(self):
        if self.location is not None and not os.path.exists(self.location):
            raise Exception, "GlobusConfig: Globus directory does not exist."

        return self.location

    def SetLocation(self, location):
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Environment", 0,
                                  _winreg.KEY_ALL_ACCESS)
            _winreg.SetValueEx(key, "GLOBUS_LOCATION", 0,
                               _winreg.REG_EXPAND_SZ, location)
            self.location = location
            return 1
        except WindowsError:
            log.exception("Couldn't setup GLOBUS_LOCATION.")
            return 0

        # This propogates the change to all running apps
        self.SendSettingChange()
        

    def GetCACertDir(self):
        if self.caCertDir is not None and not os.path.exists(self.caCertDir):
            raise Exception, "GlobusConfig: CA Certificate dir does not exist."

        return self.caCertDir
    
    def SetCACertDir(self, cacertdir):
        gkey = self._GetGlobusKey()
        try:
            _winreg.SetValueEx(gsikey, "x509_cert_dir", 0,
                               _winreg.REG_EXPAND_SZ, cacertdir)
            self.caCertDir = cacertdir
        except:
            log.exception("Couldn't set the x509_cert_dir registry value.")
            self.caCertDir = None

        # This propogates the change to all running apps
        self.SendSettingChange()
            
    def GetProxyFileName(self):
        if self.proxyFileName is not None and \
               not os.path.exists(self.proxyFileName):
            raise Exception, "GlobusConfig: proxy file does not exist."

        return self.proxyFileName
    
    def SetProxyFilename(self, filename):
        gkey = self._GetGlobusKey()
        try:
            _winreg.SetValueEx(gsikey, "x509_user_proxy", 0,
                               _winreg.REG_EXPAND_SZ, filename)
            self.proxyFileName = filename
        except:
            log.exception("Couldn't set the x509_user_proxy registry value.")
            self.proxyFileName = None

        # This propogates the change to all running apps
        self.SendSettingChange()
            
    def GetCertFileName(self):
        if self.certFileName is not None and \
               not os.path.exists(self.certFileName):
            raise Exception, "GlobusConfig: certificate file does not exist."

        return self.certFileName

    def SetCertFileName(self, filename):
        gkey = self._GetGlobusKey()
        try:
            _winreg.SetValueEx(gsikey, "x509_user_cert", 0,
                               _winreg.REG_EXPAND_SZ, filename)
            self.certFileName = filename
        except:
            log.exception("Couldn't set the x509_user_cert registry value.")
            self.certFileName = None

        # This propogates the change to all running apps
        self.SendSettingChange()
            
    def GetKeyFileName(self):
        if self.keyFileName is not None and \
               not os.path.exists(self.keyFileName):
            raise Exception, "GlobusConfig: key file does not exist."

        return self.keyFileName

    def SetKeyFileName(self, filename):
        gkey = self._GetGlobusKey()
        try:
            _winreg.SetValueEx(gsikey, "x509_user_key", 0,
                               _winreg.REG_EXPAND_SZ, filename)
            self.keyFileName = filename
        except:
            log.exception("Couldn't set the x509_user_key registry value.")
            self.keyFileName = None

        # This propogates the change to all running apps
        self.SendSettingChange()
            
class UserConfig(AccessGrid.Config.UserConfig):
    """
    A user config object encapsulates all of the configuration data for
    a running instance of the Access Grid Toolkit software.

    @ivar profile: the user profile
    @ivar tempDir: a temporary directory for files for this user
    @ivar appDir: The directory for system installed shared applications
    @ivar nodeServicesDir: the directory for system installed node services
    @ivar servicesDir: the directory for system installed services
    @ivar pkgCacheDir: The directory of shared application and node
    service packages for all users of this installation.
    @ivar configDir: The directory for installation configuration.

    @type profileFile: the filename of the client profile
    @type tempDir: string
    @type appDir: string
    @type nodeServicesDir: string
    @type servicesDir: string
    @type configDir: string
    @type pkgCacheDir: string
    """
    theUserConfigInstance = None

    def instance(initIfNeeded=1):
        if UserConfig.theUserConfigInstance == None:
            UserConfig(initIfNeeded)

        return UserConfig.theUserConfigInstance

    instance = staticmethod(instance)
    
    def __init__(self, initIfNeeded):

        if UserConfig.theUserConfigInstance is not None:
            raise Exception, "Only one instance of User Config is allowed."

        UserConfig.theUserConfigInstance = self

        self.initIfNeeded = initIfNeeded
        
        self.configDir = None
        self.tempDir = None
        self.appDir = None
        self.pkgCacheDir = None
        self.sharedAppDir = None
        self.nodeServiceDir = None
        self.servicesDir = None
        self.profileFilename = None

        self._Initialize()
        
    def _Initialize(self):
        self.GetConfigDir()
        self.GetTempDir()
        self.GetProfile()
        self.SetRTPDefaults()

        # These are new and so can fail
        try:
            self.GetPkgCacheDir()
        except:
            log.warn("No Package Cache!")
            
        try:
            self.GetSharedAppDir()
        except:
            log.warn("No Shared App Dir!")
        try:
            self.GetNodeServicesDir()
        except:
            log.warn("No Node Services Dir!")
        try:
            self.GetServicesDir()
        except:
            log.warn("No Services Dir!")

    def GetProfile(self):
        if self.profileFilename == None:
            self.profileFilename = os.path.join(self.GetConfigDir(), "profile")
            
        return self.profileFilename

    def SetRTPDefaults(self):
        """
        Set registry values used by vic and rat for identification
        """
        if self.profileFilename == None:
            raise Exception, "Can't set RTP Defaults without a valid profile."
        pass
#         #
#         # Set RTP defaults according to the profile
#         #
#         k = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
#                             r"Software\Mbone Applications\common",
#                             0,
#                             _winreg.KEY_SET_VALUE)

#         # Vic reads these values (with '*')
#         _winreg.SetValueEx(k, "*rtpName", 0,
#                            _winreg.REG_SZ, self.profile.name)
#         _winreg.SetValueEx(k, "*rtpEmail", 0,
#                            _winreg.REG_SZ, self.profile.email)
#         _winreg.SetValueEx(k, "*rtpPhone", 0,
#                            _winreg.REG_SZ, self.profile.phoneNumber)
#         _winreg.SetValueEx(k, "*rtpLoc", 0,
#                            _winreg.REG_SZ, self.profile.location)
#         _winreg.SetValueEx(k, "*rtpNote", 0,
#                            _winreg.REG_SZ, str(self.profile.publicId) )

#         # Rat reads these (without '*')
#         _winreg.SetValueEx(k, "rtpName", 0,
#                            _winreg.REG_SZ, self.profile.name)
#         _winreg.SetValueEx(k, "rtpEmail", 0,
#                            _winreg.REG_SZ, self.profile.email)
#         _winreg.SetValueEx(k, "rtpPhone", 0,
#                            _winreg.REG_SZ, self.profile.phoneNumber)
#         _winreg.SetValueEx(k, "rtpLoc", 0,
#                            _winreg.REG_SZ, self.profile.location)
#         _winreg.SetValueEx(k, "rtpNote", 0,
#                            _winreg.REG_SZ, str(self.profile.publicId) )

#         _winreg.CloseKey(k)

    def GetConfigDir(self):
        global AGTK_USER

        try:
            self.configDir = os.environ[AGTK_USER]
        except:
            try:
                base = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
                self.configDir = os.path.join(base, "AccessGrid")
            except:
                # check to make it if needed
                self.configDir = ""
                
        return self.configDir

    def GetTempDir(self):
        if self.tempDir == None:
            self.tempDir = win32api.GetTempPath()

        if not os.access(self.tempDir, os.W_OK):
            log.error("UserConfig configuration: TempDir %s is not writable", self.tempDir)

        return self.tempDir
    
    def GetPkgCacheDir(self):
        if self.pkgCacheDir == None:
            ucd = self.GetConfigDir()
            self.pkgCacheDir = os.path.join(ucd, "PackageCache")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if self.pkgCacheDir is not None and not os.path.exists(self.pkgCacheDir):
                os.mkdir(self.pkgCacheDir)

        # Check the installation
        if self.pkgCacheDir is not None and not os.path.exists(self.pkgCacheDir):
            raise Exception, "AGTkConfig: pkg cache dir does not exist."            
        return self.pkgCacheDir

    def GetSharedAppDir(self):
        if self.appDir == None:
            ucd = self.GetConfigDir()
            self.appDir = os.path.join(ucd, "SharedApplications")

        # Check dir and create it if needed.
        if self.initIfNeeded:
            if self.appDir is not None and not os.path.exists(self.appDir):
                os.mkdir(self.appDir)

        # Check the installation
        if self.appDir is not None and not os.path.exists(self.appDir):
            raise Exception, "AGTkConfig: app dir does not exist."

        return self.appDir

    def GetNodeServicesDir(self):
        if self.nodeServicesDir == None:
            ucd = self.GetConfigDir()
            self.nodeServicesDir = os.path.join(ucd, "NodeServices")

        # Check dir and create it if needed.
        if self.initIfNeeded:
            if self.nodeServicesDir is not None and not os.path.exists(self.nodeServicesDir):
                os.mkdir(self.nodeServicesDir)

        # Check the installation
        if self.nodeServicesDir is not None and not os.path.exists(self.nodeServicesDir):
            raise Exception, "AGTkConfig: node service dir does not exist."

        # check to make it if needed
        return self.nodeServicesDir

    def GetServicesDir(self):
        if self.servicesDir == None:
            ucd = self.GetConfigDir()
            self.servicesDir = os.path.join(ucd, "Services")

        # Check dir and create it if needed.
        if self.initIfNeeded:
            if self.servicesDir is not None and not os.path.exists(self.servicesDir):
                os.mkdir(self.servicesDir)

        # Check the installation
        if self.servicesDir is not None and not os.path.exists(self.servicesDir):
            raise Exception, "AGTkConfig: services dir does not exist."

        return self.servicesDir

class SystemConfig(AccessGrid.Config.SystemConfig):
    """
    The SystemConfig object encapsulates all system dependent
    configuration data, it should be extended to retrieve and store
    additional information as necessary.

    @var tempDir: the system temp directory.
    @type tempDir: string
    """
    theSystemConfigInstance = None

    def instance():
        if SystemConfig.theSystemConfigInstance == None:
            SystemConfig()

        return SystemConfig.theSystemConfigInstance
    
    instance = staticmethod(instance)
    
    def __init__(self):
        if SystemConfig.theSystemConfigInstance is not None:
            raise Exception, "Only one instance of SystemConfig is allowed."

        SystemConfig.theSystemConfigInstance = self
        
        self.tempDir = None
        self.hostname = None
        
    def GetTempDir(self):
        """
        Get the path to the system temp directory.
        """
        if self.tempDir == None:
            winPath = win32api.GetWindowsDirectory()
            self.tempDir = os.path.join(winPath, "TEMP")
            
        return self.tempDir
        
    def GetProxySettings(self):
        """
        If the system has a proxy server defined for use, return its
        address.  The return value is actually a list of tuples
        (server address, enabled).  There are at least two places to
        look for these values.
        
        WinHttp defines  a proxy at
        
        HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings\Connections\WinHttpSettings 
        
        Unfortunately it stores its value as a binary string; it's meant to be
        accessed via the WinHttpGetDefaultProxyConfiguration call or by the
        proxycfg.exe program. For now, we'll just use the IE setting:
        
        IE defines a proxy at:
        
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings
        
        The key ProxyServer has the name of the proxy, and ProxyEnable
        is nonzero if it is enabled for use.
        """

        proxies = []

        k = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
        
        try:
            (val, vtype) = _winreg.QueryValueEx(k, "ProxyServer")

            proxyStr = str(val)

            if proxyStr.find(":") >= 0:
                # We have hostname and port
                proxy = proxyStr.split(":", 2)
            else:
                # Just a hostname.
                proxy = (proxyStr, None)

        except WindowsError:
            proxy = None

        # Check to see if this proxy is enabled.
        enabled = 0

        if proxy is None:
            return proxies

        try:
            (val, vtype) = _winreg.QueryValueEx(k, "ProxyEnable")
            enabled = val
        except WindowsError:
            pass

        if proxy is not None:
            proxies.append((proxy, enabled))
            
        return proxies

    def FileSystemFreeSpace(self, path):
        """
        Retrieve the amount of free space on the file system the path is
        housed on.
        """
        #
        # Otherwise use win32api.GetDiskFreeSpace.
        #
        # From the source to win32api:
        #
        # The return value is a tuple of 4 integers, containing
        # the number of sectors per cluster, the number of bytes per sector,
        # the total number of free clusters on the disk and the total number of
        # clusters on the disk.
        #
        
        try:
            x = win32api.GetDiskFreeSpace(path)
            
            freeBytes = x[0] * x[1] * x[2]
        except:
            freeBytes = None
            
        return freeBytes

    def GetUsername(self):
        try:
            user = win32api.GetUserName()
            user.replace(" ", "")
            return user
        except:
            raise
        
    def FindRegistryEnvironmentVariable(self, varname):
        """
        Find the definition of varname in the registry.
        
        Returns the tuple (global_value, user_value).
        
        We can use this to determine if the user has set an environment
        variable at the commandline if it's causing problems.
        
        """
        env_key = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
        global_reg = None
        user_reg = None
        
        k = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, env_key)
        
        try:
            (val, valuetype) = _winreg.QueryValueEx(k, varname)
            global_reg = val
        except:
            pass
        k.Close()
        
        # Read the user registry
        k = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Environment")
        
        try:
            (val, valuetype) = _winreg.QueryValueEx(k, varname)
            user_reg = val
        except:
            pass
        k.Close()
        
        
        return (global_reg, user_reg)
    
    def SendSettingChange(self):
        """
        This updates all windows with registry changes to the
        HKCU\Environment key.
        """
        import win32gui, win32con
        
        ret = win32gui.SendMessageTimeout(win32con.HWND_BROADCAST,
                                          win32con.WM_SETTINGCHANGE, 0,
                                          "Environment",
                                          win32con.SMTO_NORMAL, 1000)
        return ret

    def EnumerateInterfaces(self):
        """
        Enumerate the interfaces present on a windows box.
        
        Run ipconfig /all
        """

        adapter_re = re.compile("^Ethernet adapter (.*):$")
        ip_re = re.compile("^\s*IP Address.*:\s+(\d+\.\d+\.\d+\.\d+)")
        dns_re = re.compile("^\s*DNS Servers.*:\s+(\S+)")

        ipconfig = os.path.join(os.getenv("SystemRoot"), "system32",
                                "ipconfig.exe")
        p = os.popen(r"%s /all" % ipconfig, "r")

        adapters = []
        dns_servers = []

        for l in p:
            l = l.strip()
            m = adapter_re.search(l)
            if m is not None:
                cur_adapter = {'name': m.group(1),
                               'ip': None,
                               'dns': None}
                cur_adapter['name'] = m.group(1)
                adapters.append(cur_adapter)

            m = ip_re.search(l)
            if m is not None:
                cur_adapter['ip'] = m.group(1)
            m = dns_re.search(l)
            if m is not None:
                cur_adapter['dns'] = m.group(1)
                dns_servers.append(m.group(1))

        p.close()

        return adapters

    def GetLocalIPAddress(self):
        """
        Get our IP address. We use the heuristic that the address we
        want to advertise is the one that corresponds to the active
        default route. If there isn't a default route, pick the lowest-metric
        interface from the routing table. If we don't have anything there,
        return 127.0.0.1
        
        """

        route = os.path.join(os.getenv("SystemRoot"), "system32",
                             "route.exe")

        if not os.path.isfile(route):
            log.error("Cannot find route command: %s", route)
            return "127.0.0.1"
        
        p = os.popen(r"%s print" % route, "r")

        def_routes = []
        host_routes = []
        def_gw = None

        for l in p:
            parts = l.strip().split()
            if parts[0] == "0.0.0.0":
                interf = parts[3]
                metric= parts[4]
                gw = parts[2]
                def_routes.append((metric, interf, gw))
            elif parts[0] == "255.255.255.255":
                host_routes.append((parts[4], parts[3]))
            elif l.startswith("Default Gateway"):
                def_gw = parts[2]

        #
        # If we have no default routes, pick the lowest-metric
        # limited broadcast route (one with a destination of 255.255.255.255).
        #

        if len(def_routes) == 0:
            #
            # Back off to the host routes
            #

            if len(host_routes) == 0:
                #
                # No chance.
                #
                return "127.0.0.1"

            host_routes.sort()

            return host_routes[0][1]

        # sort by metric
        def_routes.sort()

        # find the default gateway in the list
        #

        def_int = None
        if def_gw is not None:
            for m, i, g in def_routes:
                if g == def_gw:
                    def_int = i
                    break

        #
        # Return the interface for the route
        # marked as default, if there is one.
        #
        if def_int is not None:
            return def_int

        #
        # Otherwise, return the lowest-metric default route.
        #
        return def_routes[0][1]
    
class MimeConfig(AccessGrid.Config.MimeConfig):
    """
    The MimeConfig object encapsulates in single object the management
    of mime types. This provides a cross platform solution so the AGTk
    can leverage legacy configuration and applications for data
    viewing.
    """
    theMimeConfigInstance = None

    def instance():
        if MimeConfig.theMimeConfigInstance == None:
            MimeConfig()

        return MimeConfig.theMimeConfigInstance

    instance = staticmethod(instance)
    
    def __init__(self):
        if MimeConfig.theMimeConfigInstance is not None:
            raise Exception, "Only one instance of MimeConfig is allowed."

        MimeConfig.theMimeConfigInstance = self
    
    def RegisterMimeType(self, mimeType, extension, fileType, description,
                         cmds):
        """
        mimeType - mimetype designator
        extension - file extension
        (doesn't have to be 3 letters, does have to start with a .)
        fileType - file type, doesn't matter, just unique
        description - free form description of the type
        
        list of:
        verb - name of command
        command - the actual command line
        commandDesc - a description (menu format) for the command
        
        ----
        
        This function gets the mime type registered with windows via
        the registry.

        The following documentation is from wxWindows, src/msw/mimetype.cpp:

            1. "HKCR\MIME\Database\Content Type" contains subkeys for
            all known MIME types, each key has a string value
            "Extension" which gives (dot preceded) extension for the
            files of this MIME type.

            2. "HKCR\.ext" contains

                a) unnamed value containing the "filetype"

                b) value "Content Type" containing the MIME type


            3. "HKCR\filetype" contains

                a) unnamed value containing the description

                b) subkey "DefaultIcon" with single unnamed value
                giving the icon index in an icon file

                c) shell\open\command and shell\open\print subkeys
                containing the commands to open/print the file (the
                positional parameters are introduced by %1, %2, ... in
                these strings, we change them to %s ourselves)

        """
        # Do 1. from above
        try:
            regKey = _winreg.CreateKey(_winreg.HKEY_CLASSES_ROOT,
                                   "MIME\Database\Content Type\%s" % mimeType)
            _winreg.SetValueEx(regKey, "Extension", 0,
                               _winreg.REG_SZ, extension)
            _winreg.CloseKey(regKey)
        except EnvironmentError:
            log.debug("Couldn't open registry for mime registration!")

        # Do 2. from above
        try:
            regKey = _winreg.CreateKey(_winreg.HKEY_CLASSES_ROOT, extension)

            _winreg.SetValueEx(regKey, "", 0, _winreg.REG_SZ, fileType)
            _winreg.SetValueEx(regKey, "Content Type", 0,
                               _winreg.REG_SZ, mimeType)

            _winreg.CloseKey(regKey)
        except EnvironmentError:
            log.debug("Couldn't open registry for mime registration!")

        # Do 3. from above
        try:
            regKey = _winreg.CreateKey(_winreg.HKEY_CLASSES_ROOT, fileType)
            
            _winreg.SetValueEx(regKey, "", 0, _winreg.REG_SZ, description)
            
            icoKey = _winreg.CreateKey(regKey, "DefaultIcon")
            _winreg.SetValueEx(icoKey, "", 0, _winreg.REG_SZ, "")
            _winreg.CloseKey(icoKey)
            
            shellKey = _winreg.CreateKey(regKey, "shell")
            
            for trio in cmds:
                (verb, command, commandDesc) = trio
                verbKey = _winreg.CreateKey(shellKey, verb)
                _winreg.SetValueEx(verbKey, "", 0, _winreg.REG_SZ, commandDesc)
                cmdKey = _winreg.CreateKey(verbKey, "command")
                # Make sure this is quoted
                lwords = command.split(' ')
                lwords[0] = "\"%s\"" % lwords[0]
                
                newcommand = " ".join(lwords)
                _winreg.SetValueEx(cmdKey, "", 0, _winreg.REG_SZ, newcommand)
                _winreg.CloseKey(cmdKey)
                _winreg.CloseKey(verbKey)

            _winreg.CloseKey(shellKey)

            _winreg.CloseKey(regKey)
        except EnvironmentError, e:
            log.debug("Couldn't open registry for mime registration!")

    def GetMimeCommands(self, mimeType = None, ext = None):
        """
        This gets the mime commands from one of the three types of
        specifiers windows knows about. Depending on which is passed
        in the following trail of information is retrieved:

            1. "HKCR\MIME\Database\Content Type" contains subkeys for
            all known MIME types, each key has a string value
            "Extension" which gives (dot preceded) extension for the
            files of this MIME type.

            2. "HKCR\.ext" contains
    
                a) unnamed value containing the "filetype"
    
                b) value "Content Type" containing the MIME type

            3. "HKCR\filetype" contains

                a) unnamed value containing the description

                b) subkey "DefaultIcon" with single unnamed value
                giving the icon index in an icon file

                c) shell\open\command and shell\open\print subkeys
                containing the commands to open/print the file (the
                positional parameters are introduced by %1, %2, ... in
                these strings, we change them to %s ourselves)
        """
        cdict = dict()
        filetype = None
        extension = ext

        log.debug("MimeType: %s", mimeType)

        if mimeType != None:
            try:
                key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT,
                                   "MIME\Database\Content Type\%s" % mimeType)
                extension, type = _winreg.QueryValueEx(key, "Extension")
                _winreg.CloseKey(key)
            except WindowsError:
                log.warn("Couldn't open registry for mime types: %s",
                         mimeType)
                return cdict

        log.debug("Extension: %s", extension)

        if extension != None:
            if extension[0] != ".":
                extension = ".%s" % extension
                try:
                    key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT,
                                          "%s" % extension)
                    filetype, type = _winreg.QueryValueEx(key, "")
                    _winreg.CloseKey(key)
                except WindowsError:
                    log.warn("Couldn't open registry for file extension: %s.",
                             extension)
                    return cdict

        log.debug("FileType: %s", filetype)

        if filetype != None:
            try:
                key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT,
                                      "%s\shell" % filetype)
                nCommands = _winreg.QueryInfoKey(key)[0]

                log.debug("Found %d commands for filetype %s.", nCommands,
                          filetype)

                for i in range(0,nCommands):
                    commandName = _winreg.EnumKey(key, i)
                    command = None
                    # Always use caps for names to make life easier
                    try:
                        ckey = _winreg.OpenKey(key, "%s\command" % commandName)
                        command, type = _winreg.QueryValueEx(ckey,"")
                        _winreg.CloseKey(ckey)
                    except:
                        log.warn("Couldn't get command for name: <%s>",
                                 commandName)
                    commandName = commandName.capitalize()
                    cdict[commandName] = command
                    
                _winreg.CloseKey(key)

            except EnvironmentError:
                warnStr = "Couldn't retrieve list of commands: (mimeType: %s) \
                (fileType: %s)"
                log.warn(warnStr, mimeType, filetype)
                return cdict

        return cdict

    def GetMimeType(self, extension = None):
        mimeType = None
        if extension != None:
            if extension[0] != ".":
                extension = ".%s" % extension
                try:
                    key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT,
                                          "%s" % extension)
                    mimeType, type = _winreg.QueryValueEx(key, "Content Type")
                    _winreg.CloseKey(key)
                except WindowsError:
                    log.warn("Couldn't open registry for file extension: %s.",
                             extension)
                    return mimeType
                
        return mimeType

# Simple inline tests to make sure this module and all of it's classes
# are working

if __name__ == "__main__":
    print "AGTk Configuration:"

    try:
        tkConf = AGTkConfig.instance()
    except Exception, e:
        tkConf = None
        print "Error trying to retrieve AGTk Configuration:\n", e

    if tkConf is not None:
        try:
            print "\tVersion: ", tkConf.GetVersion()
            print "\tConfigDir: ", tkConf.GetConfigDir()
            print "\tInstallDir: ", tkConf.GetInstallDir()
            print "\tDocDir: ", tkConf.GetDocDir()
            print "\tPkgCacheDir: ", tkConf.GetPkgCacheDir()
            print "\tSharedAppDir: ", tkConf.GetSharedAppDir()
            print "\tNodeServicesDir: ", tkConf.GetNodeServicesDir()
            print "\tServicesDir: ", tkConf.GetServicesDir()
        except Exception, e:
            print "Error trying to retrieve AGTk Configuration:\n", e
        
    print "Globus Configuration:"
    try:
        globusConf = GlobusConfig.instance(0)
    except Exception, e:
        print "Error retrieving Globus Configuration:\n", e
        
    if globusConf is not None:
        try:
            print "\tGlobus Location: ", globusConf.GetLocation()
            print "\tGlobus Hostname: ", globusConf.GetHostname()
            print "\tGlobus CA Cert Dir: ", globusConf.GetCACertDir()
            print "\tGlobus Proxy File: ", globusConf.GetProxyFileName()
            print "\tGlobus Cert File: ", globusConf.GetCertFileName()
            print "\tGlobus Key File: ", globusConf.GetKeyFileName()
        except Exception, e:
            print "Error trying to retrieve the Globus Configuration:\n", e
    else:
        print "The globus config object is: ", globusConf
        
    print "System Configuration:"
    try:
        sysConf = SystemConfig.instance()
    except Exception, e:
        print "Error trying to retrieve the System Configuration:\n", e
        sysConf = None

    if sysConf is not None:
        try:
            print "\tSystem Hostname: ", sysConf.GetHostname()
            print "\tSystem Temp Dir: ", sysConf.GetTempDir()
            freespace = sysConf.GetFileSystemFreeSpace(os.path.join("."))
            print "\tSystem File System Free Space (on /): ", freespace
            print "\tSystem Current Username: ", sysConf.GetUsername()
            iflist = sysConf.EnumerateInterfaces()
            print "\tSystem Network Interface: "
            for interface in iflist:
                print "\t\tName: %8s IP: %15s DNS: %s" % (interface['name'],
                                                        interface['ip'],
                                                        interface['dns'])
            print "\tSystem Default Route: ", sysConf.GetDefaultRouteIP()
        except Exception, e:
            print "Error trying to retrieve the System Configuration:\n", e
    else:
        print "Thee system config object is: ", sysConf
