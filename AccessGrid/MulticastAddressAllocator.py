#-----------------------------------------------------------------------------
# Name:        MulticastAddressAllocator.py
# Purpose:     This class manages multicast address allocation.
#
# Author:      Robert Olson, Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: MulticastAddressAllocator.py,v 1.4 2003-01-21 16:57:12 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
import socket
import struct

from random import Random
import time
import NetworkLocation

class MulticastAddressAllocator:
    __doc__ = """

    """

    RANDOM = "random"
    INTERVAL = "interval"

    baseAddress = ''
    addressMask = ''

    allocatedAddresses = []
    portBase = 0
    portMask = 0
    allocatedPorts = []
    random = None
    mask = ''
    

    def __init__(self, baseAddress = None, addressMask = None, 
                 portBase = 49152, portMask = 0x3fff):
        """
        We initialize this class with the information needed to allocate
        addresses. A base address and address mask imply we're allocating
        from a GLOP address space. If a base address and mask are not supplied
        the allocator allocates from the SDR address space.
        """
        if baseAddress == None:
            # 224.2.128.0

            self.baseAddress = socket.htonl(0xe0028000) 
        else:
            self.baseAddress = struct.unpack("L", 
                                        socket.inet_aton(baseAddress))[0]
        
        if addressMask == None:
            # 255.255.128.0
            self.addressMask = socket.htonl(0xffff8000)
        else:
            self.addressMask = socket.htonl(~((1 << (32 - addressMask)) - 1))
            
        self.portBase = portBase
        self.portMask = portMask
        self.random = Random(time.clock())

        self.addressAllocationMethod = MulticastAddressAllocator.INTERVAL


    def SetBaseAddress(self, baseAddress ):
        #self.lowerAddress = socket.htonl(baseAddress)
        self.lowerAddress = baseAddress

    def GetBaseAddress(self):
        return self.lowerAddress

    def SetAddressMask(self, addressMask = None):
        self.addressMask = addressMask

    def GetAddressMask( self ):
        return self.addressMask

    def SetAddressAllocationMethod( self, method ):
        self.addressAlloctionMethod = method

    def GetAddressAllocationMethod( self ):
        return self.addressAllocationMethod
    
    def AllocatePort(self):
        """
        We allocate only even numbered ports since that is the requirement
        for rtp encapsulated streams.
        """
        randomNumber = self.random.randrange(self.portBase, 65535, 2)
        port = (randomNumber & self.portMask) + self.portBase
        self.allocatedPorts.append(port)    
        return port
    
    def RecyclePort(self, port):
        self.allocatedPorts.remove(port)
        
    def AllocateAddress(self):
        randomNumber = self.random.randrange(sys.maxint)        
        newAddress = self.baseAddress & self.addressMask
        newAddress = newAddress | (randomNumber & ~self.addressMask)
    
        addressString = socket.inet_ntoa(struct.pack("L", newAddress))
        self.allocatedAddresses.append(addressString)
        
        return addressString

    def RecycleAddress(self, address):
        self.addressesInUse.remove(address)
        
if __name__ == "__main__":
    iter = 10
    multicastAddressAllocator = MulticastAddressAllocator()
    print "%d random addresses: " % (iter)
    for i in range(0, iter):
        print multicastAddressAllocator.AllocateAddress()
        
    multicastAddressAllocator = MulticastAddressAllocator("233.2.171.1", 24)
    print "%d random ANL GLOP addresses: " % (iter)
    for i in range(0, iter):
        print multicastAddressAllocator.AllocateAddress()

    print "%d random ports:" % (iter)
    for i in range(0, iter):
        print multicastAddressAllocator.AllocatePort()    
