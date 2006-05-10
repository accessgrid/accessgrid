#-----------------------------------------------------------------------------
# Name:        Config.py
# Purpose:     Configuration objects for applications using the toolkit.
#              there are config objects for various sub-parts of the system.
# Created:     2003/05/06
# RCS-ID:      $Id: Config.py,v 1.6 2006-05-10 01:30:04 willing Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Config.py,v 1.6 2006-05-10 01:30:04 willing Exp $"

import sys
from AccessGrid.Platform import IsWindows, IsLinux, IsOSX, IsFreeBSD

if IsWindows():
    from AccessGrid.Platform.win32.Config import *
elif IsLinux() or IsOSX() or IsFreeBSD():
    from AccessGrid.Platform.unix.Config import *
else:
    print "No support for Platform %s" % sys.platform
