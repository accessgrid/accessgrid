#-----------------------------------------------------------------------------
# Name:        unittest_Utilities.py
# Purpose:     
#   
# Created:     2004/08/04
# Copyright:   (c) 2004
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
    
"""
Unittest for Version

"""

import os, unittest
from AccessGrid import Utilities, Platform

class AGUtilitiesTestCase(unittest.TestCase):
    """A test case for Version."""

    def testIsExecFileAvailable(self):
        # Test for a file that should always be executable for us.
        if Platform.IsWindows():
            assert Utilities.IsExecFileAvailable("python.exe")
        else:
            assert Utilities.IsExecFileAvailable("python")
            # create a non-executable file
            tmpfile = os.path.join(Platform.Config.SystemConfig.instance().GetTempDir(), "tmpnonexecfile")
            f = open(tmpfile, "w")
            f.write("test")
            f.close()
            # verify the file was created and is non-executable.
            assert os.path.exists(tmpfile) and not Utilities.IsExecFileAvailable(tmpfile)
            os.remove(tmpfile)
        # Test a file that shouldn't exist
        assert not Utilities.IsExecFileAvailable("_ThisIsAnInvalidCommand.exe")

def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(AGUtilitiesTestCase)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')
