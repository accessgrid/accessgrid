#-----------------------------------------------------------------------------
# Name:        Config.py
# Purpose:     Configuration objects for applications using the toolkit.
#              there are config objects for various sub-parts of the system.
# Created:     2003/05/06
# RCS-ID:      $Id: Config.py,v 1.10 2004-04-21 21:37:24 olson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Config.py,v 1.10 2004-04-21 21:37:24 olson Exp $"

import os
import sys
import struct
import time
import select
import socket

from AccessGrid import Log
log = Log.GetLogger(Log.Toolkit)

class AGTkConfig:
    """
    This class encapsulates a system configuration for the Access Grid
    Toolkit. This object provides primarily read-only access to configuration
    data that is created when the toolkit is installed.

    @type version: string
    @ivar version: The version of this installation.
    @type installDir: string
    @ivar installDir: The directory this toolkit is installed in.
    @type docDir: string
    @ivar docDir: The directory for documentation for the toolkit.
    @type appDir: string
    @ivar appDir: The directory for system installed shared applications
    @type nodeServicesDir: string
    @ivar nodeServicesDir: the directory for system installed node services
    @type servicesDir: string
    @ivar servicesDir: the directory for system installed services
    @type pkgCacheDir: string
    @ivar pkgCacheDir: The directory of shared application and node
    service packages for all users of this installation.
    @type configDir: string
    @ivar configDir: The directory for installation configuration.
    """
    def __init__(self):
        pass

    def _repr_(self):
        str = "Access Grid Toolkit Configuration:\n"
        str += "Version: %s\n" % self.GetVersion()
        str += "InstallDir: %s\n" % self.GetInstallDir()
        str += "DocDir: %s\n" % self.GetDocDir()
        str += "LogDir: %s\n" % self.GetLogDir()
        str += "PkgCacheDir: %s\n" % self.GetPkgCacheDir()
        str += "ConfigDir: %s\n" % self.GetConfigDir()
        str += "SharedAppDir: %s\n" % self.GetSharedAppDir()
        str += "NodeServicesDir: %s\n" % self.GetNodeServicesDir()
        str += "ServicesDir: %s\n" % self.GetServicesDir()
    
        return str

    def __str__(self):
        return self._repr_()
    
    def GetVersion(self):
        raise "This should not be called directly, but through a subclass."

    def GetInstallDir(self):
        raise "This should not be called directly, but through a subclass."

    def GetDocDir(self):
        raise "This should not be called directly, but through a subclass."

    def GetLogDir(self):
        raise "This should not be called directly, but through a subclass."

    def GetPkgCacheDir(self):
        raise "This should not be called directly, but through a subclass."

    def GetConfigDir(self):
        raise "This should not be called directly, but through a subclass."

    def GetSharedAppDir(self):
        raise "This should not be called directly, but through a subclass."

    def GetNodeServicesDir(self):
        raise "This should not be called directly, but through a subclass."

    def GetServicesDir(self):
        raise "This should not be called directly, but through a subclass."

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
    def __init__(self, initEnvIfNeeded=0):
        """
        This is the constructor, the only argument is used to indicate
        a desire to intialize the existing environment if it is discovered
        to be uninitialized.

        @param initEnvIfNeeded: a flag indicating if this object should
        initialize the system if it is not.

        @type initEnvIfNeeded: integer
        """
        raise "This should not be called directly, but through a subclass."

    def _repr_(self):
        str = "Globus Configuration:\n"
        str += "Location: %s\n" % self.GetLocation()
        str += "Hostname: %s\n" % self.GetHostname()
        str += "Server Flag: %s\n" % self.GetServerFlag()
        str += "CA Cert Dir: %s\n" % self.GetCACertDir()
        str += "Proxy Filename: %s\n" % self.GetProxyFileName()
        str += "Cert Filename: %s\n" % self.GetCertFileName()
        str += "Key Filename: %s\n" % self.GetKeyFileName()

        return str

    # We define our own setenv/unsetenv to prod both the pyGlobus
    # environment and the standard python environment.
    def Setenv(self, name, val):
        global pyGlobusSetenv

        os.environ[name] = val
        
        print "normal setenv %s=%s" %(name, val)
        
        if pyGlobusSetenv:
            print "pyGlobus setenv %s=%s" %(name, val)
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

    def __str__(self):
        return self._repr_()

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
            #
            # It has to really be a fqdn.
            #
            if hostname.find(".") < 0:
                return self._SetHostnameToLocalIP()

            #
            # And one has to be able to bind to it.
            #
            
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

    def _SetHostnameToLocalIP(self):
        try:
            self.hostname = SystemConfig.instance().GetLocalIPAddress()
            log.debug("retrieved local IP address %s", self.hostname)
        except:
            self.hostname = "127.0.0.1"
            
            log.exception("Failed to determine local IP address, using %s",
                          self.hostname)

        self.Setenv("GLOBUS_HOSTNAME", self.hostname)

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
        
