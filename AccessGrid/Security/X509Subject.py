#-----------------------------------------------------------------------------
# Name:        Subject.py
# Purpose:     Abstraction of a user in the system.
#
# Author:      Robert Olson
#
# Created:     
# RCS-ID:      $Id: X509Subject.py,v 1.6 2004-04-06 18:29:58 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
Subjects are the basic security handle on entities that want to be a
part of the security environment.
"""

__revision__ = "$Id: X509Subject.py,v 1.6 2004-04-06 18:29:58 eolson Exp $"


# external imports
from OpenSSL_AG.crypto import X509NameType
                                          
# imports from the AGTk
from AccessGrid.Security.Subject import Subject, InvalidSubject

class InvalidString(Exception):
    """
    A type other than string was present when a string was expected.
    """
    pass

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
        components = map(lambda a: a.split('='), self.name[1:].split('/'))
        cn = []
        
        for item in components:
            if item[0] == 'CN':
                cn.append(item[1])
                
        return ", ".join(cn)
            
                
def CreateSubjectFromString(subjectString):
    """
    Utility function that creates an X509Subject from a string, which
    should be a dn of the form:

    /O=Access Grid/OU=agdev-ca.mcs.anl.gov/OU=mcs.anl.gov/CN=Ivan Judson

    @param subjectString: the DN of the subject
    @type subjectString: string.
    """
    if type(subjectString) != type(""):
        raise InvalidString

    return X509Subject(subjectString)


if __name__ == "__main__":
    s = X509Subject("/O=Access Grid/OU=agdev-ca.mcs.anl.gov/OU=mcs.anl.gov/CN=Ivan Judson")
    print s.GetCN()
    s = X509Subject('/O=Access Grid/OU=agdev-ca.mcs.anl.gov/OU=mcs.anl.gov/CN=Robert Olson/CN=10435713')
    print s.GetCN()
  
