#-----------------------------------------------------------------------------
# Name:        NetUtilitiesLinux.py
# Purpose:     Utility routines for network manipulation, linux specific.
#
# Author:      Robert Olson
#
# Created:     9/11/2003
# RCS-ID:      $Id: NetUtilitiesLinux.py,v 1.1 2003-09-11 21:37:27 olson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys

__all__ = ["GetHTTPProxyAddresses"]

def GetHTTPProxyAddresses():
    """
    If the system has a proxy server defined for use, return its address.

    The return value is actually a list of tuples (server address, enabled).

    """

    return []
    
