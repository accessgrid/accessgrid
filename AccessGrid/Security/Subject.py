#-----------------------------------------------------------------------------
# Name:        Subject.py
# Purpose:     Abstraction of a user in the system.
#
# Author:      Robert Olson
#
# Created:     
# RCS-ID:      $Id: Subject.py,v 1.3 2004-02-25 18:29:31 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Subjects are the basic security handle on entities that want to be a
part of the security environment.
"""

__revision__ = "$Id: Subject.py,v 1.3 2004-02-25 18:29:31 eolson Exp $"
__docformat__ = "restructuredtext en"

import xml.dom.minidom

class InvalidSubject(Exception):
    """
    This is an invalid subject.
    """
    pass

class SubjectTypesDifferent(Exception):
    """
    Subject types don't match.
    """
    pass

class Subject:
    """
    A Subject instance represents an AG user.

    A Subject can be identified by various authentication
    mechanisms. we currently support X509 certificates (per Globus).
    """
    
    def __init__(self, name, auth_type, auth_data = None):
        self.name = name
        self.auth_type = auth_type
        self.auth_data = auth_data

    def __cmp__(self, other):
        if self.auth_type != other.auth_type:
            raise SubjectTypesDifferent
        
        if (self.name == other.name and
            self.auth_data == other.auth_data):
            return 1
        else:
            return 0
        
    def _repr_(self):
        domImpl = xml.dom.minidom.getDOMImplementation()
        doc = domImpl.createDocument(xml.dom.minidom.EMPTY_NAMESPACE,
                                     "Subject", None)
        return self.ToXML(doc).toxml()

    def __str__(self):
        return self._repr_()
        
    def ToXML(self, doc):
        sx = doc.createElement("Subject")
        # This converts the actual complicated object into a simple string
        sx.setAttribute("name", "%s" % self.name)
        sx.setAttribute("auth_type", self.auth_type)
        sx.setAttribute("auth_data", "%s" % self.auth_data)
        return sx

    def GetName(self):
        return self.name

    def GetAuthenticationType(self):
        return self.auth_type

    def GetAuthenticationData(self):
        return self.auth_data

    def GetSubject(self):
        return (self.auth_type, self.name, self.auth_data)



