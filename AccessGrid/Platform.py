#-----------------------------------------------------------------------------
# Name:        Platform.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2003/09/02
# RCS-ID:      $Id: Platform.py,v 1.44 2003-08-28 18:03:48 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import os
import sys
import getpass
import mimetypes, mailcap

import logging

log = logging.getLogger("AG.Platform")

# Global env var
AGTK = 'AGTK'
AGTK_LOCATION = 'AGTK_LOCATION'
AGTK_USER = 'AGTK_USER'
AGTK_INSTALL = 'AGTK_INSTALL'

# Windows Defaults
WIN = 'win32'

# This gets updated with a call to get the version
AGTkRegBaseKey = "SOFTWARE\\Access Grid Toolkit\\2.1.1"

def isWindows():
    if sys.platform == WIN:
	return 1
    else:
	return 0

# Linux Defaults
LINUX = 'linux2'
AGTkBasePath = "/etc/AccessGrid"

def isLinux():
    if sys.platform == LINUX:
	return 1
    else:
	return 0

# Mac OS X Defaults
OSX='darwin'
AGTkBasePath="/etc/AccessGrid"
        
def isOSX():
    if sys.platform == OSX:
	return 1
    else:
	return 0

try:
    import _winreg
    import win32api
    from win32com.shell import shell, shellcon
except:
    pass


def GetSystemConfigDir():
    """
    Determine the system configuration directory
    """
   
    try:
        configDir = os.environ[AGTK_LOCATION]
    except:
        configDir = ""

    """
    If environment variable not set, check for settings from installation.
    """

    if "" == configDir:

        if isWindows():
            base = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
            configDir = os.path.join(base, "AccessGrid")

        elif isLinux() or isOSX():
            configDir = AGTkBasePath

    return configDir

def GetUserConfigDir():
    """ 
    Determine the user configuration directory
    """

    try:
        configDir = os.environ[AGTK_USER]
    except:
        configDir = ""

    """
    If environment variable not set, check for settings from installation.
    """
    
    if "" == configDir:
        if isWindows():
            base = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
            configDir = os.path.join(base, "AccessGrid")
        elif isLinux() or isOSX():
            configDir = os.path.join(os.environ["HOME"],".AccessGrid")

    return configDir

def GetUserAppPath():
    """
    """
    
    ucd = GetUserConfigDir()

    appPath = os.path.join(ucd, "SharedApplications")

    return appPath
    
def GetConfigFilePath( configFile ):
    """
    Locate given file in configuration directories:  
        first check user dir, then system dir; 
        return None if not found
    """

    systemConfigPath = GetSystemConfigDir()
    pathToFile = os.path.join(systemConfigPath,configFile)
    if os.path.exists( pathToFile ):
        return pathToFile

    return None

def GetInstallDir():
    """ 
    Determine the install directory
    """

    try:
        installDir = os.environ[AGTK_INSTALL]
    except:
        installDir = ""

    if installDir != "":
        return installDir;

    if isWindows():
        try:
            AG20 = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, AGTkRegBaseKey)
            installDir, type = _winreg.QueryValueEx(AG20,"InstallPath")
            installDir = os.path.join(installDir, "bin")
        except WindowsError:
            log.exception("Cannot open install directory reg key")
            installDir = ""
    elif isLinux() or isOSX():
        installDir = "/usr/bin"

    return installDir

def GetSharedDocDir():
    """ 
    Determine the shared doc directory
    """

    try:
        sharedDocDir = os.environ[AGTK_INSTALL]
    except:
        sharedDocDir = ""

    if sharedDocDir != "":
        return sharedDocDir;

    if isWindows():
        try:
            AG20 = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, AGTkRegBaseKey)
            sharedDocDir, type = _winreg.QueryValueEx(AG20,"InstallPath")
            sharedDocDir = os.path.join(sharedDocDir, "doc")
        except WindowsError:
            log.exception("Cannot open InstallPath directory reg key")
            sharedDocDir = ""

    elif isLinux() or isOSX():
        sharedDocDir = "/usr/share/doc/AccessGrid/Documentation"

    return sharedDocDir

def GetTempDir():
    """
    Return a directory in which temporary files may be written.
    """

    if isWindows():
        return win32api.GetTempPath()
    else:
        return "/tmp"


def GetSystemTempDir():
    """
    Return a directory in which temporary files may be written.
    The system temp dir is guaranteed to not be tied to any particular user.
    """

    if isWindows():
        winPath = win32api.GetWindowsDirectory()
        return os.path.join(winPath, "TEMP")
    else:
        return "/tmp"

