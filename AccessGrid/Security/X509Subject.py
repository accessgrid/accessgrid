#-----------------------------------------------------------------------------
# Name:        Subject.py
# Purpose:     Abstraction of a user in the system.
#
# Author:      Robert Olson
#
# Created:     
# RCS-ID:      $Id: X509Subject.py,v 1.4 2004-03-18 21:39:35 lefvert Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
Subjects are the basic security handle on entities that want to be a
part of the security environment.
"""

__revision__ = "$Id: X509Subject.py,v 1.4 2004-03-18 21:39:35 lefvert Exp $"


# external imports
from OpenSSL_AG.crypto import X509NameType
                                          
# imports from the AGTk
from AccessGrid.Security.Subject import Subject, InvalidSubject

class X509Subject(Subject):
    """
    This is the X509 Subject, which is a specific subclass of the
    subject class used in X509 certificate based systems.

    @cvar AUTH_TYPE: the authentication type, 'x509' for this class.
    @type AUTH_TYPE: string
    """

    AUTH_TYPE = "x509"
    AUTH_ANON = "anonymous"

    def __init__(self, name, auth_data = None):
        """
        @param name: the name of the subject
        @param auth_data: opaque data associated with this subject.
        @type name: string
        @type auth_data: string
        """
        Subject.__init__(self, name, self.AUTH_TYPE, auth_data)

    def GetCN(self):
        """
        Return a short form of the CN in an X509Subject object.

        @return: name as a string.
        """
        return self.name.split('=')[-1]
        
def CreateSubjectFromString(subjectString):
    """
    Utility function that creates an X509Subject from a string, which
    should be a dn of the form:

    /O=Access Grid/OU=agdev-ca.mcs.anl.gov/OU=mcs.anl.gov/CN=Ivan Judson

    @param subjectString: the DN of the subject
    @type subjectString: string.
    """
    return X509Subject(subjectString)
