#-----------------------------------------------------------------------------
# Name:        Config.py
# Purpose:     Configuration objects for applications using the toolkit.
#              there are config objects for various sub-parts of the system.
# Created:     2003/05/06
# RCS-ID:      $Id: Config.py,v 1.3 2004-04-05 18:34:49 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Config.py,v 1.3 2004-04-05 18:34:49 judson Exp $"

from AccessGrid.Platform import IsWindows, IsLinux, IsOSX

if IsWindows():
    from AccessGrid.Platform.win32.Config import *
elif IsLinux() or IsOSX():
    from AccessGrid.Platform.unix.Config import *
else:
    log.warn("Platform doesn't have a platform-specific module for %s",
             sys.platform)
