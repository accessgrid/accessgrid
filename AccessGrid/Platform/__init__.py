#-----------------------------------------------------------------------------
# Name:        __init__.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2003/08/02
# RCS-ID:      $Id: __init__.py,v 1.4 2004-03-12 05:23:12 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
Platform sub modules.
"""
__revision__ = "$Id: __init__.py,v 1.4 2004-03-12 05:23:12 judson Exp $"
__docformat__ = "restructuredtext en"

# mechanisms to support multiple hosting environments and to set defaults
import sys

# Global env var
AGTK = 'AGTK'
AGTK_LOCATION = 'AGTK_LOCATION'
AGTK_USER = 'AGTK_USER'
AGTK_INSTALL = 'AGTK_INSTALL'

WIN = 'win32'
LINUX = 'linux2'
OSX = 'darwin'

def isWindows():
    """Function that retusn 1 if the platform is windows, 0 otherwise """
    if sys.platform == WIN:
        return 1
    else:
        return 0

def isLinux():
    """Function that retusn 1 if the platform is linux, 0 otherwise """
    if sys.platform == LINUX:
        return 1
    else:
        return 0

def isOSX():
    """Function that retusn 1 if the platform is os x, 0 otherwise """
    if sys.platform == OSX:
        return 1
    else:
        return 0

if isWindows():
    from AccessGrid.Platform.win32 import Config as Config
    from AccessGrid.Platform.win32 import PersonalNode as PersonalNode
    from AccessGrid.Platform.win32 import ProcessManager as ProcessManager
elif isLinux():
    from AccessGrid.Platform.linux2 import Config as Config
    from AccessGrid.Platform.linux2 import PersonalNode as PersonalNode
    from AccessGrid.Platform.linux2 import ProcessManager as ProcessManager
elif isOSX():
    from AccessGrid.Platform.darwin import Config as Config
    from AccessGrid.Platform.darwin import PersonalNode as PersonalNode
    from AccessGrid.Platform.darwin import ProcessManager as ProcessManager
else:
    log.warn("Platform doesn't have a platform-specific module for %s",
             sys.platform)
