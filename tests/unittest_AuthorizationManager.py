#-----------------------------------------------------------------------------
# Name:        unittest_AuthorizationManager.py
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
Unittest for AuthorizationManager.

"""

import signal, time
import unittest

from AccessGrid.AuthorizationManager import AuthorizationManager

class AuthorizationManagerTestCase(unittest.TestCase):
    """A test case for AuthorizationManager."""

    def testAuthorizationManagerDefault(self):
        a = AuthorizationManager()
        assert 0 == len(a.GetAuthorizedUsers())

    def testSetUsers(self):
        a = AuthorizationManager()
        userlist =  ["jim","bob","yogi"]
        a.SetAuthorizedUsers(userlist)
        assert userlist == a.GetAuthorizedUsers()

    def testAddUser(self):
        a = AuthorizationManager()
        a.AddAuthorizedUser("pepe")
        a.AddAuthorizedUser("thekingprawn")
        assert "pepe" in a.GetAuthorizedUsers()
        assert "thekingprawn" in a.GetAuthorizedUsers()

    def testRemoveUser(self):
        a = AuthorizationManager()
        a.AddAuthorizedUser("yogi")
        assert "yogi" in a.GetAuthorizedUsers()
        a.AddAuthorizedUser("bear")
        assert "bear" in a.GetAuthorizedUsers()

        a.RemoveAuthorizedUser("yogi")
        assert "yogi" not in a.GetAuthorizedUsers()
        a.RemoveAuthorizedUser("bear")
        assert "bear" not in a.GetAuthorizedUsers()

    def testAuthorizeUserInList(self):
        a = AuthorizationManager()
        a.AddAuthorizedUser("PicinicBasket")
        assert a.Authorize("PicinicBasket")

    def testAuthorizeUserNotInList(self):
        a = AuthorizationManager()
        assert not a.Authorize("Orko")
        a.AddAuthorizedUser("NotOrko")
        assert not a.Authorize("Orko")


def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(AuthorizationManagerTestCase)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')

