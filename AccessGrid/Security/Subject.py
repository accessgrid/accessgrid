#-----------------------------------------------------------------------------
# Name:        Subject.py
# Purpose:     Abstraction of a user in the system.
#
# Author:      Robert Olson
#
# Created:     
# RCS-ID:      $Id: Subject.py,v 1.14 2004-12-08 16:48:07 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
Subjects, as described in AGEP-0105.txt.

Subjects are the basic security handle on entities that want to be a
part of the secure Access Grid Toolkit.
"""

__revision__ = "$Id: Subject.py,v 1.14 2004-12-08 16:48:07 judson Exp $"

# External Imports
import xml.dom.minidom


# Internal Imports
from AccessGrid.GUID import GUID


class SubjectAlreadyPresent(Exception):
    """
    This is already present.
    """
    pass

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
    mechanisms. we currently support X509 certificates.
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
        @returns: the id attribute which is a globally unique
        identifier in a string.
        """
        return id(self) 

    
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

        # Should return:
        # self > other = 1
        # self == other = 0
        # self < other = -1
        
        if not isinstance(other, Subject):
            return -1

        result1 = cmp(str(self.name), str(other.name))
        result2 = cmp(self.auth_data, other.auth_data)

        # Both name and auth_data are the same
        if result1 == 0 and result2 == 0:
            return 0
        else:
            # Otherwise, return value based on name comparison.
            return result1

               
        # If they are not the same type, raise an exception
        #if self.auth_type != other.auth_type:
        #   raise SubjectTypesDifferent
        
        # If the names match and the auth_data matches...
        #if (self.name == other.name and
        #    self.auth_data == other.auth_data):
        # They're the same return 1
        #    return 1
        #else:
        # They don't match
        #    return 0
        
                    
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
        doc.documentElement.appendChild(c)
        
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

if __name__ == "__main__":
    from AccessGrid.Security.X509Subject import X509Subject
    from AccessGrid.Security.Role import Role
       
    s1 = X509Subject("1")
    s2 = X509Subject("2")
    s3 = X509Subject("3")
    r1 = Role("role1")
       
    subDict = {}
    subDict[s1] = "1"
    subDict[s2] = "2"
    subDict[s3] = "3"
    sllist = []
    sllist.append(s1)
    sllist.append(s2)
    sllist.append(s3)
    
    print 'is s1 == r1 ', s1 == r1
    print 's1 is s1 ', s1 is s1
    print 's1 is s2 ', s1 is s2
    print 's1 == s2 ', s1 == r1
    
    print 'is s1 in subdir', s1 in subDict
    print 'is s2 in subdir', s2 in subDict
    print 'is r1 in subdir', r1 in subDict
    print 'subdict hads key r1 ', r1 in subDict.keys()
    print 'is s1 in the list ', s1 in sllist
    print 'is s1 r1', s1 is r1

    sllist.remove(s3)
    for i in sllist:
        print i.name
    
    '''
    Should return
    is s1 == r1  0
    s1 is s1  1
    s1 is s2  0
    s1 == s2  0
    is s1 in subdir 1
    is s2 in subdir 1
    is r1 in subdir 0
    subdict hads key r1  0
    is s1 in the list  1
    is s1 r1 0
    1
    2
    '''
        
