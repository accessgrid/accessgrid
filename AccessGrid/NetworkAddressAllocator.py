#-----------------------------------------------------------------------------
# Name:        NetworkAddressAllocator.py
# Purpose:     This class manages multicast address allocation.
#
# Author:      Robert Olson, Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: NetworkAddressAllocator.py,v 1.3 2004-03-31 22:13:26 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: NetworkAddressAllocator.py,v 1.3 2004-03-31 22:13:26 turam Exp $"
__docformat__ = "restructuredtext en"

import sys
import socket
import struct
from random import Random

class NoFreePortsError(Exception):
    pass

class NetworkAddressAllocator:
    """
    This class provides a clean API for allocating general network
    addresses. For typical unicast networks this devolves to picking
    port numbers. So that's all that's done here.
    """
    RANDOM = "random"
    INTERVAL = "interval"
    
    def __init__(self, portBase = 49152, portMax=65535):
        """
        We only need to initialize port information.
        """
        self.portBase = portBase
        self.portMax = portMax
        
        self.allocatedPorts = []
        self.random = Random()

        self.allocationMethod = NetworkAddressAllocator.RANDOM
        
    def SetAllocationMethod( self, method ):
        self.allocationMethod = method
        return self.allocationMethod
    
    def GetAllocationMethod( self ):
        return self.allocationMethod

    def SetPortBase(self, portBase):
        self.portBase = portBase

    def SetPortMax(self, portMax):
        self.portMax = portMax

    def AllocatePort(self, even = 0):
        """
        if the even flag is set we allocate only an even port to support
        RTP standard use cases.
        """
        
        # Check to see whether any ports are available
        numPorts = 1 + (self.portMax - self.portBase)/2
        if numPorts == len(self.allocatedPorts):
            raise NoFreePortsError
            
        port = self.AllocatePortInRange(even,self.portBase,self.portMax)
        return port
        
    def AllocatePortInRange(self, even, portBase, portMax):
    
        # Check to see if port is used
        if even:
            modulus = 2
        else:
            modulus = 1
        while 1:
            port = self.random.randrange(portBase, portMax, modulus)
            if port in self.allocatedPorts:
                continue
            
            try:
                s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
                s.bind(("", port ) )
                s.close()
                break
            except socket.error:
                continue
            
        self.allocatedPorts.append(port)
        return port
    
        
    def RecyclePort(self, port):
        self.allocatedPorts.remove(port)
        return port
    
if __name__ == "__main__":
    iter = 10
    netAddressAllocator = NetworkAddressAllocator()
    print "%d random ports: " % (iter)
    for i in range(0, iter):
        print netAddressAllocator.AllocatePort()

    print "%d random even ports: " % (iter)
    for i in range(0, iter):
        print netAddressAllocator.AllocatePort(1)

