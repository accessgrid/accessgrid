#-----------------------------------------------------------------------------
# Name:        Action.py
# Purpose:     The class that does the authorization work.
#
# Author:      Ivan R. Judson
#
# Created:     
# RCS-ID:      $Id: Action.py,v 1.2 2004-02-24 21:33:07 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Actions, as described in AGEP-0105.txt.
"""

__revision__ = "$Id: Action.py,v 1.2 2004-02-24 21:33:07 judson Exp $"
__docformat__ = "restructuredtext en"

import xml.dom.minidom

class ActionNotFound(Exception):
    """
    This action was not found.
    """
    pass

class ActionAlreadyPresent(Exception):
    """
    This action was not found.
    """
    pass

class Action:
    TYPE = "Invalid"
    def __init__(self, name, roles=[]):
        self.name = name
        self.roles = roles

    def _repr_(self):
        domImpl = xml.dom.minidom.getDOMImplementation()
        doc = domImpl.createDocument(xml.dom.minidom.EMPTY_NAMESPACE,
                                     "Action", '')
        return self.ToXML(doc).toxml()

    def __str__(self):
        return self._repr_()
    
    def ToXML(self, doc):
        ax = doc.createElement("Action")
        ax.setAttribute("name", self.name)
        for r in self.roles:
            ax.appendChild(r.ToXML(doc))
        return ax
    
    def GetName(self):
        return self.name

    def SetName(self, name):
        self.name = name
        return name

    def FindRole(self, roleName):
        for r in self.roles:
            if r.GetName() == roleName:
                return r
            
    def GetRoles(self):
        return roles

    def SetRoles(self, roles):
        self.roles = roles
        return roles

    def AddRole(self, role):
        self.roles.append(role)
        return role

    def RemoveRole(self, role):
        self.roles.remove(role)
        return role
    
    def HasRole(self, role):
        if role in self.roles:
            return 1
        else:
            return 0

    def GetRolesAsStrings(self):
        return str(self.roles)
    
class MethodAction(Action):
    TYPE = "Method"
    pass
