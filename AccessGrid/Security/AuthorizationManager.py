#-----------------------------------------------------------------------------
# Name:        AuthorizationManager.py
# Purpose:     The class that does the authorization work.
#
# Author:      Ivan R. Judson
#
# Created:     
# RCS-ID:      $Id: AuthorizationManager.py,v 1.20 2004-05-27 22:21:31 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Authorization Manager, as described in AGEP-0105.txt.

The authorization manager is the coordinating object for most of the
authorization implementation. It manages authorization policies and
provides external interfaces for managing and using the role based
authorization layer.
"""

__revision__ = "$Id: AuthorizationManager.py,v 1.20 2004-05-27 22:21:31 turam Exp $"

# External Imports
import os
import xml.dom.minidom

from AccessGrid import Log
#AGTk Importsfrom AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.hosting import Decorate, Reconstitute, Client
from AccessGrid.GUID import GUID
from AccessGrid.Security.Role import RoleNotFound, RoleAlreadyPresent, InvalidRole
from AccessGrid.Security.Role import Everybody, Role
from AccessGrid.Security.Action import Action
from AccessGrid.Security.Action import ActionNotFound, ActionAlreadyPresent
from AccessGrid.Security.Action import MethodAction
from AccessGrid.Security import X509Subject

from AccessGrid.ClientProfile import ClientProfileCache
from AccessGrid.Platform.Config import UserConfig

log = Log.GetLogger(Log.Security)

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
    The Authorization Manager class is the object that is added to
    objects that want to enable authorization. This provides the
    encapsulation of the authorization implementation.
    """
    def __init__(self):
        """
        The constructor, initializes itself.
        """
        self.id = str(GUID())
        self.roles = list()
        self.actions = list()
        self.defaultRoles = list()
        self.defaultRoles.append(Everybody)
        self.parent = None

        # Yeah, I know
        self.profileCachePrefix = "serverProfileCache"
        userConfig = UserConfig.instance()
        self.profileCachePath = os.path.join(userConfig.GetConfigDir(),
                                             self.profileCachePrefix)
        self.profileCache = ClientProfileCache(self.profileCachePath)
        
    def _repr_(self):
        """
        This method converts the object to XML.
        """
        return self.ToXML()

    def __str__(self):
        """
        This method converts the object to a string.

        @return: string
        """
        return self._repr_()
    
    def ExportPolicy(self):
        """
        This method creates a string representation of the
        Authorization Policy this object implements.

        @return: a string (XML Formatted) representing the policy.
        """
        return self.ToXML()

    def ImportPolicy(self, policy):
        """
        This method takes a string that is an XML representation of an
        authorization policy. This policy is parsed and this object is
        configured to enforce the specified policy.

        @param policy: the policy as a string
        @type policy: an XML formatted string
        """
        # Internal function to create a role
        def unpackRole(node):
            sl = list()
            for s in node.childNodes:
                s = X509Subject.X509Subject(s.attributes["name"].value,
                                            s.attributes["auth_data"].value)
                if sl.count(s) == 0:
                    sl.append(s)

            roleType = None
            if "TYPE" in node.attributes.keys():    
                roleType = node.attributes["TYPE"].value
            r = Role(node.attributes["name"].value, sl)

            if "default" in node.attributes.keys():    
                return (r, 1)
            else:
                return(r, 0)

        # Internal function to create an action
        def unpackAction(node):
            a = MethodAction(node.attributes["name"].value)
            for rn in node.childNodes:
                (r, dr) = unpackRole(rn)
                a.AddRole(r)

            return a

        # Reset current configuration
        self.roles = []
        self.actions = []
        
        domP = xml.dom.minidom.parseString(policy)
        
        roleElements = domP.getElementsByTagName("Role")

        for c in roleElements:
            (r, default) = unpackRole(c)
            try:
                self.AddRole(r, default = default)
            except:
                # Don't add the role
                pass

        for c in domP.getElementsByTagName("Action"):
            a = unpackAction(c)
            try:
                self.AddAction(a)
            except:
                # Don't add the action
                pass

    def ToXML(self):
        """
        We're going to try a new serialization process, using XML. We
        create this by creating a document then serializing it.

        @return: an XML formatted string
        """
        domImpl = xml.dom.minidom.getDOMImplementation()
        authDoc = domImpl.createDocument(xml.dom.minidom.EMPTY_NAMESPACE,
                                         "AuthorizationPolicy", None)
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
        """
        This is the real workhorse of authorization, checking to see
        if a given subject is authorized for a given action.

        @param subject: the subject we're curious about
        @param action: the action to check the subject against.
        @type subject: an AccessGrid.Security.Subject
        @type action: an AccessGrid.Security.Action

        @returns: 0 if not authorized, 1 if authorized.
        """
        # By default no authorization happens
        auth = 0

        # this gets us all the roles for this action
        rolelist = self.GetRoles(action=action)

        for role in rolelist:
            if role.HasSubject(subject):
                auth = 1

        return auth

    def AddAction(self, action):
        """
        Adds an action to this authorization manager.

        @param action: the action to add
        @type action: an AccessGrid.Security.Action object

        @raise ActionAlreadyPresent: if it's already part of this
        authorization manager.
        """
        if not self.FindAction(action.GetName()):
            self.actions.append(action)
            return action
        else:
            raise ActionAlreadyPresent

    def AddActions(self, actionList):
        """
        Add a list of actions, uses AddAction internally.

        @param actionList: a list of actions to add
        @type actionList: a list of AccessGrid.Security.Action objects.
        """
        for a in actionList:
            self.AddAction(a)
        
    def RemoveAction(self, action):
        """
        Remove an action from this authorization manager.

        @param action: the action to remove
        @type action: an AccessGrid.Security.Action object.

        @raise ActionNotFound: if the specified action is not found.
        """
                
        if action in self.actions:
            self.actions.remove(action)
        else:
            raise ActionNotFound

    def GetActions(self, subject=None, role=None):
        """
        Get a list of actions, perhaps for a subject or a role.

        @param subject: a subject to get the actions for
        @param role: a role to get actions for
        @type subject: AccessGrid.Security.Subject
        @type role: AccessGrid.Security.Role

        @returns: a list of AccessGrid.Security.Action objects
        """
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
        """
        Find an action by name.

        @param name: the name of the action to find
        @type name: string
        @return: a matching AccessGrid.Security.Action object or None
        """
        for a in self.actions:
            if a.GetName() == name:
                return a
        return None
    
    def AddRole(self, role, default = 0):
        """
        Add a role to this authorization manager.

        @param role: the role to add
        @param default: a flag indicating if the role is a default role
        @type role: AccessGrid.Security.Role object
        @type default: integer flag
        @return: nothing
        @raise RoleAlreadyPresent: if the role is already known.
        """
        if default:
            r = self.defaultRoles
        else:
            r = self.roles

        if None == role:
            raise InvalidRole

        if not self.FindRole(role.name):
            r.append(role)
        else:
            raise RoleAlreadyPresent

        return role
    

    def RemoveRole(self, role):
        """
        Remove a Role from this authorization manager.

        @param role: the role to remove
        @type role: AccessGrid.Security.Role object
        @return: nothing
        @raise RoleNotFound: if the role isn't found
        """
        if role in self.roles:
            self.roles.remove(role)
        else:
            raise RoleNotFound

    def AddRoles(self, roleList):
        """
        Add multiple roles to the authorization manager.
        This calls AddRole for each role in the list.
        
        @param roleList: the list of roles to add
        @type roleList: list of AccessGrid.Security.Role objects.
        @return: nothing
        """
        for r in roleList:
            self.AddRole(r)
        
    def GetRoles(self, action=None):
        """
        Get the list of Roles, optionally the roles associated with an action.

        @param action: an Action to retrieve roles for
        @type action: AccessGrid.Security.Action object.
        @return: list of AccessGrid.Security.Role objects
        """
        if action == None:
            rolelist = self.roles
        else:

            # ---------------------------------------------------
            # This allows old clients that uses IsValid() to connect
            # to new server.
            
            if action.GetName() == "_IsValid":
                action.SetName("IsValid")
                
            # ---------------------------------------------------

            foundAction = self.FindAction(action.GetName())

            
            if not foundAction:
                raise ActionNotFound(action.GetName())
                
            rolelist = foundAction.GetRoles()

        return rolelist

    def FindRole(self, name):
        """
        Find a role in this authorization manager.

        @param name: the name of the role to find
        @type name: string
        @return: the AccessGrid.Security.Role object or None
        """
                        
        for r in self.roles:
            if r.name == name:
                return r
        return None
    
    def GetRolesForSubject(self, subject):
        """
        Get all the roles the specified subject is part of.

        @param subject: the subject that the roles must contain
        @type subject: AccessGrid.Security.Subject
        @return: list of AccessGrid.Security.Role objects
        """
        rolelist = list()

        for r in self.roles:
            if r.HasSubject(subject):
                rolelist.append(r)

        return rolelist
    
    def GetSubjects(self, role=None):
        """
        Get the subjects known by this authorization manager, possibly for the
        specified role.

        @param role: the role to retrieve subjects for
        @type role: AccessGrid.Security.Role object
        @return: a list of AccessGrid.Security.Subject objects
        """

        subjectlist = list()
                   
        if role == None or role == 'None':
            for r in self.roles:
                for s in r.GetSubjects():
                    subjectlist.append(s)
        else:
            subjectlist = role.GetSubjects()
                      
        return subjectlist

    def GetParent(self):
        """
        Get the parent object.

        The parent authorization manager is used to provide a
        hierarchy of authorization. Currently, there is only one level
        allowed, ie, every authorization manager can have a parent,
        but when traversed (looking for authorization information) the
        tree is only ascended one level.
        """
	return self.parent

    def GetDefaultRoles(self):
        """
        Return the list of default roles for this authorization manager.

        @return: list of AccessGrid.Security.Role objects.
        """
	return self.defaultRoles

    def SetRoles(self, action, roles):
        """
        Sets the roles for the specified action.

        @param action: the action to set roles for
        @param roles: the list of roles to set the action with
        @type action: AccessGrid.Security.Action object
        @type roles: a list of AccessGrid.Security.Role objects

        @raise ActionNotFound: when the specified action is not found
        """
        a = self.FindAction(action)
        if a != None:
            a.SetRoles(roles)
        else:
            raise ActionNotFound

    def SetSubjects(self, role, subjects):
        """
        Set the subjects for the specified role.

        @param role: the role to set subjects for
        @param subjects: the list of subjects for the role
        @type role: AccessGrid.Security.Role object
        @type subjects: a list of AccessGrid.Security.Subject objects

        @raise RoleNotFound: when the specified role is not found
        """
	r = self.FindRole(role)
        if r != None:
            r.SetSubjects(subjects)
        else:
            raise RoleNotFound
        
    def SetParent(self, authMgr):
        """
        Set the parent authorization manager of this authorization manager.

        @param authMgr: the parent authorization manager
        @type authMgr: AccessGrid.Security.AuthorizationManager object
        """
        self.parent = authMgr

    def SetDefaultRoles(self, roles=[]):
        """
        Set the default roles for this authorization manager.

        @param roles: the list of roles that should be default
        @type roles: a list of AccessGrid.Security.Role objects
        """
        self.defaultRoles=roles

