#-----------------------------------------------------------------------------
# Name:        ProcessManager.py
# Purpose:     platform magic
# Created:     2003/05/06
# RCS-ID:      $Id: ProcessManager.py,v 1.2 2004-03-24 21:25:08 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: ProcessManager.py,v 1.2 2004-03-24 21:25:08 eolson Exp $"

from AccessGrid.Platform import isWindows, isLinux, isOSX

if isWindows():
    from AccessGrid.Platform.win32.ProcessManager import *
elif isLinux() or isOSX():
    from AccessGrid.Platform.unix.ProcessManager import *
else:
    log.warn("Platform doesn't have a platform-specific module for %s",
             sys.platform)
