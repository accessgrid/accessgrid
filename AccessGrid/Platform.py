#-----------------------------------------------------------------------------
# Name:        Platform.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2003/09/02
# RCS-ID:      $Id: Platform.py,v 1.3 2003-02-13 20:11:31 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import os
import sys

WinGPI = "wgpi.exe"
LinuxGPI = "grid-proxy-init"

def GPI():
    GlobusBin = os.path.join(os.environ['GLOBUS_LOCATION'], 'bin')
    files = os.listdir(GlobusBin)
    for f in files:
        print "File: %s" % f
        if f == WinGPI:
            print "WINDOWS: %s" % os.path.join(GlobusBin, f)
            os.spawnv(os.P_WAIT, os.path.join(GlobusBin, f), [])
        elif f == LinuxGPI:
            print "LINUX %s" % os.path.join(GlobusBin, f)

try:    import _winreg
except: pass

def GetSystemConfigDir():
    """
    Determine the system configuration directory
    """

    configDir = ""
    if sys.platform == 'win32':
        x=_winreg.ConnectRegistry(None,_winreg.HKEY_LOCAL_MACHINE)
        y=_winreg.OpenKey(x, r"SOFTWARE\AccessGridToolkit\2.0\ConfigPath")
        configDir = _winreg.QueryValue(y,None)

    elif sys.platform == 'linux2': 
        configDir = "/etc/AccessGrid/config"
    return configDir

def GetUserConfigDir():
    """ 
    Determine the user configuration directory
    """

    configDir = ""
    if sys.platform == 'win32':
        x=_winreg.ConnectRegistry(None,_winreg.HKEY_LOCAL_MACHINE)
        y=_winreg.OpenKey(x, r"SOFTWARE\AccessGridToolkit\2.0\UserConfigPath")
        configDir = _winreg.QueryValue(y,None)

    elif sys.platform == 'linux2': 
        
        configDir = os.environ["HOME"] + os.sep + ".AccessGrid"

    return configDir

def GetConfigFilePath( configFile ):
    """
    Locate given file in configuration directories:  
        first check user dir, then system dir; 
        return None if not found
    """

    userConfigPath = GetUserConfigDir()
    pathToFile = userConfigPath + os.sep + configFile
    if os.path.exists( pathToFile ):
        return pathToFile

    systemConfigPath = GetSystemConfigDir()
    pathToFile = systemConfigPath + os.sep + configFile
    if os.path.exists( pathToFile ):
        return pathToFile

    return None