class AuthorizationManagerI(SOAPInterface):
    """
    Authorization manager network interface.
    """
    def __init__(self, impl):
        """
        The server side interface object. This gets an implementation
        to initialize itself with.

        @param impl: the implementation object this interface represents
        @type impl: AccessGrid.Security.AuthorizationManager
        """
        SOAPInterface.__init__(self, impl)

    def _authorize(self, *args, **kw):
        """
        The authorization callback.
        """
        subject, action = self._GetContext()

        log.info("Authorizing action: %s for subject %s", action.name,
                 subject.name)

        return self.impl.IsAuthorized(subject, action)

    def TestImportExport(self, policy):
        """
        A test call that verifies the policy can be imported and
        exported without modification.

        @param policy: an authorization policy
        @type policy: a string containing an XML formatted policy.
        """
        self.impl.ImportPolicy(policy)

    def ImportPolicy(self, policy):
        """
        Import policy.

        @param policy: an authorization policy
        @type policy: a string containing an XML formatted policy.
        """
        self.impl.ImportPolicy(policy)
        
    def GetPolicy(self):
        """
        Retrieve the policy.

        @return: a string containing an XML formatted authorization policy.
        """
        return self.impl.ToXML()
    
    def AddRole(self, role):
        """
        Add a role to the authorization manager.

        @param role: the role to add.
        @type role: AccessGrid.Security.Role object
        """
        #role = Role(name)
        r = Reconstitute(role)
        r2 = self.impl.AddRole(r)
        newRole = Decorate(r2)
        return newRole

    def FindRole(self, name):
        """
        Find a role in this authorization manager.

        @param name: the name of the role to find
        @type name: string
        @return: the AccessGrid.Security.Role object or None
        """
        r = self.impl.FindRole(name)
        return Decorate(r)

    def RemoveRole(self, name):
        """
        Remove a role from the authorization manager.

        @param name: the name of the role to remove.
        @type name: string
        """
        r = self.impl.FindRole(name)

        if not r:
            raise RoleNotFound(name)
        
        self.impl.RemoveRole(r)

    def ListRoles(self, action = None):
        """
        Retrieve the entire list of Roles.

        This involves marshalling data across the wire.

        @param action: the action to list roles for, if none is specified, list all known roles.
        @type action: AccessGrid.Security.Action
        
        @return: a list of AccessGrid.Security.Role objects
        """
        if action == None:
            roles = self.impl.GetRoles()
        else:
            a = Reconstitute(action)
            a1 = self.impl.FindAction(a)

            if not a1:
                raise ActionNotFound(a.name)
            
            roles = a1.GetRoles()
            
        dr = Decorate(roles)
        return dr

    def AddAction(self, action):
        """
        Add an action to the authorization manager.

        @param action: the action to add
        @type action: AccessGrid.Security.Action object
        """
        a = Reconstitute(action)
        action = self.impl.AddAction(a)
        a1 = Decorate(action)
        return a1
        
    def RemoveAction(self, name):
        """
        Remove an action from the authorization manager.

        @param name: the name of the action to remove
        @type name: string.
        """
        a = self.impl.FindAction(name)

        if not a:
            raise ActionNotFound(name)
        
        self.impl.RemoveAction(a)

    def ListActions(self, subject = None, role = None):
        """
        List the actions known by this authorization manager.

        WARNING: this has to marshall data.
        
        @return: a list of AccessGrid.Security.Action objects.
        """
        r = Reconstitute(role)
        s = Reconstitute(subject)
        alist = self.impl.GetActions(s, r)
        al = Decorate(alist)
        return al

    def ListSubjects(self, role=None):
        """
        List subjects that are in a specific role.

        WARNING: this has to marshall data.

        @param role: the role to list the subjects of.
        @type role: an AccessGrid.Security.Role object
        @return: a list of AccessGrid.Security.Subject objects
        """

        subjs = None
        if role == None:
            # This is not a great engineering solution, and we should
            # probably revisit it with a better plan.
            profiles = cache.LoadAllProfiles()
            subjs = map(lambda x:
                X509Subject.CreateSubjectFromString(x.GetDistinguishedName()),
                        profiles)
        else:
            r = Reconstitute(role)
            roleR = self.impl.FindRole(r.name)
            
            if not roleR :
                raise RoleNotFound(name)
            
            subjs = self.impl.GetSubjects(roleR)

        subjs2 = Decorate(subjs)
        return subjs2

    def AddSubjectsToRole(self, role, subjectList):

        """
        Add a subject to a particular role.
        This uses AddSubjectsToRole internally.
        
        WARNING: this has to marshall data.

        @param subjectList: the subject list to add
        @param role: the role to add the subject to
        @type subjectList: list of AccessGrid.Security.Subject objects
        @type role: AccessGrid.Security.Role object
        """
        r = Reconstitute(role)
        role = self.impl.FindRole(r.name)
        sl = Reconstitute(subjectList)

        if not role:
            return RoleNotFound(r.name)
            
        for s in sl:
            subject = Decorate(s)
            role.AddSubject(subject)

    def AddRoleToAction(self, action, role):
        """
        Add a role to the specified action.

        WARNING: this has to marshall data.

        @param role: the role to add to the action
        @param action: the action that gets the role added
        @type role: AccessGrid.Security.Role object
        @type action: AccessGrid.Security.Action object
        """
        an = Reconstitute(action)
        a = self.impl.FindAction(an.name)

        if not a:
            raise ActionNotFound(an.name)
        
        r = Reconstitute(role)
        
        a.AddRole(r)


    def AddRolesToAction(self, action, roleList):
        """
        Add multiple roles to an action.
        
        WARNING: this has to marshall data.

        @param roleList: the list of roles to add to the action.
        @param action: the action that gets the roles added to it
        @type roleList: a list of AccessGrid.Security.Role objects
        @type action: an AccessGrid.Security.Action object
        """
        rl = Reconstitute(roleList)
        an = Reconstitute(action)
        a = self.impl.FindAction(an.name)

        if not a:
            raise ActionNotFound(an.name)
        
        for r in rl:
            a.AddRole(r)
            
    def RemoveSubjectsFromRole(self, role, subjectList):
        """
        Remove multiple subjects from the role.
        
        WARNING: this has to marshall data.

        @param subjectList: the list of subjects to remove
        @param role: the role to remove the subject from
        @type subjectList: a list of AccessGrid.Security.Subject objects
        @type role: AccessGrid.Security.Role object
        """
        rn = Reconstitute(role)
        r = self.impl.FindRole(rn.name)
        
        if not r:
            raise RoleNotFound(rn.name)
        
        sl = Reconstitute(subjectList)
        for s in sl:
            r.RemoveSubject(s)
            
    def RemoveRoleFromAction(self, action, role):
        """
        Remove a Role from the action.
        
        WARNING: this has to marshall data.

        @param role: the role to remove from the action
        @param action: the action to remove the role from
        @type role: AccessGrid.Security.Role object
        @type action: AccessGrid.Security.Action object
        """
        an = Reconstitute(action)
        rn = Reconstitute(role)
        a = self.impl.FindAction(an.name)

        if not a:
            return ActionNotFound(an.name)
        
        r = a.FindRole(rn.name)

        if not r:
            return RoleNotFound(rn.name)
      
        a.RemoveRole(r)

    def GetRolesForSubject(self, subject):
        """
        Get the list of roles the subject is a part of.

        WARNING: this has to marshall data.

        @param subject: the subject the roles are for
        @type subject: AccessGrid.Security.Subject object

        @returns: list of AccessGrid.Security.Role objects
        """
        s = Reconstitute(subject)

        rl = self.impl.GetRolesForSubject(s)

        r = Decorate(rl)

        return r

    def IsAuthorized(self, subject, action):
        """
        Check to see if the subject authorized for the action.
        
        WARNING: this has to marshall data.

        @param subject: the subject being verified.
        @param action: the action the subject is being verified for.
        @type subject: AccessGrid.Security.Subject object
        @type action: AccessGrid.Security.Action object.
        """
        s = Reconstitute(subject)
        a = Reconstitute(action)

        return self.impl.IsAuthorized(s, a)

