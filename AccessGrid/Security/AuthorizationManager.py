#-----------------------------------------------------------------------------
# Name:        AuthorizationManager.py
# Purpose:     The class that does the authorization work.
#
# Author:      Ivan R. Judson
#
# Created:     
# RCS-ID:      $Id: AuthorizationManager.py,v 1.3 2004-02-25 18:33:04 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Authorization Manager, as described in AGEP-0105.txt.
"""

__revision__ = "$Id: AuthorizationManager.py,v 1.3 2004-02-25 18:33:04 eolson Exp $"
__docformat__ = "restructuredtext en"

import sys
import xml.dom.minidom
#from xml.dom.ext import PrettyPrint

from AccessGrid.hosting.SOAPInterface import SOAPInterface
from AccessGrid.hosting import Decorate, Reconstitute, Client, IWrapper
from AccessGrid.GUID import GUID
from AccessGrid.Security.Role import RoleNotFound, RoleAlreadyPresent
from AccessGrid.Security.Role import Everybody, Role
from AccessGrid.Security.Action import ActionNotFound, ActionAlreadyPresent
from AccessGrid.Security.Action import MethodAction
from AccessGrid.Security import X509Subject

class InvalidParent(Exception):
    """
    The authorization manager was not valid.
    """
    pass

class CircularReferenceWithParent(Exception):
    """
    The parent authorization manager and this one refer to each other.
    """
    pass

class AuthorizationManager:
    """
    """
    def __init__(self):
        self.id = str(GUID())
        self.roles = list()
        self.actions = list()
        self.defaultRoles = list()
        self.defaultRoles.append(Everybody)
        self.parent = None

    def _repr_(self):
        return self.ToXML().toxml()

    def __str__(self):
        return self._repr_()
    
    def ExportPolicy(self):
        return self.ToXML()

    def ImportPolicy(self, policy):
        def unpackRole(node):
            sl = list()
            for s in node.childNodes:
                s = X509Subject.X509Subject(s.attributes["name"].value,
                                            s.attributes["auth_data"].value)
                if sl.count(s) == 0:
                    sl.append(s)
            r = Role(node.attributes["name"].value, sl)
            if node.attributes.has_key("default"):    
                return (r, 1)
            else:
                return(r, 0)
        
        def unpackAction(node):
            a = MethodAction(node.attributes["name"].value)
            for rn in node.childNodes:
                (r, dr) = unpackRole(rn)
                a.AddRole(r)

            return a
        
        domP = xml.dom.minidom.parseString(policy)
        
        for c in domP.getElementsByTagName("Role"):
            (r, default) = unpackRole(c)
            try:
                self.AddRole(r, default = default)
            except:
                print "Not adding Role."

        for c in domP.getElementsByTagName("Action"):
            a = unpackAction(c)
            try:
                self.AddAction(a)
            except:
                print "Not adding action"

    def ToXML(self):
        """
        We're going to try a new serialization process.
        The policy is:
        id = GUID
        roles = list of roles
        default roles = list of roles
        actions = list of actions

        role = name, list of subjects
        action = name, list of roles
        """
        domImpl = xml.dom.minidom.getDOMImplementation()
        authDoc = domImpl.createDocument(xml.dom.minidom.EMPTY_NAMESPACE,
                                         "AuthorizationPolicy", '')
        authP = authDoc.documentElement

        for r in self.roles:
            authP.appendChild(r.ToXML(authDoc))

        for r in self.defaultRoles:
            dr = r.ToXML(authDoc)
            dr.setAttribute("default","1")
            authP.appendChild(dr)

        for a in self.actions:
            authP.appendChild(a.ToXML(authDoc))

        rval = authDoc.toxml()

        return rval
    
    def IsAuthorized(self, subject, action):
        # By default no authorization happens
        auth = 0

        # this gets us all the roles for this action
        rolelist = self.GetRoles(action=action)

        for role in rolelist:
            if role.HasSubject(subject):
                if role.TYPE == "Deny":
                    # Deny overrides anything else
                    return 0
                
                if role.TYPE == "Accept":
                    # We only authorize if the subject is explicitly authorized
                    auth = 1

        return auth

    def AddAction(self, action):
        if not self.FindAction(action.GetName()):
            self.actions.append(action)
        else:
            raise ActionAlreadyPresent

    def AddActions(self, actionList):
        for a in actionList:
            self.AddAction(a)
        
    def RemoveAction(self, action):
        if action in self.actions:
            self.actions.remove(action)
        else:
            raise ActionNotFound

    def GetActions(self, subject=None, role=None):
        if subject == None and role == None:
            # Just return the list of actions
            actionlist = self.actions
        elif subject != None and role == None:
            # Return the list of actions for this subject
            actionlist = list()
            roles = self.GetRolesForSubject(subject)
            for r in roles:
                for a in self.actions:
                    if a.HasRole(r) and a not in actionlist:
                        actionlist.append(a)
        elif subject == None and role != None:
            # Return the list of actions for this role
            actionlist = list()
            for a in self.actions:
                if a.HasRole(role) and a not in actionlist:
                    actionlist.append(a)
        else:
            print "GetActions called with both a subject and a role"

        return actionlist

    def FindAction(self, name):
        for a in self.actions:
            if a.GetName() == name:
                return a
            
    def AddRole(self, role, default = 0):
        if default:
            r = self.defaultRoles
        else:
            r = self.roles

        if not self.FindRole(role.GetName()):
            r.append(role)
        else:
            raise RoleAlreadyPresent

    def RemoveRole(self, role):
        if role in self.roles:
            self.roles.remove(role)
        else:
            raise RoleNotFound

    def AddRoles(self, roleList):
        for r in roleList:
            self.AddRole(r)
        
    def GetRoles(self, action=None):
        if action == None:
            rolelist = self.roles
        else:
            rolelist = self.GetAction(action).GetRoles()

        return rolelist

    def FindRole(self, name):
        for r in self.roles:
            if r.GetName() == name:
                return r

    def GetRolesForSubject(self, subject):
        rolelist = list()

        for r in self.roles:
            if r.HasSubject(subject):
                rolelist.append(r)

        return rolelist
    
    def GetSubjects(self, role=None):
        subjectlist = list()

        if role == None:
            for r in self.roles:
                subjectlist.append(r.GetSubjects)
        else:
            subjectlist = role.GetSubjects()
            
        return subjectlist

    def GetParent(self):
	return self.parent

    def GetDefaultRoles(self):
	return self.defaultRoles

    def SetRoles(self, action, roles):
        a = self.FindAction(action)
        if a != None:
            a.SetRoles(roles)
        else:
            raise ActionNotFound

    def SetSubjects(self, role, subjects):
	r = self.FindRole(role)
        if r != None:
            r.SetSubjects(subjects)
        else:
            raise RoleNotFound
        
    def SetParent(authMgr):
        self.parent = authMgr

    def SetDefaultRoles(self, roles=[]):
        self.defaultRoles=roles

class AuthorizationManagerI(SOAPInterface):
    """
    Authorization manager network interface.
    """
    def __init__(self, impl):
        SOAPInterface.__init__(self, impl)

    def TestImportExport(self, p):
        self.impl.ImportPolicy(p)
        
    def GetPolicy(self):
        return self.impl.ToXML()
    
    def AddRole(self, name):
        """
        """
        role = Role(name)
        self.impl.AddRole(role)

    def RemoveRole(self, name):
        """
        """
        r = self.impl.FindRole(name)
        self.impl.RemoveRole(r)

    def ListRoles(self):
        """
        Return a list of role names.
        """
        roles = self.impl.GetRoles()
        dr = Decorate(roles)
        return dr

    def AddAction(self, name):
        """
        """
        a = Action(name)
        self.impl.AddAction(a)

    def RemoveAction(self, name):
        """
        """
        a = self.impl.FindAction(actionName)
        self.imple.RemoveAction(a)

    def ListActions(self):
        """
        """
        alist = self.impl.GetActions()
        al = Decoreate(alist)
        return al
    
    def ListSubjectsInRole(self, role):
        """
        """
        r = Reconstitute(role)
        roleR = self.impl.FindRole(r)
        subjs = self.impl.GetSubjects(roleR)
        subjs2 = Decorate(subjs)
        return subjs2

    def ListRolesInAction(self, action):
        """
        """
        a = self.impl.FindAction(actionName)
        rl = a.GetRoles()
        r = Decorate(rl)
        return r
    
    def AddSubjectsToRole(self, role, subjectList):
        """
        """
        r = Reconstitute(role)
        role = self.impl.FindRole(role.name)
        sl = Reconstitute(subjectList)
        for s in sl:
            role.AddSubject(s)

    def AddRoleToAction(self, action, role):
        """
        """
        an = Reconstitute(action)
        a = self.impl.FindAction(an.name)
        r = Reconstitute(role)
        a.AddRole(r)

    def AddRolesToAction(self, action, roleList):
        """
        """
        rl = Reconstitute(roleList)
        an = Reconstitute(action)
        a = self.impl.FindAction(an.name)
        for r in rl:
            a.AddRole(r)
            
    def RemoveSubjectsFromRole(self, role, subjectList):
        """
        """
        rn = Reconstitute(role)
        r = self.impl.FindRole(rn.name)
        sl = Reconstitute(subjectList)
        for s in sl:
            r.RemoveSubject(s)
            
    def RemoveRoleFromAction(self, action, role):
        """
        """
        an = Reconstitute(action)
        rn = Reconstitute(role)
        a = self.impl.FindAction(an.name)
        r = a.FindRole(rn.name)

        a.RemoveRole(r)

    def GetRolesForSubject(self, subject):
        """
        By default you should only be able to get roles for yourself,
        unless you are an administrator.
        """
        s = Reconstitute(subject)

        rl = self.impl.GetRolesForSubject(s)

        r = Decorate(rl)

        return r

class AuthorizationManagerIW(IWrapper):
    """
    This object is designed to provide a simple interface that hides
    the network plumbing between clients and servers.
    """
    def __init__(self, url=None):
        IWrapper.__init__(self, url)

    def TestImportExport(self, p):
        self.proxy.TestImportExport(p)
        
    def GetPolicy(self):
        return self.proxy.GetPolicy()
    
    def AddRole(self, name):
        """
        """
        return self.proxy.AddRole(name)

    def RemoveRole(self, name):
        """
        """
        return self.proxy.RemoveRole(name)

    def ListRoles(self):
        """
        """
        rs = self.proxy.ListRoles()
        rs2 = Reconstitute(rs)
        return rs2

    def AddAction(self, name):
        """
        """
        return self.proxy.AddAction(name)

    def RemoveAction(self, name):
        """
        """
        return self.proxy.RemoveAction(name)

    def ListActions(self):
        """
        """
        return self.proxy.ListActions()

    def ListSubjectsInRole(self, role):
        """
        """
        r = Decorate(role)
        sl = self.proxy.ListSubjectsInRole(r) 
        s = Reconstitute(sl)
        return s

    def ListRolesInAction(self, action):
        """
        """
        r = self.proxy.ListRolesInAction(action)
        rl = Reconstitute(r)
        return rl

    def AddSubjectToRole(self, subj, role):
        """
        """
        subjList = [subj,]
        r = Decorate(role)
        s = Decorate(subjList)
        return self.proxy.AddSubjectsToRole(r, s)

    def AddSubjectsToRole(self, subjList, role):
        """
        """
        r = Decorate(role)
        sl = Decorate(subjList)

        self.proxy.AddSubjectsToRole(r, sl)
        
    def AddRoleToAction(self, role, action):
        """
        """
        r = Decorate(role)
        a = Decorate(action)

        self.proxy.AddRoleToAction(a, r)
        
    def AddRolesToAction(self, roleList, action):
        """
        """
        rl = Decorate(roleList)
        a = Decorate(action)

        self.proxy.AddRolesToAction(rl, a)

    def RemoveSubjectFromRole(self, subj, role):
        """
        """
        subjList = [subj,]
        sl = Decorate(subjList)
        r = Decoreate(role)

        self.proxy.RemoveSubjectsFromRole(r, sl)

    def RemoveSubjectsFromRole(self, subjList, role):
        """
        """
        sl = Decorate(subjList)
        r = Decorate(role)

        self.proxy.RemoveSubjectsFromRole(r, sl)

    def RemoveRoleFromAction(self, role, action):
        """
        """
        r = Decorate(role)
        a = Decorate(action)

        self.proxy.RemoveRoleFromAction(a, r)

    def IsAuthorized(self, subject, action):
        """
        """
        s = Decorate(subject)
        a = Decorate(action)

        self.proxy.IsAuthorized(s, a)

class AuthorizationMixIn(AuthorizationManager):
   """
   This allows object to inherit Authorization.
   """
   def __init__(self):
       self.authManager = AuthorizationManager()
       self.rolesRequired = list()
       
   def GetAuthorizationManager(self):
       return self.hostingEnvironment.GetURLForObject(self.authManager)

   def GetRoles(self):
       return self.rolesRequired

   def AddRole(self, role):
       self.rolesRequired.append(role)
  
class AuthorizationIMixIn(AuthorizationManagerI):
    """
    """
    def GetAuthorizationManager(self):
        return self.impl.GetAuthorizationManager()

class AuthorizationIWMixIn(AuthorizationManagerIW):
    def GetAuthorizationManager(self):
        """
        This is the cool part, we've built it so this is a real object.
        """
        url = self.proxy.GetAuthorizationManager()
        amiw = AuthorizationManagerIW(url=url)
        return amiw

