#-----------------------------------------------------------------------------
# Name:        Utilities.py
# Purpose:     pyGlobus helper code
# Created:     2003/08/02
# RCS-ID:      $Id: Utilities.py,v 1.6 2004-09-10 03:58:53 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
pyGlobus hosting environment utility classes and functions.
"""

__revision__ = "$Id: Utilities.py,v 1.6 2004-09-10 03:58:53 judson Exp $"

from pyGlobus import io, ioc, security

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

    attr = io.TCPIOAttr()

    attr.set_authentication_mode(ioc.GLOBUS_IO_SECURE_AUTHENTICATION_MODE_GSSAPI)
    attr.set_channel_mode(ioc.GLOBUS_IO_SECURE_CHANNEL_MODE_GSI_WRAP)
    attr.set_delegation_mode(ioc.GLOBUS_IO_SECURE_DELEGATION_MODE_NONE)
    
    attr.set_restrict_port(0)
    attr.set_reuseaddr(1)
    attr.set_nodelay(1)

    return attr

def CreateTCPAttrDefaultSSL():
    """
    Create a TCP attr with common defaults for SSL compatibility.
    This does not set authorization or authentication modes.

    """

    attr = io.TCPIOAttr()

    attr.set_authentication_mode(ioc.GLOBUS_IO_SECURE_AUTHENTICATION_MODE_GSSAPI)
    attr.set_channel_mode(ioc.GLOBUS_IO_SECURE_CHANNEL_MODE_SSL_WRAP)
    attr.set_delegation_mode(ioc.GLOBUS_IO_SECURE_DELEGATION_MODE_FULL_PROXY)
    
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
    authdata = io.AuthData()

    authmode = ioc.GLOBUS_IO_SECURE_AUTHORIZATION_MODE_SELF

    attr.set_authorization_mode(authmode, authdata)

    return attr
    

def CreateTCPAttrCallbackAuth(auth_cb):
    """
    Create a TCP attr to invoke auth_cb for authorization decisions.

    http://www-unix.globus.org/api/c-globus-2.0-beta1/globus_io/html/group__security.html#a7


    """

    attr = CreateTCPAttrDefault()

    authdata = io.AuthData()

    authdata.set_callback(auth_cb, None)
    authmode = ioc.GLOBUS_IO_SECURE_AUTHORIZATION_MODE_CALLBACK

    attr.set_authorization_mode(authmode, authdata)

    return attr

def CreateTCPAttrCallbackAuthSSL(auth_cb):
    """
    Create a TCP attr to invoke auth_cb for authorization decisions.

    http://www-unix.globus.org/api/c-globus-2.0-beta1/globus_io/html/group__security.html#a7


    """

    attr = CreateTCPAttrDefaultSSL()

    authdata = io.AuthData()

    authdata.set_callback(auth_cb, None)
    authmode = ioc.GLOBUS_IO_SECURE_AUTHORIZATION_MODE_CALLBACK

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
    
#
# Create get_certificate_locations from either old AG pyGlobus build
# or from the new 2.4 pyGlobus.
#

#
# First the 2.0/2.2 pyGlobus which has a sslutilsc module.
#

try:
    from pyGlobus import sslutilsc
    get_certificate_locations = sslutilsc.get_certificate_locations
except:
    # This is old old old pyGlobus modified by ANL
    pass

#
# Alternatively, the 2.4 version. We need to emulate the
# behavior of the get_certificate_locations call.
#

try:
    from pyGlobus.security import get_cert_dir, get_proxy_filename
    from pyGlobus.security import get_user_cert_filename

    def get_certificate_locations():
        """
        returns a dictionary of the form:
        foo['cert_dir'] = dir
        foo['user_proxy'] = file
        foo['user_cert'] = file
        foo['user_key'] = file
        """
        retDict = dict()

        try:
            retDict['cert_dir'] = get_cert_dir()
        except:
            # handle error
            pass

        try:
            retDict['user_proxy'] = get_proxy_filename()
        except:
            # handle error
            pass

        try:
            user_ck_tuple = get_user_cert_filename()
            if user_ck_tuple[0] == 0:
                retDict['user_cert'] = user_ck_tuple[1][0]
                retDict['user_key'] = user_ck_tuple[1][1]
            else:
                # handle error
                pass
        except:
            pass

        return retDict

except:
    pass

def GetCNFromX509Subject(subject):
    """
    Return a short form of the CN in an X509Subject object.

    @param subject:  Name to extract CN from
    @type subject: X509Subject
    """
    
    cn = []
    for what, val in subject.get_name_components():
        if what == "CN":
           cn.append(val)
    return ", ".join(cn)

