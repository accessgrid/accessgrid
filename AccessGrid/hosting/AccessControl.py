#-----------------------------------------------------------------------------
# Name:        AccessControl.py
# Purpose:     Server-side method invocation support.
#
# Author:      Robert Olson
#
# Created:     
# RCS-ID:      $Id: AccessControl.py,v 1.8 2003-08-04 22:16:07 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Access Control mechanisms for the AG system.

"""

#
# This is an unfortunate import from the individual hosting environment.
#
# The fix is likely to provide the invoke-with-security-mgr functionality
# as a function here, and invoke from a wrapper that is hosted within
# ServiceObject.
#

import sys, types
import logging
log = logging.getLogger("AG.hosting.AccessControl")

from AccessGrid.hosting.pyGlobus.Utilities import SecureConnectionInfo
from AccessGrid.hosting.pyGlobus.AGGSISOAP import MethodSig, faultType

#
# The following is some magic (borrowed from Zope. Thanks guys!)
# to achieve thread-specific security managers.
#
# _managers maps from thread id to the security manager for that thread.
#

_managers = {}

#
# Define a method to get our identity.
# This makes the code work when we're not using threads. We'll
# probably always be using threads, but better safe then sorry.
#

try:
    import thread
except:
    get_ident = lambda: 0
else:
    get_ident = thread.get_ident

#
# Authentication types, used in the Subject class
#

AUTH_X509 = "x509"
AUTH_ANONYMOUS = "anonymous"

class Subject:
    """
    A Subject instance represents an AG user.

    A Subject can be identified by various authentication mechanisms. we currently
    support X509 certificates (per Globus).

    """
    
    def __init__(self, name, auth_type, auth_data = None):
        self.name = name
        self.auth_type = auth_type
        self.auth_data = auth_data

    def GetName(self):
        return self.name

    def GetAuthenticationType(self):
        return self.auth_type

    def GetAuthenticationData(self):
        return self.auth_data

    def GetSubject(self):
        return (self.auth_type, self.name, self.auth_data)

    def IsUser(self, user):
        """
        Returns true if this subject is the same as the passed-in user.
        user can be a string, in whcih case we assume that the username is an
        X509 DN. It can be a standard (authtype, name, authinfo) tuple, in which case we
        compare the DN. Or it can be a Subject instance, in which case we compare the subjects
        as returned by GetSubject.
        """

        # Feh, there is a better way to do this but I can't remember at the moment
        if type(user) == type(""):
            # print "Match on string ", user
            return self.name == user and self.auth_type == AUTH_X509
        elif type(user) == type(()):
            # print "Match on tuple ", self.GetSubject()
            return user == self.GetSubject()
        elif isinstance(user, Subject):
            # print "match on obj ", self.GetSubject()
            return user.GetSubject() == self.GetSubject()
        else:
            return 0
            
    def __repr__(self):
        return str(self.GetSubject())

class Role:
    """
    A Role instance represents a list of Subjects (users).

    It is used to represent all the users belonging to specific 
       permission sets or "roles."
    For example, if a Role is called "AllowedEntry", it is most
       likely a list of users users are allowed to enter something.

    """

    def __init__(self, role_name, role_manager):
        self.name = role_name
        self.manager = role_manager
        self.subjects = []

    def GetName(self):
        return self.name

    def GetMembership(self):
        return self.manager.GetRoleList()

    def AddSubject(self, subject):
        for s in self.subjects:
            if isinstance(s, Subject):
                if s.IsUser(subject):
                    return
            elif isinstance(subject, Subject):
                if subject.IsUser(s):
                    return
            elif type(s) == type(subject):
                if s == subject:
                    return 
            else:
                raise "UnknownSubjectTypeError"
               
        self.subjects.append(subject)

    def RemoveSubject(self, subject):
        #print "Remove Subject: self.subjects:", self.subjects
        for i in range(len(self.subjects)-1, -1, -1):
            if isinstance(self.subjects[i], Subject):
                if self.subjects[i].isUser(subject):
                    del self.subjects[i]
            elif self.subjects[i] == subject:
                del self.subjects[i]

    def HasSubject(self, subject):
        for s in self.subjects:
            if isinstance(s, Subject):
                if s.IsUser(subject):
                    return 1
            elif s == subject:
                    return 1
        return 0

    def GetSubjectList(self):
        return self.subjects

    def GetSubjectListAsStrings(self):
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
            else:
                raise "InvalidSubjectError"
        return subjectStringList


class RoleAlreadyRegistered(Exception):
    """
    This role already has been registered in the RoleManager.
    """

    pass

class InvalidExternalRoleManager(Exception):
    """
    This role RoleManager was not valid.
    """

class CircularReferenceInRoles(Exception):
    """
    This role RoleManager was not valid.
    """


class RoleManager:
    """
    A RoleManager provides the mechanism for apps to register and query roles.

    A resource that gates access based on roles will use a RoleManager instance
    to determine if the subject requesting access is a member of the appropriate role.

    A resource that holds the information necessary to assign subjects to
    roles will act as (either inheriting from or providing an instance of) a
    RoleManager. 

    """

    def __init__(self):
        self.validRoles = {}
        # Other role managers that this role manager knows about.
        self.roleManagers = {}

    def GetRoleList(self):
        """
        Return the list of Role objects, one for each role currently registered.
        """
        return self.validRoles.keys()

    def GetExternalRoleManagerList(self):
        """
        Return the list of Role Manager objects.
        Store external role managers that we may include roles from.
        """
        return self.roleManagers.keys()

    def GetExternalRoleManager(self, manager_name):
        """
        Return the list of Role Manager objects.
        Store external role managers that we may include roles from.
        """
        if manager_name in self.roleManagers:
            return self.roleManagers[manager_name]
        else:
            mgrs_strng = ""
            for a in self.GetExternalRoleManagerList():
                mgrs_strng.append(a)
            raise InvalidExternalRoleManager(manager_name + " requested from possible: " + mgrs_strng + ".")

    def GetRole(self, role_name):
        """
        Return a role instance with the matching role name.
        """
        return self.validRoles[role_name]

    def RegisterRole(self, role_name):
        """
        Add role_name as a valid role for this RoleManager.

        Returns the Role object for this role.
        """

        if self.validRoles.has_key(role_name):
            raise RoleAlreadyRegistered(role_name)

        role = Role(role_name, self)
        self.validRoles[role_name] = role
        return role

    def RegisterExternalRoleManager(self, name, role_manager):
        self.roleManagers[name] = role_manager 

    def DetermineRoles(self, subject):
        """
        Determine which roles the given subject belongs to.
        """

        raise NotImplementedError


def CreateSubjectFromGSIContext(context):
    initiator, acceptor, valid_time, mechanism_oid, flags, local_flag, open_flag = context.inquire()
    subj_name = initiator.display()
    return Subject(subj_name, AUTH_X509)

class SecurityManager:
    """
    """
    def __init__(self, roleManager, soapContext, threadId):
        self.role_manager = roleManager
        self.soap_context = soapContext
        self.thread_id = threadId

        #
        # Globus-specific for now
        #

        self.subject = CreateSubjectFromGSIContext(self.soap_context.security_context)


    def GetSubject(self):
        return self.subject

    def ValidateUserInList(self, userList):
        """
        Determine if the current subject is in userList
        """

        #print "ValidateUser", userList, self.subject
 
        #
        # Doh! User passed in just a single user, not a list. Wrap it for him.
        #
        # There might be a better way to do this comparison. for instance, it
        # will fail if a UserList instance is passed in, or a tuple.
        #
        if type(userList) != types.ListType:
            userList = [userList]

        # Check if all users are members of this role. 
        if "ALL_USERS" in userList:
            return 1
        
        for user in userList:
            if self.subject.IsUser(user):
                return 1

        return 0

    def ValidateRole(self, roleList, roleManager):
        if roleManager is None:
            return 0
        for role in roleList:
            if isinstance(role, Role):
                if role.name in roleManager.GetRoleList():
                    return 1
            elif role in roleManager.GetRoleList():
                return 1
            # Check for matches with roles included from other role managers.
            elif role.startswith("Role."): # external role
                external_role_name = s.lstrip("Role.")
                for rm in roleManager.GetExternalManagerList():
                   if external_role_name in rm.GetRoleList():
                       return 1
        return 0

    def ValidateUserInRole(self, role_name, role_manager, recursed_roles=[]):
        subject = self.GetSubject()
        return self._ValidateUserInRole(subject, role_name, role_manager, recursed_roles)

    def _ValidateUserInRole(self, user, role_name, role_manager, recursed_roles=[]):
        """
        Verify user is in role, given a user name, role name, and role manager.
        recursed_roles are used to make sure we don't have any circular references
           that would cause infinite loops.
        Role names that start with "Role." usually refer to an external role manager.
        """
        # Make sure we don't look through the same list twice.
        if role_name in recursed_roles: 
            recursed_strings = ""
            for s in recursed_roles:
                recursed_strings += " " + s
            log.exception("Role rules have circular reference.  role name: %s, previous roles: %s", role_name, recursed_strings)
            raise CircularReferenceInRoles(role_name + " previous roles: " + recursed_strings)
            return 0

        ### Check if role refers to an external rolemanager
        if role_name.startswith("Role."): # external role
            separated_name = role_name.split(".")
            if len(separated_name) < 3: # Expecting "Role.xxxx.xxxx"
                raise "InvalidRoleName" 
            erm = role_manager.GetExternalRoleManager(separated_name[1])
            erm_role_name = role_name.lstrip("Role.")
            erm_role = erm.GetRole(erm_role_name)
            if self.ValidateUserInList(erm_role.GetSubjectList()):
                log.info("User %s authorized for role %s", user, erm_role.name)
                #print "User",user,"authorized for role",  erm_role.name
                return 1
            else:
                # Check if this role contains references to other roles.
                for r in erm_role.GetSubjectList():
                    if r.name.startswith("Role."):
                        #print "recursing with :", r
                        tmp_recursed_roles = recursed_roles[:]
                        tmp_recursed_roles.append(erm_role_name) # append current role so we don't infinitely recurse.
                        ret_val = self.ValidateUserInRole(r, role_manager, tmp_recursed_roles)
                        if ret_val:
                            log.info("User %s authorized for role %s", user, r.name)
                            #print "User",user,"authorized for role",  r.name
                            return 1
            # Failed to find user in role. 
            log.info("User %s not authorized for role: %s", user, role_name)
            #print "User",user,"not authorized for role",  role_name
            return 0

        ### Handle standard (internal) roles.
        role = role_manager.validRoles[role_name]

        if self.ValidateRole([role], role_manager):
        
            if self.ValidateUserInList(role_manager.GetRole(role_name).GetSubjectList()):
                log.info("User %s authorized for role %s", user, role.name)
                #print "User",user,"authorized for role",  role.name
                return 1
            else:
                # Check if this role contains references to other roles.
                # If so, call this function again to process the an external role.
                for r in role.GetSubjectList():
                    if r.startswith("Role."):
                        #print "recursing with :", r
                        tmp2_recursed_roles = recursed_roles[:]
                        tmp2_recursed_roles.append(role_name) # append current role so we don't infinitely recurse.
                        ret_val = self.ValidateUserInRole(r, role_manager, tmp2_recursed_roles)
                        if ret_val:
                            log.info("User %s authorized for role %s", user, role.name)
                            #print "User",user,"authorized for role",  role.name
                            return 1
                
            # Failed to find user in role. 
            log.info("User %s not authorized for role: %s", user, role.name)
            #print "User",user,"not authorized for role",  role.name
            #print "Valid subjects in the role are:", role.GetSubjectListAsStrings()
            return 0
        else:
            #print "Role " + role.name + " is not valid."
            log.exception("Role " + role.name + " is not valid.")
            raise "InvalidRole"
        return 0 


    def __repr__(self):
        return "SecurityManager(rolemgr=%s, soapContext=%s, threadId=%s)" % (
            self.role_manager,
            self.soap_context,
            self.thread_id)

def GetSecurityManager():
    """
    Return the SecurityManager instance for this thread.

    Returns None if none is registered (this might
    be a main program thread with no identity registered).
    """
    
    thread_id = get_ident()
    if _managers.has_key(thread_id):
        return _managers[thread_id]
    else:
        return None

class InvocationWrapper(MethodSig):
    """
    An InvocationWrapper provides the security manager context setup for a method call.

    It derives from SOAP.MethodSig so that the SOAP engine will
    automatically invoke the method through this wrapper.
    """
    
    def __init__(self, callback, pass_connection_info, service_object):

        MethodSig.__init__(self, callback, keywords = 0, context = 1)

        self.callback = callback
        self.pass_connection_info = pass_connection_info
        self.service_object = service_object

        self.__name__ = callback.__name__

    def __call__(self, *args, **kwargs):
        """
        Invoked when this instance is "called" as a function.

        Set up the security context, invoke the callback, tear down the
        security context, and return.
        """

        # print "IN call ", kwargs
        soap_context  = kwargs["_SOAPContext"]

        role_mgr = None
        if self.service_object is not None:
            #print "getting role_mgr from: ", self.service_object
            role_mgr = self.service_object.GetRoleManager()
        else:
            log.exception("Can't get role_mgr, self.service_object is None")

        # print "invocationwrapper: context=%s role_mgr=%s" % (soap_context, role_mgr)

        thread_id = get_ident()
        # print "Got thread  id ", thread_id
        _managers[thread_id] = SecurityManager(role_mgr, soap_context, thread_id)

        try:
            if self.pass_connection_info:

                cinfo = SecureConnectionInfo(soap_context.security_context)

                args = (cinfo,) + args

            # print "callback=%s args=%s" % (self.callback, args)
            rc = self.callback(*args)

        except Exception, e:

              # print "call raised exception: ", e
              log.exception("Exception '%s' in call to %s", str(e), self.callback)
              del _managers[thread_id]
            

              import traceback
              info = sys.exc_info()

              ftype = traceback.format_exception_only(info[0], info[1])
              fault = faultType(faultcode = str(info[0]),
                                faultstring = ftype[0])
              fault._setDetail("".join(traceback.format_exception(
                                    info[0], info[1], info[2])))
              raise fault
        else:
              del _managers[thread_id]

        # print "Wrapper returning ", rc
        return rc