class UserConfig:
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

    @type profile: a Client Profile
    @type tempDir: string
    @type appDir: string
    @type nodeServicesDir: string
    @type servicesDir: string
    @type configDir: string
    @type pkgCacheDir: string
    """
    def __init__(self):
        raise "This should not be called directly, but through a subclass."

    def _repr_(self):
        str = "User Configuration:\n"
        str += "Profile File: %s\n" % self.GetProfile()
        str += "Config Dir: %s\n" % self.GetConfigDir()
        str += "Temp Dir: %s\n" % self.GetTempDir()
        str += "Log Dir: %s\n" % self.GetLogDir()
        str += "Pkg Cache Dir: %s\n" % self.GetPkgCacheDir()
        str += "Shared App Dir: %s\n" % self.GetSharedAppDir()
        str += "Node Services Dir: %s\n" % self.GetNodeServicesDir()
        str += "Services Dir: %s\n" % self.GetServicesDir()
        return str

    def __str__(self):
        return self._repr_()
    
    def GetProfile(self):
        raise "This should not be called directly, but through a subclass."

    def GetLogDir(self):
        raise "This should not be called directly, but through a subclass."

    def GetTempDir(self):
        raise "This should not be called directly, but through a subclass."
    
    def GetPkgCacheDir(self):
        raise "This should not be called directly, but through a subclass."

    def GetConfigDir(self):
        raise "This should not be called directly, but through a subclass."

    def GetSharedAppDir(self):
        raise "This should not be called directly, but through a subclass."

    def GetNodeServicesDir(self):
        raise "This should not be called directly, but through a subclass."

    def GetServicesDir(self):
        raise "This should not be called directly, but through a subclass."

    def SetRTPDefaults(self):
        raise "This should not be called directly, but through a subclass."

class SystemConfig:
    """
    The SystemConfig object encapsulates all system dependent
    configuration data, it should be extended to retrieve and store
    additional information as necessary.

    @ivar tempDir: the system temp directory.
    @type tempDir: string
    """
    def __init__(self):
        raise "This should not be called directly, but through a subclass."

    def _repr_(self):
        str = "System Configuration:\n"
        str += "Temp Dir: %s\n" % self.GetTempDir()
        str += "HTTP Proxy Settings: %s\n" % self.GetProxySettings()
        str += "F/S Free Space(/): %s\n" % self.FileSystemFreeSpace("/")
        str += "Username: %s\n" % self.GetUsername()
        str += "Local IP Address: %s\n" % self.GetLocalIPAddress()
        str += "Local Network Interfaces:\n"
        for i in self.EnumerateInterfaces():
            str += "\tName: %8s IP: %15s DNS: %s\n" % (i['name'], i['ip'],
                                                       i['dns'])
        return str

    def __str__(self):
        return self._repr_()
    
    def GetTempDir(self):
        """
        Get the path to the system temp directory.
        """
        raise "This should not be called directly, but through a subclass."
        
    def GetHostname(self):
        """
        Retrieve the local hostname.
        """
        if self.hostname == None:
            try:
                self.hostname = socket.getfqdn()
            except:
                self.hostname = None
                raise
        
        return self.hostname

    def GetProxySettings(self):
        """
        Retrieve local HTTP proxy settings.
        """
        err_str = "This should not be called directly, but through a subclass."
        raise Exception(err_str)

    def FileSystemFreeSpace(self, path):
        """
        Retrieve the amount of free space on the file system the path is
        housed on.
        """
        err_str = "This should not be called directly, but through a subclass."
        raise Exception(err_str)

    def _GetSNTPTime(self, server, timeout=0.3):
        """
        Retrieve the time from the given time server, with a timeout.
        
        @param server: Hostname or IP address of the time server.
        
        @param timeout: Timeout for the request, in seconds (fractions
        allowed).
        
        @return: Time from that server, in seconds-since-1970, or None
        if the request failed for any reason.
        
        Thanks the ASPN python recipes folks for this.
        (http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/117211)
        """
        TIME1970 = 2208988800L      # Thanks to F.Lundh
        client = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
        data = '\x1b' + 47 * '\0'
        client.sendto( data, (server, 123 ))

        x = select.select([client], [], [], timeout)
        if x[0] != []:
        
            data, address = client.recvfrom( 1024 )
            client.close()
            if data:
                t = struct.unpack( '!12I', data )[10]
                t -= TIME1970
                return t
            else:
                client.close()
                return None
        else:
            client.close()
            return None
        
    def CheckClock(self, limit=10):
        """
        Retrieve the SNTP time and compare this clock against it.
        """
        try:
            rtime = self._GetSNTPTime()
        except:
            rtime = None

        if rtime is not None:
            diff = int(time.time() - rtime)
            absdiff = abs(diff)

            if absdiff > limit:
                return (1, diff)
            else:
                return (0, diff)
        else:
            return (-1, None)
        
class MimeConfig:
    """
    The MimeConfig object encapsulates in single object the management
    of mime types. This provides a cross platform solution so the AGTk
    can leverage legacy configuration and applications for data
    viewing.
    """
    def __init__(self):
        err_str = "This should not be called directly, but through a subclass."
        raise Exception(err_str)
    
    def GetMimeType(extension = None):
        raise "This should not be called directly, but through a subclass."

    def GetMimeCommands(mimeType = None, ext = None):
        raise "This should not be called directly, but through a subclass."

    def RegisterMimeType():
        raise "This should not be called directly, but through a subclass."
