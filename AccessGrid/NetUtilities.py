#-----------------------------------------------------------------------------
# Name:        NetUtilities.py
# Purpose:     Utility routines for network manipulation.
#
# Author:      Robert Olson
#
# Created:     9/11/2003
# RCS-ID:      $Id: NetUtilities.py,v 1.6 2004-02-26 16:46:10 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: NetUtilities.py,v 1.6 2004-02-26 16:46:10 judson Exp $"
__docformat__ = "restructuredtext en"

import sys
import struct
import time
import select
import socket
from AccessGrid.Platform import isOSX, isWindows, isLinux

TIME1970 = 2208988800L      # Thanks to F.Lundh

if isWindows():
    from AccessGrid.Platform.win32.NetUtilities import *
elif isLinux():
    from AccessGrid.Platform.linux2.NetUtilities import *
elif isOSX():
    from AccessGrid.Platform.darwin.NetUtilities import *
else:
    log.warn("NetUtilities doesn't have a platform-specific module for %s",
             sys.platform)

#
# Thanks the ASPN python recipes folks for this.
# (http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/117211)
#

def GetSNTPTime(server, timeout):
    """
    Retrieve the time from the given time server, with a timeout.

    @param server: Hostname or IP address of the time server.

    @param timeout: Timeout for the request, in seconds (fractions allowed).

    @return: Time from that server, in seconds-since-1970, or None if
    the request failed for any reason.
    
    """

    client = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
    data = '\x1b' + 47 * '\0'
    client.sendto( data, (server, 123 ))

    x = select.select([client], [], [], timeout)
    if x[0] != []:
        
        data, address = client.recvfrom( 1024 )
        client.close()
        if data:
            t = struct.unpack( '!12I', data )[10]
            t -= TIME1970
            return t
        else:
            client.close()
            return None
    else:
        client.close()
        return None

import socket
import pyGlobus.utilc

def GetHostname():
    """
    Return the local hostname.

    This uses the pyGlobus mechanism when possible, in order
    to get a hostname that Globus will be happy with.

    """
    ret, host = pyGlobus.utilc.get_hostname(256)
    if ret != 0:
        host = socket.getfqdn()
    return host

