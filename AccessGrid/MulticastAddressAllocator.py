#-----------------------------------------------------------------------------
# Name:        MulticastAddressAllocator.py
# Purpose:     This class manages multicast address allocation.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: MulticastAddressAllocator.py,v 1.1.1.1 2002-12-16 22:25:37 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import NetworkLocation
from random import Random
import time

class MulticastAddressAllocator:
    __doc__ = """
    
    """
    lowerAddress = ''
    addressMask = ''
    allocateRandom = 0
    allocatedAddresses = []
    random = None
    
    def __init__(self, lowerAddress = '0.0.0.0', addressMask = '0', 
                 allocateRandom = 1):
        self.lowerAddress = lowerAddress
        self.addressMask = addressMask
        self.allocateRandom = allocateRandom
        self.random = Random(time.clock())
        
    def SetLowerAddress(self, lowerAddress = None):
        self.lowerAddress = lowerAddress
        
    def GetLowerAddress(self):
        return self.lowerAddress
    
    def SetAddressMask(self, addressMask = None):
        self.addressMask = addressMask
        
    def SetAllocateRandom(self, allocateRandom = 1):
        self.allocateRandom = allocateRandom
        
    def GetAllocateRandom(self):
        return self.allocateRandom
    
    def allocateAddress(self):
        address = ''
        # This should actually do something to create the address it returns.
        self.allocatedAddresses[address]
        
        return address
        
    def recycleAddress(self, address):
        self.allocatedAddresses[address]