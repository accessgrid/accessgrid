#-----------------------------------------------------------------------------
# Name:        Config.py
# Purpose:     Configuration objects for applications using the toolkit.
#              there are config objects for various sub-parts of the system.
# Created:     2003/05/06
# RCS-ID:      $Id: Config.py,v 1.2 2004-03-26 19:29:54 olson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Config.py,v 1.2 2004-03-26 19:29:54 olson Exp $"

import sys
import struct
import time
import select
import socket

from AccessGrid import Utilities

class AGTkConfig:
    """
    This class encapsulates a system configuration for the Access Grid
    Toolkit. This object provides primarily read-only access to configuration
    data that is created when the toolkit is installed.

    @var version: The version of this installation.
    @var installDir: The directory this toolkit is installed in.
    @var docDir: The directory for documentation for the toolkit.
    @var appDir: The directory for system installed shared applications
    @var nodeServicesDir: the directory for system installed node services
    @var servicesDir: the directory for system installed services
    @var pkgCacheDir: The directory of shared application and node
    service packages for all users of this installation.
    @var configDir: The directory for installation configuration.

    @type appDir: string
    @type nodeServicesDir: string
    @type servicesDir: string
    @type configDir: string
    @type pkgCacheDir: string
    @type version: string
    @type installDir: string
    @type docDir: string
    """
    def __init__(self):
        raise "This should not be called directly, but through a subclass."
        
    def GetVersion(self):
        raise "This should not be called directly, but through a subclass."

    def GetInstallDir(self):
        raise "This should not be called directly, but through a subclass."

    def GetDocDir(self):
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

class GlobusConfig:
    """
    This object encapsulates the information required to correctly configure
    Globus and pyGlobus for use with the Access Grid Toolkit.

    @var location: the location of the globus installation
    @var caCertDir: the directory of Certificate Authority Certificates
    @var hostname: the Hostname for the globus configuration
    @var proxyFile: THe filename for the globus proxy
    @var certFile: The filename of the X509 certificate.
    @var keyFile: The filename of the X509 key.
    """
    def __init__(self, initEnvIfNeeded=0):
        """
        This is the constructor, the only argument is used to indicate
        a desire to intialize the existing environment if it is discovered
        to be uninitialized.

        @param initIfNeeded: a flag indicating if this object should
        initialize the system if it is not.

        @type initIfNeeded: integer
        """
        raise "This should not be called directly, but through a subclass."

    def GetLocation(self):
        raise "This should not be called directly, but through a subclass."
    
    def GetCACertDir(self):
        raise "This should not be called directly, but through a subclass."
    
    def GetHostname(self):
        """
        Return the local hostname.

        This uses the pyGlobus mechanism when possible, in order
        to get a hostname that Globus will be happy with.
        """

        try:
            from pyGlobus import utilc
            ret, self.hostname = utilc.get_hostname(256)

            if ret != 0:
                self.hostname = socket.getfqdn()
        except:
            log.exception("pyGlobus hostname retrieval failed")
            self.hostname = socket.getfqdn()

        return self.hostname
    
    def GetProxyFileName(self):
        raise "This should not be called directly, but through a subclass."
    
    def GetCertFileName(self):
        raise "This should not be called directly, but through a subclass."

    def GetKeyFileName(self):
        raise "This should not be called directly, but through a subclass."    

class UserConfig:
    """
    A user config object encapsulates all of the configuration data for
    a running instance of the Access Grid Toolkit software.

    @var profile: the user profile
    @var tempDir: a temporary directory for files for this user
    @var appDir: The directory for system installed shared applications
    @var nodeServicesDir: the directory for system installed node services
    @var servicesDir: the directory for system installed services
    @var pkgCacheDir: The directory of shared application and node
    service packages for all users of this installation.
    @var configDir: The directory for installation configuration.

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

    def GetProfile(self):
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

    @var tempDir: the system temp directory.
    @type tempDir: string
    """
    def __init__(self):
        raise "This should not be called directly, but through a subclass."

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
            except Exception, e:
                self.hostname == None
                raise
        
        return self.hostname

    def GetProxySettings(self):
        """
        Retrieve local HTTP proxy settings.
        """
        raise "This should not be called directly, but through a subclass."

    def FileSystemFreeSpace(self,path):
        """
        Retrieve the amount of free space on the file system the path is
        housed on.
        """
        raise "This should not be called directly, but through a subclass."

    def _GetSNTPTime(self, timeout=0.3):
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
        raise "This should not be called directly, but through a subclass."
    
    def GetMimeType(extension = None):
        raise "This should not be called directly, but through a subclass."

    def GetMimeCommands(mimeType = None, ext = None):
        raise "This should not be called directly, but through a subclass."

    def RegisterMimeType():
        raise "This should not be called directly, but through a subclass."
