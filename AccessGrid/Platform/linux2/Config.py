#-----------------------------------------------------------------------------
# Name:        Config.py
# Purpose:     Configuration objects for applications using the toolkit.
#              there are config objects for various sub-parts of the system.
# Created:     2003/05/06
# RCS-ID:      $Id: Config.py,v 1.3 2004-03-12 19:59:24 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Config.py,v 1.3 2004-03-12 19:59:24 eolson Exp $"

import os
import mimetypes
import mailcap
import socket

from pyGlobus import utilc

from AccessGrid import Log
import AccessGrid.Config

from AccessGrid.Platform import AGTK_USER, AGTK_INSTALL, AGTK_LOCATION
from AccessGrid.Version import GetVersion

log = Log.GetLogger(Log.Platform)
Log.SetDefaultLevel(Log.Platform, Log.INFO)

class AGTkConfig(AccessGrid.Config.AGTkConfig):
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
    theAGTkConfigInstance = None

    AGTkBasePath = "/etc/AccessGrid"

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
        if self.installBase == None:
            try:
                self.installBase = os.environ[AGTK_INSTALL]
            except:
                self.installBase = "/usr/bin"

        # remove trailing "\bin" if it's there
        if self.installBase.endswith("bin"):
            self.installBase = os.path.join(os.path.split(self.installBase)[:-1])[0]
            
        # Check the installation
        if not os.path.exists(self.installBase):
            raise Exception, "AGTkConfig: installation base does not exist."
        
        return self.installBase
        
    def GetConfigDir(self):
        try:
            self.configDir = os.environ[AGTK_LOCATION]
        except:
            self.configDir = AGTkBasePath
            
        return self.configDir

    def GetInstallDir(self):
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
            
        try:
            self.docDir = os.environ[AGTK_INSTALL]
        except:
            self.docDir = os.path.join(self.installBase, "share", "doc",
                                       "AccessGrid", "Documentation")

        # Check the installation
        if self.docDir is not None and not os.path.exists(self.docDir):
            raise Exception, "AGTkConfig: doc dir does not exist."

        return self.docDir

    def GetPkgCacheDir(self):
        if self.pkgCacheDir == None:
            ucd = self.GetConfigDir()
            self.pkgCacheDir = os.path.join(ucd, "PackageCache")

        # Check the installation
        if self.pkgCacheDir is not None and not os.path.exists(self.pkgCacheDir):
            raise Exception, "AGTkConfig: pkg cache dir does not exist."            
        return self.pkgCacheDir

    def GetSharedAppDir(self):
        if self.appDir == None:
            ucd = self.GetConfigDir()
            self.appDir = os.path.join(ucd, "SharedApplications")

        # Check the installation
        if self.appDir is not None and not os.path.exists(self.appDir):
            raise Exception, "AGTkConfig: app dir does not exist."

        return self.appDir

    def GetNodeServicesDir(self):
        if self.nodeServicesDir == None:
            ucd = self.GetConfigDir()
            self.nodeServicesDir = os.path.join(ucd, "NodeServices")

        # Check the installation
        if self.nodeServicesDir is not None and not os.path.exists(self.nodeServicesDir):
            raise Exception, "AGTkConfig: node service dir does not exist."

        return self.nodeServicesDir

    def GetServicesDir(self):
        if self.servicesDir == None:
            ucd = self.GetConfigDir()
            self.servicesDir = os.path.join(ucd, "Services")

        # Check the installation
        if self.servicesDir is not None and not os.path.exists(self.servicesDir):
            raise Exception, "AGTkConfig: services dir does not exist."

        return self.servicesDir

class GlobusConfig(AccessGrid.Config.GlobusConfig):
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
        
    def _Initialize(self):
        """
        This is a placeholder for doing per user initialization that
        should happen the first time the user runs any toolkit
        application. For now, I'm putting globus registry crud in
        here, later there might be other stuff.
        """
        if os.environ.has_key('GLOBUS_LOCATION'):
            self.location = os.environ['GLOBUS_LOCATION']

        if os.environ.has_key('GLOBUS_HOSTNAME'):
            self.hostname = os.environ['GLOBUS_HOSTNAME']

        if os.environ.has_key('X509_CERT_DIR'):
            self.caCertDir = os.environ['X509_CERT_DIR']
    
        if os.environ.has_key('X509_USER_PROXY'):
            self.proxyFileName = os.environ['X509_USER_PROXY']
    
        if os.environ.has_key('X509_USER_CERT'):
            self.certFileName = os.environ['X509_USER_CERT']
    
        if os.environ.has_key('X509_USER_KEY'):
            self.keyFileName = os.environ['X509_USER_KEY']
    
    def GetLocation(self):
        if self.location is not None and not os.path.exists(self.location):
            raise Exception, "GlobusConfig: Globus directory does not exist."

        return self.location

    def GetCACertDir(self):
        if self.caCertDir is not None and not os.path.exists(self.caCertDir):
            raise Exception, "GlobusConfig: CA Certificate dir does not exist."

        return self.caCertDir
    
    def GetProxyFileName(self):
        if self.proxyFileName is not None and not os.path.exists(self.proxyFileName):
            raise Exception, "GlobusConfig: proxy file does not exist."

        return self.proxyFileName
    
    def GetCertFileName(self):
        if self.certFileName is not None and not os.path.exists(self.certFileName):
            raise Exception, "GlobusConfig: certificate file does not exist."

        return self.certFileName

    def GetKeyFileName(self):
        if self.keyFileName is not None and not os.path.exists(self.keyFileName):
            raise Exception, "GlobusConfig: key file does not exist."

        return self.keyFileName

