#-----------------------------------------------------------------------------
# Name:        unittest_NetworkLocation.py
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
Unittest for NetworkLocation

"""

import signal, time, os
import unittest
from AccessGrid.NetworkLocation import NetworkLocation, UnicastNetworkLocation, MulticastNetworkLocation

class NetworkLocationTestCase(unittest.TestCase):
    """A test case for NetworkLocation."""

    def testConstructor(self):
       n = NetworkLocation("vv2.mcs.anl.gov", 9000)
       assert n.GetHost() == "vv2.mcs.anl.gov"
       assert n.GetPort() == 9000

    def testGetSetHost(self):
       n = NetworkLocation("vv2.mcs.anl.gov", 9000)
       n.SetHost("vv2.mcs.anl.gov")
       assert n.GetHost() == "vv2.mcs.anl.gov"

    def testGetSetPort(self):
       n = NetworkLocation("vv2.mcs.anl.gov", 9000)
       n.SetPort(9000)
       assert n.GetPort() == 9000

class UnicastNetworkLocationTestCase(unittest.TestCase):
    """A test case for UnicastNetworkLocation."""

    def testConstructor(self):
       n = UnicastNetworkLocation("vv2.mcs.anl.gov", 9000)
       assert n.GetHost() == "vv2.mcs.anl.gov"
       assert n.GetPort() == 9000

    def testGetSetHost(self):
       n = UnicastNetworkLocation("vv2.mcs.anl.gov", 9000)
       n.SetHost("vv2.mcs.anl.gov")
       assert n.GetHost() == "vv2.mcs.anl.gov"

    def testGetSetPort(self):
       n = UnicastNetworkLocation("vv2.mcs.anl.gov", 9000)
       n.SetPort(9000)
       assert n.GetPort() == 9000

class MulticastNetworkLocationTestCase(unittest.TestCase):
    """A test case for MulticastNetworkLocation."""

    def testDefaultConstructor(self):
       n = MulticastNetworkLocation()

    def testConstructor(self):
       n = MulticastNetworkLocation("vv2.mcs.anl.gov", 9000, 127)
       assert n.GetHost() == "vv2.mcs.anl.gov"
       assert n.GetPort() == 9000

    def testGetSetHost(self):
       n = MulticastNetworkLocation() 
       n.SetHost("vv2.mcs.anl.gov")
       assert n.GetHost() == "vv2.mcs.anl.gov"

    def testGetSetPort(self):
       n = MulticastNetworkLocation() 
       n.SetPort(9000)
       assert n.GetPort() == 9000

    def testGetSetTTL(self):
       n = MulticastNetworkLocation() 
       n.SetTTL(255)
       assert n.GetTTL() == 255


def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(NetworkLocationTestCase)
    suite2 = unittest.makeSuite(UnicastNetworkLocationTestCase)
    suite3 = unittest.makeSuite(MulticastNetworkLocationTestCase)
    return unittest.TestSuite([suite1,suite2,suite3])

if __name__ == '__main__':
    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')