class AuthorizationManagerIW(SOAPIWrapper):
    """
    This object is designed to provide a simple interface that hides
    the network plumbing between clients and servers. The client side
    of this is just a functional interface through this object.
    """
    def __init__(self, url=None):
        """
        Create the client side object for the authorization service
        specified by the url.

        @param url: url to the authorization service
        @type url: a string containing the url
        """
        SOAPIWrapper.__init__(self, url)

    def TestImportExport(self, policy):
        """
        A test call that verifies the policy can be imported and
        exported without modification.

        @param policy: an authorization policy
        @type policy: a string containing an XML formatted policy.
        """
        self.proxy.TestImportExport(policy)

    def ImportPolicy(self, policy):
        """
        Imports a policy.

        @param policy: an authorization policy
        @type policy: a string containing an XML formatted policy.
        """
        self.proxy.ImportPolicy(policy)
            
    def GetPolicy(self):
        """
        Retrieve the policy.

        @return: a string containing an XML formatted authorization policy.
        """
        return self.proxy.GetPolicy()
    
    def AddRole(self, name):
        """
        Add a role to the authorization manager.

        @param name: the name of the role to add.
        @type name: string
        """
        # Create a role from the name.
        r = Decorate(Role(name))
        role = self.proxy.AddRole(r)
        r1 = Reconstitute(role)
        return r1

    def FindRole(self, name):
        """
        Find a role in this authorization manager.

        @param name: the name of the role to find
        @type name: string
        @return: the AccessGrid.Security.Role object or None
        """
        
        r = self.proxy.FindRole(name)

        return Reconstitute(r)
        
    def RemoveRole(self, name):
        """
        Remove a role from the authorization manager.

        @param name: the name of the role to remove.
        @type name: string
        """
        self.proxy.RemoveRole(name)

    def ListRoles(self):
        """
        Retrieve the entire list of Roles.

        This involves marshalling data across the wire.

        @return: a list of AccessGrid.Security.Role objects
        """
        rs = self.proxy.ListRoles()
        rs2 = Reconstitute(rs)
        return rs2

    def AddAction(self, name):
        """
        Add an action to the authorization manager.

        @param name: the name of the action to add
        @type name: string
        """
        # Create action from name.
        a = Decorate(Action(name))
        action = self.proxy.AddAction(a)

        a1 = Reconstitute(a)
        return a1

    def RemoveAction(self, name):
        """
        Remove an action from the authorization manager.

        @param name: the name of the action to remove
        @type name: string.
        """
        self.proxy.RemoveAction(name)

    def ListActions(self, subject = None, role = None):
        """
        List the actions known by this authorization manager.

        WARNING: this has to marshall data.
        
        @return: a list of AccessGrid.Security.Action objects.
        """

        r = Decorate(role)
        s = Decorate(subject)
        al = self.proxy.ListActions(s, r)
        a =  Reconstitute(al)
        return a

    def ListSubjects(self, role = None):
        """
        List subjects that are in a specific role.

        WARNING: this has to marshall data.

        @param role: the role to list the subjects of.
        @type role: an AccessGrid.Security.Role object
        @return: a list of AccessGrid.Security.Subject objects
        """
        if role != None:
            r = Decorate(role)
            sl = self.proxy.ListSubjects(r) 
        else:
            sl = self.proxy.ListSubjects(r) 

        s = Reconstitute(sl)
        return s

    def ListRolesInAction(self, action):
        """
        List the roles associated with a specific action.

        WARNING: this has to marshall data.

        @param action: the action to list roles for.
        @type action: AccessGrid.Security.Action

        @return: list of AccessGrid.Security.Role objects
        """
        r = self.proxy.ListRolesInAction(action)
        rl = Reconstitute(r)
        return rl

    def AddSubjectToRole(self, subj, role):
        """
        Add a subject to a particular role.
        This uses AddSubjectsToRole internally.
        
        WARNING: this has to marshall data.

        @param subj: the subject to add
        @param role: the role to add the subject to
        @type subj: AccessGrid.Security.Subject object
        @type role: AccessGrid.Security.Role object
        """
        subjList = [subj,]
        r = Decorate(role)
        s = Decorate(subjList)
          
        self.proxy.AddSubjectsToRole(r, s)

    def AddSubjectsToRole(self, subjList, role):
        """
        Add a list of subjects to a  particular role.
        
        WARNING: this has to marshall data.

        @param subjList: a list of subjects
        @param role: the role to add the subjects to
        @type subjList: a list of AccessGrid.Security.Subject objects
        @type role: AccessGrid.Security.Role object
        """
        r = Decorate(role)
        sl = Decorate(subjList)

        self.proxy.AddSubjectsToRole(r, sl)
        
    def AddRoleToAction(self, role, action):
        """
        Add a role to the specified action.

        WARNING: this has to marshall data.

        @param role: the role to add to the action
        @param action: the action that gets the role added
        @type role: AccessGrid.Security.Role object
        @type action: AccessGrid.Security.Action object
        """
        r = Decorate(role)
        a = Decorate(action)

        self.proxy.AddRoleToAction(a, r)
        
    def AddRolesToAction(self, roleList, action):
        """
        Add multiple roles to an action.
        
        WARNING: this has to marshall data.

        @param roleList: the list of roles to add to the action.
        @param action: the action that gets the roles added to it
        @type roleList: a list of AccessGrid.Security.Role objects
        @type action: an AccessGrid.Security.Action object
        """
        rl = Decorate(roleList)
        a = Decorate(action)

        self.proxy.AddRolesToAction(rl, a)

    def RemoveSubjectFromRole(self, subj, role):
        """
        Remove the subject from the role.
        
        WARNING: this has to marshall data.

        @param subj: the subject to remove
        @param role: the role to remove the subject from
        @type subj: AccessGrid.Security.Subject object
        @type role: AccessGrid.Security.Role object
        """
        subjList = [subj,]
        sl = Decorate(subjList)
        r = Decorate(role)

        self.proxy.RemoveSubjectsFromRole(r, sl)

    def RemoveSubjectsFromRole(self, subjList, role):
        """
        Remove multiple subjects from the role.
        
        WARNING: this has to marshall data.

        @param subjList: the list of subjects to remove
        @param role: the role to remove the subject from
        @type subjList: a list of AccessGrid.Security.Subject objects
        @type role: AccessGrid.Security.Role object
        """
        sl = Decorate(subjList)
        r = Decorate(role)

        self.proxy.RemoveSubjectsFromRole(r, sl)

    def RemoveRoleFromAction(self, role, action):
        """
        Remove a Role from the action.
        
        WARNING: this has to marshall data.

        @param role: the role to remove from the action
        @param action: the action to remove the role from
        @type role: AccessGrid.Security.Role object
        @type action: AccessGrid.Security.Action object        
        """
        r = Decorate(role)
        a = Decorate(action)

        self.proxy.RemoveRoleFromAction(a, r)

    def GetRolesForSubject(self, subject):
        """
        Get the list of roles the subject is a part of.

        WARNING: this has to marshall data.

        @param subject: the subject the roles are for
        @type subject: AccessGrid.Security.Subject object

        @returns: list of AccessGrid.Security.Role objects
        """
        s = Decorate(subject)

        rl = self.proxy.GetRolesForSubject(s)

        r = Reconstitute(rl)

        return r

    def IsAuthorized(self, subject, action):
        """
        Check to see if the subject authorized for the action.
        
        WARNING: this has to marshall data.

        @param subject: the subject being verified.
        @param action: the action the subject is being verified for.
        @type subject: AccessGrid.Security.Subject object
        @type action: AccessGrid.Security.Action object.
        """
        s = Decorate(subject)
        a = Decorate(action)

        self.proxy.IsAuthorized(s, a)

