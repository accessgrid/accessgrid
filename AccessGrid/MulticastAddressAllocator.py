#-----------------------------------------------------------------------------
# Name:        MulticastAddressAllocator.py
# Purpose:     This class manages multicast address allocation.
#
# Author:      Robert Olson, Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: MulticastAddressAllocator.py,v 1.9 2003-02-10 14:47:35 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
import socket
import struct
from random import Random
import time

import NetworkLocation

class MulticastAddressAllocator:
    """
    This class provides a clean API for allocating multicast addresses. It can 
    provide addresses either randomly from the predefined SDP pool or randomly
    from a pool provided by the user.
    """

    RANDOM = "random"
    INTERVAL = "interval"

    def __init__(self, baseAddress = None, addressMask = None,
                 portBase = 49152):
        """
        We initialize this class with the information needed to allocate
        addresses. A base address and address mask imply we're allocating
        from a GLOP address space. If a base address and mask are not supplied
        the allocator allocates from the SDR address space.
        """
        self.allocatedAddresses = []
        self.allocatedPorts = []
        
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
        self.random = Random(time.clock())

        self.addressAllocationMethod = MulticastAddressAllocator.INTERVAL

    def SetBaseAddress(self, baseAddress):
        self.baseAddress = struct.unpack("L", socket.inet_aton(baseAddress))[0]
                                        
    def GetBaseAddress(self):
        return socket.inet_ntoa(struct.pack('L', self.baseAddress))

    def SetAddressMask(self, addressMask = None):
        self.addressMask = addressMask

    def GetAddressMask( self ):
        return self.addressMask

    def SetAddressAllocationMethod( self, method ):
        self.addressAllocationMethod = method

    def GetAddressAllocationMethod( self ):
        return self.addressAllocationMethod

    def AllocatePort(self):
        """
        We allocate only even numbered ports since that is the requirement
        for rtp encapsulated streams.
        """
        inUse = 0
        port = self.random.randrange(self.portBase, 65535, 2)
        # Check to see if port is used
        while port in self.allocatedPorts and inUse:
            port = self.random.randrange(self.portBase, 65535, 2)
            try:
                s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
                s.bind(("", port ) )
                s.close()
                inUse = 0
            except socket.error:
                inUse = 1
                continue
        self.allocatedPorts.append(port)
        return port
        
    def RecyclePort(self, port):
        self.allocatedPorts.remove(port)

    def AllocateAddress(self):
        randomNumber = self.random.randrange(sys.maxint)
        newAddress = self.baseAddress & self.addressMask
        newAddress = newAddress | (randomNumber & ~self.addressMask)
        addressString = socket.inet_ntoa(struct.pack("L", newAddress))
        
        while addressString in self.allocatedAddresses:
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
