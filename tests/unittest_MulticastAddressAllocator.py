#-----------------------------------------------------------------------------
# Name:        unittest_MulticastAddressAllocator.py
# Purpose:     
#
# Author:      Eric C. Olson
#   
# Created:     2003/05/14
# RCS-ID:    
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
Unittest for MulticastAddressAllocator

"""

import signal, time, os
import unittest
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator 
from AccessGrid.NetworkAddressAllocator import NetworkAddressAllocator

class MulticastAddressAllocatorTestCase(unittest.TestCase):
    """A test case for MulticastAddressAllocator."""

    # if a base address and mask are not supplied, we are using SDR address space.
    def testSDRConstructor(self):
       m = MulticastAddressAllocator() 

    # if a base address and mask are supplied, we are using GLOP address space.
    def testGLOPConstructor(self):
       m = MulticastAddressAllocator(baseAddress="233.2.171.1", addressMaskSize=24, portBase=61284) 
       assert m.GetAddressMask() == 24
       assert m.portBase == 61284

    def testAllocateSDRAddresses(self):
       m = MulticastAddressAllocator()
       for i in range(0, 10):
           address = m.AllocateAddress()
           assert address != "" 
           assert address in m.allocatedAddresses

    def testAllocateGLOPAddresses(self):
       m = MulticastAddressAllocator("233.2.171.1", 24)
       for i in range(0, 10):
           address = m.AllocateAddress()
           assert address != "" 
           assert address in m.allocatedAddresses

    def testAllocateGLOPPorts(self):
       m = MulticastAddressAllocator("233.2.171.1", 24)
       for i in range(0, 10):
           port = m.AllocatePort()
           assert port != 0
           assert port in m.allocatedPorts

    def testSetGetBaseAddress(self):
       m = MulticastAddressAllocator() 
       # this argument is for testing, it's may not be a valid base address.
       m.SetBaseAddress("127.0.0.1")
       assert "127.0.0.1" == m.GetBaseAddress()

    def testSetGetAddressMask(self):
       m = MulticastAddressAllocator() 
       # this argument is for testing, it's may not be a valid address mask.
       m.SetAddressMask(12)
       assert 12 == m.GetAddressMask()

    def testSetGetAddressAllocationMethod(self):
       m = MulticastAddressAllocator() 
       m.SetAllocationMethod(NetworkAddressAllocator.INTERVAL)
       assert NetworkAddressAllocator.INTERVAL == m.GetAllocationMethod()

    def testRecyclePort(self):
       m = MulticastAddressAllocator() 
       port = m.AllocatePort()
       assert port in m.allocatedPorts
       m.RecyclePort(port)
       assert port not in m.allocatedPorts

    def testRecycleAddress(self):
       m = MulticastAddressAllocator() 
       address = m.AllocateAddress()
       assert address != ""
       assert address in m.allocatedAddresses
       m.RecycleAddress(address)
       assert address not in m.allocatedAddresses

def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(MulticastAddressAllocatorTestCase)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')

