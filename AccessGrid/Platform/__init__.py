#-----------------------------------------------------------------------------
# Name:        __init__.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: __init__.py,v 1.9 2004-09-10 03:58:53 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
Platform sub modules.
"""
__revision__ = "$Id: __init__.py,v 1.9 2004-09-10 03:58:53 judson Exp $"

# mechanisms to support multiple hosting environments and to set defaults
import sys

# Global env var
AGTK_LOCATION = 'AGTK_LOCATION'
AGTK_USER = 'AGTK_USER'
AGTK_INSTALL = 'AGTK_INSTALL'

WIN = 'win32'
LINUX = 'linux2'
OSX = 'darwin'

def IsWindows():
    """Function that retusn 1 if the platform is windows, 0 otherwise """
    if sys.platform == WIN:
        return 1
    else:
        return 0

def IsLinux():
    """Function that retusn 1 if the platform is linux, 0 otherwise """
    if sys.platform == LINUX:
        return 1
    else:
        return 0

def IsOSX():
    """Function that retusn 1 if the platform is os x, 0 otherwise """
    if sys.platform == OSX:
        return 1
    else:
        return 0

isWindows = IsWindows
isLinux = IsLinux
isOSX = IsOSX

if IsWindows():
    from AccessGrid.Platform.win32 import Config as Config
    from AccessGrid.Platform.win32 import ProcessManager as ProcessManager
elif IsLinux() or IsOSX():
    from AccessGrid.Platform.unix import Config as Config
    from AccessGrid.Platform.unix import ProcessManager as ProcessManager
else:
    print "No support for Platform %s" % sys.platform
