#-----------------------------------------------------------------------------
# Name:        MulticastAddressAllocator.py
# Purpose:     This class manages multicast address allocation.
# Created:     2002/12/12
# RCS-ID:      $Id: MulticastAddressAllocator.py,v 1.19 2004-09-07 13:48:59 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: MulticastAddressAllocator.py,v 1.19 2004-09-07 13:48:59 judson Exp $"
__docformat__ = "restructuredtext en"

import sys
import socket
import struct
from random import Random

from AccessGrid.NetworkAddressAllocator import NetworkAddressAllocator

class MulticastAddressAllocator(NetworkAddressAllocator):
    """
    This class provides a clean API for allocating multicast addresses. It can 
    provide addresses either randomly from the predefined SDP pool or randomly
    from a pool provided by the user.
    """

    RANDOM = "random"
    INTERVAL = "interval"
    SDR_BASE_ADDRESS = '224.2.128.0'
    SDR_MASK_SIZE = 17

    def __init__(self, baseAddress = None, addressMaskSize = 24,
                 portBase = 49152):
        """
        We initialize this class with the information needed to allocate
        addresses. A base address and address mask imply we're allocating
        from a GLOP address space. If a base address and mask are not supplied
        the allocator allocates from the SDR address space.
        """
        NetworkAddressAllocator.__init__(self, portBase)
        
        self.baseAddress = baseAddress
        self.addressMaskSize = addressMaskSize
        self.allocatedAddresses = []
        
        if self.baseAddress == None:
            # 224.2.128.0
            self.baseAddress = struct.unpack("<L",
               socket.inet_aton(MulticastAddressAllocator.SDR_BASE_ADDRESS))[0]
            self.addressMaskSize = MulticastAddressAllocator.SDR_MASK_SIZE
        else:
            self.baseAddress = struct.unpack("<L",
                                        socket.inet_aton(baseAddress))[0]

        self.addressMask = socket.htonl(~((1<<(32-self.addressMaskSize))-1))

    def SetBaseAddress(self, baseAddress):
        self.baseAddress = struct.unpack("<L",
                                         socket.inet_aton(baseAddress))[0]
        return self.baseAddress
                                        
    def GetBaseAddress(self):
        return socket.inet_ntoa(struct.pack('<L', self.baseAddress))

    # These don't mean what they did before! IRJ-2002-2-22
    def SetAddressMask(self, addressMaskSize = 24):
        self.addressMaskSize = addressMaskSize
        self.addressMask = socket.htonl(~((1<<(32-self.addressMaskSize))-1))
        return self.addressMaskSize

    def GetAddressMask( self ):
        return self.addressMaskSize

    def AllocateAddress(self):
        randomNumber = self.random.randrange(sys.maxint)
        newAddress = self.baseAddress & self.addressMask
        newAddress = newAddress | (randomNumber & ~self.addressMask)
        addressString = socket.inet_ntoa(struct.pack("<L", newAddress))
        
        while addressString in self.allocatedAddresses:
            randomNumber = self.random.randrange(sys.maxint)
            newAddress = self.baseAddress & self.addressMask
            newAddress = newAddress | (randomNumber & ~self.addressMask)
            addressString = socket.inet_ntoa(struct.pack("<L", newAddress))
 
        self.allocatedAddresses.append(addressString)

        return addressString

    def RecycleAddress(self, address):
        self.allocatedAddresses.remove(address)
        return address

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

    print "%d random even ports: " % (iter)
    for i in range(0, iter):
        print multicastAddressAllocator.AllocatePort(1)

    mask = 28
    multicastAddressAllocator.SetAddressMask(mask)
    print "%d random addresses with mask %d:" % (iter,mask)
    for i in range(0, iter):
        print multicastAddressAllocator.AllocateAddress()
