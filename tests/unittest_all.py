#-----------------------------------------------------------------------------
# Name:        unittest_all.py
# Purpose:     
#
# Author:      Eric C. Olson
#   
# Created:     2003/04/01
# RCS-ID:    
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import unittest

def suite():
    # List modules to test
    modules_to_test = [
        'unittest_AGNodeService',
        'unittest_AGParameter',
        'unittest_AGServiceManager',
        'unittest_ClientProfile',
        'unittest_Descriptions',
        'unittest_GUID',
        'unittest_MulticastAddressAllocator',
        'unittest_NetworkLocation',
        'unittest_Node',
        'unittest_Platform',
        'unittest_VenueServer',
        'unittest_version'
        ]

    alltests = unittest.TestSuite()
    for module in map(__import__, modules_to_test):
       alltests.addTest(unittest.findTestCases(module))
    return alltests

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

