#-----------------------------------------------------------------------------
# Name:        Role.py
# Purpose:     Abstraction of a role in the system.
#
# Author:      Robert Olson
#
# Created:     
# RCS-ID:      $Id: Role.py,v 1.15 2004-04-08 20:52:10 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Roles, as described in AGEP-0105.txt.

Roles are analagous to groups, although in our implementation they are
much more dynamic. We programmatically create, destroy and modify
roles.
"""

__revision__ = "$Id: Role.py,v 1.15 2004-04-08 20:52:10 eolson Exp $"

# external imports
import xml.dom.minidom

# AGTk imports
from AccessGrid.Security.Subject import Subject, InvalidSubject
from AccessGrid.Toolkit import Application
from AccessGrid.Security.Subject import SubjectAlreadyPresent

class RoleNotFound(Exception):
    """
    This exception is raised when the role is not found.
    """
    pass

class RoleAlreadyPresent(Exception):
    """
    This exception is raised when the role is already known by the software.
    """
    pass

class InvalidRole(Exception):
    """
    An invalid role was operated upon, specified, or retrieved.
    """
    pass

class DefaultIdentityNotRemovable(Exception):
    """
    This exception is raised when an attempt to remove the identity of
    the user running the process (the Default Identity). It's a bad
    idea to allow the removal of this subject without very careful
    consideration of what's going to happen. In all cases we currently
    don't allow this removal and raise this exception instead.
    """
    pass

class Role:
    '''
    A Role instance represents a group of Subjects (users). The group
    probably has some contextual meaning, such as "Users found in the
    Venue" or "Users who can modify my data".
    
    For example, if a Role is called "AllowedEntry", it is most
    likely a list of users users are allowed to enter something.

    @cvar TYPE: the type of role, used in doing Role Arithematic.
    @type TYPE: string
    '''

    TYPE = "Invalid"

    def __init__(self, role_name, subjects=None):
        """
        @param role_name: the name of the role to create
        @param subjects: a list of subjects to initialize this role with.
        @type role_name: string
        @type subjects: a list of AccessGrid.Security.Subject objects
        """
        if not subjects:
            self.subjects = []
        else:
            self.subjects = subjects
        
        self.name = role_name
        self.requireDefaultId = 0
       
    def _repr_(self):
        """
        This method creates a DOM document that represents the role.

        @return: a string formatted as XML.
        """
        domImpl = xml.dom.minidom.getDOMImplementation()
        doc = domImpl.createDocument(xml.dom.minidom.EMPTY_NAMESPACE,
                                     "Role", '')
        # create the child node, then attach it to the document
        c = self.ToXML(doc)
        doc.documentElement.appendChild(c)
        
        return doc.toxml()

    def __str__(self):
        """
        This method provides a string reprsentation of the Role.

        @return: string
        """
        return self._repr_()
    
    def ToXML(self, doc):
        """
        This method creates the XML specific to the Role class.

        @param doc: a DOM document to create the Role XML from.
        @type doc: xml.dom.minidom document

        @return: a dom document node.
        """
        rx = doc.createElement("Role")
        rx.setAttribute("name", self.name)
        for s in self.subjects:
            rx.appendChild(s.ToXML(doc))

        return rx
        
    def GetName(self):
        """
        An accessor for the Role name attribute.

        @returns: string form of the name
        """
        return self.name

    def GetSubjects(self):
        """
        An accessor for the list of subjects that are in this Role.

        @return: a list of AccessGrid.Security.Subject objects.
        """
        return self.subjects

    def GetRequireDefault(self):
        '''
        An accessor to set if we are allowed to remove default
        subject from this role.

        @return: 1 if this role requires default subject, otherwise 0.
        '''
        return self.requireDefaultId

    def SetRequireDefault(self, flag):
        '''
        An accessor to check if we are allowed to remove dafault
        subject from this role.

        @param flag: 1 if this role requires default subject, otherwise 0.
        @type flag: int
        '''
        self.requireDefaultId = flag

    def SetSubjects(self, sl):
        """
        An accessor to set the list of subjects associated with this Role.
        This replaces any previously existing list.

        @param sl: a list of subjects to set this Role with.
        @type sl: a list of AccessGrid.Security.Subject objects.
        """
        self.subject = sl
        
    def GetSubjectListAsStrings(self):
        """
        This method returns the subject list as strings.

        @return: a list of strings of subjects.
        """
        l = map(lambda x: "%s" % x.GetName(), self.subjects)
        return l
    
    def AddSubject(self, subject):
        """
        This new AddSubject is more strict than the old one. It only
        works with subject objects.

        @param subject: the subject to add to this role
        @type subject: AccessGrid.Security.Subject object

        @raises InvalidSubject: when the subject specified is not a
        subclass of the AccessGrid.Security.Subject base class.
        """
        if not isinstance(subject, Subject):
            raise InvalidSubject

        for s in self.subjects:
            if s.name == subject.name:
                raise SubjectAlreadyPresent(s.name)

        self.subjects.append(subject)
   
    def RemoveSubject(self, subject):
        """
        This method removes the specified subject from the role.

        @param subject: the subject to be removed.
        @type subject: AccessGrid.Security.Subject object

        @raises InvalidSubject: when the subject passed in not a
        subclass of the AccessGrid.Security.Subject base class.
        """
        if not isinstance(subject, Subject):
            raise InvalidSubject

        if Application.instance().GetDefaultSubject() == subject and self.requireDefaultId:
            raise DefaultIdentityNotRemovable(subject)
        
        if subject not in self.subjects:
            raise InvalidSubject("Subject %s does not exist in role %s"%(subject.name, self.name))

        self.subjects.remove(subject)

    def FindSubject(self, subjectName):
        """
        This method retrieves the subject for the specified name.

        @param subjectName: a string representing the subject.
        @type subjectName: string

        @returns: an AccessGrid.Security.Subject object or None.
        """
        for s in self.subjects:
            if s.GetName() == subjectName:
                return s
        return None
    
    def HasSubject(self, subject):
        """
        Thie method verifies that a subject is in this Role.

        @param subject: the subject to be verified.
        @type subject: an AccessGrid.Security.Subject object.

        @return: 0 if not in this Role, 1 if in this Role.
        """
        if not isinstance(subject, Subject):
            raise InvalidSubject

        if subject in self.subjects:
            return 1
        elif self.name == "Everybody":
            return 1
        else:
            return 0

# Some default roles
Everybody = Role("Everybody")
Everybody.SetRequireDefault(1)
Administrators = Role("Administrators")

if __name__ == "__main__":
    
    from AccessGrid.Security.X509Subject import X509Subject
    
    r = Role("test")
    r.RemoveSubject(X509Subject("Susanne1"))
    #r.AddSubject(X509Subject("Susanne1"))
    #r.AddSubject(X509Subject("Susanne1"))
