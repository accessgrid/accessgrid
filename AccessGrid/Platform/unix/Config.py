#-----------------------------------------------------------------------------
# Name:        Config.py
# Purpose:     Configuration objects for applications using the toolkit.
#              there are config objects for various sub-parts of the system.
# Created:     2003/05/06
# RCS-ID:      $Id: Config.py,v 1.24 2004-05-06 20:26:30 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Config.py,v 1.24 2004-05-06 20:26:30 eolson Exp $"

import os
import mimetypes
import mailcap
import socket
import getpass

from pyGlobus import security

from AccessGrid import Log
import AccessGrid.Config

from AccessGrid.Platform import AGTK_USER, AGTK_LOCATION
from AccessGrid.Version import GetVersion
from AccessGrid.Types import AGVideoResource

log = Log.GetLogger(Log.Platform)
Log.SetDefaultLevel(Log.Platform, Log.INFO)

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
        self.GetSharedAppDir()
        self.GetNodeServicesDir()
        self.GetServicesDir()
        
    def GetVersion(self):
        return self.version

    def GetBaseDir(self):
        if self.installBase == None:
            try:
                self.installBase = os.environ[AGTK_LOCATION]
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
            basePath = os.environ[AGTK_LOCATION]
            self.configDir = os.path.join(basePath, "Config")
        except:
            self.configDir = os.path.join(self.AGTkBasePath, "Config")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if self.configDir is not None and \
                   not os.path.exists(self.configDir):
                os.mkdir(self.configDir)

        if self.configDir is not None and not os.path.exists(self.configDir):
            raise IOError("AGTkConfig: config dir %s does not exist." % (self.configDir))

        return self.configDir

    GetInstallDir = GetBaseDir

    def GetBinDir(self):
        if self.installBase == None:
            self.GetBaseDir()

        self.installDir = os.path.join(self.installBase, "bin")

        # Check the installation
        if self.installDir is not None and not os.path.exists(self.installDir):
            raise Exception, "AGTkConfig: install dir does not exist."

        return self.installDir

    def GetDocDir(self):
        if self.installBase == None:
            self.GetBaseDir()
            
        self.docDir = os.path.join(self.installBase, "share", "doc",
                                       "AccessGrid", "Documentation")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if self.docDir is not None and \
                   not os.path.exists(self.docDir):
                if os.path.exists(self.installBase):
                    os.makedirs(self.docDir)

        # Check the installation
        if self.docDir is not None and not os.path.exists(self.docDir):
            raise Exception, "AGTkConfig: doc dir does not exist."

        return self.docDir

    def GetLogDir(self):
        if self.logDir == None:
            ucd = self.GetConfigDir()
            self.logDir = os.path.join(ucd, "Logs")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if self.logDir is not None and \
                   not os.path.exists(self.logDir):
                os.mkdir(self.logDir)


        # Check the installation
        if self.logDir is not None and \
               not os.path.exists(self.logDir):
            raise Exception, "AGTkConfig: log dir does not exist."            
 
        return self.logDir
    
    def GetSharedAppDir(self):
        if self.appDir == None:
            ucd = self.GetConfigDir()
            self.appDir = os.path.join(ucd, "SharedApplications")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if not os.path.exists(self.appDir):
                os.mkdir(self.appDir)

        if not os.path.exists(self.appDir):
            raise Exception, "AGTkConfig: app dir does not exist."

        return self.appDir

    def GetNodeServicesDir(self):
        if self.nodeServicesDir == None:
            ucd = self.GetConfigDir()
            self.nodeServicesDir = os.path.join(ucd, "NodeServices")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if not os.path.exists(self.nodeServicesDir):
                os.mkdir(self.nodeServicesDir)

        if not os.path.exists(self.nodeServicesDir):
            raise Exception, "AGTkConfig: node service dir does not exist."

        return self.nodeServicesDir

    def GetServicesDir(self):
        if self.servicesDir == None:
            ucd = self.GetConfigDir()
            self.servicesDir = os.path.join(ucd, "Services")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if not os.path.exists(self.servicesDir):
                os.mkdir(self.servicesDir)

        if not os.path.exists(self.servicesDir):
            raise Exception, "AGTkConfig: services dir does not exist."

        return self.servicesDir