class AuthorizationMixIn:
   """
   This allows object to inherit Authorization.
   """
   def __init__(self):
       """
       Normal constructor stuff, it initializes itself.
       """
       self.authManager = AuthorizationManager()
       self.rolesRequired = list()

   def GetAuthorizationManager(self):
       """
       Get the URL for the Authorization Manager.

       @return: a string containt the url to the authorization service.
       """
       # This hosting enviroment is assumed to come from the implementation
       # not the actual authorization manager. This is icky mix-in design.
       return self.hostingEnvironment.FindURLForObject(self.authManager)

   def GetRequiredRoles(self):
       """
       Return a list of roles required by this implementation for
       authorization to work.

       @return: a list of AccessGrid.Security.Role objects.
       """
       return self.rolesRequired

   def AddRequiredRole(self, role):
       """
       Add a role to the list of required roles for this implementation.

       @param role: the role to add
       @type role: AccessGrid.Security.Role object
       """
       self.rolesRequired.append(role)

class AuthorizationIMixIn(AuthorizationManagerI):
    """
    A MixIn class to provide the server side authorization infrastructure.
    """
    def GetAuthorizationManager(self):
        """
        Accessor to retrieve the authorization manager from the mixin.

        @returns: string containing the URL to the authorization interface.
        """
        return self.impl.GetAuthorizationManager()

class AuthorizationIWMixIn(AuthorizationManagerIW):
    """
    A MixIn class for the client side authorization support.
    """
    def GetAuthorizationManager(self):
        """
        This method retrieves the URL, then creates a client object using it.

        This is the cool part, we've built it so this is a real object.

        @return: AccessGrid.Security.AuthorizationManager.AuthoriationMangerIW
        """
        url = self.proxy.GetAuthorizationManager()
        amiw = AuthorizationManagerIW(url=url)
        return amiw

