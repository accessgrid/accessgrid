

"""
pyGlobus hosting environment utility classes and functions.
"""

import socket
import pyGlobus.io
import pyGlobus.ioc
import pyGlobus.utilc
import pyGlobus.security

class SecureConnectionInfo:
    """
    Wrapper for the security information passed in a pyGlobus security context.

    This was used in the connection_info passing mechanism, will be deprecated
    in favor of use of SecurityManager.
    
    """
    
    def __init__(self, context):

        initiator, acceptor, valid_time, mechanism_oid, flags, local_flag, open_flag = context.inquire()

        self.initiator = initiator
        self.acceptor = acceptor

    def get_remote_name(self):
        return self.initiator.display()

    def __repr__(self):
        return "SecureConnectionInfo(initiator=%s, acceptor=%s)"  % (self.initiator.display(), self.acceptor.display())


def CreateTCPAttrDefault():
    """
    Create a TCP attr with common defaults.
    This does not set authorization or authentication modes.

    """

    attr = pyGlobus.io.TCPIOAttr()

    attr.set_authentication_mode(pyGlobus.ioc.GLOBUS_IO_SECURE_AUTHENTICATION_MODE_GSSAPI)
    attr.set_channel_mode(pyGlobus.ioc.GLOBUS_IO_SECURE_CHANNEL_MODE_GSI_WRAP)
    attr.set_delegation_mode(pyGlobus.ioc.GLOBUS_IO_SECURE_DELEGATION_MODE_NONE)
    
    attr.set_restrict_port(0)
    attr.set_reuseaddr(1)
    attr.set_nodelay(1)

    return attr

def CreateTCPAttrDefaultSSL():
    """
    Create a TCP attr with common defaults for SSL compatibility.
    This does not set authorization or authentication modes.

    """

    attr = pyGlobus.io.TCPIOAttr()

    attr.set_authentication_mode(pyGlobus.ioc.GLOBUS_IO_SECURE_AUTHENTICATION_MODE_GSSAPI)
    attr.set_channel_mode(pyGlobus.ioc.GLOBUS_IO_SECURE_CHANNEL_MODE_SSL_WRAP)
    attr.set_delegation_mode(pyGlobus.ioc.GLOBUS_IO_SECURE_DELEGATION_MODE_FULL_PROXY)
    
    attr.set_restrict_port(0)
    attr.set_reuseaddr(1)
    attr.set_nodelay(1)

    return attr

def CreateTCPAttrSelfAuth():
    """
    Create a TCP attr to allow only connections from self.

    http://www-unix.globus.org/api/c-globus-2.0-beta1/globus_io/html/group__security.html#a7


    """

    attr = CreateTCPAttrDefault()

    authmode = pyGlobus.ioc.GLOBUS_IO_SECURE_AUTHORIZATION_MODE_SELF

    attr.set_authorization_mode(authmode, authdata)

    return attr
    

def CreateTCPAttrCallbackAuth(auth_cb):
    """
    Create a TCP attr to invoke auth_cb for authorization decisions.

    http://www-unix.globus.org/api/c-globus-2.0-beta1/globus_io/html/group__security.html#a7


    """

    attr = CreateTCPAttrDefault()

    authdata = pyGlobus.io.AuthData()

    authdata.set_callback(auth_cb, None)
    authmode = pyGlobus.ioc.GLOBUS_IO_SECURE_AUTHORIZATION_MODE_CALLBACK

    attr.set_authorization_mode(authmode, authdata)

    return attr

def CreateTCPAttrCallbackAuthSSL(auth_cb):
    """
    Create a TCP attr to invoke auth_cb for authorization decisions.

    http://www-unix.globus.org/api/c-globus-2.0-beta1/globus_io/html/group__security.html#a7


    """

    attr = CreateTCPAttrDefaultSSL()

    authdata = pyGlobus.io.AuthData()

    authdata.set_callback(auth_cb, None)
    authmode = pyGlobus.ioc.GLOBUS_IO_SECURE_AUTHORIZATION_MODE_CALLBACK

    attr.set_authorization_mode(authmode, authdata)

    return attr

def CreateTCPAttrAlwaysAuth():
    """
    Create a TCP attr that allows all connections.

    """

    def always_allow_cb(server, g_handle, remote_user, context):
        return 1

    attr = CreateTCPAttrCallbackAuth(always_allow_cb)

    return attr
    
def CreateTCPAttrAlwaysAuthSSL():
    """
    Create a TCP attr that allows all connections.

    """

    def always_allow_cb(server, g_handle, remote_user, context):
        return 1

    attr = CreateTCPAttrCallbackAuthSSL(always_allow_cb)

    return attr
    
def GetHostname():
    """
    Return the local hostname.

    This uses the pyGlobus mechanism when possible, in order
    to get a hostname that Globus will be happy with.

    """

    ret, host = pyGlobus.utilc.get_hostname(256)
    if ret != 0:
        host = socket.getfqdn()
    return host
