#-----------------------------------------------------------------------------
# Name:        unittest_AGParameter.py
# Purpose:     
#
# Author:      Eric C. Olson
#   
# Created:     2003/05/07
# RCS-ID:    
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
Unittest for AGParameter

"""

import signal, time
import unittest

from AccessGrid.AGParameter import *

class AGParameterTestCase(unittest.TestCase):
    """A test case for AGParameter."""

   # ValueParameter

    def testValueParameter(self):
        # Test default constructor
        name = "testValueParameter"
        v = ValueParameter(name)
        assert v.name == name
        assert v.type == ValueParameter.TYPE
        # Test passing value to constructor
        val = 5
        v2 = ValueParameter(name, val)
        assert v2.value == val

    def testSetValueParameter(self):
        v = ValueParameter("testValueParameter2")
        v.SetValue(5)
        assert v.value == 5

   # TextParameter

    def testTextParameter(self):
        # Test default constructor
        name = "testTextParameter"
        v = TextParameter(name)
        assert v.name == name
        assert v.type == TextParameter.TYPE
        # Test passing value to constructor
        v2 = TextParameter(name, "test text")
        assert v2.value == "test text"

    def testSetTextParameter(self):
        v = TextParameter("testTextParameter2")
        v.SetValue("test text2")
        assert v.value == "test text2"

    # RangeParameter

    def testRangeParameter(self):
        name = "testRangeParameter"
        val = 5
        low = 1
        high = 9
        v = RangeParameter(name, val, low, high)
        assert v.name == name
        assert v.type == RangeParameter.TYPE
        assert v.value == val 

    def testSetRangeParameter(self):
        val = 5
        low = 1
        high = 9
        v = RangeParameter("testRangeParameter2", val, low, high)
        v.SetValue(6)
        assert v.value == 6

    def testSetTooLowRangeParameter(self):
        v = RangeParameter("testRangeParameter3", 5, 1, 9)

        # Set range too low
        out_of_range_detected = 0
        try:
            v.SetValue(0)
        except ValueError:
            out_of_range_detected = 1
        else:
            assert 0 

        # make sure exception was thrown for being out of range.
        assert out_of_range_detected

    def testSetTooHighRangeParameter(self):
        v = RangeParameter("testRangeParameter4", 5, 1, 9)

        # Set range too high
        out_of_range_detected = 0
        try:
            v.SetValue(20)
        except ValueError:
            out_of_range_detected = 1
        else:
            assert 0 

        # make sure exception was thrown for being out of range.
        assert out_of_range_detected

    # Option Parameter
        
    def testOptionSetParameter(self):
        name = "testOptionParameter"
        value = "optionA"
        options = ["optionA", "optionB", "optionC"]
        v = OptionSetParameter(name, value, options)
        assert v.name == name
        assert v.type == OptionSetParameter.TYPE
        assert v.value == value
        assert v.options == options

    def testSetValidOptionSetParameter(self):
        name = "testOptionParameter2"
        options = [16, 32, 64]
        value = 16
        v = OptionSetParameter(name, value, options)
        v.SetValue(32)
        assert v.value == 32

    def testSetInvalidOptionSetParameter(self):
        name = "testOptionParameter3"
        options = [16, 32, 64]
        value = 16
        v = OptionSetParameter(name, value, options)

        invalid_option = 0
        try:
            v.SetValue(47)
        except KeyError:
            invalid_option = 1
        else:
            assert 0 

        # make sure exception was thrown for being invalid.
        assert invalid_option

def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(AGParameterTestCase)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')