class GlobusConfig(AccessGrid.Config.GlobusConfig):
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
        self.location = None
        self.serverFlag = None
        
        # First, get the paths to stuff we need
        uappdata = os.environ['HOME']
        agtkdata = AGTkConfig.instance().GetConfigDir()
        
        self.installdir = AGTkConfig.instance().GetInstallDir()
            
        self.distKeyFileName = os.path.join(uappdata, ".globus", "userkey.pem")
        self.distCertFileName = os.path.join(uappdata, ".globus", "usercert.pem")

        self.proxyFileName = os.path.join(UserConfig.instance().GetTempDir(),
                                          "x509up_u%s" %(os.getuid()))
        self.distCACertDir = os.path.join(agtkdata, "CAcertificates")

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
        else:
            if self.initIfNeeded:
                self.SetLocation(self.installdir)
                
        if os.environ.has_key('GLOBUS_HOSTNAME'):
            self.hostname = os.environ['GLOBUS_HOSTNAME']
	    print "<<< set hostname to ", self.hostname
        else:
	    print "<<< need to compute hostname ", self.initIfNeeded
            if self.initIfNeeded:
		print "<<< Init hostname"
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

        UserConfig.theUserConfigInstance = self

        self.initIfNeeded = initIfNeeded
        
        self.configDir = None
        self.tempDir = None
        self.appDir = None
        self.sharedAppDir = None
        self.nodeServicesDir = None
        self.servicesDir = None
        self.profileFilename = None
        self.logDir = None
        
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
            print "No Shared App Dir!"
        try:
            self.GetNodeServicesDir()
        except:
            print "No Node Service Dir!"
        try:
            self.GetServicesDir()
        except:
            print "No Service Dir!"

    def GetProfile(self):
        if self.profileFilename == None:
            self.profileFilename = os.path.join(self.GetConfigDir(), "profile")
            
        return self.profileFilename

    def GetConfigDir(self):
        global AGTK_USER

        try:
            self.configDir = os.environ[AGTK_USER]
        except:
            self.configDir = os.path.join(os.environ["HOME"],".AccessGrid")

        try:
            if not os.path.exists(self.configDir):
                os.mkdir(self.configDir)
        except:
            log.exception("Can not create config directory %s", self.configDir)
            raise

        return self.configDir

    def GetTempDir(self):
        if self.tempDir == None:
            self.tempDir = "/tmp"

        if not os.access(self.tempDir, os.W_OK):
            log.error("UserConfig configuration: TempDir %s is not writable", self.tempDir)

        return self.tempDir
    
    def GetLogDir(self):
        if self.logDir == None:
            ucd = self.GetConfigDir()
            self.logDir = os.path.join(ucd, "Logs")

        # check to make it if needed
        if self.initIfNeeded:
            if not os.path.exists(self.logDir):
                os.mkdir(self.logDir)

        if not os.path.exists(self.logDir):
            raise Exception, "AGTkConfig: log dir does not exist."

        return self.logDir

    def GetSharedAppDir(self):
        if self.appDir == None:
            ucd = self.GetConfigDir()
            self.appDir = os.path.join(ucd, "SharedApplications")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if not os.path.exists(self.appDir):
                os.mkdir(self.appDir)

        if not os.path.exists(self.appDir):
            raise Exception, "AGTkConfig: app dir does not exist."

        return self.appDir

    def GetNodeServicesDir(self):
        if self.nodeServicesDir == None:
            ucd = self.GetConfigDir()
            self.nodeServicesDir = os.path.join(ucd, "NodeService")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if not os.path.exists(self.nodeServicesDir):
                os.mkdir(self.nodeServicesDir)

        if not os.path.exists(self.nodeServicesDir):
            raise Exception, "AGTkConfig: node service dir does not exist."

        return self.nodeServicesDir

    def GetServicesDir(self):
        if self.servicesDir == None:
            ucd = self.GetConfigDir()
            self.servicesDir = os.path.join(ucd, "Services")

        # check to make it if needed
        return self.servicesDir

    def SetRtpDefaults(self, profile ):
        """
        Set registry values used by vic and rat for identification
        """
        #
        # Write the rtp defaults file
        #
        rtpDefaultsText="*rtpName: %s\n*rtpEmail: %s\n*rtpLoc: %s\n*rtpPhone: \
                         %s\n*rtpNote: %s\n"
        rtpDefaultsFile=open( os.path.join(os.environ["HOME"], ".RTPdefaults"),"w")
        rtpDefaultsFile.write( rtpDefaultsText % ( profile.name,
        profile.email,
        profile.location,
        profile.phoneNumber,
        profile.publicId ) )
        rtpDefaultsFile.close()

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
        
    def GetResources(self):
    
        deviceList = dict()
        
        videodevpath = '/proc/video/dev'
        v4lctlexe = '/usr/bin/v4lctl'
        
        if os.path.exists(videodevpath):
            # Get list of devices
            cmd = "ls /proc/video/dev | grep video"
            fh = os.popen(cmd,'r')
            for line in fh.readlines():
                device = os.path.join('/dev',line.strip())
                deviceList[device] = None
            fh.close()

            # Determine ports for devices
            if os.path.exists(v4lctlexe):
                portString = ""
                for d in deviceList.keys():
                    cmd = "v4lctl list -c %s" % d
                    fh = os.popen(cmd)
                    for line in fh.readlines():
                        if line.startswith('input'):
                            portString = line.split('|')[-1]
                            deviceList[d] = portString.strip()
                            break
            else:
                log.info("%s not found; can't get ports", v4lctlexe)
        else:
            log.info("%s does not exist; no video devices detected",
                     videodevpath)
        

        # Force x11 onto the list
        deviceList['x11'] = 'x11'

        # Create resource objects
        resourceList = list()
        for device,portString in deviceList.items():
            r = AGVideoResource('video', device, 'producer',
                                portString.split())
            resourceList.append(r)
        
        return resourceList

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

        Written with this use case example:
        RegisterMimeType("application/x-ag-pkg", ".agpkg", "agpkg file", "Access Grid Package", ["agpm.py", "/usr/bin/agpm.py --wait-for-input", ""])
        
        ----
        """
        # Temporarily handle one command until code is added for multiple commands.
        cmd = cmds[0]

        short_extension = ""
        if len(extension) > 0:
            # remove the "." from the front
            short_extension = extension[1:]
        homedir = os.environ['HOME']

        # --- .DESKTOP FILES BASE INFORMATION --- (KDE)

        # User
        kdeMimeInfo = """[Desktop Entry]
