#-----------------------------------------------------------------------------
# Name:        Platform.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2003/09/02
# RCS-ID:      $Id: Platform.py,v 1.13 2003-03-25 15:34:41 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import os
import sys

import logging

log = logging.getLogger("AG.Platform")

# Global env var
AGTK = 'AGTK'

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
except:
    pass

def GetSystemConfigDir():
    """
    Determine the system configuration directory
    """

    configDir = ""
    if sys.platform == WIN:
        AG20 = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, AGTkRegBaseKey)
        configDir, type = _winreg.QueryValueEx(AG20,"ConfigPath")

    elif sys.platform == LINUX:
        configDir = AGTkBasePath

    return configDir

def GetUserConfigDir():
    """ 
    Determine the user configuration directory
    """

    configDir = ""
    if sys.platform == WIN:
        AG20 = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, AGTkRegBaseKey)
        configDir, type = _winreg.QueryValueEx(AG20,"UserConfigPath")

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

    installDir = ""
    if sys.platform == WIN:
        AG20 = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, AGTkRegBaseKey)
        installDir, type = _winreg.QueryValueEx(AG20,"InstallPath")

    elif sys.platform == LINUX:
        installDir = "/usr/bin"

    return installDir

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
        
            
