#-----------------------------------------------------------------------------
# Name:        unittest_GUID.py
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
Unittest for GUID

"""

import signal, time, os
import unittest
from AccessGrid import Platform
from AccessGrid.GUID import GUID

class GUIDTestCase(unittest.TestCase):
    """A test case for GUID."""

    def testGUIDDefaultConstructor(self):
       g = GUID() 

    def testGUIDConstructor(self):
       g = GUID("asdadsf") 

    def testRepeatGUID(self):
       g1 = GUID("asdadsf") 
       g2 = GUID("asdadsf") 
       assert g1.guid == g2.guid

    def testRepeatGUID2(self):
       g1 = GUID()
       g2 = GUID()
       assert g1.guid != g2.guid

    def testRepeatGUID3(self):
       g1 = GUID("abcdefG")
       g2 = GUID("abcdefZ")
       assert g1.guid != g2.guid

def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(GUIDTestCase)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')

