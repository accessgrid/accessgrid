#-----------------------------------------------------------------------------
# Name:        ProcessManager.py
# Purpose:     Abstract platform Processmanagement instances.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: ProcessManager.py,v 1.3 2003-09-16 07:20:18 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: ProcessManager.py,v 1.3 2003-09-16 07:20:18 judson Exp $"
__docformat__ = "restructuredtext en"

from AccessGrid.Platform import isWindows, isLinux, isOSX

if isWindows():
    from AccessGrid.ProcessManagerWin32 import ProcessManagerWin32 as ProcessManager
elif isLinux():
    from AccessGrid.ProcessManagerUnix import ProcessManagerUnix as ProcessManager
