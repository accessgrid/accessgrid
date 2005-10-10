#-----------------------------------------------------------------------------
# Name:        Config.py
# Purpose:     Configuration objects for applications using the toolkit.
#              there are config objects for various sub-parts of the system.
# Created:     2003/05/06
# RCS-ID:      $Id: Config.py,v 1.5 2005-10-10 16:18:14 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Config.py,v 1.5 2005-10-10 16:18:14 eolson Exp $"

import sys
from AccessGrid.Platform import IsWindows, IsLinux, IsOSX, IsFreeBSD5

if IsWindows():
    from AccessGrid.Platform.win32.Config import *
elif IsLinux() or IsOSX() or IsFreeBSD5():
    from AccessGrid.Platform.unix.Config import *
else:
    print "No support for Platform %s" % sys.platform
