#-----------------------------------------------------------------------------
# Name:        Client.py
# Purpose:     
#
# Author:      Robert D. Olson
#
# Created:     2003/08/02
# RCS-ID:      $Id: Client.py,v 1.8 2003-02-21 16:15:24 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""GSI/SOAP client library

This module provides a helper class Client that wraps
the creation of the SOAP server proxy.
"""

from AGGSISOAP import SOAPProxy, Config, debugHeader, debugFooter, __version__
import AGGSISOAP
import urllib
import string

FaultType = AGGSISOAP.faultType

class AuthCallbackException(Exception):
    pass

class Handle:
    def __init__(self, url, namespace = None, authCallback = None):

        self.url = url
        self.proxy = None
        self.namespace = namespace
        self.authCallback = authCallback

    def GetURL(self):
        return self.url

    def GetProxy(self):

        if self.proxy is None:
            self.proxy = self.CreateProxy()
        return self.proxy

    def CreateProxy(self):
        #
        # See if we're https or http - route
        # https to the GSI one for now.
        #

        type, uri = urllib.splittype(self.url)

        if type == "https":
            proxy = create_proxy(self.url,
                                      self.namespace,
                                      self.authCallback)
        else:
            proxy = SOAPProxy(self.url, self.namespace)

        return proxy

    def IsValid(self):
        """
        Determine if this handle points to a valid web service.

        We do this by simply attempting to invoke the _IsValid method on
        a new proxy.
        """

        proxy = self.CreateProxy()
        try:
            ret = proxy._IsValid()
            return ret
        except Exception, e:
            # print "Attempt at calling isvalid fails: ", e
            return 0

    def Implements(self, method):
        """
        Determine if this handle points to a valid web service and if that
        web service implements the method named "method".
        """

        proxy = self.CreateProxy()
        try:
            ret = proxy._Implements(str(method))
            return ret
        except Exception, e:
            # print "Attempt at calling Implements fails: ", e
            return 0
        

    def __repr__(self):
        return self.url

    #
    # Mappings to other naming style
    #

    get_url = GetURL
    get_proxy = GetProxy

def create_proxy(url, namespace, authCallback = None):
    
    from AGGSISOAP import SOAPConfig
    import Utilities

    if authCallback is None:
        io_attr = Utilities.CreateTCPAttrAlwaysAuth()
    else:
        io_attr = Utilities.CreateTCPAttrCallbackAuth(authCallback)


    config = SOAPConfig(tcpAttr = io_attr, debug = 0)

    # print "creating proxy on ", url, " ioattr is ", io_attr

    proxy = SOAPProxy(url, namespace,
                      transport = HTTPTransport,
                      config = config)

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
            r = GSIHTTP(real_addr, tcpAttr = config.tcpAttr)
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
            data = r.getfile().read(contentLen, contentLen)

            s = 'Incoming SOAP len=%s contentLen=%s' % (len(data), contentLen)
            debugHeader(s)
            print data,
            if data[-1] != '\n':
                print
            debugFooter(s)

        if code not in (200, 500):
            raise HTTPError(code, msg)

        if not config.dumpSOAPIn:
            data = r.getfile().read(contentLen, contentLen)

        # return response payload
        return data
