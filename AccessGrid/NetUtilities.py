#-----------------------------------------------------------------------------
# Name:        NetUtilities.py
# Purpose:     Utility routines for network manipulation.
#
# Author:      Robert Olson
#
# Created:     9/11/2003
# RCS-ID:      $Id: NetUtilities.py,v 1.2 2003-09-16 07:20:18 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: NetUtilities.py,v 1.2 2003-09-16 07:20:18 judson Exp $"
__docformat__ = "restructuredtext en"

import sys

if sys.platform == "win32":

    from NetUtilitiesWin32 import *

elif sys.platform.startswith("linux"):

    from NetUtilitiesLinux import *

else:

    log.warn("NetUtilities doesn't have a platform-specific module for %s", sys.platform)
    
