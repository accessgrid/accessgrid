#-----------------------------------------------------------------------------
# Name:        Subject.py
# Purpose:     Abstraction of a user in the system.
#
# Author:      Robert Olson
#
# Created:     
# RCS-ID:      $Id: X509Subject.py,v 1.2 2004-02-24 21:33:07 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Subjects are the basic security handle on entities that want to be a
part of the security environment.
"""

__revision__ = "$Id: X509Subject.py,v 1.2 2004-02-24 21:33:07 judson Exp $"
__docformat__ = "restructuredtext en"


"""
This is the X509 Subject, which is a specific subclass of the subject.
"""

from OpenSSL_AG.crypto import X509NameType

from AccessGrid.Security.Subject import Subject, InvalidSubject

class X509Subject(Subject):
    AUTH_TYPE = "x509"
    AUTH_ANON = "anonymous"

    def __init__(self, name, auth_data = None):
        Subject.__init__(self, name, self.AUTH_TYPE, auth_data)

def CreateSubjectFromString(subjectString):
    return X509Subject(subjectString)
