#-----------------------------------------------------------------------------
# Name:        AuthorizationManager.py
# Purpose:     The class that does the authorization work.
# Created:     
# RCS-ID:      $Id: AuthorizationManager.py,v 1.35 2005-11-01 18:35:50 turam Exp $
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

__revision__ = "$Id: AuthorizationManager.py,v 1.35 2005-11-01 18:35:50 turam Exp $"

# External Imports
import os
import xml.dom.minidom

from AccessGrid import Log
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
        
        self.identificationRequired = 0
        
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
        log.debug('Authorizing action %s for %s', action, subject)
        action = MethodAction(action)
        
        # this gets us all the roles for this action
        rolelist = self.GetRoles(action=action)
        
        if subject == None:
            if self.IsIdentificationRequired():
                log.debug('Rejecting access from unidentified user; id required')
                return 0
            else:
                if Everybody in rolelist:
                    log.debug('Accepting access from unidentified user as part of Everybody role')
                    return 1
                else:
                    log.debug('Rejecting access from unidentified user as part of Everybody role')
                    return 0
                
        for role in rolelist:
            if role.HasSubject(subject.name):
                log.debug('Accepting access from %s', subject.name)
                return 1    
                
        log.debug('Rejecting access from %s', subject.name)
        return 0
        
    def RequireIdentification(self,boolFlag):
        self.identificationRequired = boolflag
    
    def IsIdentificationRequired(self):
        return self.identificationRequired

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
        
    def GetActions(self, inSubject=None, inRole=None):
        """
        Get a list of actions, perhaps for a subject or a role.

        @param subjectName: name of subject to get the actions for
        @param roleName: name of role to get actions for
        @type subject: string
        @type role: string
        @return: a list of actions
        @rtype: [AccessGrid.Security.Action]
        """
        
        if inSubject == None and inRole == None:
            # Just return the list of actions
            actionlist = self.actions
        elif inSubject != None and inRole == None:
            # Return the list of actions for this subject
            actionlist = list()
            roles = self.GetRolesForSubject(inSubject.name)
            for r in roles:
                for a in self.actions:
                    if a.HasRole(r.name) and a not in actionlist:
                        actionlist.append(a)
        elif inSubject == None and inRole != None:
            # Return the list of actions for this role
            actionlist = list()
            for a in self.actions:
                if a.HasRole(inRole.name) and a not in actionlist:
                    actionlist.append(a)
        else:
            raise Exception("GetActions called with both a subject and a role")

        return actionlist[:]
        
    def FindAction(self, actionName):
        """
        Find an action by name.

        @param name: the name of the action to find
        @type name: string
        @return: Action or None
        @rtype: AccessGrid.Security.Action 
        """
        for a in self.actions:
            if str(a.name) == str(actionName):
                return a
           
        return None
    
    def AddRoleToAction(self, inAction, inRole):
        """
        Encapsulation method, outside callers should not have to interact
        with anything but an authorization manager. This method hides the
        details of adding roles to actions.
        """
        role = self.FindRole(inRole.name)

        if role is None:
            log.error("Couldn't find role: %s", inRole.name)
            raise RoleNotFound(inRole.name)

        action = self.FindAction(inAction.name)
            
        if action is None:
            log.error("Coudn't find action: %s", inAction.name)
            action = Action(inAction.name)
            self.AddAction(action)
                  
        if not action.HasRole(role):
            action.AddRole(role)
        else:
            log.warn("Not adding role %s to action %s, it's already there.",
                     inRole.name, inAction.name)


    def AddRolesToAction(self, roleList, action):
        """
        Add multiple roles to an action.
    
        @param roleList: the list of roles to add to the action.
        @param action: the action that gets the roles added to it
        @type roleList: [AccessGrid.Security.Role]
        @type action: AccessGrid.Security.Action 
        """
        rl = []
        
        a = self.FindAction(action.name)
        
        if not a:
            raise ActionNotFound(action.name)
        
        for r in rl:
            a.AddRole(r)

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
    
    def AddSubjectToRole(self, inSubject, inRole):
        """
        Encapsulation method, outside callers should not have to interact
        with anything but an authorization manager. This method hides the
        details of adding subjects to roles.
        """

        log.debug("Adding Subject: %s to Role: %s", inSubject.name, inRole.name)
        
        role = self.FindRole(inRole.name)

        if role is None:
            log.error("Couldn't find role: %s", inRole.name)
            raise RoleNotFound(inRole.name)
                   
        if not role.HasSubject(inSubject.name):
            role.AddSubject(inSubject)
        else:
            log.warn("Not adding subject %s to role %s, it's already there.",
                     inSubject.name, inRole.name)

    def GetRolesForSubject(self, inSubject):
        """
        Get all the roles the specified subject is part of.

        @param subjectName: the name of the subject that the roles must contain
        @type subjectName: string
        @return: a list of roles
        @rtype: AccessGrid.Security.Role 
        """
        rolelist = list()

        for r in self.roles:
            if r.HasSubject(inSubject.name):
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
        
    def RemoveSubjectFromRole(self, subject, role):
        """ 
        Remove multiple subjects from the role.
        
        @param subjectList: the list of subjects to remove
        @param role: the role to remove the subject from
        @type subjectList: [AccessGrid.Security.X509Subject] 
        @type role: AccessGrid.Security.Role 
        """
        r = self.FindRole(role.name)
        
        if not r:
            raise RoleNotFound(role.name)
        
        r.RemoveSubject(subject)

    def RemoveSubjectsFromRole(self, subjectList, role):
        """ 
        Remove multiple subjects from the role.
        
        @param subjectList: the list of subjects to remove
        @param role: the role to remove the subject from
        @type subjectList: [AccessGrid.Security.X509Subject] 
        @type role: AccessGrid.Security.Role 
        """
        r = self.FindRole(role.name)
        
        if not r:
            raise RoleNotFound(role.name)
        
        for s in subjectList:
            subject = X509Subject.X509Subject.CreateSubject(s)
            r.RemoveSubject(subject)

    def RemoveRoleFromAction(self, role, action):
        """
        Remove a role from the action.
        
        @param role: the role to remove from the action
        @param action: the action to remove the role from
        @type role: AccessGrid.Security.Role
        @type action: AccessGrid.Security.Action 
        """
        
        # cheating
        role.name = str(role.name)
        action.name = str(action.name)
        
        
        a = self.FindAction(action.name)

        if not a:
            raise ActionNotFound(action.name)
        
        r = a.FindRole(role.name)

        if not r:
            raise RoleNotFound(role.name)
            
        a.RemoveRole(r)


    ListSubjects = GetSubjects
    ListRoles = GetRoles
    ListActions = GetActions
    GetPolicy = ToXML
    ListRolesInAction = GetRoles
        



if __name__ == "__main__":
    import logging
    import sys
    from AccessGrid import Toolkit
    
    
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
