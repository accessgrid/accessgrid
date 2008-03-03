#-----------------------------------------------------------------------------
# Name:        UrllibTransport.py
# Purpose:     Transport class for doing xmlrpc through a proxy server
# Created:     2006/03/08
# RCS-ID:      $Id: UrllibTransport.py,v 1.5 2007/05/04 20:27:19 eolson Exp $
# Copyright:   (c) 2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------


import httplib
import xmlrpclib
import socket
import base64



class TimeoutHTTPConnection(httplib.HTTPConnection):
    def __init__(self, host, port=None, strict=None, timeout=0):
        httplib.HTTPConnection.__init__(self,host,port,strict)
        self.timeout = timeout
    def connect(self):
        """Connect to the host and port specified in __init__."""
        msg = "getaddrinfo returns an empty list"
        for res in socket.getaddrinfo(self.host, self.port, 0,
                                      socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
                if self.timeout:
                    self.sock.settimeout(self.timeout)
                if self.debuglevel > 0:
                    print "connect: (%s, %s)" % (self.host, self.port)
                self.sock.connect(sa)
            except socket.error, msg:
                if self.debuglevel > 0:
                    print 'connect fail:', (self.host, self.port)
                if self.sock:
                    self.sock.close()
                self.sock = None
                continue
            break
        if not self.sock:
            raise socket.error, msg
            
class TimeoutHTTP(httplib.HTTP):
    def __init__(self, host='', port=None, strict=None, timeout=0):
    
        # some joker passed 0 explicitly, meaning default port
        if port == 0:
            port = None

        # Note that we may pass an empty string as the host; this will throw
        # an error when we attempt to connect. Presumably, the client code
        # will call connect before then, with a proper host.
        self._setup(TimeoutHTTPConnection(host, port, strict, timeout=timeout))

class TimeoutTransport(xmlrpclib.Transport):
    def __init__(self,timeout):
        if hasattr(xmlrpclib.Transport,'__init__'):
            xmlrpclib.Transport.__init__(self)
        self.timeout = timeout
        self.httpconn = None
    def make_connection(self, host):
        host, extra_headers, x509 = self.get_host_info(host)
        if self.httpconn:
            self.freeconn()
        self.httpconn = TimeoutHTTP(host,timeout=self.timeout)
        return self.httpconn
            
    def freeconn(self):
        if self.httpconn:
            self.httpconn.close()
            self.httpconn = None
            
    def __del__(self):
        self.freeconn()
#
# The following code is adapted from:
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/523016
class UrllibTransport(xmlrpclib.Transport):
    '''Handles an HTTP transaction to an XML-RPC server via urllib
    (urllib includes proxy-server support)
    jjk  07/02/99'''

    def __init__(self, proxy, timeout=0):
        self.proxy = proxy
        self.timeout = timeout
        self.httpconn = None

    def set_proxy(self, proxy):
        self.proxy = proxy

    def request(self, host, handler, request_body, verbose = None):
        '''issue XML-RPC request
        cflewis 08/03/07'''
        import urllib
        from urllib import unquote, splittype, splithost

        type, r_type = splittype(self.proxy)
        phost, XXX = splithost(r_type)

        puser_pass = None
        if '@' in phost:
            user_pass, phost = phost.split('@', 1)
            if ':' in user_pass:
                user, password = user_pass.split(':', 1)
                puser_pass = base64.encodestring('%s:%s' % (unquote(user),
                                                unquote(password))).strip()

        urlopener = urllib.FancyURLopener({'http':'http://%s'%phost})

        if not puser_pass:
            urlopener.addheaders = [('User-agent', self.user_agent)]
        else:
            urlopener.addheaders = [('User-agent', self.user_agent),
                                    ('Proxy-authorization', 'Basic ' + puser_pass) ]

        host = unquote(host)
        f = urlopener.open("http://%s%s"%(host,handler), request_body)

        self.verbose = verbose 
        return self.parse_response(f)


    def make_connection(self, host):
        host, extra_headers, x509 = self.get_host_info(host)
        self.httpconn = TimeoutHTTP(host,timeout=self.timeout)
        return self.httpconn
        
    def freeconn(self):
        if self.httpconn:
            self.httpconn.close()
            self.httpconn = None
            
    def __del__(self):
        self.freeconn()
        
        
