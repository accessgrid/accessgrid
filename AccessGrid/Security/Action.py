#-----------------------------------------------------------------------------
# Name:        Action.py
# Purpose:     The class that does the authorization work.
#
# Author:      Ivan R. Judson
#
# Created:     
# RCS-ID:      $Id: Action.py,v 1.4 2004-03-02 19:07:12 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Actions, as described in AGEP-0105.txt.

Actions are actions that can be authorized by the role based
authorization software. These actions can be anything, currently we
only use MethodActions, which provide a mechanism for authorizing
method invocation on services. There's no real limitation to what
actions can be or what they can be used for however.
"""

__revision__ = "$Id: Action.py,v 1.4 2004-03-02 19:07:12 judson Exp $"

import xml.dom.minidom

class ActionNotFound(Exception):
    """
    This exception is raised when an action is not found.
    """
    pass

class ActionAlreadyPresent(Exception):
    """
    This exception is raised when an action is already known by the software.
    """
    pass

class Action:
    """
    The Action base class.

    @cvar TYPE: The type of the action object, currently this is an opaque string.
    @type TYPE: string
    
    This class provides all the common action functionality. 
    """
    TYPE = "Invalid"
    def __init__(self, name, roles=[]):
        """
        @param name: This is the name of the Action.
        @param roles: This is a list of roles to initialize the action with.
        @type name: string
        @type roles: list of AccessGrid.Security.Role objects.
        @return: The return of this is an Action object.
        """
        self.name = name
        self.roles = roles

    def _repr_(self):
        """
        The repr method produces an XML representation of the action object.
        """
        domImpl = xml.dom.minidom.getDOMImplementation()
        doc = domImpl.createDocument(xml.dom.minidom.EMPTY_NAMESPACE,
                                     "Action", '')
        return self.ToXML(doc).toxml()

    def __str__(self):
        """
        The __str__ method provides a way to print this object as a string.
        """
        return self._repr_()
    
    def ToXML(self, doc):
        """
        The ToXML converts this objects to a DOM subtree of the specified
        DOM Document.

        @param doc: the DOM document this xml should be a part of.
        @type doc: an xml.dom.minidom Document
        """
        ax = doc.createElement("Action")
        ax.setAttribute("name", self.name)
        for r in self.roles:
            ax.appendChild(r.ToXML(doc))
        return ax
    
    def GetName(self):
        """
        Simple accessor for the name attribute.

        @return: the name of the action
        """
        return self.name

    def SetName(self, name):
        """
        This is the accessor that sets the name of the action.

        @param name: the name being specified for this action.
        @type name: string

        @return: the name the action is set to
        """
        self.name = name
        return name

    def FindRole(self, roleName):
        """
        This method searchs for a Role object (by name) in this
        action. If it is found it is returned, otherwise None is
        returned.

        @param roleName: the name of the role being searched for.
        @type roleName: string

        @return: the role found that matches roleName or None
        """
        for r in self.roles:
            if r.GetName() == roleName:
                return r
        return None
    
    def GetRoles(self):
        """
        This method retrieves the list of roles assocatied with this action.

        @return: the list of roles in this object.
        """
        return self.roles

    def SetRoles(self, roles):
        """
        This method sets the action's role list, it overwrites the
        previous value.

        @param roles: a list of roles to set the actions roles to
        @type roles: a list of AccessGrid.Security.Role objects.
        @return: a list of roles added.
        """
        self.roles = roles
        return roles

    def AddRole(self, role):
        """
        This method adds a role to the action.

        @param role: the role to add to this action.
        @type role: AccessGrid.Security.Role

        @return: the role that was added to this action.
        """
        self.roles.append(role)
        return role

    def RemoveRole(self, role):
        """
        Remove a role from the action.

        @param role: a role to remove from this action.
        @type role: AccessGrid.Security.Role
        @return: the role removed is returned
        """
        self.roles.remove(role)
        return role
    
    def HasRole(self, role):
        """
        This method checks to see if the specified role is found in the
        action.

        @param role: a role to find in the action.
        @type role: AccessGrid.Security.Role

        @return: a flag indicating if the role was found (1) or not (0)
        """
        if role in self.roles:
            return 1
        else:
            return 0

    def GetRolesAsStrings(self):
        """
        Returns the list of roles as strings.
        """
        return str(self.roles)
    
class MethodAction(Action):
    """
    The Method Action class.

    Method actions are created for all methods on objects that expose
    them via SOAP. This provides a way to authorize per-method access
    on the objects.

    @cvar TYPE: The type of the action object, currently this is an opaque string.
    @type TYPE: string
    """
    TYPE = "Method"
    pass
