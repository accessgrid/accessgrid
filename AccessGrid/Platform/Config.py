#-----------------------------------------------------------------------------
# Name:        Config.py
# Purpose:     Configuration objects for applications using the toolkit.
#              there are config objects for various sub-parts of the system.
# Created:     2003/05/06
# RCS-ID:      $Id: Config.py,v 1.2 2004-03-24 21:25:08 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Config.py,v 1.2 2004-03-24 21:25:08 eolson Exp $"

from AccessGrid.Platform import isWindows, isLinux, isOSX

if isWindows():
    from AccessGrid.Platform.win32.Config import *
elif isLinux() or isOSX():
    from AccessGrid.Platform.unix.Config import *
else:
    log.warn("Platform doesn't have a platform-specific module for %s",
             sys.platform)
