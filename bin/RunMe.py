#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        user.py
# Purpose:     This is a quick hack to make the alpha easier to use.
#
# Author:      Ivan R. Judson
#
# Created:     2003/06/02
# RCS-ID:      $Id: RunMe.py,v 1.1 2003-02-28 21:08:50 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
import os
import signal

if sys.platform == 'win32':
    from AccessGrid.ProcessManagerWin32 import ProcessManagerWin32 as ProcessManager 
else:
    from AccessGrid.ProcessManagerUnix import ProcessManagerUnix as ProcessManager

pm = ProcessManager()

pm.start_process(sys.executable, ["AGNodeService.py"])
pm.start_process(sys.executable, ["AGServiceManager.py"])

vcpic = os.spawnv(os.P_WAIT, sys.executable,
                  [sys.executable, "VenueClient.py"])

pm.terminate_all_processes()

