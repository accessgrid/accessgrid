#-----------------------------------------------------------------------------
# Name:        Server.py
# Purpose:     
#
# Author:      Ivan R. Judson, Robert D. Olson
#
# Created:     2003/29/01
# RCS-ID:      $Id: Server.py,v 1.8 2004-03-05 21:45:00 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
SOAPpy server wrappers

This module provides helper classes for servers using the SOAPpy server.
"""
__revision__ = "$Id: Server.py,v 1.8 2004-03-05 21:45:00 judson Exp $"

# External imports
from threading import Thread, Event

from SOAPpy.GSIServer import ThreadingGSISOAPServer, GSIConfig
from SOAPpy.Server import ThreadingSOAPServer, GetSOAPContext
from SOAPpy.Config import SOAPConfig

class Server:
    """
    The server base class provides all the functionality required for
    a SOAP server based upon the SOAPpy module.
    """
    def __init__(self, addr, server):
        """
        @param addr: the address for the server to listen on
        @param server: the server object to use
        @type addr: (host, port) tuple
        @type server: one of ThreadingGSISOAPServer or ThreadingSOAPServer
        """
        self.addr = addr
        self._server = server
        self._running = Event()
        self._serving = dict()
        
    def IsRunning(self):
        """
        This is simply an accessor that returns the value of the running flag.
        @return: a flag that indicates if the server is running.
        """
        return self._running.isSet()
    
    def Run(self):
        """
        Run the server.

        This method runs the server (that is, causes it to listen for
        and process incoming messages) in the current thread. It does
        not return.
        """
        self._running.set()

        while(self._running.isSet()):
            try:
                self._server.handle_request()
            except:
                # This exception is silent, THIS IS BAD
                pass

        # Don't call server_close() here because handle_request() is blocking.
        #   We break out of handle_request() when server_close() is called from 
        #   Stop().  If we start doing non-blocking calls in handle_request(), 
        #   we can call server_close() here instead of in Stop().
        #   
        # self._server.server_close()
        
    def RunInThread(self):
        """
        Start the server in a new thread.

        This method causes the server to begin listening for and
        processing incoming messages in a new message-handling thread. It
        returns immediately.
        """

        server_thread = Thread(target = self.Run)
        server_thread.start()
        self._running.wait()
        
    def Stop(self):
        """
        Stops the server if it is running.
        """
        if self._running.isSet():
           self._running.clear()
           self._server.server_close()

    def GetPort(self):
        """
        Return the port on which this server is listening.

        @return: the port number
        """
        return self._server.port

    def GetURLBase(self):
        """
        Return the base URL that represents this server.

        @return: the url of the server
        """
        return "https://%s:%s" % self._server.server_address

    # Convenient encapsulations
    def RegisterObject(self, obj, namespace = '', path = ''):
        """
        This method is used to register an object with the server.

        We wrap this call to provide handy lookup access so we can find
        objects when we need them.
        """
        # by convention path is always /<somethin>
        uri = "%s%s" % (self.GetURLBase(), path)
        if self._serving.has_key(uri):
            print "Warning! Registering two objects at the same endpoint!"
            print "Endpoint: ", uri
            print "Object 1: ", self._serving[uri]
            print "Object 2: ", obj

        self._serving[uri] = obj
        self._server.registerObject(obj, namespace=namespace, path = path)

    def UnregisterObject(self, obj):
        """
        This method removes a object from the server, making it unavailable.

        Again, a wrapper to provide custom bookkeeping, then use
        SOAPpy directly underneath.
        """
        for u,o in self._serving.items():
            if obj == o:
                del self._serving[u]
        self._server.unregisterObject(obj)

    # Don't forget we expose interfaces, so
    # interfaces.impl == passed in object
    def FindObject(self, obj):
        """
        A lookup method to find the interface the SOAP Server is
        exposing for a given implementation object.

        @param obj: an object to find the interface for
        @type obj: a python object
        @return: a tuple (url, interface object) or (None, None)
        """
        for u,o in self._serving.items():
            if obj == o.impl:
                return u,o
        return None,None
            
    def GetURLForObject(self, obj):
        """
        Retrieve the url that represents the web service endpoint for
        the specified object.

        @param obj: the object to find the URL of
        @type obj: a python object

        @return: the url or None
        """
        for u,o in self._serving.items():
            if obj == o.impl:
                return u
        return None

    def FindObjectForURL(self, url):
        """
        Return the interface object located at the endpoint specified
        by the URL.

        @param url: the url of the object to look for
        @type url: string

        @return: the interface object or None
        """
        for u,o in self._serving.items():
            if u == url:
                return o
        return None

    def FindObjectForPath(self, path):
        """
        Return the interface object located at the path specified. The
        path is a sub-part of the URL.

        @param path: the path to the object
        @type path: string
        @return: the itnerface object or None
        """
        match_url = "%s%s" % (self.GetURLBase(), path)
        return self.FindObjectForURL(match_url)

    def FindPathForObject(self, obj):
        """
        Retrieve the path that represents the web service endpoint for
        the specified object.

        @param obj: the object to find the URL of
        @type obj: a python object

        @return: the path or None
        """
        path = None
        URL = self.FindURLForObject(obj)
        if URL != None:
            if URL[0:5] == 'httpg':
                path = urlparse.urlparse(URL[6:])[2]
            else:
                path = urlparse.urlparse(URL)[2]
        return path
        
class SecureServer(Server):
    """
    The SecureServer extends the SOAPpy server base class to use
    GSIHTTP for connections.
    """
    def __init__(self, addr, debug = 0):
        """
        @param addr: the address the server should listen on
        @param debug: a debug flag to pass down internally

        @type addr: (host, port) tuple
        @type debug: 0, or 1
        """
        # This is where you set things for debugging
        self.config = GSIConfig()
        self.config.debug = debug
        if debug:
            self.config.dumpFaultInfo = 1

        s = ThreadingGSISOAPServer(addr, config = self.config)
        Server.__init__(self, addr, s)
        
class InsecureServer(Server):
    """
    The InsecureServer class derives from the SOAPpy server, but doesn't
    require any authorization information. It uses stock HTTP.
    """
    def __init__(self, addr, debug = 0):
        """
        @param addr: the address the server should listen on
        @param debug: a debug flag to pass down internally

        @type addr: (host, port) tuple
        @type debug: 0, or 1
        """
        # This is where you set things for debugging
        self.config = SOAPConfig()
        self.config.debug = debug
        if debug:
            self.config.dumpFaultInfo = 1

        s = ThreadingSOAPServer(addr, config = self.config)
        Server.__init__(self, addr, s)
        