Version=%s
Encoding=UTF-8
Hidden=false
Icon=ag.ico
Type=MimeType
Patterns=%s
MimeType=%s
Comment=%s
        """ % (str(GetVersion()), "*" + extension, mimeType, description) 
        #   ("2.2", "*.agpkg", "application/x-ag-pkg", "Access Grid Package")

        kdeAppInfo="""[Desktop Entry]
Version=%s
Encoding=UTF-8
MultipleArgs=false
Terminal=1
Icon=ag.ico
Exec=%s
Type=Application
MimeType=%s
Name=%s
Comment=%s
        """ % (str(GetVersion()), cmd[1], mimeType, cmd[0], cmd[2])
        #    ("2.2", "/usr/bin/agpm.py", "application/x-ag-pkg", "Access Grid Package Manager" or "agpm.py", comment)


        # --- GNOME BASE INFORMATION ---

        defAppId = cmd[0] # use verb for the defaultAppId

        gnomeAppInfo="""
%s
        requires_terminal=true
        command=%s
        can_open_multiple_files=false
        name=%s
        mime_types=%s
        """ % (defAppId, cmd[1], defAppId, mimeType)
        #  %("agpm.py", "/usr/bin/agpm.py", "agpm.py", application/x-ag-pkg")

        gnomeKeyInfo = """
