#-----------------------------------------------------------------------------
# Name:        unittest_Version.py
# Purpose:     
#
# Author:      Eric C. Olson
#   
# Created:     2003/08/20
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
    
"""
Unittest for Version

"""

import unittest
from AccessGrid.Toolkit import GetVersion, CreateVersionFromString

class AGVersionTestCase(unittest.TestCase):
    """A test case for Version."""

    def testA(self):
       a = GetVersion()
       b = GetVersion()
       assert a == b
       assert a >= b
       assert a <= b
       assert not a < b
       assert not a > b
       assert not (a <> b)
       assert a.AsString() == b.AsString()
       assert a.AsTuple3() == b.AsTuple3()

    def testB(self):
       a = CreateVersionFromString("2.1.0")
       b = CreateVersionFromString("2.0.0")
       assert not a == b
       assert a >= b
       assert not a <= b
       assert a > b
       assert not a < b
       assert a <> b
       assert a.AsString() == "2.1.0"
       assert b.AsString() == "2.0.0"
       assert a.AsTuple3() == (2,1,0)
       assert b.AsTuple3() == (2,0,0)

    def testC(self):
       a = CreateVersionFromString("2.1.0")
       b = CreateVersionFromString("2.1.1")
       assert not a == b
       assert not a >= b
       assert a <= b
       assert not a > b
       assert a < b
       assert a <> b
       assert a.AsString() == "2.1.0"
       assert b.AsString() == "2.1.1"
       assert a.AsTuple3() == (2,1,0)
       assert b.AsTuple3() == (2,1,1)

    def testC(self):
       a = CreateVersionFromString("2.0.1")
       b = CreateVersionFromString("2.1.1")
       assert not a == b
       assert not a >= b
       assert a <= b
       assert not a > b
       assert a < b
       assert a <> b
       assert a.AsString() == "2.0.1"
       assert b.AsString() == "2.1.1"
       assert a.AsTuple3() == (2,0,1)
       assert b.AsTuple3() == (2,1,1)

    def testD(self):
       a = CreateVersionFromString("0.2.3")
       b = CreateVersionFromString("1.2.3")
       assert not a == b
       assert not a >= b
       assert a <= b
       assert not a > b
       assert a < b
       assert a <> b
       assert a.AsString() == "0.2.3"
       assert b.AsString() == "1.2.3"
       assert a.AsTuple3() == (0,2,3)
       assert b.AsTuple3() == (1,2,3)

    def testD(self):
       a = CreateVersionFromString("1.2.3")
       b = CreateVersionFromString("0.2.3")
       assert not a == b
       assert not a <= b
       assert a >= b
       assert not a < b
       assert a > b
       assert a <> b
       assert a.AsString() == "1.2.3"
       assert b.AsString() == "0.2.3"
       assert a.AsTuple3() == (1,2,3)
       assert b.AsTuple3() == (0,2,3)

def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(AGVersionTestCase)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')