def GetUsername():

    if isWindows():
        try:
            user = win32api.GetUserName()
            user.replace(" ", "")
            return user
        except:
            pass

    return getpass.getuser()


def GetFilesystemFreeSpace(path):
    """
    Determine the amount of free space available in the filesystem
    containing <path>.

    Returns a value in bytes.
    """

    #
    # On Unix-like systems (including Linux) we can use os.statvfs.
    #
    # f_bsize is the "preferred filesystem block size"
    # f_frsize is the "fundamental filesystem block size"
    # f_bavail is the number of blocks free
    #
    if hasattr(os, "statvfs"):
        x = os.statvfs(path)

        #
        # On some older linux systems, f_frsize is 0. Use f_bsize instead then.
        # cf http://www.uwsg.iu.edu/hypermail/linux/kernel/9907.3/0019.html
        #
        if x.f_frsize == 0:
            blockSize = x.f_bsize
        else:
            blockSize = x.f_frsize

        freeBytes = blockSize * x.f_bavail

    elif isWindows():

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

        x = win32api.GetDiskFreeSpace(path)

        freeBytes = x[0] * x[1] * x[2]
    else:
        freeBytes = None

    return freeBytes
        
if isWindows():

    def FindRegistryEnvironmentVariable(varname):
        """
        Find the definition of varname in the registry.

        Returns the tuple (global_value, user_value).

        We can use this to determine if the user has set an environment
        variable at the commandline if it's causing problems.

        """

        global_reg = None
        user_reg = None

        #
        # Read the system registry
        #
        k = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
        try:
            (val, type) = _winreg.QueryValueEx(k, varname)
            global_reg = val
        except:
            pass
        k.Close()

        #
        # Read the user registry
        #

        k = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Environment")
                            
        try:
            (val, type) = _winreg.QueryValueEx(k, varname)
            user_reg = val
        except:
            pass
        k.Close()


        return (global_reg, user_reg)

#
# Windows register mime type function
#

