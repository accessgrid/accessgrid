#-----------------------------------------------------------------------------
# Name:        Subject.py
# Purpose:     Abstraction of a user in the system.
#
# Author:      Robert Olson
#
# Created:     
# RCS-ID:      $Id: Subject.py,v 1.8 2004-03-04 20:09:02 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
Subjects, as described in AGEP-0105.txt.

Subjects are the basic security handle on entities that want to be a
part of the secure Access Grid Toolkit.
"""

__revision__ = "$Id: Subject.py,v 1.8 2004-03-04 20:09:02 judson Exp $"

# External Imports
import xml.dom.minidom

# Internal Imports
from AccessGrid.GUID import GUID

class InvalidSubject(Exception):
    """
    An invalid subjects was operated upon, specified, or retrieved.
    """
    pass

class SubjectTypesDifferent(Exception):
    """
    Subjects of differing types were compared or operated on.
    """
    pass

class Subject:
    """
    A Subject is an instance of a credential used by an AG User.

    A Subject can be identified by various authentication
    mechanisms. we currently support X509 certificates (per Globus).
    """
    def __init__(self, name, auth_type, auth_data = None, id = str(GUID())):
        """
        @param name: the name of the subject
        @param auth_type: the type of authentication used for the subject
        @param auth_data: opaque authentication specific data
        @param id: a globally unique identifier for this object
        @type name: string
        @type auth_type: string
        @type auth_data: string
        @type id: a string containing a globally unique identifier
        """
        self.name = name
        self.auth_type = auth_type
        self.auth_data = auth_data
        self.id = id

    def __hash__(self):
        """
        A hash method so subjects can be used as dictionary keys.

        @returns: the id attribute which is a globally unique identifier in a string.
        """
        return long(self.id, 16)
    
    def __cmp__(self, other):
        """
        Comparison operator, so two subjects can be compared.

        This method compares this subject with the one specified. If
        they match it returns one otherwise it returns 0.

        @param other: the subject to compare this one with
        @type other: AccessGrid.Security.Subject

        @return: 1 if they match, 0 otherwise.
        @raise SubjectTypesDifferent: if subject types don't match.
        
        """
        # If they're not the same type, raise an exception
        if self.auth_type != other.auth_type:
            raise SubjectTypesDifferent

        # If the names match and the auth_data matches...
        if (self.name == other.name and
            self.auth_data == other.auth_data):
            # They're the same return 1
            return 1
        else:
            # They don't match
            return 0
        
    def _repr_(self):
        """
        This method creates an XML representation of the subject.

        @return: a string containing the XML representation of the subject.
        """
        # Retrieve the DOM implementation, and create dom document
        domImpl = xml.dom.minidom.getDOMImplementation()
        doc = domImpl.createDocument(xml.dom.minidom.EMPTY_NAMESPACE,
                                     "Subject", None)

        # Create the child xml
        c = self.ToXML(doc)
        
        # Add it to the document
        doc.appendChild(c)
        
        # Serialize this object as part of that document
        return doc.toxml()

    def __str__(self):
        """
        This method converts the subject to a string.

        @return: string
        """
        return self._repr_()
        
    def ToXML(self, doc):
        """
        This method extends the specified doc object with an xml
        representation of this subject.

        @param doc: a DOM document to add this object to
        @type doc: xml.dom.minidom document

        @return: a the new 
        """
        sx = doc.createElement("Subject")
        # This converts the actual complicated object into a simple string
        sx.setAttribute("name", "%s" % self.name)
        sx.setAttribute("auth_type", self.auth_type)
        sx.setAttribute("auth_data", "%s" % self.auth_data)
        return sx

    def GetName(self):
        """
        This accessor returns the subject name.

        @return: the name as a string
        """
        return self.name

    def GetAuthenticationType(self):
        """
        This accessor returns the authentication type.

        @return: the authentication type as a string.
        """
        return self.auth_type

    def GetAuthenticationData(self):
        """
        This accessory returns the authentication data.

        @return: the authentication data
        """
        return self.auth_data

    def GetSubject(self):
        """
        This returns a tuple containing the subject data, this is
        probably for legacy use.

        @return: a tuple that represents this subject.
        """
        return (self.auth_type, self.name, self.auth_data)



