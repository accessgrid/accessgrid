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

from AccessGrid.hosting.pyGlobus.utilities import SecureConnectionInfo
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

class RoleManager:

    def __init__(self):
        pass

    def GetRoleList(self):
        pass

    def RegisterRole(self, role_name):
        pass

    def DetermineRoles(self, subject):
        pass

def getSecurityManager():
    pass

class SecurityManager:

    def __init__(self, roleManager, soapContext, threadId):
        self.role_manager = roleManager
        self.soap_context = soapContext
        self.thread_id = threadId

        #
        # Globus-specific for now
        #

        context = self.soap_context.security_context
        initiator, acceptor, valid_time, mechanism_oid, flags, local_flag, open_flag = context.inquire()
        subj_name = initiator.display()
        self.subject = Subject(subj_name, AUTH_X509)

    def GetSubject(self):
        return self.subject

    def ValidateUser(self, userList):
        """
        Determine if the current subject is in userList
        """

        #
        # Doh! User passed in just a single user, not a list. Wrap it for him.
        #
        if type(userList) != type([]):
            userList = [userList]
        
        for user in userList:
            if self.subject.IsUser(user):
                return 1

        return 0

    def ValidateRole(self, roleList):
        pass

    def __repr__(self):
        return "SecurityManager(rolemgr=%s, soapContext=%s, threadId=%s)" % (
            self.role_manager,
            self.soap_context,
            self.thread_id)

def GetSecurityManager():
    thread_id = get_ident()
    return _managers[thread_id]

class InvocationWrapper(MethodSig):

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

            del _managers[thread_id]

            fault = faultType(faultstring = str(e))
            raise fault
        else:
            del _managers[thread_id]

        # print "Wrapper returning ", rc
        return rc
