#-----------------------------------------------------------------------------
# Name:        ProcessManager.py
# Purpose:     Abstract platform Processmanagement instances.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: ProcessManager.py,v 1.4 2004-02-19 18:10:10 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: ProcessManager.py,v 1.4 2004-02-19 18:10:10 eolson Exp $"
__docformat__ = "restructuredtext en"

from AccessGrid.Platform import isWindows, isLinux, isOSX

if isWindows():
    from AccessGrid.ProcessManagerWin32 import ProcessManagerWin32 as ProcessManager
elif isLinux() or isOSX():
    from AccessGrid.ProcessManagerUnix import ProcessManagerUnix as ProcessManager
