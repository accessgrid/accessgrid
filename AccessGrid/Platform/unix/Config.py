#-----------------------------------------------------------------------------
# Name:        Config.py
# Purpose:     Configuration objects for applications using the toolkit.
#              there are config objects for various sub-parts of the system.
# Created:     2003/05/06
# RCS-ID:      $Id: Config.py,v 1.81 2007-07-16 19:14:04 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Config.py,v 1.81 2007-07-16 19:14:04 turam Exp $"

import sys
import os
import mimetypes
import mailcap
import socket
import getpass
import shutil
import resource


from AccessGrid import Log
from AccessGrid import Config

from AccessGrid.Platform import AGTK_USER, AGTK_LOCATION, IsOSX, IsLinux, IsFreeBSD
from AccessGrid.Version import GetVersion

if IsLinux() or IsFreeBSD():
    import fcntl
    import struct
    import glob


log = Log.GetLogger(Log.Platform)
Log.SetDefaultLevel(Log.Platform, Log.INFO)

class AGTkConfig(Config.AGTkConfig):
    """
    This class encapsulates a system configuration for the Access Grid
    Toolkit. This object provides primarily read-only access to configuration
    data that is created when the toolkit is installed.

    """
    if IsFreeBSD():
        AGTkBasePath = "/usr/local/etc/AccessGrid3"
    else:
        AGTkBasePath = "/etc/AccessGrid3"

    def instance(initIfNeeded=0):
        if AGTkConfig.theAGTkConfigInstance == None:
            AGTkConfig(initIfNeeded)

        return AGTkConfig.theAGTkConfigInstance

    instance = staticmethod(instance)

    def GetBaseDir(self):
        if self.installBase == None:
            try:
                self.installBase = os.environ[AGTK_LOCATION]
            except:
                self.installBase = self.AGTkBasePath

        # remove trailing "\bin" if it's there
        if self.installBase.endswith("bin"):
            self.installBase = os.path.join(os.path.split(self.installBase)[:-1])[0]
            
        # Check the installation
        if not os.path.exists(self.installBase):
            raise Exception, "AGTkConfig: installation base does not exist."
        
        return self.installBase
        
    def GetInstallDir(self):
        try:
            self.installDir = os.environ[AGTK_LOCATION]
        except:
            if IsFreeBSD():
                self.installDir = "/usr/local"
            else:
                self.installDir = "/usr"

        # Check dir and make it if needed.
        if self.initIfNeeded:
            if self.installDir is not None and \
                   not os.path.exists(self.installDir):
                os.mkdir(self.installDir)

        # Check the installation
        if self.installDir is not None and not os.path.exists(self.installDir):
            raise Exception, "AGTkConfig: install dir does not exist."

        return self.installDir 

    def GetBinDir(self):
        binDir = os.path.join(self.GetInstallDir(), "bin")
        return binDir

    def GetDocDir(self):
        if sys.platform == 'darwin':
            self.docDir = os.path.join(self.GetInstallDir(), "doc")
        else:
            self.docDir = os.path.join(self.GetInstallDir(), "share", "doc",
                                       "AccessGrid-" + str(GetVersion()))
    #    # Check dir and make it if needed.
    #    if self.initIfNeeded:
    #        if self.docDir is not None and \
    #               not os.path.exists(self.docDir):
    #            if os.path.exists(self.GetBaseDir()):
    #                os.makedirs(self.docDir)

    #    # Check the installation
    #    #if self.docDir is not None and not os.path.exists(self.docDir):
    #    #    raise Exception, "AGTkConfig: doc dir does not exist."
    #
        return self.docDir

