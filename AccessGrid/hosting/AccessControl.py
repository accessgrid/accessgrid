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

import sys
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

    def __init__(self, role_name, role_manager):
        self.name = role_name
        self.manager = role_manager

    def GetName(self):
        return self.name

    def GetMembership(self):
        return self.manager.GetRoleList()

class RoleAlreadyRegistered(Exception):
    """
    This role already has been registered in the RoleManager.
    """

    pass

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

    def GetRoleList(self):
        """
        Return the list of Role objects, one for each role currently registered.
        """

        raise NotImplementedError


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

    def ValidateUser(self, userList):
        """
        Determine if the current subject is in userList
        """

        #
        # Doh! User passed in just a single user, not a list. Wrap it for him.
        #
        # There might be a better way to do this comparison. for instance, it
        # will fail if a UserList instance is passed in, or a tuple.
        #
        if type(userList) != types.ListType:
            userList = [userList]
        
        for user in userList:
            if self.subject.IsUser(user):
                return 1

        return 0

    def ValidateRole(self, roleList):
        if self.role_manager is None:
            return 0
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
            role_mgr = self.service_object.GetRoleManager()

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
              log.exception("Exception in call to %s", self.callback)
              del _managers[thread_id]
            
              fault = faultType(faultstring = str(e))

              import traceback
              info = sys.exc_info()

              fault._setDetail("".join(traceback.format_exception(
                                    info[0], info[1], info[2])))
              raise fault
        else:
              del _managers[thread_id]

        # print "Wrapper returning ", rc
        return rc
