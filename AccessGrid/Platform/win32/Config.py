#-----------------------------------------------------------------------------
# Name:        Config.py
# Purpose:     Configuration objects for applications using the toolkit.
#              there are config objects for various sub-parts of the system.
# Created:     2003/05/06
# RCS-ID:      $Id: Config.py,v 1.48 2004-09-09 05:19:40 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Config.py,v 1.48 2004-09-09 05:19:40 judson Exp $"

import os
import sys
import socket
import re


from pyGlobus import utilc

import AccessGrid.Config
from AccessGrid import Log
from AccessGrid.Platform import AGTK_USER, AGTK_LOCATION
from AccessGrid.Version import GetVersion
from AccessGrid.Types import AGVideoResource

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
    @ivar configDir: The directory for installation configuration.

    @type appDir: string
    @type nodeServicesDir: string
    @type servicesDir: string
    @type configDir: string
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
        AccessGrid.Config.AGTkConfig.__init__(self)
        AGTkConfig.theAGTkConfigInstance = self

        # Set the flag to initialize if needed
        self.initIfNeeded = initIfNeeded
        
        # Initialize state
        self.version = GetVersion()
        self.installBase = None
        self.installDir = None
        self.configDir = None
        self.logDir = None
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
        self.GetLogDir()
        self.GetSharedAppDir()
        self.GetNodeServicesDir()
        self.GetServicesDir()
        
    def GetVersion(self):
        return self.version

    def GetInstallDir(self):
        if self.installDir is None:
            self.installDir = self.GetBaseDir()
            
        return self.installDir

    def GetBaseDir(self):
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
            raise IOError("AGTkConfig: installation base does not exist %s." %self.installBase)
        
        return self.installBase
        
    def GetConfigDir(self):
        if self.installBase == None:
            self.GetBaseDir()

        self.configDir = os.path.join(self.installBase, "Config")
      
        # Check dir and make it if needed.
        if self.initIfNeeded:
            if self.configDir is not None and \
                   not os.path.exists(self.configDir):
                os.mkdir(self.configDir)

        if self.configDir is not None and not os.path.exists(self.configDir):
            raise IOError("AGTkConfig: config dir does not exist %s." %self.configDir)

        return self.configDir

    def GetBinDir(self):
        if self.installBase == None:
            self.GetBaseDir()

        self.installDir = os.path.join(self.installBase, "bin")

        # Check the installation
        if self.installDir is not None and not os.path.exists(self.installDir):
            raise IOError("AGTkConfig: install dir does not exist %s."%self.installDir)

        return self.installDir

    def GetDocDir(self):
        if self.installBase == None:
            self.GetBaseDir()

        self.docDir = os.path.join(self.installBase, "doc")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if self.docDir is not None and \
                   not os.path.exists(self.docDir):
                os.mkdir(self.docDir)

        # Check the installation
        if self.docDir is not None and not os.path.exists(self.docDir):
            raise IOError("AGTkConfig: doc dir does not exist %s."%self.docDir)

        return self.docDir

    def GetLogDir(self):
        if self.logDir == None:
            ucd = self.GetBaseDir()
            self.logDir = os.path.join(ucd, "Logs")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if self.logDir is not None and \
                   not os.path.exists(self.logDir):
                try:
                    os.mkdir(self.logDir)
                except:
                    log.exception("Couldn't make log dir.")

        # Check the installation
        
        if self.logDir is not None and \
               not os.path.exists(self.logDir):
            raise IOError("AGTkConfig: log dir does not exist %s."%self.logDir)
 
        return self.logDir
    
    def GetSharedAppDir(self):
        if self.appDir == None:
            ucd = self.GetBaseDir()
            self.appDir = os.path.join(ucd, "SharedApplications")

        # Check dir and create it if needed.
        if self.initIfNeeded:
            if self.appDir is not None and not os.path.exists(self.appDir):
                try:
                    os.mkdir(self.appDir)
                except:
                    log.exception("Couldn't make app dir.")

        # Check the installation
        if self.appDir is not None and not os.path.exists(self.appDir):
            raise IOError("AGTkConfig: app dir does not exist %s." %self.appDir)

        return self.appDir

    def GetNodeServicesDir(self):
        if self.nodeServicesDir == None:
            ucd = self.GetBaseDir()
            self.nodeServicesDir = os.path.join(ucd, "NodeServices")

        # Check dir and create it if needed.
        if self.initIfNeeded:
            if self.nodeServicesDir is not None and \
                   not os.path.exists(self.nodeServicesDir):
                try:
                    os.mkdir(self.nodeServicesDir)
                except:
                    log.exception("Couldn't make node services dir.")

        # Check the installation
        if self.nodeServicesDir is not None and \
               not os.path.exists(self.nodeServicesDir):
            raise IOError("AGTkConfig: node service dir does not exist %s."%self.nodeServicesDir)

        return self.nodeServicesDir

    def GetServicesDir(self):
        if self.servicesDir == None:
            ucd = self.GetBaseDir()
            self.servicesDir = os.path.join(ucd, "Services")

        # Check dir and create it if needed.
        if self.initIfNeeded:
            if self.servicesDir is not None and \
                   not os.path.exists(self.servicesDir):
                try:
                    os.mkdir(self.servicesDir)
                except:
                    log.exception("Couldn't make services dir.")

        # Check the installation
        if self.servicesDir is not None and \
               not os.path.exists(self.servicesDir):
            raise IOError("AGTkConfig: services dir does not exist %s."%self.servicesDir)

        return self.servicesDir