class UserConfig(Config.UserConfig):
    """
    A user config object encapsulates all of the configuration data for
    a running instance of the Access Grid Toolkit software.

    @ivar profileFilename: the user profile
    @type profileFilename: the filename of the client profile
    """

    def instance(initIfNeeded=0):
        if UserConfig.theUserConfigInstance == None:
            UserConfig(initIfNeeded)

        return UserConfig.theUserConfigInstance

    instance = staticmethod(instance)
    
    def GetBaseDir(self):
        global AGTK_USER

        try:
            self.baseDir = os.environ[AGTK_USER]
        except:
            self.baseDir = os.path.join(os.environ['HOME'], ".AccessGrid3")

        try:
            # Create directory if it doesn't exist
            if self.initIfNeeded:
                # Create directory if it doesn't exist
                if not os.path.exists(self.baseDir):
                    os.mkdir(self.baseDir)
            
        except:
            log.exception("Can not create base directory")
            # check to make it if needed
            self.baseDir = ""
                
        return self.baseDir

    def GetTempDir(self):
        if self.tempDir == None:
            self.tempDir = "/tmp"

        if not os.access(self.tempDir, os.W_OK):
            log.error("UserConfig configuration: TempDir %s is not writable", self.tempDir)

        return self.tempDir

    def GetProxyFile(self):
        if not self.proxyFile:
            proxyFileName = 'x509up_u%d' % os.getuid()
            self.proxyFile = os.path.join(self.GetTempDir(),
                                          proxyFileName)
        return self.proxyFile

