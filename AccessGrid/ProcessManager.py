#-----------------------------------------------------------------------------
# Name:        ProcessManager.py
# Purpose:     Abstract platform Processmanagement instances.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: ProcessManager.py,v 1.1 2003-08-28 20:36:13 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from AccessGrid.Platform import isWindows, isLinux, isOSX

if isWindows():
    from AccessGrid.ProcessManagerWin32 import ProcessManagerWin32 as ProcessManager
elif isLinux():
    from AccessGrid.ProcessManagerPipes import ProcessManagerPipes as ProcessManager