class GlobusConfig(AccessGrid.Config.GlobusConfig):
    """
    This object encapsulates the information required to correctly configure
    Globus and pyGlobus for use with the Access Grid Toolkit.

    HKCU\Software\Globus
    HKCU\Software\Globus\GSI
    HKCU\Software\Globus\GSI\x509_user_proxy = {%TEMP%|{win}\temp}\proxy
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
        self.hostname = None
        self.serverFlag = None
        
        # First, get the paths to stuff we need
        uappdata = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
        agtkdata = AGTkConfig.instance().GetConfigDir()

        self.location = AGTkConfig.instance().GetInstallDir()
        self.proxyFileName = os.path.join(UserConfig.instance().GetTempDir(),
                                          "proxy")
        self.distCACertDir = os.path.join(agtkdata, "CAcertificates")
        self.distCertFileName = os.path.join(uappdata, "globus", "usercert.pem")
        self.distKeyFileName = os.path.join(uappdata, "globus", "userkey.pem")

        self._Initialize()
        
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

    def _Initialize(self):
        """
        right now we just want to check and see if registry settings
        are in place for the various parts.
        """

        # Zero, get keys we need
        gsikey = self.GetGlobusKey()
        
        # next try to setup GLOBUS_LOCATION, if it's not already set
        if os.getenv("GLOBUS_LOCATION") is None:
            self.SetLocation(self.location)

        # Check GLOBUS_HOSTNAME
        self.SetHostname()

        #
        # Check for values out of the registry.
        # It doesn't matter if they're not there; we're going to completely
        # configure our environment later on.
        # 
        try:
            (self.distKeyFileName, type) = _winreg.QueryValueEx(gsikey,
                                                             "x509_user_key")
        except WindowsError:
            pass

        try:
            (self.distCertFileName, type) = _winreg.QueryValueEx(gsikey,
                                                                 "x509_user_cert")
        except WindowsError:
            pass

        try:
            (self.distCACertDir, type) = _winreg.QueryValueEx(gsikey,
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

        AccessGrid.Config.GlobusConfig.SetUserCert(self, cert, key)

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
        
class UserConfig(AccessGrid.Config.UserConfig):
    """
    A user config object encapsulates all of the configuration data for
    a running instance of the Access Grid Toolkit software.

    @ivar profileFilename: the user profile
    @ivar tempDir: a temporary directory for files for this user
    @ivar appDir: The directory for system installed shared applications
    @ivar nodeServicesDir: the directory for system installed node services
    @ivar servicesDir: the directory for system installed services
    @ivar configDir: The directory for installation configuration.

    @type profileFilename: the filename of the client profile
    @type tempDir: string
    @type appDir: string
    @type nodeServicesDir: string
    @type servicesDir: string
    @type configDir: string
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

        AccessGrid.Config.UserConfig.__init__(self)
        UserConfig.theUserConfigInstance = self

        self.initIfNeeded = initIfNeeded

        self.baseDir = None
        self.logDir = None
        self.configDir = None
        self.tempDir = None
        self.appDir = None
        self.sharedAppDir = None
        self.nodeServicesDir = None
        self.servicesDir = None
        self.profileFilename = None

        self._Initialize()
        
    def _Initialize(self):
        self.GetConfigDir()
        self.GetTempDir()
        self.GetProfile()
        self.GetLogDir()

        # These are new and so can fail
        try:
            self.GetSharedAppDir()
        except:
            log.warn("No Shared App Dir!")
        try:
            self.GetNodeServicesDir()
        except:
            log.warn("No Node Service Dir!")
        try:
            self.GetServicesDir()
        except:
            log.warn("No Service Dir!")

        # Move old config files to new location.
        if self.initIfNeeded:
            self._Migrate()
   
    def GetBaseDir(self):
        global AGTK_USER
       
        try:
            self.baseDir = os.environ[AGTK_USER]
                        
            # Create directory if it doesn't exist
            if self.initIfNeeded:
                if not os.path.exists(self.baseDir):
                    os.mkdir(self.baseDir)
                                 
        except:
            try:
                base = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
                self.baseDir = os.path.join(base, "AccessGrid")

                if self.initIfNeeded:
                    # Create directory if it doesn't exist
                    if not os.path.exists(self.baseDir):
                        os.mkdir(self.baseDir)
                
            except:
                log.exception("Can not create base directory")
                # check to make it if needed
                self.baseDir = ""
                
        return self.baseDir

    def GetProfile(self):
        if self.profileFilename == None:
            self.profileFilename = os.path.join(self.GetConfigDir(), "profile")
            
        return self.profileFilename

    def GetConfigDir(self):
        if self.configDir == None:
            ucd = self.GetBaseDir()
            self.configDir = os.path.join(ucd, "Config")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if self.configDir is not None and \
                   not os.path.exists(self.configDir):
                os.mkdir(self.configDir)

        # Check the installation
        if self.configDir is not None and \
               not os.path.exists(self.configDir):
            raise Exception, "AGTkConfig: config dir does not exist %s."%self.configDir

        return self.configDir
        
    def GetTempDir(self):
        if self.tempDir == None:
            self.tempDir = win32api.GetTempPath()

        if not os.access(self.tempDir, os.W_OK):
            log.error("UserConfig configuration: TempDir %s is not writable",
                      self.tempDir)

        return self.tempDir
    
    def GetLogDir(self):
        if self.logDir == None:
            ucd = self.GetBaseDir()
            self.logDir = os.path.join(ucd, "Logs")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if self.logDir is not None and \
                   not os.path.exists(self.logDir):
                os.mkdir(self.logDir)


        # Check the installation
        if self.logDir is not None and \
               not os.path.exists(self.logDir):
            raise Exception, "AGTkConfig: log dir does not exist %s."%self.logDir 

        return self.logDir
    
    def GetSharedAppDir(self):
        if self.appDir == None:
            ucd = self.GetBaseDir()
            self.appDir = os.path.join(ucd, "SharedApplications")

        # Check dir and create it if needed.
        if self.initIfNeeded:
            if self.appDir is not None and not os.path.exists(self.appDir):
                os.mkdir(self.appDir)

        # Check the installation
        if self.appDir is not None and not os.path.exists(self.appDir):
            raise Exception, "AGTkConfig: app dir does not exist %s."%self.appDir

        return self.appDir

    def GetNodeServicesDir(self):
        if self.nodeServicesDir == None:
            ucd = self.GetBaseDir()
            self.nodeServicesDir = os.path.join(ucd, "NodeServices")

        # Check dir and create it if needed.
        if self.initIfNeeded:
            if self.nodeServicesDir is not None and \
                   not os.path.exists(self.nodeServicesDir):
                os.mkdir(self.nodeServicesDir)

        # Check the installation
        if self.nodeServicesDir is not None and \
               not os.path.exists(self.nodeServicesDir):
            raise Exception, "AGTkConfig: node service dir does not exist %s."%self.nodeServicesDir

        # check to make it if needed
        return self.nodeServicesDir

    def GetServicesDir(self):
        if self.servicesDir == None:
            ucd = self.GetBaseDir()
            self.servicesDir = os.path.join(ucd, "Services")

        # Check dir and create it if needed.
        if self.initIfNeeded:
            if self.servicesDir is not None and \
                   not os.path.exists(self.servicesDir):
                os.mkdir(self.servicesDir)

        # Check the installation
        if self.servicesDir is not None and \
               not os.path.exists(self.servicesDir):
            raise Exception, "AGTkConfig: services dir does not exist %s."%self.servicesDir

        return self.servicesDir