class SystemConfig(Config.SystemConfig):
    """
    The SystemConfig object encapsulates all system dependent
    configuration data, it should be extended to retrieve and store
    additional information as necessary.

    @ivar tempDir: the system temp directory.
    @type tempDir: string
    """

    def instance():
        if SystemConfig.theSystemConfigInstance == None:
            SystemConfig()

        return SystemConfig.theSystemConfigInstance
    
    instance = staticmethod(instance)
    
    def GetTempDir(self):
        """
        Get the path to the system temp directory.
        """
        if self.tempDir == None:
            self.tempDir = "/tmp"
            
        return self.tempDir
        
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
        Enumerate the interfaces present on the box.
        
        Run ipconfig /all
        """
        adapters = []
        return adapters

    def PerformanceSnapshot(self):
        """
        This method grabs a snapshot of relevent system information to report
        it. This helps track the effect of the AG Toolkit on the system.
        """
        perfData = dict()

        names = [
            "User Time",
            "System Time",
            "Max Memory Size",
            "Shared Memory Size",
            "Unshared Memory Size",
            "Unshared Stack Size",
            "Page Faults (No I/O)",
            "Page Faults (I/O)",
            "Swap Outs",
            "Block Input Ops",
            "Block Output Ops",
            "Messages Sent",
            "Messages Received",
            "Signals Received",
            "Voluntary Context Switches",
            "Involuntary Context Switches"
            ]

        try:
            ru = resource.getrusage(resource.RUSAGE_BOTH)
            perfData["Stats"] = "Both"
        except ValueError, e:
            try:
                ru = resource.getrusage(resource.RUSAGE_SELF)
                perfData["Stats"] = "Self"
            except resource.error, e:
                log.exception("Error getting performance data")
                ru = None

        if ru is not None:
            for i in range(0, 16):
                perfData[names[i]] = ru[i]
                
        return perfData

    def AppFirewallConfig(self, path, enableFlag):
        """
        This call enables or disables an applications access via a firewall.
        """
        pass

    def GetDefaultRouteIP(self):
        """
        Retrieve the IP address of the interface that the
        default route points to.
        """
        return None
        
    if IsOSX():
        # OSX implementation
        def GetResources(self):

            # deviceList['Mac OS X'] = ['Mac OS X']
            deviceList = dict()
            osxVGrabScanExe = os.path.join(AGTkConfig.instance().GetBinDir(),
                                      'osx-vgrabber-scan')
            if os.path.exists(osxVGrabScanExe):
                try:
                    log.info("Using osx-vgrabber-scan to get devices")
                    log.debug("osx-vgrabber-scan = %s", osxVGrabScanExe)
                    f = os.popen(osxVGrabScanExe,'r')
                    filelines = f.readlines()
                    f.close()

                    log.debug("filelines = %s", filelines)

                    for line in filelines:

                        splitLine = line.strip().split(',')
                        if len(splitLine) > 1:
                            portList = splitLine[1:]
                            device = splitLine[0]
                            deviceList[device] = portList
                            log.info("%s has ports: %s", device, portList)
                        else:
                            log.info("%s: no suitable input ports found", device)

                except:
                    log.exception("osx vgrabber device scan failed")

            # Create resource objects
            resourceList = list()
            for device,portList in deviceList.items():
                try:
                    resourceList.append((device,portList))
                except Exception, e:
                    log.exception("Unable to add video resource to list. device: " + device + "  portlist: " + portList)

            return resourceList

    elif IsFreeBSD():
        def GetResources(self):
            # Determine ports for devices
            deviceList = dict()
            for device in glob.glob("/dev/bktr[0-9]*"):
                if os.path.isdir(device):
                    continue

                fd = None
                try:
                    fd = os.open(device, os.O_RDONLY)
                except Exception, e:
                    log.info("open: %s", e)
                    continue

                portList = ["RCA", "Port-1", "Port-2", "Port-3", "S-Video", "RGB"]

                os.close(fd)

                if len(portList) > 0:
                    deviceList[device] = portList
                    log.info("FreeBSD: %s has ports: %s", device, portList)
                else:
                    log.info("FreeBSD: %s: no suitable input ports found", device)

            # Force x11 onto the list
            deviceList['x11'] = ['x11']

            # Create resource objects
            resourceList = list()
            for device,portList in deviceList.items():
                try:
                    resourceList.append([device,portList])
                except Exception, e:
                    log.exception("Unable to add video resource to list. device: " + device + "  portlist: " + portList)

            return resourceList

    elif IsLinux():
        # Linux implementation
        def GetResources(self):
            # V4L video_capability struct defined in linux/videodev.h :
            #   struct video_capability {
            #     char name[32];
            #     int type;
            #     int channels;   # Num channels
            #     int audios;     # Num audio devices
            #     int maxwidth;   # Supported width
            #     int maxheight;  # and height
            #     int minwidth;   # Supported width
            #     int minheight;  # and height
            #   };
            VIDIOCGCAP_FMT = "32siiiiiii"   # video_capability struct format string
            if sys.byteorder == "little":
                VIDIOCGCAP     = -2143521279    # 0x803C7601
            else:
                VIDIOCGCAP     = 0x403c7601

            # V4L video_channel struct defined in linux/videodev.h :
            #   struct video_channel {
            #     int channel;
            #     char name[32];
            #     int tuners;
            #     __u32 flags;
            #     __u16 type;
            #     __u16 norm;
            #   };
            VIDIOCGCHAN_FMT = "i32siIHH"   # video_channel struct format string
            VIDIOCGCHAN     = -1070565886  # 0xC0307602

            VID_TYPE_CAPTURE = 0x1 # V4L device can capture capability flag

            # Determine ports for devices
            deviceList = dict()
            for device in glob.glob("/dev/video[0-9]*"):
                if os.path.isdir(device):
                    continue

                fd = None
                try:
                    fd = os.open(device, os.O_RDWR)
                except Exception, e:
                    log.info("V4L open: %s", e)
                    continue

                desc = ""; capType = 0; numPorts = 0
                try:
                    cap = struct.pack(VIDIOCGCAP_FMT, "", 0, 0, 0, 0, 0, 0, 0);
                    r = fcntl.ioctl(fd, VIDIOCGCAP, cap)
                    (desc, capType, numPorts, x, x, x, x, x) = struct.unpack(VIDIOCGCAP_FMT, r)
                    desc = desc.replace("\x00", "")
                except Exception, e:
                    log.info("V4L ioctl %s VIDIOCGCAP: %s", device, e)
                    os.close(fd)
                    continue

                log.info("V4L %s description: %s", device, desc)

                if not (capType & VID_TYPE_CAPTURE):
                    os.close(fd)
                    log.info("V4L %s: device can not capture", device)
                    continue

                v4lPortList = []
                for i in range(numPorts):
                    port = ""
                    try:
                        chan = struct.pack(VIDIOCGCHAN_FMT, i, "", 0, 0, 0, 0);
                        r = fcntl.ioctl(fd, VIDIOCGCHAN, chan)
                        port = struct.unpack(VIDIOCGCHAN_FMT, r)[1]
                        v4lPortList.append(port.replace("\x00", ""))
                    except Exception, e:
                        log.info("V4L ioctl %s VIDIOCGCHAN: %s", device, e)

                os.close(fd)

                if len(v4lPortList) > 0:
                    deviceList["V4L:" + device] = v4lPortList
                    log.info("V4L %s has ports: %s", device, v4lPortList)
                else:
                    log.info("V4L %s: no suitable input ports found", device)


            # V4L2 capability struct defined in linux/videodev2.h :
            #   struct v4l2_capability {
            #        __u8    driver[16];      # i.e. "bttv"
            #        __u8    card[32];        # i.e. "Hauppauge WinTV"
            #        __u8    bus_info[32];    # "PCI:" + pci_name(pci_dev)
            #        __u32   version;         # should use KERNEL_VERSION()
            #        __u32   capabilities;    # Device capabilities
            #        __u32   reserved[4];
            #   };
            V4L2_CAPABILITY_FMT = "16s32s32sII4I"   # v4l2_capability struct format string

            if sys.byteorder == "little":
                VIDIOC_QUERYCAP = -2140645888 # 0x80685600
            else:
                VIDIOC_QUERYCAP = 0x40685600

            # V4L2 input struct defined in linux/videodev2.h :
            #   struct v4l2_input {
            #        __u32        index;      #  Which input
            #        __u8         name[32];   #  Label
            #        __u32        type;       #  Type of input
            #        __u32        audioset;   #  Associated audios
            #        __u32        tuner;      #  Associated tuner
            #        __u64        std;
            #        __u32        status;
            #        __u32        reserved[4];
            #   };
            V4L2_INPUT_FMT = "I32sIIILI4I"   # v4l2_input struct format string

            if struct.calcsize('P') == 8:
                # 64 bit V4L2
                VIDIOC_ENUMINPUT = 0xC050561A
            else:
                # 32 bit V4L2
                VIDIOC_ENUMINPUT = -1068739046 # 0xC04C561A


            V4L2_CAP_VIDEO_CAPTURE = 0x01  # V4L2 device can capture capability flag

            for device in glob.glob("/dev/video[0-9]*"):
                if os.path.isdir(device):
                    continue

                fd = None
                try:
                    fd = os.open(device, os.O_RDWR)
                except Exception, e:
                    log.info("V4L2 open: %s", e)
                    continue

                desc = ""; capType = 0
                try:
                    cap = struct.pack(V4L2_CAPABILITY_FMT, "", "", "", 0, 0, 0, 0, 0, 0);
                    r = fcntl.ioctl(fd, VIDIOC_QUERYCAP, cap)
                    (x, desc, x, x, capType, x, x, x, x) = struct.unpack(V4L2_CAPABILITY_FMT, r)
                    desc = desc.replace("\x00", "")
                    log.info("V4L2 %s description: %s", device, desc)
                except Exception, e:
                    print "ioctl", device, "VIDIOC_QUERYCAP:", e
                    os.close(fd)
                    continue

                if not (capType & V4L2_CAP_VIDEO_CAPTURE):
                    os.close(fd)
                    log.info("V4L2 %s: device can not capture", device)
                    continue

                v4l2PortList = []
                index = 0
                while (1):
                    try:
                        input = struct.pack(V4L2_INPUT_FMT, index, "", 0, 0, 0, 0, 0, 0, 0, 0, 0);
                        r = fcntl.ioctl(fd, VIDIOC_ENUMINPUT, input)
                        (index, inputName, x, x, x, x, x, x, x, x, x ) = struct.unpack(V4L2_INPUT_FMT, r)
 
                        v4l2PortList.append(inputName.replace("\x00", ""))

                    except OverflowError :
                        log.exception("V4L2 port name probe OverflowError: assume buggy 64bit python2.4 and use name from V4L probe")
                        if len(v4lPortList) >  index:
                            v4l2PortList.append(v4lPortList[index])
                        break

                    except Exception :
                        break

                    index += 1

                os.close(fd)

                if len(v4l2PortList) > 0:
                    deviceList["V4L2:" + device] = v4l2PortList
                    log.info("V4L2 %s has ports: %s", device, v4l2PortList)
                else:
                    log.info("V4L2 %s: no suitable input ports found", device)

            # Force x11 onto the list
            deviceList['x11'] = ['x11']

            # Create resource objects
            resourceList = list()
            for device,v4l2PortList in deviceList.items():
                try:
                    resourceList.append([device,v4l2PortList])
                except Exception, e:
                    log.exception("Unable to add video resource to list. device: " + device + "  portlist: " + v4l2PortList)

            return resourceList


class MimeConfig(Config.MimeConfig):
    """
    The MimeConfig object encapsulates in single object the management
    of mime types. This provides a cross platform solution so the AGTk
    can leverage legacy configuration and applications for data
    viewing.
    """

    def instance():
        if MimeConfig.theMimeConfigInstance == None:
            MimeConfig()

        return MimeConfig.theMimeConfigInstance

    instance = staticmethod(instance)

    def UnregisterMimeType(self, mimeType):

        # --- Remove, General LINUX/UNIX local user mimetype/mailcap --- #

        mimeFile = os.path.join(os.environ['HOME'], ".mime.types")
        bakMimeFile = os.path.join(os.environ['HOME'], ".mime.types.bak")
        tmpMimeFile = os.path.join(os.environ['HOME'], ".mime.types.tmp")
        mailcapFile = os.path.join(os.environ['HOME'], ".mailcap")
        bakMailcapFile = os.path.join(os.environ['HOME'], ".mailcap.bak")
        tmpMailcapFile = os.path.join(os.environ['HOME'], ".mailcap.tmp")

        if os.path.exists(mimeFile):
            # Backup old file
            shutil.copyfile(mimeFile, bakMimeFile)

            # MimeType file: read line by line and remove the mimeType
            fr = open(mimeFile, "r")
            fw = open(tmpMimeFile, "w")
            line = fr.readline()
            while len(line) > 0:
                if not line.startswith(mimeType):
                    fw.write(line)
                line = fr.readline()
            fr.close()
            fw.close()

            # Now copy tmp file into place
            shutil.copyfile(tmpMimeFile, mimeFile)

            # Remove tmp file
            os.remove(tmpMimeFile)

        if os.path.exists(mailcapFile):
            # Backup old file
            shutil.copyfile(mailcapFile, bakMailcapFile)

            # Mailcap file: read line by line and remove mimeType
            fr = open(mailcapFile, "r")
            fw = open(tmpMailcapFile, "w")
            line = fr.readline()
            while len(line) > 0:
                if not line.startswith(mimeType):
                    fw.write(line)
                line = fr.readline()
            fr.close()
            fw.close()

            # Now copy tmp file into place
            shutil.copyfile(tmpMailcapFile, mailcapFile)

            # Remove tmp file
            os.remove(tmpMailcapFile)
    
    def UnregisterMimeType(self, mimeType):

        # --- Remove, General LINUX/UNIX local user mimetype/mailcap --- #

        mimeFile = os.path.join(os.environ['HOME'], ".mime.types")
        bakMimeFile = os.path.join(os.environ['HOME'], ".mime.types.bak")
        tmpMimeFile = os.path.join(os.environ['HOME'], ".mime.types.tmp")
        mailcapFile = os.path.join(os.environ['HOME'], ".mailcap")
        bakMailcapFile = os.path.join(os.environ['HOME'], ".mailcap.bak")
        tmpMailcapFile = os.path.join(os.environ['HOME'], ".mailcap.tmp")

        if os.path.exists(mimeFile):
            # Backup old file
            shutil.copyfile(mimeFile, bakMimeFile)

            # MimeType file: read line by line and remove the mimeType
            fr = open(mimeFile, "r")
            fw = open(tmpMimeFile, "w")
            line = fr.readline()
            while len(line) > 0:
                if not line.startswith(mimeType):
                    fw.write(line)
                line = fr.readline()
            fr.close()
            fw.close()

            # Now copy tmp file into place
            shutil.copyfile(tmpMimeFile, mimeFile)

            # Remove tmp file
            os.remove(tmpMimeFile)

        if os.path.exists(mailcapFile):
            # Backup old file
            shutil.copyfile(mailcapFile, bakMailcapFile)

            # Mailcap file: read line by line and remove mimeType
            fr = open(mailcapFile, "r")
            fw = open(tmpMailcapFile, "w")
            line = fr.readline()
            while len(line) > 0:
                if not line.startswith(mimeType):
                    fw.write(line)
                line = fr.readline()
            fr.close()
            fw.close()

            # Now copy tmp file into place
            shutil.copyfile(tmpMailcapFile, mailcapFile)

            # Remove tmp file
            os.remove(tmpMailcapFile)
        
    
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

        Written with this use case example:
        RegisterMimeType("application/x-ag3-pkg", ".agpkg3", "agpkg3 file", "Access Grid 3 Package", ["agpm3.py", "/usr/bin/agpm3.py --wait-for-input --package", ""])
        
        ----
        """
        if sys.platform in ['darwin']:
            return

        # Temporarily handle one command until code is added for multiple commands.
        cmd = cmds[0]

        short_extension = ""
        if len(extension) > 0:
            # remove the "." from the front
            short_extension = extension[1:]
        homedir = os.environ['HOME']

        # --- General LINUX/UNIX local user mimetype/mailcap --- #
        
        # First unregister
        self.UnregisterMimeType(mimeType)

        # Write to Mime/Mailcap Files
        mimeFile = os.path.join(os.environ['HOME'], ".mime.types")
        mailcapFile = os.path.join(os.environ['HOME'], ".mailcap")
       
        mimeA = open(mimeFile, "a")   # Append 
        mimeA.write(mimeType + " " + short_extension + "\n")
        mimeA.close()

        mailcapA = open(mailcapFile, "a")   # Append 
        generalMimeCommand = cmd[1].replace("%f", "%s") # has %s instead of %f
        mailcapA.write(mimeType + ";" + generalMimeCommand + "\n")
        mailcapA.close()


        # --- .DESKTOP FILES BASE INFORMATION --- (KDE)

        from AccessGrid.Utilities import IsExecFileAvailable
        if IsExecFileAvailable("kde-config"):

            # User
            kdeMimeInfo = """[Desktop Entry]
Version=%s
Encoding=UTF-8
Hidden=1
Icon=ag.ico
Type=MimeType
Patterns=%s
MimeType=%s
Comment=%s
""" % (str(GetVersion()), "*" + extension, mimeType, description) 
            #   ("2.2", "*.agpkg", "application/x-ag3-pkg", "Access Grid 3 Package")

            kdeAppInfo="""[Desktop Entry]
Version=%s
Encoding=UTF-8
Hidden=1
MultipleArgs=false
Terminal=1
Icon=ag.ico
Exec=%s
Type=Application
MimeType=%s
Name=%s
Comment=%s
""" % (str(GetVersion()), cmd[1], mimeType, cmd[0], cmd[2])
            #    ("2.2", "/usr/bin/agpm3.py", "application/x-ag3-pkg", "Access Grid 3 Package Manager" or "agpm3.py", comment)


        # --- GNOME BASE INFORMATION ---

        defAppId = cmd[0] # use verb for the defaultAppId

        gnomeAppInfo="""
%s
        requires_terminal=true
        command=%s
        can_open_multiple_files=false
        name=%s
        mime_types=%s
        """ % (defAppId, cmd[1].strip("%f"), defAppId, mimeType)
        #  %("agpm3.py", "/usr/bin/agpm3.py", "agpm3.py", application/x-ag3-pkg")

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
        #     ("x-ag3-pkg", "agpm3.py", "Access Grid 3 Package", "agpm3.py")

        gnomeMimeInfo="%s\n        ext: %s\n" % (mimeType, short_extension)  
        #                                       ("x-ag3-pkg", "agpkg")


        # --- KDE USER REGISTRATION ---

        if IsExecFileAvailable("kde-config"):
            # First find the user and system app paths.
            # query them since applnk-redhat can't work for everybody.
            f = os.popen("kde-config --path apps")
            result = f.read()
            f.close()
            pathList = result.split(":")
            kdeUserApps = ""
            # if kde-config failed, the paths should stay == ""
            for path in pathList:
                if path.find(homedir) != -1:
                    kdeUserApps = path # expecting /home/user/.kde/share/applnk[-redhat]

            # Find the user and system mime paths.
            f = os.popen("kde-config --path mime")
            result = f.read()
            f.close()
            pathList = result.split(":")
            kdeUserMime = ""
            # if kde-config failed, the paths should stay == ""
            for path in pathList:
                if path.find(homedir) != -1:
                    kdeUserMime = path # expecting /home/user/.kde/share/applnk[-redhat]

            userMimeFile = os.path.join(kdeUserMime, extension[1:] + ".desktop")
            userAppFile = os.path.join(kdeUserApps, cmd[0] +".desktop")

            # Copy KDE files into place
            if len(userMimeFile) > 0 and os.path.exists(kdeUserMime):
                if not os.path.exists(userMimeFile): # don't overwrite
                    mimeFd = open(userMimeFile, "w")
                    mimeFd.write(kdeMimeInfo)
                    mimeFd.close()

            if len(userAppFile) > 0 and os.path.exists(kdeUserApps):
                if not os.path.exists(userAppFile): # don't overwrite
                    appFd = open(userAppFile, "w")
                    appFd.write(kdeAppInfo)
                    appFd.close()


        # --- GNOME USER REGISTRATION ---

        # if gnome files exist, register with them.
        gnomeAppDir = os.path.join(homedir, ".gnome", "application-info")
        gnomeMimeDir = os.path.join(homedir, ".gnome", "mime-info")
        gnomeAppFile = os.path.join(gnomeAppDir, cmd[0] + ".applications")
        gnomeKeysFile = os.path.join(gnomeMimeDir, cmd[0] + ".keys")
        gnomeMimeFile = os.path.join(gnomeMimeDir, cmd [0] + ".mime")
        if os.path.exists(gnomeAppDir) and os.path.exists(gnomeMimeDir):
            log.info("registering file type " + extension + " with gnome")

            if not os.path.exists(gnomeAppFile): # don't overwrite
                f = open(gnomeAppFile, "w")
                f.write(gnomeAppInfo)
                f.close()

            if not os.path.exists(gnomeKeysFile): # don't overwrite
                f = open(gnomeKeysFile, "w")
                f.write(gnomeKeyInfo)
                f.close()

            if not os.path.exists(gnomeMimeFile): # don't overwrite
                f = open(gnomeMimeFile, "w")
                f.write(gnomeMimeInfo)
                f.close()

        else:
            log.info("gnome directory " + gnomeAppDir + " or " + gnomeMimeDir + " not found, not registering file type " + extension + " with gnome")


        """
        registerSystem = 1
        if registerSystem:

        # --- KDE SYSTEM REGISTRATION ---

            # general paths
            genSystemAppDir = "/usr/share/applications"
            genSystemAppFile = os.path.join(genSystemAppDir, cmd[0] + ".desktop")
            genSystemMimeDir = "/usr/share/mimelnk/application"
            genSystemMimeFile = os.path.join(genSystemMimeDir, extension[1:] + ".desktop")

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
            gnomeSystemMimeFile = os.path.join(gnomeSystemMimeDir, cmd[0] + ".mime")
            gnomeSystemKeysFile = os.path.join(gnomeSystemMimeDir, cmd[0] + ".keys")
            gnomeSystemAppDir = "/usr/share/application-registry"
            gnomeSystemAppFile = os.path.join(gnomeSystemAppDir, cmd[0] + ".applications")
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
        mimeFile = os.path.join(os.environ['HOME'],".mime.types")
        mimetypes.init([mimeFile])
        
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
            print "\tNode Config Dir: ", userConf.GetNodeConfigDir()
            print "\tService Dir: ", userConf.GetServicesDir()
            print "\tLocal Services Dir: ", userConf.GetLocalServicesDir()
        except Exception, e:
            print "Error trying to retrieve the user Configuration:\n", e
    else:
        print "The user config object is: ", userConf
