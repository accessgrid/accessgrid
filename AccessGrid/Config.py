#-----------------------------------------------------------------------------
# Name:        Config.py
# Purpose:     Configuration objects for applications using the toolkit.
#              there are config objects for various sub-parts of the system.
# Created:     2003/05/06
# RCS-ID:      $Id: Config.py,v 1.33 2005-10-25 17:14:44 lefvert Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Config.py,v 1.33 2005-10-25 17:14:44 lefvert Exp $"

import os
import sys
import re
import struct
import time
import select
import socket
import shutil

from AccessGrid import Log
from AccessGrid.Version import GetVersion
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
    @type nodeConfigDir: string
    @ivar nodeConfigDir: the directory for system installed node configs
    @type servicesDir: string
    @ivar servicesDir: the directory for system installed services
    service packages for all users of this installation.
    @type configDir: string
    @ivar configDir: The directory for installation configuration.
    """
    theAGTkConfigInstance = None

    def __init__(self, initIfNeeded=0):
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
        self.nodeConfigDir = None
        self.appDir = None
        self.docDir = None
        
        # Now fill in data
        self._Initialize()
        
    def _Initialize(self):
        self.GetBaseDir()
        self.GetInstallDir()
        self.GetConfigDir()
        self.GetDocDir()
        self.GetLogDir()
        self.GetSharedAppDir()
        self.GetNodeServicesDir()
        self.GetNodeConfigDir()
        self.GetServicesDir()

    def _repr_(self):
        tmpstr = "Access Grid Toolkit Configuration:\n"
        tmpstr += "Version: %s\n" % self.GetVersion()
        tmpstr += "InstallDir: %s\n" % self.GetInstallDir()
        tmpstr += "DocDir: %s\n" % self.GetDocDir()
        tmpstr += "LogDir: %s\n" % self.GetLogDir()
        tmpstr += "ConfigDir: %s\n" % self.GetConfigDir()
        tmpstr += "SharedAppDir: %s\n" % self.GetSharedAppDir()
        tmpstr += "NodeServicesDir: %s\n" % self.GetNodeServicesDir()
        tmpstr += "ServicesDir: %s\n" % self.GetServicesDir()
    
        return tmpstr

    def __str__(self):
        return self._repr_()
    
    def GetVersion(self):
        return self.version

    def GetInstallDir(self):
        raise Exception, "This should not be called directly, but through a subclass."

    def GetDocDir(self):
        raise Exception, "This should not be called directly, but through a subclass."

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
 
        return str(self.logDir)

    def GetConfigDir(self):
        self.configDir = os.path.join(self.GetBaseDir(), "Config")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if self.configDir is not None and \
                   not os.path.exists(self.configDir):
                os.mkdir(self.configDir)

        if self.configDir is not None and not os.path.exists(self.configDir):
            raise IOError("AGTkConfig: config dir %s does not exist." % (self.configDir))

        return str(self.configDir)

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

        return str(self.appDir)

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

        return str(self.nodeServicesDir)

    def GetNodeConfigDir(self):
    
        if self.nodeConfigDir == None:
            ucd = self.GetConfigDir()
            self.nodeConfigDir = os.path.join(ucd, "nodeConfig")

        # Check dir and create it if needed.
        if self.initIfNeeded:
            if self.nodeConfigDir is not None and \
                   not os.path.exists(self.nodeConfigDir):
                try:
                    os.mkdir(self.nodeConfigDir)
                except:
                    log.exception("Couldn't make node config dir.")

        if not os.path.exists(self.nodeConfigDir):
            raise Exception, "AGTkConfig: node config dir does not exist: %s." % self.nodeConfigDir

        return str(self.nodeConfigDir)

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

        return str(self.servicesDir)


class UserConfig:
    """
    A user config object encapsulates all of the configuration data for
    a running instance of the Access Grid Toolkit software.

    @ivar profile: the user profile
    @ivar tempDir: a temporary directory for files for this user
    @ivar appDir: The directory for system installed shared applications
    @ivar nodeServicesDir: the directory for system installed node services
    @ivar servicesDir: the directory for system installed services
    @ivar configDir: The directory for installation configuration.

    @type profile: a Client Profile
    @type tempDir: string
    @type appDir: string
    @type nodeServicesDir: string
    @type localServicesDir: string
    @type nodeConfigDir: string
    @type servicesDir: string
    @type configDir: string
    """

    theUserConfigInstance = None

    def __init__(self, initIfNeeded):

        if UserConfig.theUserConfigInstance is not None:
            raise Exception, "Only one instance of User Config is allowed."

        UserConfig.theUserConfigInstance = self

        self.initIfNeeded = initIfNeeded

        self.configDir = None
        self.baseDir = None
        self.tempDir = None
        self.appDir = None
        self.sharedAppDir = None
        self.nodeServicesDir = None
        self.nodeConfigDir = None
        self.localServicesDir = None
        self.servicesDir = None
        self.profileFilename = None
        self.preferencesFilename = None
        self.logDir = None
        self.preferencesFilename = None

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
            self.GetNodeConfigDir()
        except:
            print "No Node Config Dir!"
        try:
            self.GetServicesDir()
        except:
            print "No Service Dir!"

        # Move old config files to new location.
        if self.initIfNeeded:
            self._Migrate()
   

    def _repr_(self):
        tmpstr = "User Configuration:\n"
        tmpstr += "Profile File: %s\n" % self.GetProfile()
        tmpstr += "Config Dir: %s\n" % self.GetConfigDir()
        tmpstr += "Temp Dir: %s\n" % self.GetTempDir()
        tmpstr += "Log Dir: %s\n" % self.GetLogDir()
        tmpstr += "Shared App Dir: %s\n" % self.GetSharedAppDir()
        tmpstr += "Node Services Dir: %s\n" % self.GetNodeServicesDir()
        tmpstr += "Services Dir: %s\n" % self.GetServicesDir()
        return tmpstr

    def __str__(self):
        return self._repr_()

    def _CopyFile(self, oldFile, newFile):
        '''
        If newFile does not exist, move oldFile to newFile.
        '''
        # Never overwrite new configs
        if not os.path.exists(newFile) and os.path.exists(oldFile):
            log.debug('copy %s to %s' %(oldFile, newFile))
            shutil.copyfile(oldFile, newFile)
            
    def _CopyDir(self, oldDir, newDir):
        '''
        if newDir does not exist, move oldDir to newDir.
        '''
        # Never overwrite new configs
        if not os.path.exists(newDir) and os.path.exists(oldDir):
            log.debug('copy %s to %s' %(oldDir, newDir))
            shutil.copytree(oldDir, newDir)

    def _Migrate(self):
        '''
        Make sure old info gets moved to new location.
        '''
        oldPath = os.path.join(self.baseDir, "profile")
        newPath = os.path.join(self.configDir, "profile")
        self._CopyFile(oldPath, newPath)

        oldPath = os.path.join(self.baseDir, "myVenues.txt")
        newPath = os.path.join(self.configDir, "myVenues.txt")
        self._CopyFile(oldPath, newPath)
                
        oldPath = os.path.join(self.baseDir, "certRepo")
        newPath = os.path.join(self.configDir, "certRepo")
        self._CopyDir(oldPath, newPath)

        oldPath = os.path.join(self.baseDir, "trustedCACerts")
        newPath = os.path.join(self.configDir, "trustedCACerts")
        self._CopyDir(oldPath, newPath)
        
        oldPath = os.path.join(self.baseDir, "personalDataStore")
        newPath = os.path.join(self.configDir, "personalDataStore")
        self._CopyDir(oldPath, newPath)
        
        oldPath = os.path.join(self.baseDir, "profileCache")
        newPath = os.path.join(self.configDir, "profileCache")
        self._CopyDir(oldPath, newPath)
        
        oldPath = os.path.join(self.baseDir, "nodeConfig")
        newPath = os.path.join(self.configDir, "nodeConfig")
        self._CopyDir(oldPath, newPath)
    
    def GetProfile(self):
        if self.profileFilename == None:
            self.profileFilename = os.path.join(self.GetConfigDir(), "profile")
            
        return self.profileFilename

    def GetPreferences(self):
        if self.preferencesFilename == None:
            self.preferencesFilename = os.path.join(self.GetConfigDir(),
                                                    "preferences")

        return self.preferencesFilename

    def GetBaseDir(self):
        raise Exception, "This should not be called directly, but through a subclass."

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

        return str(self.logDir)

    def GetTempDir(self):
        raise Exception, "This should not be called directly, but through a subclass."
    
    def GetConfigDir(self):
    
        if self.configDir == None:
            ucd = self.GetBaseDir()
            self.configDir = os.path.join(ucd, "Config")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if self.configDir is not None and \
                   not os.path.exists(self.configDir):
                try:
                    os.mkdir(self.configDir)
                except:
                    log.exception("Couldn't create user config dir")

        # Check the installation
        if self.configDir is not None and \
               not os.path.exists(self.configDir):
            raise Exception, "AGTkConfig: config dir does not exist %s."%self.configDir

        return str(self.configDir)
        

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

        return str(self.appDir)

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
        return str(self.nodeServicesDir)


    def GetLocalServicesDir(self):
        if self.localServicesDir == None:
            ucd = self.GetBaseDir()
            self.localServicesDir = os.path.join(ucd, "local_services")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if not os.path.exists(self.localServicesDir):
                os.mkdir(self.localServicesDir)

        if not os.path.exists(self.localServicesDir):
            raise Exception, "AGTkConfig: local services dir does not exist."

        return str(self.localServicesDir)

    def GetNodeConfigDir(self):
        if self.nodeConfigDir == None:
            ucd = self.GetConfigDir()
            self.nodeConfigDir = os.path.join(ucd, "nodeConfig")

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if not os.path.exists(self.nodeConfigDir):
                os.mkdir(self.nodeConfigDir)

        if not os.path.exists(self.nodeConfigDir):
            raise Exception, "AGTkConfig: node service dir does not exist."

        return str(self.nodeConfigDir)

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

        return str(self.servicesDir)

class SystemConfig:
    """
    The SystemConfig object encapsulates all system dependent
    configuration data, it should be extended to retrieve and store
    additional information as necessary.

    @ivar tempDir: the system temp directory.
    @type tempDir: string
    """

    theSystemConfigInstance = None

    def __init__(self):
        if SystemConfig.theSystemConfigInstance is not None:
            raise Exception, "Only one instance of SystemConfig is allowed."

        SystemConfig.theSystemConfigInstance = self
        
        self.tempDir = None
        self.hostname = None

    def _repr_(self):
        tmpstr = "System Configuration:\n"
        tmpstr += "Temp Dir: %s\n" % self.GetTempDir()
        tmpstr += "HTTP Proxy Settings: %s\n" % self.GetProxySettings()
        tmpstr += "F/S Free Space(/): %s\n" % self.GetFileSystemFreeSpace("/")
        tmpstr += "Username: %s\n" % self.GetUsername()
        tmpstr += "Local IP Address: %s\n" % self.GetLocalIPAddress()
        tmpstr += "Local Network Interfaces:\n"
        for i in self.EnumerateInterfaces():
            tmpstr += "\tName: %8s IP: %15s DNS: %s\n" % (i['name'], i['ip'],
                                                       i['dns'])
        return tmpstr

    def __str__(self):
        return self._repr_()
        
    def GetUsername(self):
        """
        Get the name of the user
        """
        raise Exception, "This should not be called directly, but through a subclass."

        
    def EnumerateInterfaces(self):
        """
        Enumerate network interfaces
        """
        raise Exception, "This should not be called directly, but through a subclass."
        
    
    def GetTempDir(self):
        """
        Get the path to the system temp directory.
        """
        raise Exception, "This should not be called directly, but through a subclass."
        
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

    def GetFileSystemFreeSpace(self, path):
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
            rtime = self._GetSNTPTime('ntp-1.accessgrid.org')
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

    def GetLocalIPAddress(self):
	#
	# Attempt to determine our local hostname based on the
	# network environment.
	#
	# This implementation reads the routing table for the default route.
	# We then look at the interface config for the interface that holds the default.
	#
	#
	# Linux routing table:
	# [olson@yips 0.0.0]$ netstat -rn
	#     Kernel IP routing table
	#     Destination     Gateway         Genmask         Flags   MSS Window  irtt Iface
	#     140.221.34.32   0.0.0.0         255.255.255.224 U         0 0          0 eth0
	#     169.254.0.0     0.0.0.0         255.255.0.0     U         0 0          0 eth0
	#     127.0.0.0       0.0.0.0         255.0.0.0       U         0 0          0 lo
	#     0.0.0.0         140.221.34.61   0.0.0.0         UG        0 0          0 eth0
	# 
	#     Mac routing table:
	# 
	#     bash-2.05a$ netstat -rn
	#     Routing tables
	# 
	#  Internet:
	#     Destination        Gateway            Flags    Refs      Use  Netif Expire
	#     default            140.221.11.253     UGSc       12      120    en0
	#     127.0.0.1          127.0.0.1          UH         16  8415486    lo0
	#     140.221.8/22       link#4             UCS        12        0    en0
	#     140.221.8.78       0:6:5b:f:51:c4     UHLW        0      183    en0    408
	#     140.221.8.191      0:3:93:84:ab:e8    UHLW        0       92    en0    622
	#     140.221.8.198      0:e0:98:8e:36:e2   UHLW        0        5    en0    691
	#     140.221.9.6        0:6:5b:f:51:d6     UHLW        1       63    en0   1197
	#     140.221.10.135     0:d0:59:34:26:34   UHLW        2     2134    en0   1199
	#     140.221.10.152     0:30:1b:b0:ec:dd   UHLW        1      137    en0   1122
	#     140.221.10.153     127.0.0.1          UHS         0        0    lo0
	#     140.221.11.37      0:9:6b:53:4e:4b    UHLW        1      624    en0   1136
	#     140.221.11.103     0:30:48:22:59:e6   UHLW        3      973    en0   1016
	#     140.221.11.224     0:a:95:6f:7:10     UHLW        1        1    en0    605
	#     140.221.11.237     0:1:30:b8:80:c0    UHLW        0        0    en0   1158
	#     140.221.11.250     0:1:30:3:1:0       UHLW        0        0    en0   1141
	#     140.221.11.253     0:d0:3:e:70:a      UHLW       13        0    en0   1199
	#     169.254            link#4             UCS         0        0    en0
	# 
	#     Internet6:
	#     Destination                       Gateway                       Flags      Netif Expire
	#                                                                     UH          lo0
	#     fe80::%lo0/64                                                   Uc          lo0
	#                                       link#1                        UHL         lo0
	#     fe80::%en0/64                     link#4                        UC          en0
	#     0:a:95:a8:26:68               UHL         lo0
	#     ff01::/32                                                       U           lo0
	#     ff02::%lo0/32                                                   UC          lo0
	#     ff02::%en0/32                     link#4                        UC          en0

	try:
	    fh = os.popen("netstat -rn", "r")
	except:
	    return "127.0.0.1"

	interface_name = None
	for l in fh:
	    cols = l.strip().split()

	    if len(cols) > 0 and (cols[0] == "default" or cols[0] == "0.0.0.0"):
		interface_name = cols[-1]
		break
	    
	fh.close()
	
	# print "Default route on ", interface_name

	#
	# Find ifconfig.
	#

	ifconfig = None

	path = os.environ["PATH"].split(":")
	path.extend(["/sbin", "/usr/sbin"])
	for p in path: 
	    i = os.path.join(p, "ifconfig")
	    if os.access(i, os.X_OK):
		ifconfig = i
		break

	if ifconfig is None:
	    print >> sys.stderr, "Ifconfig not found"
	    return "localhost"

	# print >> sys.stderr, "found ifconfig ", ifconfig

	try:
	    fh = os.popen(ifconfig+ " " + interface_name, "r")
	except:
	    print >> sys.stderr, "Could not run ", ifconfig
	    return "localhost"

	ip = None

	linux_re = re.compile("inet\s+addr:(\d+\.\d+\.\d+\.\d+)\s+")
	mac_re = re.compile("inet\s+(\d+\.\d+\.\d+\.\d+)\s+")

	for l in fh:
	    #
	    # Mac:
	    #         inet 140.221.10.153 netmask 0xfffffc00 broadcast 140.221.11.255
	    # Linux:
	    #           inet addr:140.221.34.37  Bcast:140.221.34.63  Mask:255.255.255.224
	    #

	    l = l.strip()

	    m = linux_re.search(l)
	    if m:
		#
		# Linux hit.
		#
		ip = m.group(1)
		break

	    m = mac_re.search(l)

	    if m:
		#
		# Mac hit.
		#
		ip = m.group(1)
		break
	fh.close()

	if ip is None:
	    print >> sys.stderr, "Didn't find an IP"
	    return "127.0.0.1"

	return ip

    def AppFirewallConfig(self, path, enableFlag):
        """
        This call enables or disables an applications access via a firewall.
        """
        err_str = "This should not be called directly, but through a subclass."
        raise Exception(err_str)

class MimeConfig:
    """
    The MimeConfig object encapsulates in single object the management
    of mime types. This provides a cross platform solution so the AGTk
    can leverage legacy configuration and applications for data
    viewing.
    """
    theMimeConfigInstance = None

    def __init__(self):
        MimeConfig.theMimeConfigInstance = self
    
    def GetMimeType(self,extension = None):
        raise Exception, "This should not be called directly, but through a subclass."

    def GetMimeCommands(self,mimeType = None, ext = None):
        raise Exception, "This should not be called directly, but through a subclass."

    def RegisterMimeType(self, mimeType, extension, fileType, description,
                         cmds):
        raise Exception, "This should not be called directly, but through a subclass."
