#-----------------------------------------------------------------------------
# Name:        UrllibTransport.py
# Purpose:     Transport class for doing xmlrpc through a proxy server
# Created:     2006/03/08
# RCS-ID:      $Id: UrllibTransport.py,v 1.4 2007-05-03 21:44:20 turam Exp $
# Copyright:   (c) 2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------


import httplib
import xmlrpclib
import socket



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
            xmlrpclib.Transport.__init__()
        self.timeout = timeout
    def make_connection(self, host):
        host, extra_headers, x509 = self.get_host_info(host)
        httpconn = TimeoutHTTP(host,timeout=self.timeout)
        return httpconn
    

#
# The following code is adapted from:
# http://starship.python.net/crew/jjkunce/python/xmlrpc_urllib_transport.py
#
class UrllibTransport(xmlrpclib.Transport):
    '''Handles an HTTP transaction to an XML-RPC server via urllib
    (urllib includes proxy-server support)
    jjk  07/02/99'''

    def __init__(self, proxy, timeout=0):
        self.proxy = proxy
        self.timeout = timeout

    def request(self, host, handler, request_body, verbose = None):
        '''issue XML-RPC request
        jjk  07/02/99'''
        import urllib
        self.verbose = verbose
        urlopener = urllib.URLopener(proxies = {"http": self.proxy})
        urlopener.addheaders = [('User-agent', self.user_agent)]
        # probably should use appropriate 'join' methods instead of 'http://'+host+handler
        f = urlopener.open('http://'+host+handler, request_body)
        return(self.parse_response(f))

    def make_connection(self, host):
        host, extra_headers, x509 = self.get_host_info(host)
        httpconn = TimeoutHTTP(host,timeout=self.timeout)
        return httpconn
    