class UserConfig(AccessGrid.Config.UserConfig):
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
            print "No Package Cache!"
            
        try:
            self.GetSharedAppDir()
        except:
            print "No Shared App Dir!"
        try:
            self.GetNodeServicesDir()
        except:
            print "No Node Services Dir!"
        try:
            self.GetServicesDir()
        except:
            print "No Services Dir!"

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
        """
    rtpDefaultsText="*rtpName: %s\n*rtpEmail: %s\n*rtpLoc: %s\n*rtpPhone: \
                     %s\n*rtpNote: %s\n"
    rtpDefaultsFile=open( os.path.join(os.environ["HOME"], ".RTPdefaults"),"w")
    rtpDefaultsFile.write( rtpDefaultsText % ( profile.name,
    profile.email,
    profile.location,
    profile.phoneNumber,
    profile.publicId ) )
    rtpDefaultsFile.close()
        """
        pass

    def GetConfigDir(self):
        global AGTK_USER

        try:
            self.configDir = os.environ[AGTK_USER]
        except:
            self.configDir = os.path.join(os.environ["HOME"],".AccessGrid")

        return self.configDir

    def GetTempDir(self):
        if self.tempDir == None:
            self.tempDir = "/tmp"

        return self.tempDir
    
    def GetPkgCacheDir(self):
        if self.pkgCacheDir == None:
            ucd = self.GetConfigDir()
            self.pkgCacheDir = os.path.join(ucd, "PackageCache")

        # check to make it if needed
        return self.appDir

    def GetSharedAppDir(self):
        if self.appDir == None:
            ucd = self.GetConfigDir()
            self.appDir = os.path.join(ucd, "SharedApplications")

        # check to make it if needed
        return self.appDir

    def GetNodeServicesDir(self):
        if self.nodeServicesDir == None:
            ucd = self.GetConfigDir()
            self.nodeServicesDir = os.path.join(ucd, "NodeServices")

        # check to make it if needed
        return self.nodeServicesDir

    def GetServicesDir(self):
        if self.servicesDir == None:
            ucd = self.GetConfigDir()
            self.servicesDir = os.path.join(ucd, "Services")

        # check to make it if needed
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
            self.tempDir = "/tmp"
            
        return self.tempDir
        
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
        If the system has a proxy server defined for use, return its
        address.  The return value is actually a list of tuples
        (server address, enabled).
        """
        proxies = []
        return proxies

    def GetFileSystemFreeSpace(self, path):
        """
        Determine the amount of free space available in the filesystem
        containing <path>.
        
        Returns a value in bytes.
        """
        # f_bsize is the "preferred filesystem block size"
        # f_frsize is the "fundamental filesystem block size"
        # f_bavail is the number of blocks free
        if hasattr(os, "statvfs"):
            x = os.statvfs(path)

            # On some older linux systems, f_frsize is 0. Use f_bsize
            # instead then.
            # cf http://www.uwsg.iu.edu/hypermail/linux/kernel/9907.3/0019.html
            if x.f_frsize == 0:
                blockSize = x.f_bsize
            else:
                blockSize = x.f_frsize

            freeBytes = blockSize * x.f_bavail
        else:
            freeBytes = None

        return freeBytes

    def GetUsername(self):
        return getpass.getuser()
    
    def EnumerateInterfaces(self):
        """
        Enumerate the interfaces present on a windows box.
        
        Run ipconfig /all
        """
        adapters = []
        return adapters

    def GetDefaultRouteIP(self):
        """
        Retrieve the IP address of the interface that the
        default route points to.
        """
        return None
    
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
        """
        pass
    
    def GetMimeCommands(self, mimeType = None, ext = None):
        """
        """
        cdict = dict()
        view = 'view'
        
        if mimeType == None:
            mimeType = GetMimeType(extension = ext)
            
        # We only care about mapping view to Open
        caps = mailcap.getcaps()

        # This always returns a tuple, so this should be safe
        if mimeType != None:
            match = mailcap.findmatch(caps, mimeType, view)[1]
        else:
            return cdict

        if match != None:
            cdict['Open'] = match[view]

        return cdict

    def GetMimeType(self, extension = None):
        fauxFn = ".".join(["Faux", extension])
        mimetypes.init()
        
        # This is always a tuple so this is Ok
        mimeType = mimetypes.guess_type(fauxFn)[0]
        
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
