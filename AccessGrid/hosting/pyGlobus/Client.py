"""GSI/SOAP client library

This module provides a helper class Client that wraps
the creation of the SOAP server proxy.
"""

def myCallback(server, g_handle, remote_user, context):
    print "myCallback. Remote user is %s" % remote_user
    return 1

from AGGSISOAP import SOAPProxy, Config
import urllib
import string

class AuthCallbackException(Exception):
    pass

class Handle:
    def __init__(self, url, namespace = None,
                 authCallback = None, authCallbackArg = None):

        self.url = url
        self.proxy = None
        self.namespace = namespace
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
                                          self.namespace,
                                          self.authCallback,
                                          self.authCallbackArg)
            else:
                self.proxy = SOAPProxy(self.url, self.namespace)

        return self.proxy

    def __repr__(self):
        return self.url

def create_proxy(url, namespace,
                 authCallback = None, authCallbackArg = None):
    
    from pyGlobus import io, ioc
    from AGGSISOAP import Config

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

    proxy = SOAPProxy(url, namespace,
                      transport = HTTPTransport,
                      config = Config)

    return proxy
            
class HTTPTransport:
    # Need a Timeout someday?
    def call(self, addr, data, soapaction = '', encoding = None,
             http_proxy = None, config = Config,
             tcpAttr = None):

        import httplib
        from pyGlobus.io import GSIHTTP
        from AGGSISOAP import SOAPAddress, SOAPUserAgent
        
        if not isinstance(addr, SOAPAddress):
            addr = SOAPAddress(addr, config)

        # Build a request
        if http_proxy:
            real_addr = http_proxy
            real_path = addr.proto + "://" + addr.host + addr.path
        else:
            real_addr = addr.host
            real_path = addr.path
            
        if addr.proto == 'https':
            r = GSIHTTP(real_addr, tcpAttr = tcpAttr)
        else:
            r = httplib.HTTP(real_addr)

        r.putrequest("POST", real_path)

        r.putheader("Host", addr.host)
        r.putheader("User-agent", SOAPUserAgent())
        t = 'text/xml';
        if encoding != None:
            t += '; charset="%s"' % encoding
        r.putheader("Content-type", t)
        r.putheader("Content-length", str(len(data)))
        r.putheader("SOAPAction", '"%s"' % soapaction)

        if config.dumpHeadersOut:
            s = 'Outgoing HTTP headers'
            debugHeader(s)
            print "POST %s %s" % (real_path, r._http_vsn_str)
            print "Host:", addr.host
            print "User-agent: SOAP.py " + __version__ + " (actzero.com)"
            print "Content-type:", t
            print "Content-length:", len(data)
            print 'SOAPAction: "%s"' % soapaction
            debugFooter(s)

        r.endheaders()

        if config.dumpSOAPOut:
            s = 'Outgoing SOAP'
            debugHeader(s)
            print data,
            if data[-1] != '\n':
                print
            debugFooter(s)

        # send the payload
        r.send(data)

        # read response line
        code, msg, headers = r.getreply()
        l = string.split(headers.headers[-1], ":")
        contentLen = int(l[1].strip())
        if config.dumpHeadersIn:
            s = 'Incoming HTTP headers'
            debugHeader(s)
            if headers.headers:
                print "HTTP/1.? %d %s" % (code, msg)
                print "\n".join(map (lambda x: x.strip(), headers.headers))
            else:
                print "HTTP/0.9 %d %s" % (code, msg)
            debugFooter(s)

        if config.dumpSOAPIn:
            data = r.getfile().read(contentLen)

            s = 'Incoming SOAP'
            debugHeader(s)
            print data,
            if data[-1] != '\n':
                print
            debugFooter(s)

        if code not in (200, 500):
            raise HTTPError(code, msg)

        if not config.dumpSOAPIn:
            data = r.getfile().read(contentLen)

        # return response payload
        return data
