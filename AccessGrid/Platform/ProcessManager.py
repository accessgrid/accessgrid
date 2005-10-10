#-----------------------------------------------------------------------------
# Name:        ProcessManager.py
# Purpose:     platform magic
# Created:     2003/05/06
# RCS-ID:      $Id: ProcessManager.py,v 1.5 2005-10-10 16:18:14 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: ProcessManager.py,v 1.5 2005-10-10 16:18:14 eolson Exp $"

import sys
from AccessGrid.Platform import IsWindows, IsLinux, IsOSX, IsFreeBSD5

if IsWindows():
    from AccessGrid.Platform.win32.ProcessManager import *
elif IsLinux() or IsOSX() or IsFreeBSD5():
    from AccessGrid.Platform.unix.ProcessManager import *
else:
    print "No support for Platform %s" % sys.platform
