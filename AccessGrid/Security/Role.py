#-----------------------------------------------------------------------------
# Name:        Role.py
# Purpose:     Abstraction of a role in the system.
#
# Author:      Robert Olson
#
# Created:     
# RCS-ID:      $Id: Role.py,v 1.2 2004-02-24 21:33:07 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Roles
"""

__revision__ = "$Id: Role.py,v 1.2 2004-02-24 21:33:07 judson Exp $"
__docformat__ = "restructuredtext en"

import xml.dom.minidom
from xml.dom.ext import PrettyPrint

from AccessGrid.Security.Subject import Subject, InvalidSubject
from AccessGrid.Toolkit import GetApplication

class RoleNotFound(Exception):
    """
    This role was not found.
    """
    pass

class RoleAlreadyPresent(Exception):
    """
    This role already has been created.
    """
    pass

class DefaultIdentityNotRemovable(Exception):
    """
    This role was not found.
    """
    pass

class LastSubjectNotRemovable(Exception):
    """
    This role was not found.
    """
    pass

class Role:
    """
    A Role instance represents a list of Subjects (users).
    
    It is used to represent all the users belonging to specific 
    permission sets or "roles."
    For example, if a Role is called "AllowedEntry", it is most
    likely a list of users users are allowed to enter something.
    """

    TYPE = "Invalid"

    def __init__(self, role_name, subjects=list()):
        self.name = role_name
        self.subjects = subjects

    def _repr_(self):
        domImpl = xml.dom.minidom.getDOMImplementation()
        doc = domImpl.createDocument(xml.dom.minidom.EMPTY_NAMESPACE,
                                     "Role", '')
        return self.ToXML(doc).toxml()

    def __str__(self):
        return self._repr_()
    
    def ToXML(self, doc):
        rx = doc.createElement("Role")
        rx.setAttribute("name", self.name)
        for s in self.subjects:
            rx.appendChild(s.ToXML(doc))

        return rx
        
    def __str__(self):
        return self._repr_()
        
    def GetName(self):
        return self.name

    def GetSubjects(self):
        return self.subjects

    def SetSubjects(self, sl):
        self.subject = sl
        
    def GetSubjectListAsStrings(self):
        l = map(lambda x: "%s" % x, self.subjects)
        return l
    
    def AddSubject(self, subject):
        """
        This new AddSubject is more strict than the old one. It only
        works with subject objects.
        """
        if not isinstance(subject, Subject):
            return InvalidSubject

        print "Adding Subject to Role (%s) : %s\n"  % (self.name, subject)
        self.subjects.append(subject)

    def RemoveSubject(self, subject):
        if not isinstance(subject, Subject):
            return InvalidSubject

        di = GetApplication().GetCertificateManager().GetDefaultIdentity()

        if di == subject:
            raise DefaultIdentityNotRemovable

        self.subjects.remove(subject)

    def FindSubject(self, subjectName):
        for s in self.subjects:
            if s.GetName() == subjectName:
                return s
            
    def HasSubject(self, subject):
        if issubclass(subject, Subject):
            return InvalidSubject

        if subject in self.subjects:
            return 1
        else:
            return 0

    """
    Methods from previous implementation that try to do alot of type
    interpretation.
    """
    
    def AddSubjectOld(self, subject):
        """
        Accepts strings, Subjects, or X509Name.
        Converts X509Names to Subjects before adding.
        """
        if type(subject) == type(""):
            if len(subject) == 0:
                return # don't append zero length strings

        subject_to_add = subject
        # Convert X509Name to Subject
        if type(subject) == X509NameType:
            subject_to_add = Subject(str(subject), AUTH_X509)

        for s in self.subjects:
            if isinstance(s, Subject):
                if s.IsUser(subject_to_add):
                    return
            elif isinstance(subject_to_add, Subject):
                if subject_to_add.IsUser(s):
                    return
            # If they are both strings
            elif type(s) == type(subject_to_add):
                if s == subject_to_add:
                    return 
            else:
                # Soap gives errors when sending the type of a variable
                #  as a string so strip out punctuation characters.
                strng = ""
                for a in str(type(subject_to_add)):
                    if not a in string.punctuation or a == "_":
                        strng += a
                raise InvalidSubjectTypeError(strng)
               
        self.subjects.append(subject_to_add)

    def RemoveSubjectOld(self, subject):
        subject_to_remove = subject
        # Convert X509Name to Subject
        if type(subject) == X509NameType:
            subject_to_remove = Subject(str(subject), AUTH_X509)

        for i in range(len(self.subjects)-1, -1, -1):
            if isinstance(self.subjects[i], Subject):
                if self.subjects[i].IsUser(subject_to_remove):
                    del self.subjects[i]
            elif self.subjects[i] == subject_to_remove:
                del self.subjects[i]

    def HasSubjectOld(self, subject):
        test_subject = subject
        # Convert X509Name to Subject
        if type(subject) == X509NameType:
            test_subject = Subject(str(subject), AUTH_X509)

        for s in self.subjects:
            if isinstance(s, Subject):
                if s.IsUser(test_subject):
                    return 1
            if isinstance(test_subject, Subject):
                if test_subject.IsUser(s):
                    return 1
            elif s == test_subject:
                    return 1
        return 0

    def GetSubjectListAsStringsOld(self):
        """
        Return a subject list in a more readable and parasable
        version.
        """
        subjectStringList = []
        for subj in self.GetSubjectList():
            if type(subj) == type(""):
                # print "Match on string ", subj
                subjectStringList.append(subj)
            elif type(subj) == type(()): 
            # print "Match on tuple ", self.GetSubject()
                subjectStringList.append(subj[1])
            elif isinstance(subj, Subject):
                # print "match on obj ", self.GetSubject()
                subjectStringList.append(subj.GetName())
            # X509Name shouldn't be found here, but just in case.
            elif type(subj) == X509NameType:
                subjectStringList.append(str(subj))
                log.warn("AccessGrid.hosting.AccessControl.Role.GetSubjectListAsStrings() found X509NameType")
            else:
                # Soap errors when sending the type of a variable
                #  as a string so strip out not alpha characters.
                strng = ""
                for a in str(type(subj)):
                    if not a in string.punctuation or a == "_":
                        strng += a
                raise InvalidSubjectTypeError(strng)
        return subjectStringList

class AllowRole(Role):
    TYPE = "Allow"
    pass

class DenyRole(Role):
    TYPE = "Deny"
    pass

# Some default roles
Everybody = AllowRole("EVERYBODY")
Nobody = DenyRole("NOBODY")
Administrators = AllowRole("Administrators")

