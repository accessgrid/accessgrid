#-----------------------------------------------------------------------------
# Name:        Role.py
# Purpose:     Abstraction of a role in the system.
#
# Author:      Robert Olson
#
# Created:     
# RCS-ID:      $Id: Role.py,v 1.4 2004-03-02 19:07:12 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Roles, as described in AGEP-0105.txt.

Roles are analagous to groups, although in our implementation they are
much more dynamic. We programmatically create, destroy and modify
roles.
"""

__revision__ = "$Id: Role.py,v 1.4 2004-03-02 19:07:12 judson Exp $"

# external imports
import xml.dom.minidom

# AGTk imports
from AccessGrid.Security.Subject import Subject, InvalidSubject
from AccessGrid.Toolkit import GetApplication

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
    """

    A Role instance represents a group of Subjects (users). The group
    probably has some contextual meaning, such as "Users found in the
    Venue" or "Users who can modify my data".
    
    For example, if a Role is called "AllowedEntry", it is most
    likely a list of users users are allowed to enter something.

    @cvar TYPE: the type of role, used in doing Role Arithematic.
    @type TYPE: string
    """

    TYPE = "Invalid"

    def __init__(self, role_name, subjects=list()):
        """
        @param role_name: the name of the role to create
        @param subjects: a list of subjects to initialize this role with.
        @type role_name: string
        @type subjects: a list of AccessGrid.Security.Subject objects
        """
        self.name = role_name
        self.subjects = subjects

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
        doc.appendChild(c)
        
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
        l = map(lambda x: "%s" % x, self.subjects)
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

        di = GetApplication().GetCertificateManager().GetDefaultIdentity()

        if di == subject:
            raise DefaultIdentityNotRemovable

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
        if issubclass(subject, Subject):
            return InvalidSubject

        if subject in self.subjects:
            return 1
        else:
            return 0

class AllowRole(Role):
    """
    The AllowRole is used to create allowable roles.

    Example: UsersAllowedInVenue

    @cvar TYPE: the type of role this is.
    @type TYPE: string
    """
    TYPE = "Allow"
    pass

class DenyRole(Role):
    """
    The DenyRole class is used to create denial roles.

    Example: UsersNotAllowedInVenue

    @cvar TYPE: the type of role this is.
    @type TYPE: string
    """
    TYPE = "Deny"
    pass

# Some default roles
Everybody = AllowRole("EVERYBODY")
Nobody = DenyRole("NOBODY")
Administrators = AllowRole("Administrators")

