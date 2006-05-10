#-----------------------------------------------------------------------------
# Name:        ProcessManager.py
# Purpose:     platform magic
# Created:     2003/05/06
# RCS-ID:      $Id: ProcessManager.py,v 1.6 2006-05-10 01:30:04 willing Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: ProcessManager.py,v 1.6 2006-05-10 01:30:04 willing Exp $"

import sys
from AccessGrid.Platform import IsWindows, IsLinux, IsOSX, IsFreeBSD

if IsWindows():
    from AccessGrid.Platform.win32.ProcessManager import *
elif IsLinux() or IsOSX() or IsFreeBSD():
    from AccessGrid.Platform.unix.ProcessManager import *
else:
    print "No support for Platform %s" % sys.platform
