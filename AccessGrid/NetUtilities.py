#-----------------------------------------------------------------------------
# Name:        NetUtilities.py
# Purpose:     Utility routines for network manipulation.
#
# Author:      Robert Olson
#
# Created:     9/11/2003
# RCS-ID:      $Id: NetUtilities.py,v 1.8 2004-09-09 22:12:12 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: NetUtilities.py,v 1.8 2004-09-09 22:12:12 turam Exp $"
__docformat__ = "restructuredtext en"

import struct
import select
import socket

TIME1970 = 2208988800L      # Thanks to F.Lundh

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
