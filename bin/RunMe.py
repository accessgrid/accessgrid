#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        user.py
# Purpose:     This is a quick hack to make the alpha easier to use.
#
# Author:      Ivan R. Judson
#
# Created:     2003/06/02
# RCS-ID:      $Id: RunMe.py,v 1.3 2003-03-13 14:37:30 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
import os
import signal
import time

if sys.platform == 'win32':
    from AccessGrid.ProcessManagerWin32 import ProcessManagerWin32 as ProcessManager 
else:
    from AccessGrid.ProcessManagerUnix import ProcessManagerUnix as ProcessManager

pm = ProcessManager()

pm.start_process(sys.executable, ["AGServiceManager.py"])

# This is icky but it's here to "mostly" ensure the service manager
# gets started before the node service is running
# there are much better ways to deal with this, but it should at least
# improve the odds things get going in the right order.
# there are *much* better ways to do this, if we keep this around
# we'll have to pick one of them.
time.sleep(1)

pm.start_process(sys.executable, ["AGNodeService.py"])

vcpic = os.spawnv(os.P_WAIT, sys.executable,
                  [sys.executable, "VenueClient.py"])

pm.terminate_all_processes()