%s
	default_application_id=%s
        category=Misc
        default_component_iid=
        description=%s
        icon_filename=
        default_action_type=application
        short_list_application_user_removals=
        short_list_application_user_additions=%s
        use_category_default=no
        """ % (mimeType, defAppId, description, defAppId)
        #     ("x-ag-pkg", "agpm.py", "Access Grid Package", "agpm.py")

        gnomeMimeInfo="%s\n        ext: %s\n" % (mimeType, short_extension)  
        #                                       ("x-ag-pkg", "agpkg")


        # --- KDE USER REGISTRATION ---

        # First find the user and system app paths.
        # query them since applnk-redhat can't work for everybody.
        f = os.popen("kde-config --path apps")
        result = f.read()
        f.close()
        pathList = result.split(":")
        kdeSystemApps = ""
        kdeUserApps = ""
        # if kde-config failed, the paths should stay == ""
        for path in pathList:
            if path.find(homedir) != -1:
                kdeUserApps = path # expecting /home/user/.kde/share/applnk[-redhat]
            elif path.find("kde") != -1:  # expecting /var/lib/menu/kde/Applications/
                kdeSystemApps = path  # Unused, sym links here from another dir.

        # Find the user and system mime paths.
        f = os.popen("kde-config --path mime")
        result = f.read()
        f.close()
        pathList = result.split(":")
        kdeSystemMime = ""
        kdeUserMime = ""
        # if kde-config failed, the paths should stay == ""
        for path in pathList:
            if path.find(homedir) != -1:
                kdeUserMime = path # expecting /home/user/.kde/share/applnk[-redhat]
            elif path.find("mimelnk") != -1:  # expecting /usr/share/mimelnk/
                kdeSystemMime = path

        userMimeFile = os.path.join(kdeUserMime, "agpkg.desktop")
        userAppFile = os.path.join(kdeUserApps, "agpm.desktop")

        # Copy KDE files into place
        if len(userMimeFile) > 0 and os.path.exists(userMimeFile):
            mimeFd = open(userMimeFile, "w")
            mimeFd.write(kdeMimeInfo)
            mimeFd.close()

        if len(userAppFile) > 0 and os.path.exists(kdeUserApps):
            appFd = open(userAppFile, "w")
            appFd.write(kdeAppInfo)
            appFd.close()


        # --- GNOME USER REGISTRATION ---

        # if gnome files exist, register with them.
        gnomeDir = os.path.join(homedir, ".gnome")
        gnomeAppDir = os.path.join(homedir, ".gnome", "application-info")
        gnomeMimeDir = os.path.join(homedir, ".gnome", "mime-info")
        gnomeAppFile = os.path.join(gnomeAppDir, "accessgrid.applications")
        gnomeKeysFile = os.path.join(gnomeMimeDir, "accessgrid.keys")
        gnomeMimeFile = os.path.join(gnomeMimeDir, "accessgrid.mime")
        if os.path.exists(gnomeAppDir):
            log.info("registering file type " + extension + " with gnome")

            f = open(gnomeAppFile, "w")
            f.write(gnomeAppInfo)
            f.close()

            f = open(gnomeKeysFile, "w")
            f.write(gnomeKeyInfo)
            f.close()

            f = open(gnomeMimeFile, "w")
            f.write(gnomeMimeInfo)
            f.close()

        else:
            log.info("gnome directory " + gnomeAppDir + " not found, not registering file type " + extension + " with gnome")


        """
        registerSystem = 1
        if registerSystem:

        # --- KDE SYSTEM REGISTRATION ---

            # general paths
            genSystemAppDir = "/usr/share/applications"
            genSystemAppFile = os.path.join(genSystemAppDir, "agpm.desktop")
            genSystemMimeDir = "/usr/share/mimelnk/application"
            genSystemMimeFile = os.path.join(genSystemMimeDir, "agpkg.desktop")

            if len(genSystemAppFile) > 0 and os.path.exists(genSystemAppDir):
                appFd = open(genSystemAppFile, "w" )
                appFd.write(kdeAppInfo)
                appFd.close()

            if len(genSystemMimeFile) > 0 and os.path.exists(genSystemMimeDir):
                mimeFd = open(genSystemMimeFile, "w" )
                mimeFd.write(kdeMimeInfo)
                mimeFd.close()

        # --- GNOME SYSTEM REGISTRATION ---

            gnomeSystemMimeDir = "/usr/share/mime-info"
            gnomeSystemMimeFile = os.path.join(gnomeSystemMimeDir, "accessgrid.mime")
            gnomeSystemKeysFile = os.path.join(gnomeSystemMimeDir, "accessgrid.keys")
            gnomeSystemAppDir = "/usr/share/application-registry"
            gnomeSystemAppFile = os.path.join(gnomeSystemAppDir, "accessgrid.applications")
            if os.path.exists(gnomeSystemMimeDir):
                # Keys
                f = open(gnomeSystemKeysFile, "w")
                f.write(gnomeKeyInfo)
                f.close()
                # Mime
                f = open(gnomeSystemMimeFile, "w")
                f.write(gnomeMimeInfo)
                f.close()
            else:
                log.info("gnomeSystemMimeDir does not exist: " + gnomeSystemMimeDir)
                print "ARG"
            if os.path.exists(gnomeSystemAppDir):
                # Application
                f = open(gnomeSystemAppFile, "w")
                f.write(gnomeAppInfo)
                f.close()
            else:
                log.info("gnomeSystemAppDir does not exist: " + gnomeSystemAppDir)
        """
    
    def GetMimeCommands(self, mimeType = None, ext = None):
        """
        """
        cdict = dict()
        view = 'view'
        
        if mimeType == None:
            mimeType = self.GetMimeType(extension = ext)
            
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

    print "User Configuration:"
    try:
        userConf = UserConfig.instance(0)
    except Exception, e:
        print "Error trying to retrieve the User Configuration:\n", e
        userConf = None

    if userConf is not None:
        try:
            print "\tProfile: ", userConf.GetProfile()
            print "\tConfiguration Base: ", userConf.GetBaseDir()
            print "\tConfiguration Dir: ", userConf.GetConfigDir()
            print "\tLog Dir: ", userConf.GetLogDir()
            print "\tTemp Dir: ", userConf.GetTempDir()
            print "\tShared App Dir: ", userConf.GetSharedAppDir()
            print "\tNode Service Dir: ", userConf.GetNodeServicesDir()
            print "\tService Dir: ", userConf.GetServicesDir()
        except Exception, e:
            print "Error trying to retrieve the user Configuration:\n", e
    else:
        print "The user config object is: ", userConf
