"""GSI/XMLRPC client library

This module provides a helper class Client that wraps
the creation of the XMLRPC server proxy.
"""

def myCallback(server, g_handle, remote_user, context):
    print "myCallback. Remote user is %s" % remote_user
    return 1

import xmlrpclib
import urllib

class AuthCallbackException(Exception):
    pass


class Handle:
    def __init__(self, url, authCallback = None, authCallbackArg = None):

        self.url = url
        self.proxy = None
        self.authCallback = authCallback
        self.authCallbackArg = authCallbackArg

    def get_url(self):
        return self.url

    def get_proxy(self):
        if self.proxy is None:
            #
            # See if we're https or http - route
            # https to the GSI one for now.
            #

            type, uri = urllib.splittype(self.url)

            if type == "https":
                self.proxy = create_proxy(self.url,
                                          self.authCallback,
                                          self.authCallbackArg)
            else:
                self.proxy = xmlrpclib.ServerProxy(self.url)

        return self.proxy

    def __repr__(self):
        return self.url

def create_proxy(url, authCallback = None, authCallbackArg = None):
    from pyGlobus import io, ioc
    from GSITransport import GSITransport

#    DELEGATION_MODE = ioc.GLOBUS_IO_SECURE_DELEGATION_MODE_FULL_PROXY
    DELEGATION_MODE = ioc.GLOBUS_IO_SECURE_DELEGATION_MODE_NONE
    CHANNEL_MODE = ioc.GLOBUS_IO_SECURE_CHANNEL_MODE_GSI_WRAP

    io_attr = io.TCPIOAttr()
    io_attr.set_authentication_mode(ioc.GLOBUS_IO_SECURE_AUTHENTICATION_MODE_GSSAPI)
    authdata = io.AuthData()

    if authCallback is not None:
        if not callable(authCallback):
            raise AuthCallbackException()
        
        print "callback is ", authCallback
        authdata.set_callback(authCallback, None)
        
        io_attr.set_authorization_mode(ioc.GLOBUS_IO_SECURE_AUTHORIZATION_MODE_CALLBACK, authdata)
    else:
        io_attr.set_authorization_mode(ioc.GLOBUS_IO_SECURE_AUTHORIZATION_MODE_SELF, authdata)
    

    io_attr.set_delegation_mode(DELEGATION_MODE)
    io_attr.set_nodelay(0)
    io_attr.set_channel_mode(CHANNEL_MODE)

    print "creating proxy on ", url
    
    proxy = xmlrpclib.ServerProxy(url, GSITransport(io_attr))

    return proxy
            
