#-----------------------------------------------------------------------------
# Name:        Platform.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2003/09/02
# RCS-ID:      $Id: Platform.py,v 1.21 2003-04-24 18:36:47 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import os
import sys
import getpass

import logging

log = logging.getLogger("AG.Platform")

# Global env var
AGTK = 'AGTK'
AGTK_LOCATION = 'AGTK_LOCATION'
AGTK_USER = 'AGTK_USER'
AGTK_INSTALL = 'AGTK_INSTALL'

# Windows Defaults
WIN = 'win32'
WinGPI = "wgpi.exe"
AGTkRegBaseKey = "SOFTWARE\\Access Grid Toolkit\\2.0"

# Linux Defaults
LINUX = 'linux2'
LinuxGPI = "grid-proxy-init"
AGTkBasePath = "/etc/AccessGrid"

# Mac OS X Defaults
# They will go here :-)
        

def GPICmdline():
    """
    Run grid-proxy-init to get a new proxy.
    """
    
    GlobusBin = os.path.join(os.environ['GLOBUS_LOCATION'], 'bin')

    gpiPath = os.path.join(GlobusBin, LinuxGPI)

    if os.access(gpiPath, os.X_OK):
        log.debug("Found grid-proxy-init at %s, not executing", gpiPath)

def GPIWin32():
    """
    Run wgpi.exe to get a new proxy.
    """
    
    GlobusBin = os.path.join(os.environ['GLOBUS_LOCATION'], 'bin')
    
    gpiPath = os.path.join(GlobusBin, WinGPI)

    if os.access(gpiPath, os.X_OK):
        log.debug("Excecuting gpi at %s", gpiPath)
        os.spawnv(os.P_WAIT, gpiPath, [])

#
# Determine which grid-proxy-init we should use.
#

if sys.platform == WIN:
    GPI = GPIWin32
else:
    GPI = GPICmdline

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

        if sys.platform == WIN:
            base = shell.SHGetFolderPath(0, shellcon.CSIDL_COMMON_APPDATA, 0, 0)
            configDir = os.path.join(base, "AccessGrid")

        elif sys.platform == LINUX:
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
        if sys.platform == WIN:
            base = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
            configDir = os.path.join(base, "AccessGrid")
        elif sys.platform == LINUX:
            configDir = os.path.join(os.environ["HOME"],".AccessGrid")

    return configDir

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

    if sys.platform == WIN:
        try:
            AG20 = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, AGTkRegBaseKey)
            installDir, type = _winreg.QueryValueEx(AG20,"InstallPath")
        except WindowsError:
            log.exception("Cannot open install directory reg key")
            installDir = ""

    elif sys.platform == LINUX:
        installDir = "/usr/bin"

    return installDir

def GetTempDir():
    """
    Return a directory in which temporary files may be written.
    """

    if sys.platform == WIN:
        return win32api.GetTempPath()
    else:
        return "/tmp"


def GetSystemTempDir():
    """
    Return a directory in which temporary files may be written.
    The system temp dir is guaranteed to not be tied to any particular user.
    """

    if sys.platform == WIN:
        winPath = win32api.GetWindowsDirectory()
        return os.path.join(winPath, "TEMP")
    else:
        return "/tmp"

def GetUsername():

    if sys.platform == WIN:
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

    elif sys.platform == WIN:

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
        
if sys.platform == WIN:

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
#            newcommand = u""
#            for word in lwords:
#                newcommand += "\"%s\" " % word
            _winreg.SetValueEx(cmdKey, "", 0, _winreg.REG_SZ, newcommand)
            _winreg.CloseKey(cmdKey)
            _winreg.CloseKey(verbKey)
            
        _winreg.CloseKey(shellKey)
        
        _winreg.CloseKey(regKey)
    except EnvironmentError, e:
        log.debug("Couldn't open registry for mime registration!")