def Win32RegisterMimeType(mimeType, extension, fileType, description, cmds):
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
    
    This function gets the mime type registered with windows via the registry.
    The following documentation is from wxWindows, src/msw/mimetype.cpp:
    
    1. "HKCR\MIME\Database\Content Type" contains subkeys for all known MIME
    types, each key has a string value "Extension" which gives (dot preceded)
    extension for the files of this MIME type.
    
    2. "HKCR\.ext" contains
    a) unnamed value containing the "filetype"
    b) value "Content Type" containing the MIME type
    
    3. "HKCR\filetype" contains
    a) unnamed value containing the description
    b) subkey "DefaultIcon" with single unnamed value giving the icon index in
    an icon file
    c) shell\open\command and shell\open\print subkeys containing the commands
    to open/print the file (the positional parameters are introduced by %1,
    %2, ... in these strings, we change them to %s ourselves)
    """

    # Do 1. from above
    try:
        regKey = _winreg.CreateKey(_winreg.HKEY_CLASSES_ROOT,
                                   "MIME\Database\Content Type\%s" % mimeType)
        _winreg.SetValueEx(regKey, "Extension", 0, _winreg.REG_SZ, extension)
        _winreg.CloseKey(regKey)
    except EnvironmentError, e:
        log.debug("Couldn't open registry for mime registration!")
    
    # Do 2. from above
    try:
        regKey = _winreg.CreateKey(_winreg.HKEY_CLASSES_ROOT, extension)

        _winreg.SetValueEx(regKey, "", 0, _winreg.REG_SZ, fileType)
        _winreg.SetValueEx(regKey, "Content Type", 0, _winreg.REG_SZ, mimeType)

        _winreg.CloseKey(regKey)
    except EnvironmentError, e:
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

def Win32GetMimeCommands(mimeType = None, ext = None):
    """
    This gets the mime commands from one of the three types of specifiers
    windows knows about. Depending on which is passed in the following
    trail of information is retrieved:

    1. "HKCR\MIME\Database\Content Type" contains subkeys for all known MIME
    types, each key has a string value "Extension" which gives (dot preceded)
    extension for the files of this MIME type.
    
    2. "HKCR\.ext" contains
    a) unnamed value containing the "filetype"
    b) value "Content Type" containing the MIME type
    
    3. "HKCR\filetype" contains
    a) unnamed value containing the description
    b) subkey "DefaultIcon" with single unnamed value giving the icon index in
    an icon file
    c) shell\open\command and shell\open\print subkeys containing the commands
    to open/print the file (the positional parameters are introduced by %1,
    %2, ... in these strings, we change them to %s ourselves)
    """
    cdict = dict()
    filetype = None
    extension = ext
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

    if extension != None:
        if extension[0] != ".":
            extension = ".%s" % extension
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, "%s" % extension)
            filetype, type = _winreg.QueryValueEx(key, "")
            _winreg.CloseKey(key)
        except WindowsError:
            log.warn("Couldn't open registry for file extension: %s.",
                          extension)
            return cdict

    if filetype != None:
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT,
                                  "%s\shell" % filetype)
            nCommands = _winreg.QueryInfoKey(key)[0]
            defaultCommand = _winreg.QueryValue(key, "")
            
            for i in range(0,nCommands-1):
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
            log.warn("Couldn't retrieve list of commands: (mimeType: %s) (fileType: %s)", mimeType, filetype)
            return cdict

    return cdict

def Win32GetMimeType(extension = None):
    mimeType = None
    if extension != None:
        if extension[0] != ".":
            extension = ".%s" % extension
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, "%s" % extension)
            mimeType, type = _winreg.QueryValueEx(key, "Content Type")
            _winreg.CloseKey(key)
        except WindowsError:
            log.warn("Couldn't open registry for file extension: %s.",
                          extension)
            return mimeType
        
    return mimeType

def LinuxGetMimeType(extension = None):
    """
    """
    fauxFn = ".".join(["Faux", extension])
    mimetypes.init()

    # This is always a tuple so this is Ok
    mimeType = mimetypes.guess_type(fauxFn)[0]
    
    return mimeType

def LinuxGetMimeCommands(mimeType = None, ext = None):
    """
    """
    cdict = dict()
    view = 'view'
    
    if mimeType == None:
        mimeType = LinuxGetMimeType(extension = ext)

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
    
if isWindows():
    GetMimeCommands = Win32GetMimeCommands
    GetMimeType = Win32GetMimeType
else:
    GetMimeCommands = LinuxGetMimeCommands
    GetMimeType = LinuxGetMimeType

#
# Unix Daemonize, this is not appropriate for Win32
#

def DaemonizeUnix(self):
    try:
        pid = os.fork()
    except:
        print "Could not fork"
        sys.exit(1)

        if pid:
            # Let parent die !
            sys.exit(0)
        else:
            try:
                # Create new session
                os.setsid()
            except:
                print "Could not create new session"
                sys.exit(1)

#
# Determine which daemonize we should use
#

if isWindows():
    Daemonize = lambda : None
else:
    Daemonize = DaemonizeUnix




def SetRtpDefaultsWin( profile ):
    """
    Set registry values used by vic and rat for identification
    """
    import _winreg

    #
    # Set RTP defaults according to the profile
    #
    k = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                        r"Software\Mbone Applications\common",
                        0,
                        _winreg.KEY_SET_VALUE)
    _winreg.SetValueEx(k, "rtpName", 0, _winreg.REG_SZ, profile.name)
    _winreg.SetValueEx(k, "rtpEmail", 0, _winreg.REG_SZ, profile.email)
    _winreg.SetValueEx(k, "rtpPhone", 0, _winreg.REG_SZ, profile.phoneNumber)
    _winreg.SetValueEx(k, "rtpLoc", 0, _winreg.REG_SZ, profile.location)
    _winreg.SetValueEx(k, "rtpNote", 0, _winreg.REG_SZ, str(profile.publicId) )

    _winreg.CloseKey(k)

def SetRtpDefaultsUnix( profile ):
    """
    Set registry values used by vic and rat for identification
    """
    #
    # Write the rtp defaults file
    #
    rtpDefaultsText="*rtpName: %s\n*rtpEmail: %s\n*rtpLoc: %s\n*rtpPhone: %s\n*rtpNote: %s\n"
    rtpDefaultsFile=open( os.path.join(os.environ["HOME"], ".RTPdefaults"),"w")
    rtpDefaultsFile.write( rtpDefaultsText % ( profile.name,
                                             profile.email,
                                             profile.location,
                                             profile.phoneNumber,
                                             profile.publicId ) )
    rtpDefaultsFile.close()

#
# Determine which SetRtpInfo we should use
#

if isWindows():
    SetRtpDefaults = SetRtpDefaultsWin
else:
    SetRtpDefaults = SetRtpDefaultsUnix

