#-----------------------------------------------------------------------------
# Name:        AuthorizationManager.py
# Purpose:     The class that does the authorization work.
# Created:     
# RCS-ID:      $Id: AuthorizationManager.py,v 1.33 2005-10-10 22:19:27 lefvert Exp $
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

__revision__ = "$Id: AuthorizationManager.py,v 1.33 2005-10-10 22:19:27 lefvert Exp $"

# External Imports
import os
import xml.dom.minidom

from AccessGrid import Log
#AGTk Importsfrom AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.hosting import Decorate, Reconstitute, Client
from AccessGrid.GUID import GUID
from AccessGrid.Security.Role import RoleNotFound, RoleAlreadyPresent, InvalidRole
from AccessGrid.Security.Action import Action
from AccessGrid.Security.Action import ActionNotFound, ActionAlreadyPresent
from AccessGrid.Security.Action import MethodAction
from AccessGrid.Security import X509Subject
from AccessGrid.Security.Role import Everybody, Administrators, Role

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
        self.rolesRequired = list()
                
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
            numSubjs = len(node.childNodes)
            for s in node.childNodes:
                s = X509Subject.X509Subject(str(s.attributes["name"].value),
                                            s.attributes["auth_data"].value)
                if sl.count(s) == 0:
                    sl.append(s)

            r = Role(node.attributes["name"].value, sl)

            return(r, numSubjs)

        # Internal function to create an action
        def unpackAction(node, to):
            a = MethodAction(str(node.attributes["name"].value))
            for rn in map(lambda x: x.attributes["name"].value,
                          node.childNodes):
                try:
                    r = to.FindRole(str(rn))
                    a.AddRole(r)
                except KeyError:
                    log.exception("AuthManager Import: Role Not Found.")

            return a

        # Reset current configuration
        self.roles = []
        self.actions = []

        domP = xml.dom.minidom.parseString(policy)
        
        roleElements = domP.getElementsByTagName("Role")

        for c in roleElements:
            (r, default) = unpackRole(c)
            oldr = self.FindRole(str(r.name))
            if oldr is not None:
                if len(r.subjects) >= len(oldr.subjects):
                    self.RemoveRole(oldr)
                    self.AddRole(r)
            else:
                self.AddRole(r)

        for c in domP.getElementsByTagName("Action"):
            a = unpackAction(c, self)
            try:
                self.AddAction(a)
            except:
                # Don't add the action
                log.exception("AuthManager Import: Add action failed %s."%(a.name))
               
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

        for a in self.actions:
            authP.appendChild(a.ToXML(authDoc, 1))

        rval = authDoc.toxml()

	del authP

        return rval
    
    def IsAuthorized(self, subject, action):
        """
        This is the real workhorse of authorization, checking to see
        if a given subject is authorized for a given action.

        @param subject: the subject we're curious about
        @param action: the action to check the subject against.
        @type subject: AccessGrid.Security.X509Subject
        @type action: AccessGrid.Security.Action
        @return: 0 if not authorized, 1 if authorized.
        @rtype: int
        """
        # this gets us all the roles for this action
        rolelist = self.GetRoles(action=action)

        for role in rolelist:
            if role.HasSubject(subject.name):
                return 1

        return 0

    def AddAction(self, action):
        """
        Adds an action to this authorization manager.

        @param action: the action to add
        @type action: AccessGrid.Security.Action 
       
        @raise ActionAlreadyPresent: if it's already part of this
        authorization manager.
        """
        if not self.FindAction(action.GetName()):
            self.actions.append(action)
           
    def AddActions(self, actionList):
        """
        Add a list of actions, uses AddAction internally.

        @param actionList: a list of actions to add
        @type actionList: [AccessGrid.Security.Action]
        """
        for a in actionList:
            self.AddAction(a)
        
    def RemoveAction(self, action):
        """
        Remove an action from this authorization manager.

        @param action: the action to remove
        @type action: AccessGrid.Security.Action
     
        @raise ActionNotFound: if the specified action is not found.
        """
        i = 0
        
        for a in self.actions:
            if a.name == action.name:
                del self.actions[i]
            i = i + 1
        
    def GetActions(self, subjectName=None, roleName=None):
        """
        Get a list of actions, perhaps for a subject or a role.

        @param subjectName: name of subject to get the actions for
        @param roleName: name of role to get actions for
        @type subject: string
        @type role: string
        @return: a list of actions
        @rtype: [AccessGrid.Security.Action]
        """
        if subjectName:
            if type(subjectName) != str:
                raise StringRequired("subject name should be a string %s"%subjectName)

        if roleName:
            if type(roleName) != str:
                raise StringRequired("role name should be a string %s"%roleName)
        
        if subjectName == None and roleName == None:
            # Just return the list of actions
            actionlist = self.actions
        elif subjectName != None and roleName == None:
            # Return the list of actions for this subject
            actionlist = list()
            roles = self.GetRolesForSubject(subjectName)
            for r in roles:
                for a in self.actions:
                    if a.HasRole(r.name) and a not in actionlist:
                        actionlist.append(a)
        elif subjectName == None and roleName != None:
            # Return the list of actions for this role
            actionlist = list()
            for a in self.actions:
                if a.HasRole(roleName) and a not in actionlist:
                    actionlist.append(a)
                  
        else:
            print "GetActions called with both a subject and a role"

        return actionlist[:]
        
    def FindAction(self, name):
        """
        Find an action by name.

        @param name: the name of the action to find
        @type name: string
        @return: Action or None
        @rtype: AccessGrid.Security.Action 
        """
        name = str(name)

        if type(name) != str:
            s = "action name should be a string, name: %s type: %s"%(name, type(name))
            raise StringRequired(s)
        
        for a in self.actions:
            if str(a.name) == str(name):
                return a
           
        return None
    
    def AddRoleToAction(self, actionName, roleName):
        """
        Encapsulation method, outside callers should not have to interact
        with anything but an authorization manager. This method hides the
        details of adding roles to actions.
        """
        if type(actionName)!= str and type(roleName)!= str:
            raise StringRequired("role name and action name should be strings %s %s"%(actionName, roleName))
                
        role = self.FindRole(roleName)

        if role is None:
            log.error("Couldn't find role: %s", roleName)
            raise RoleNotFound(roleName)

        action = self.FindAction(actionName)
            
        if action is None:
            log.error("Coudn't find action: %s", actionName)
            action = Action(actionName)
            self.AddAction(action)
                  
        if not action.HasRole(role):
            action.AddRole(role)
        else:
            log.warn("Not adding role %s to action %s, it's already there.",
                     roleName, actionName)


    def AddRole(self, role, default = 0):
        """
        Add a role to this authorization manager.

        @param role: the role to add
        @param default: a flag indicating if the role is a default role
                @type role: AccessGrid.Security.Role 
        @type default: int
        @return: Added role
        @rtype: AccessGrid.Security.Role
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
        @type role: AccessGrid.Security.Role 
        @raise RoleNotFound: if the role isn't found
        """
        i = 0

        for r in self.roles:
            if role.name == r.name:
                del self.roles[i]

            i = i + 1
        
    def AddRoles(self, roleList):
        """
        Add multiple roles to the authorization manager.
        This calls AddRole for each role in the list.
        
        @param roleList: the list of roles to add
        @param roleList: the list of roles to add
        @type roleList: [AccessGrid.Security.Role]
        """
        for r in roleList:
            try:
                self.AddRole(r)
            except RoleAlreadyPresent:
                log.info("Tried to add role that already exists %s", r)
        
    def GetRoles(self, action=None):
        """
        Get the list of Roles, optionally the roles associated with an action.

        @keyword action: Action to retrieve roles for, None if not set
        @type action: AccessGrid.Security.Action 
        @return: list of roles 
        @rtype: AccessGrid.Security.Role 
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
                return []
                             
            rolelist = foundAction.GetRoles()

        return rolelist

    def FindRole(self, name):
        """
        Find a role in this authorization manager.

        @param name: the name of the role to find
        @type name: string
        @return: AccessGrid.Security.Role or None
        """
        name = str(name)
        
        for r in self.roles:
            if r.name == name:
                return r
        return None
    
    def AddSubjectToRole(self, subjectName, roleName):
        """
        Encapsulation method, outside callers should not have to interact
        with anything but an authorization manager. This method hides the
        details of adding subjects to roles.
        """
        if type(subjectName)!=str or type(roleName)!= str:
            raise StringRequired("subject name and role name should be strings %s %s" %(subjectName, roleName))
        
        log.debug("Adding Subject: %s to Role: %s", subjectName, roleName)
        xs = X509Subject.CreateSubjectFromString(subjectName)
        
        role = self.FindRole(roleName)

        if role is None:
            log.error("Couldn't find role: %s", roleName)
            raise RoleNotFound(roleName)
                   
        if not role.HasSubject(subjectName):
            role.AddSubject(xs)
        else:
            log.warn("Not adding subject %s to role %s, it's already there.",
                     subjectName, roleName)

    def GetRolesForSubject(self, subjectName):
        """
        Get all the roles the specified subject is part of.

        @param subjectName: the name of the subject that the roles must contain
        @type subjectName: string
        @return: a list of roles
        @rtype: AccessGrid.Security.Role 
        """
        if type(subjectName) != str:
            raise StringRequired("subjectName should be a string %s" %(subjectName))
                
        rolelist = list()

        for r in self.roles:
            if r.HasSubject(subjectName):
                rolelist.append(r)

        return rolelist
    
    def GetSubjects(self, role=None):
        """
        Get the subjects known by this authorization manager, possibly for the
        specified role.

        @keyword role: the role to retrieve subjects for, default None
        @type role: AccessGrid.Security.Role 
        @return: a list of  roles
        @rtype: [AccessGrid.Security.X509Subject]
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
        @return: list of roles
        @rtype: [AccessGrid.Security.Role]
        """
	return self.defaultRoles

    def SetRoles(self, action, roles):
        """
        Sets the roles for the specified action.

        @param action: the action to set roles for
        @param roles: the list of roles to set the action with
        @type action: AccessGrid.Security.Action 
        @type roles: [AccessGrid.Security.Role]
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
        @type role: AccessGrid.Security.Role 
        @type subjects: [AccessGrid.Security.X509Subject]
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
        @type authMgr: AccessGrid.Security.AuthorizationManager
        """
        self.parent = authMgr

    def SetDefaultRoles(self, roles=[]):
        """
        Set the default roles for this authorization manager.
        @keyword roles: the list of roles that should be default, defaults to []
        @type roles: [AccessGrid.Security.Role]
        """
        self.defaultRoles=roles

    def GetRequiredRoles(self):
        """
        Return a list of roles required by this implementation for
        authorization to work.
        
        @return: a list of roles
        @rtype: [AccessGrid.Security.Role]
        """
        return self.rolesRequired
    
    def AddRequiredRole(self, role):
        """
        Add a role to the list of required roles for this implementation.
        
        @param role: the role to add
        @type role: AccessGrid.Security.Role 
        """
        self.rolesRequired.append(role)
        

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
        log.debug("Authorizing: %s %s", args, *kw)
        
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
        @return: An XML formatted authorization policy.
        @rtype: string
        """
        return self.impl.ToXML()
    
    def AddRole(self, role):
        """
        Add a role to the authorization manager.

        @param role: the role to add.
        @type role: AccessGrid.Security.Role object
        """
        r = Role.CreateRole(role)
        r2 = self.impl.AddRole(r)
        return r2

    def GetRoles(self, action):
        r = self.impl.GetRoles(Action.CreateAction(action))
        return r

    def FindRole(self, name):
        """
        Find a role in this authorization manager.

        @param name: the name of the role to find
        @type name: string
        @return: the AccessGrid.Security.Role object or None
        """
        r = self.impl.FindRole(name)
        return r

    def RemoveRole(self, role):
        """
        Remove a role from the authorization manager.

        @param name: role to remove
        @type name: AccessGrid.Security.Role
        """
        self.impl.RemoveRole(role)
        
    def ListRoles(self, action = None):
        """
        Retrieve the entire list of Roles.
        
        @keyword action: the action to list roles for, if none is specified, list all known roles.
        @type action: AccessGrid.Security.Action
        
        @return: a list of roles
        @rtype: [AccessGrid.Security.Role]
        """
        if action == None:
            roles = self.impl.GetRoles()
        else:
            a = Action.CreateAction(action)
            a1 = self.impl.FindAction(a)
            roles = a1.GetRoles()

        return roles

    def AddAction(self, action):
        """
        Add an action to the authorization manager.

        @param action: the action to add
        @type action: AccessGrid.Security.Action
        """
        a = Action.CreateAction(action)
        self.impl.AddAction(a)        

    def RemoveAction(self, action):
        """
        Remove an action from the authorization manager.

        @param action: the action to remove
        @type action: AccessGrid.Security.Action
        """
        a = Action.CreateAction(action)
    
        if not a:
            raise ActionNotFound(action)
        
        self.impl.RemoveAction(a)

    def ListActions(self, subject = None, role = None):
        """
        List the actions known by this authorization manager.
        @return: a list of actions
        @rtype: [AccessGrid.Security.Action]
        """
        
        roleName = None
        subjectName = None
        
        if role:
            role = Role.CreateRole(role)
            roleName = role.name
        if subject:
            subject = X509Subject.X509Subject.CreateSubject(subject)
            subjectName = subject.name
            
        alist = self.impl.GetActions(subjectName, roleName)
        return alist        

    def ListSubjects(self, role=None):
        """
        List subjects that are in a specific role.

        @keyword role: the role to list the subjects of, defaults to None
        @type role: AccessGrid.Security.Role
        @return: [AccessGrid.Security.X509Subject]
        """

        subjs = None
        if role == None:
            # This is not a great engineering solution, and we should
            # probably revisit it with a better plan.
            profiles = self.impl.profileCache.LoadAllProfiles()
            subjs = map(lambda x:
                X509Subject.CreateSubjectFromString(x.GetDistinguishedName()),
                        profiles)
        else:
            r = Role.CreateRole(role)
            roleR = self.impl.FindRole(r.name)
            
            if not roleR :
                raise RoleNotFound(r.name)
            
            subjs = self.impl.GetSubjects(roleR)

        subjs2 = Decorate(subjs)
        return subjs

    def AddSubjectsToRole(self, role, subjectList):

        """
        Add a subject to a particular role.
        This uses AddSubjectsToRole internally.
        
        @param subjectList: the subject list to add
        @param role: the role to add the subject to
        @type subjectList: [AccessGrid.Security.X509Subject]
        @type role: AccessGrid.Security.Role
        """
        r = Role.CreateRole(role)
        role = self.impl.FindRole(r.name)
                           
        if not role:
            raise RoleNotFound(r.name)
            
        for s in subjectList:
            subject = X509Subject.X509Subject.CreateSubject(s)
            role.AddSubject(subject)
            
    def AddRoleToAction(self, action, role):
        """
        Add a role to the specified action.
        @param role: the role to add to the action
        @param action: the action that gets the role added
        @type role: AccessGrid.Security.Role
        @type action: AccessGrid.Security.Action 
        """
        an = Action.CreateAction(action)
        a = self.impl.FindAction(an.GetName())
        
        if not a:
            raise ActionNotFound(an.GetName())

        r = Role.CreateRole(role)

        self.impl.AddRoleToAction(an.GetName(), r.GetName())

    def AddRolesToAction(self, roleList, action):
        """
        Add multiple roles to an action.
        
        @param roleList: the list of roles to add to the action.
        @param action: the action that gets the roles added to it
        @type roleList: [AccessGrid.Security.Role]
        @type action: AccessGrid.Security.Action 
        """
        an = Action.CreateAction(action)
        rl = []
        
        for r in roleList:
            rl.append(Role.CreateRole(r))

        a = self.impl.FindAction(an.name)

        if not a:
            raise ActionNotFound(an.name)
        
        for r in rl:
            a.AddRole(r)
            
    def RemoveSubjectsFromRole(self, role, subjectList):
        """
        Remove multiple subjects from the role.
    
        @param subjectList: the list of subjects to remove
        @param role: the role to remove the subject from
        @type subjectList: [AccessGrid.Security.X509Subject] 
        @type role: AccessGrid.Security.Role 
        """
        rn = Role.CreateRole(role)
        r = self.impl.FindRole(rn.name)
        
        if not r:
            raise RoleNotFound(rn.name)

        for s in subjectList:
            subject = X509Subject.X509Subject.CreateSubject(s)
            r.RemoveSubject(subject)
                    
    def RemoveRoleFromAction(self, action, role):
        """
        Remove a Role from the action.
        
        @param role: the role to remove from the action
        @param action: the action to remove the role from
        @type role: AccessGrid.Security.Role
        @type action: AccessGrid.Security.Action 
        """
        an = Action.CreateAction(action)
        rn = Role.CreateRole(role)

        a = self.impl.FindAction(an.name)

        if not a:
            raise ActionNotFound(an.name)
        
        r = a.FindRole(rn.name)

        if not r:
            raise RoleNotFound(rn.name)
      
        a.RemoveRole(r)

    def GetRolesForSubject(self, subject):
        """
        Get the list of roles the subject is a part of.

        @param subject: the subject the roles are for
        @type subject: AccessGrid.Security.X509Subject 

        @return: list of roles
        @rtype: [AccessGrid.Security.Role] 
        """
        s = X509Subject.X509Subject.CreateSubject(subject)

        rl = self.impl.GetRolesForSubject(s.name)
        return rl
        
    def IsAuthorized(self, subject, action):
        """
        Check to see if the subject authorized for the action.
        
        @param subject: the subject being verified.
        @param action: the action the subject is being verified for.
        @type subject: AccessGrid.Security.X509Subject 
        @type action: AccessGrid.Security.Action 
        """
        s = X509Subject.X509Subject.CreateSubject(subject)
        a = Action.CreateAction(action)
        ret = self.impl.IsAuthorized(s, a)
        return ret

