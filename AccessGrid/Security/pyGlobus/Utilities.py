#-----------------------------------------------------------------------------
# Name:        Utilities.py
# Purpose:     pyGlobus helper code
#
# Author:      Robert D. Olson
#
# Created:     2003/08/02
# RCS-ID:      $Id: Utilities.py,v 1.2 2004-02-24 21:33:08 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------


"""
pyGlobus hosting environment utility classes and functions.
"""

__revision__ = "$Id: Utilities.py,v 1.2 2004-02-24 21:33:08 judson Exp $"
__docformat__ = "restructuredtext en"

import pyGlobus.io
import pyGlobus.ioc
import pyGlobus.security

from AccessGrid.Security.X509Subject import X509Subject

def CreateSubjectFromGSIContext(context):
    try:
        initiator = context.inquire()[0]
        subject_name = initiator.display()
    except Exception, e:
        print "Can't create subject from GSI Context", e
        raise e

    return X509Subject(subject_name)

#
# These should get replaced by a Attr factory in the new pyGlobus
#

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
    
