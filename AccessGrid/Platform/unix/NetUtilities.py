#-----------------------------------------------------------------------------
# Name:        NetUtilitiesLinux.py
# Purpose:     Utility routines for network manipulation, linux specific.
#
# Author:      Robert Olson
#
# Created:     9/11/2003
# RCS-ID:      $Id: NetUtilities.py,v 1.1 2004-03-24 21:25:08 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: NetUtilities.py,v 1.1 2004-03-24 21:25:08 eolson Exp $"
__docformat__ = "restructuredtext en"

import sys

__all__ = ["GetHTTPProxyAddresses"]

def GetHTTPProxyAddresses():
    """
    If the system has a proxy server defined for use, return its address.

    The return value is actually a list of tuples (server address, enabled).

    """

    return []
    