class AuthorizationManagerIW(SOAPIWrapper):
    """
    SOAP interface to an authorization manager. The authorization manager
    is designed to provide a simple interface that hides
    the network plumbing between clients and servers. The client side
    of this is just a functional interface through this object.
    """
    def __init__(self, url=None):
        """
        Create the client side object for the authorization service
        specified by the url.

        @param url: url to the authorization service
        @param url: url to the authorization service
        """
        SOAPIWrapper.__init__(self, url)

    def TestImportExport(self, policy):
        """
        A test call that verifies the policy can be imported and
        exported without modification.

        @param policy: an XML formatted authorization policy
        @type policy: string
        """
        self.proxy.TestImportExport(policy)

    def ImportPolicy(self, policy):
        """
        Imports a policy.

        @param policy: an XML formatted authorization policy
        @type policy: string
        """
        self.proxy.ImportPolicy(policy)
            
    def GetPolicy(self):
        """
        Retrieve the policy.

        @return: An XML formatted authorization policy.
        @rtype: string
        """
        return self.proxy.GetPolicy()
    
    def AddRole(self, role):
        """
        Add a role to the authorization manager.

        @param role: the role to add.
        @type role: AccessGrid.Security.Role 
        """
        role = self.proxy.AddRole(role)
        r = Role.CreateRole(role)
        return r
      
    def FindRole(self, name):
        """
        Find a role in this authorization manager.

        @param name: the name of the role to find
        @type name: string
        @return: if found a role, otherwise None
        @rtype: AccessGrid.Security.Role
        """
        
        r = self.proxy.FindRole(name)
        return Role.CreateRole(r)
       
        
    def RemoveRole(self, role):
        """
        Remove a role from the authorization manager.
        @param name: The role to remove.
        @type name: AccessGrid.Security.Role
        """
        self.proxy.RemoveRole(role)

    def ListRoles(self):
        """
        Retrieve the entire list of Roles.
        
        @return: A list of roles
        @rtype: [AccessGrid.Security.Role]
        """
        rs = self.proxy.ListRoles()
        rl = []
        for r in rs:
            rl.append(Role.CreateRole(r))
        
        return rl

    def AddAction(self, action):
        """
        Add an action to the authorization manager.

        @param action: Action to add
        @type action: AccessGrid.Security.Action
        """
        # Create action from name.
        self.proxy.AddAction(action)
           
    def RemoveAction(self, action):
        """
        Remove an action from the authorization manager.

        @param name: The action to remove
        @type name: AccessGrid.Security.Action
        """
        self.proxy.RemoveAction(action)

    def ListActions(self, subject = None, role = None):
        """
        List the actions known by this authorization manager.

        List the actions known by this authorization manager. Please set either
        subject or role, not both at the same time.
        
        @keyword subject: List actions for this subject, defaults to None
        @type subject: AccessGrid.Security.X509Subject
        @keyword role: List actions for this role, defaults to None
        @type role: AccessGrid.Security.Role
        @return: A list of actions
        @rtype: [AccessGrid.Security.Action]
        """

        al = self.proxy.ListActions(subject, role)
        alist = []

        for a in al:
            action = Action.CreateAction(a)
            alist.append(Action.CreateAction(action))
         
        return alist

    def ListSubjects(self, role = None):
        """
        List subjects that are in a specific role.
        @keyword role: The role to list the subjects of, defaults to None
        @type role: AccessGrid.Security.Role
        @return: A list of subjects
        @rtype: [AccessGrid.Security.X509Subject]
        """
        if role != None:
            sl = self.proxy.ListSubjects(role) 
        else:
            sl = self.proxy.ListSubjects(role) 

        slist = []

        for s in sl:
            slist.append(X509Subject.X509Subject.CreateSubject(s))

        return slist

    def ListRolesInAction(self, action):
        """
        List the roles associated with a specific action.
        @param action: The action to list roles for.
        @type action: AccessGrid.Security.Action
        @return: A list of roles
        @rtype: [AccessGrid.Security.Role]
        """
        r = self.proxy.GetRoles(action)
        rl = []

        for role in r:
            rl.append(Role.CreateRole(role))
        
        return rl 
        
    def AddSubjectToRole(self, subj, role):
        """
        Add a subject to a particular role.
        This uses AddSubjectsToRole internally.

        @param subj: The subject to add
        @param role: The role to add the subject to
        @type subj: AccessGrid.Security.X509Subject
        @type role: AccessGrid.Security.Role
        """
        subjList = [subj,]
        self.proxy.AddSubjectsToRole(role, subjList)

    def AddSubjectsToRole(self, subjList, role):
        """
        Add a list of subjects to a  particular role.

        @param subjList: A list of subjects
        @param role: The role to add the subjects to
        @type subjList: [AccessGrid.Security.X509Subject]
        @type role: AccessGrid.Security.Role 
        """
        
        self.proxy.AddSubjectsToRole(role, subjList)
        
    def AddRoleToAction(self, role, action):
        """
        Add a role to the specified action.

        @param role: the role to add to the action
        @param action: the action that gets the role added
        @type role: AccessGrid.Security.Role
        @type action: AccessGrid.Security.Action
        """
        self.proxy.AddRoleToAction(action, role)       

    def AddRolesToAction(self, roleList, action):
        """
        Add multiple roles to an action.
 
        @param roleList: the list of roles to add to the action.
        @param action: the action that gets the roles added to it
        @type roleList: [AccessGrid.Security.Role]
        @type action: AccessGrid.Security.Action 
        """
        self.proxy.AddRolesToAction(roleList, action)
         
    def RemoveSubjectFromRole(self, subj, role):
        """
        Remove the subject from the role.
        
        @param subj: the subject to remove
        @param role: the role to remove the subject from
        @type subj: AccessGrid.Security.X509Subject 
        @type role: AccessGrid.Security.Role 
        """
        subjList = [subj,]
        self.proxy.RemoveSubjectsFromRole(role, subjList)

    def RemoveSubjectsFromRole(self, subjList, role):
        """
        Remove multiple subjects from the role.
        
        @param subjList: the list of subjects to remove
        @param role: the role to remove the subject from
        @type subjList: [AccessGrid.Security.X509Subject] 
        @type role: AccessGrid.Security.Role 
        """
        self.proxy.RemoveSubjectsFromRole(role, subjList)

    def RemoveRoleFromAction(self, role, action):
        """
        Remove a Role from the action.

        @param role: the role to remove from the action
        @param action: the action to remove the role from
        @type role: AccessGrid.Security.Role 
        @type action: AccessGrid.Security.Action       
        """

        self.proxy.RemoveRoleFromAction(action, role)

    def GetRolesForSubject(self, subject):
        """
        Get the list of roles the subject is a part of.

        @param subject: the subject the roles are for
        @type subject: AccessGrid.Security.X509Subject
        @return: List of roles
        @rtype: [AccessGrid.Security.Role]
        """
       
        rl = self.proxy.GetRolesForSubject(subject)
        roles = []

        for r in rl:
            roles.append(Role.CreateRole(r))

        return roles
       
    def IsAuthorized(self, subject, action):
        """
        Check to see if the subject authorized for the action.
        
        @param subject: the subject being verified.
        @param action: the action the subject is being verified for.
        @type subject: AccessGrid.Security.X509Subject 
        @type action: AccessGrid.Security.Action 
        """
        ret = self.proxy.IsAuthorized(subject,action)
        return ret


