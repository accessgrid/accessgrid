#-----------------------------------------------------------------------------
# Name:        Config.py
# Purpose:     Configuration objects for applications using the toolkit.
#              there are config objects for various sub-parts of the system.
# Created:     2003/05/06
# RCS-ID:      $Id: Config.py,v 1.1 2004-03-12 05:35:24 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Config.py,v 1.1 2004-03-12 05:35:24 judson Exp $"

from AccessGrid.Platform import isWindows, isLinux, isOSX

if isWindows():
    from AccessGrid.Platform.win32.Config import *
elif isLinux():
    from AccessGrid.Platform.linux2.Config import *
elif isOSX():
    from AccessGrid.Platform.darwin.Config import *
else:
    log.warn("Platform doesn't have a platform-specific module for %s",
             sys.platform)
