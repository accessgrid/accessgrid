#-----------------------------------------------------------------------------
# Name:        NetUtilities.py
# Purpose:     Utility routines for network manipulation.
#
# Author:      Robert Olson
#
# Created:     9/11/2003
# RCS-ID:      $Id: NetUtilities.py,v 1.1 2003-09-11 21:37:27 olson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys

if sys.platform == "win32":

    from NetUtilitiesWin32 import *

elif sys.platform.startswith("linux"):

    from NetUtilitiesLinux import *

else:

    log.warn("NetUtilities doesn't have a platform-specific module for %s", sys.platform)
    