if __name__ == "__main__":
    import logging
    import sys
    from AccessGrid import Toolkit
    from AccessGrid.Toolkit import CmdlineApplication
    
    
    app = Toolkit.CmdlineApplication()
    app.Initialize()

    # Local test, no SOAP involved

    def Show(authManager):
        print '========== roles'
        for r in authManager.GetRoles():
            print r.name
            for s in r.subjects:
                print '   ', s.name
                
        print '\n========== actions'
        for a in authManager.GetActions():
            print a.name
            for r in a.roles:
                print '***', r.name

        print '============= end actions'

    authManager = AuthorizationManager()
    authManager.AddRole(Administrators)
    authManager.AddRole(Everybody)
    
    myRole = Role("MyRole")
    
    authManager.AddRole(myRole)

    authManager.AddRequiredRole(Administrators)
    authManager.AddRequiredRole(Everybody)
    authManager.SetDefaultRoles([Administrators])

    a1 = Action("Action1") 
    a2 = Action("Action2")
    a3 = Action("Action3")
    authManager.AddActions([a1, a2])
    authManager.AddAction(a3)
   
    print '-----------------------------------'
    print '---- should show Admin, Everybody, myRole.'
    print '---- should show Action1, Action2, Action3 actions'
    Show(authManager)

    authManager.AddSubjectToRole("adminSubject",
                                 "Administrators")
    authManager.AddSubjectToRole("mySubject",
                                 "MyRole")
    authManager.AddSubjectToRole("TestList1", "MyRole")


    print '\n\n---------------------------------'
    print '---- should show adminSubject in Admins, mySubject and TestList1 in MyRole'
    Show(authManager)

    authManager.AddRoleToAction("Action2", "Administrators")
    authManager.AddRoleToAction("Action1", "MyRole")

    print '\n---------------'
    print '----- should print admins'
    print authManager.FindRole("Administrators").name

    print '\n-----------------'
    print '----- should print MyRole'
    for r in authManager.GetRolesForSubject("TestList1"):
        print r.name

    print '\n---------------------'
    print 'should print true and false'
    s = X509Subject.X509Subject("mySubject")
    print authManager.IsAuthorized(s, a1) 
    print authManager.IsAuthorized(s, a2)

    print '\n---------------------'
    print '---------- get actions for TestList1, should be Action1 '
    for a in authManager.GetActions(subjectName = "TestList1"):
        print a.name

    print '\n-------------------'
    print '------------ get actions for admins, should be Action2'
    for a in authManager.GetActions(roleName = "Administrators"):
        print a.name

    print '\n -------------------'
    print '----------- get subjects for admins'
    for s in authManager.GetSubjects(Administrators):
        print s.name

    authManager.RemoveAction(a2)
    authManager.RemoveRole(myRole)
    print '\n----------remove action 2 and role myrole'
    Show(authManager)


    # Check SOAP interface

    am = AuthorizationManagerIW("https://localhost:8000/VenueServer/Authorization")

    def Show2(authI):
        for r in authI.ListRoles():
            print r.name

            for s in authI.ListSubjects(r): 
                print '   ', s.name
                
        for a in authI.ListActions():
            print a.name

            for r in authI.ListRolesInAction(a):
                print '   ', r.name

    def Show3(authI):
        for a in authI.ListActions():
            print '---- this action', a.name
            for r in a.roles:
                print '   has this role', r.name

                for s in r.subjects:
                    print '   *** has this subject', s.name
                
    a = Action("TestAction")
    a2 = Action("TestAction2")
    r = Role("TestRole")
    r2 = Role("TestRole2")
    s = X509Subject.X509Subject("TestSubject")
    s2 = X509Subject.X509Subject("TestSubject2")

    am.AddRole(r)
    am.AddRole(r2)
    am.AddAction(a2)
    am.AddAction(a)

    am.AddRolesToAction([r], a) 
    am.AddRoleToAction(r2, a) 
    am.AddSubjectsToRole([s], r)
    am.AddSubjectToRole(s2, r)

    print '\n\n****** this should show'
    print 'TestAction with role TestRole, TestRole2'
    print 'TestAction2'
    print 'TestRole with subject TestSubject, TestSubject2'
    print 'TestRole2'
    print '*****'

    Show2(am)

    print '\n\n******* this should print TestRole'
    print am.FindRole(r.name) 

    print '\n\n******* this should print TestRole'
    for ro in am.GetRolesForSubject(s):
        print ro.name

    print '\n\n******* this should print 1'
    print am.IsAuthorized(s, a)
    print am.IsAuthorized(s2, a)

    print '\n\n******* this should print 0'
    print am.IsAuthorized(s2, a1)

    print '\n\n ****** get roles for', s.name
    for ro in am.GetRolesForSubject(s):
        print ro.name

    Show3(am)
          
    print '\n\n******* this should print TestAction'
    for ac in am.ListActions(subject = s):
        print ac.name

    print '\n\n******* this should print TestAction'
    for ac in am.ListActions(role = r):
        print ac.name

    print '\n\n******* this should print TestRole, TestRole2'
    for ro in am.ListRolesInAction(a):
        print ro.name
 
    print '\n\n******* this should print TestSubject, TestSubject2'
    for su in am.ListSubjects(r):
        print su.name
    
    am.RemoveRoleFromAction(r2, a) 
    am.RemoveSubjectFromRole(s2, r)
    am.RemoveSubjectsFromRole([s], r)
    am.RemoveAction(a) 
    am.RemoveRole(r2)

    print '\n\n******* after removing TestAction, TestRole2'
    Show2(am)

    am.RemoveRole(r)

    #am.GetPolicy()
    #am.ImportPolicy(policy) 
    #am.TestImportExport(policy) 