class SystemConfig(AccessGrid.Config.SystemConfig):
    """
    The SystemConfig object encapsulates all system dependent
    configuration data, it should be extended to retrieve and store
    additional information as necessary.

    @ivar tempDir: the system temp directory.
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

        AccessGrid.Config.SystemConfig.__init__(self)
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

        If there are different proxies for different protocols, the ProxyServer key will
        look like this:

        ftp=ftpp:2345;gopher=gopherp:3456;http=yips:8080;https=securep:1234;socks=socksp:4567

        If it is set to use the same server for all protocols, it will look like this:

        yips:8080
        
        """

        proxies = []

        k = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
        
        try:
            (val, vtype) = _winreg.QueryValueEx(k, "ProxyServer")

            proxyStr = str(val)

            # See if it is set for different protocols
            if proxyStr.find(";") < 0:
                # It is. Find the http= part.
                protos = proxyStr.split(";")
                http = filter(lambda a: a.startswith("http="), protos)
                if len(http) > 0:
                    p = http[0][5:]
                    log.debug("Found http proxy as %s from %s",
                              p, proxyStr)
                    proxyStr = p

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

    def GetFileSystemFreeSpace(self, path):
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
        
    def GetResources(self):
        """ 
        Return a list of the resources available on the system
        """
    
        deviceList = list()
        
        try:
            # Get the name of the video key in the registry
            key = "SYSTEM\\ControlSet001\\Control\\MediaResources\\msvideo"
            videoKey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key)

            # Get the number of subkeys (devices) in the key
            (nSubKeys, nValues, lastModified) = _winreg.QueryInfoKey(videoKey)

            for i in range(nSubKeys):
                # Open the key
                sVal = _winreg.EnumKey(videoKey, 0)
                sKey = _winreg.OpenKey(videoKey, sVal)
                (nSubKeys, nValues, lastModified) = _winreg.QueryInfoKey(sKey)

                # Find the device name among the key's values
                for i in range(0, nValues):
                    (vName, vData, vType) = _winreg.EnumValue(sKey, i)
                    if vName == "FriendlyName":
                        deviceList.append(vData)
                    
        except Exception:
            log.exception("Exception getting video devices")
            raise
    
        resourceList = list()
        for d in deviceList:
            r = AGVideoResource('video',d,'producer',['external-in'])
            resourceList.append(r)
        return resourceList

    def PerformanceSnapshot(self):
        """
        This method grabs a snapshot of relevent system information to report
        it. This helps track the effect of the AG Toolkit on the system.
        """
        import win32pdhutil
        perfData = dict()
        counterGroup = "Process(python)"
        counterNames = [
            "% Processor Time",
            "% User Time",
            "Handle Count",
            "Private Bytes",
            "Thread Count",
            "% Processor Time"
            ]

        for n in counterNames:
            key = "%s.%s" % (counterGroup, n)
            perfData[key] = win32pdhutil.GetPerformanceAttributes(counterGroup,
                                                                  n)
        
        return perfData

    def AppFirewallConfig(self, path, enableFlag):
        """
        This method pokes the windows registry to enable or disable an
        application in the firewall config.
        """
        if enableFlag:
            enStr = "Enabled"
        else:
            enStr = "Disabled"

        try:
            # Get the name of the firewall applications key in the registry
            key = "SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\StandardProfile\\AuthorizedApplications\\List"
            fwKey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key, 0,
                                    _winreg.KEY_ALL_ACCESS)

            # Get the number of applications currently configured
            (nSubKeys, nValues, lastModified) = _winreg.QueryInfoKey(fwKey)

            
            # Find the application among the key's values
            for i in range(0, nValues):
                (vName, vData, vType) = _winreg.EnumValue(fwKey, i)
                if path == vName:
                    # Set the flag to the value passed in
                    (p, e, d) = vData[len(vName)+1:-1].split(":")
                    print "%s %s %s" % (p, e, d)
                    vData = ":".join([vName, p, enStr, d])
                    break
                else:
                    vName = None
                    vData = None

            if vName == None:
                vName = path

            if vData == None:
                vData = "%s:*:%s:AccessGrid Software(%s)" % (path,
                                                             enStr,
                                                             path)
                
            # Put the value back in the registry
            _winreg.SetValueEx(fwKey, vName, 0,_winreg.REG_SZ, vData)

        except Exception:
            log.exception("Exception configuring firewall for application: %s",
                          path)
            raise
    
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
        example: [ (verb,command,commandDesc), ...  ]
        
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
        '''
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
        '''
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

        if extension != None and len(extension) > 0:
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
    from AccessGrid.Toolkit import CmdlineApplication

    app = CmdlineApplication.instance()

    app.Initialize("ConfigTest")
    
    try:
        tkConf = AGTkConfig.instance()
    except Exception, e:
        tkConf = None
        print "Error trying to retrieve AGTk Configuration:\n", e
    else:
        print tkConf

    try:
        sysConf = SystemConfig.instance()
    except Exception, e:
        print "Error trying to retrieve the System Configuration:\n", e
        sysConf = None
    else:
        print sysConf
        
    try:
        userConf = UserConfig.instance(0)
    except Exception, e:
        print "Error trying to retrieve the User Configuration:\n", e
        userConf = None
    else:
        print userConf

    try:
        globusConf = GlobusConfig.instance(0)
    except Exception, e:
        print "Error retrieving Globus Configuration:\n", e
        globusConf = None
    else:
        print globusConf
        
