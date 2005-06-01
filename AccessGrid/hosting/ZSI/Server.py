#-----------------------------------------------------------------------------
# Name:        Server.py
# Purpose:     
# Created:     2003/29/01
# RCS-ID:      $Id: Server.py,v 1.5 2005-06-01 13:28:29 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
ZSI server wrappers

This module provides helper classes for servers using the SOAPpy server.
"""
__revision__ = "$Id: Server.py,v 1.5 2005-06-01 13:28:29 turam Exp $"

# External imports
import urlparse
from threading import Thread, Event
from ZSI.ServiceContainer import ServiceContainer

from AccessGrid import Log
log = Log.GetLogger(Log.Hosting)
import select

def GetSOAPContext():
    return None

class _Server:
    """
    The server base class provides all the functionality required for
    a SOAP server based upon the SOAPpy module.
    """
    def __init__(self, addr, server):
        """
        @param addr: the address for the server to listen on
        @param server: the server object to use
        @type addr: (host, port) tuple
        @type server: one of ThreadingSOAPServer or ThreadingSOAPServer
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

        pause = 1 # second
        while(self._running.isSet()):
            try:
                r,w,e = select.select([self._server.socket], [], [], pause)
                if r:
                    self._server.handle_request()
            except:
                log.exception("Exception in SOAP server main loop")
                

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

        server_thread = Thread(target = self.Run, name="SOAP Server")
        server_thread.start()
        self._running.wait()
        
    def Stop(self):
        """
        Stops the server if it is running.
        """
        if self._running.isSet():
           self._running.clear()

        # Close the socket even if the thread wasn't started (isn't running).
        try:
            self._server.server_close()
        except:
            log.exception("server_close() failed")

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
        self._server.setNode(obj, path)
        return uri
    
    def UnregisterObject(self, obj, namespace='', path=''):
        """
        This method removes a object from the server, making it unavailable.

        Again, a wrapper to provide custom bookkeeping, then use
        ZSI directly underneath.
        """
        if len(path) > 0:
            # Remove specific object,path combination
            uri = "%s%s" % (self.GetURLBase(), path)
            if self._serving.has_key(uri):
                del self._serving[uri]
            
        else:
            # No path specified, remove object and any paths associated with it
            for u,o in self._serving.items():
                if obj == o:
                    del self._serving[u]
       
        if len(path)>0:
            try:
                self._server.removeNode(path)
                
            except KeyError:
                log.exception("Couldn't remove object from SOAP Server: %s", obj)
                raise 

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
            
    def FindURLForObject(self, obj):
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

import SocketServer
class ThreadingServiceContainer(SocketServer.ThreadingMixIn,ServiceContainer):
    def __init__(self, server_address, services=[]):
        ServiceContainer.__init__(self, server_address)
        
class SecureServer(_Server):
    """
    The SecureServer extends the ZSI server base class to use
    HTTPS for connections.
    """
    def __init__(self, addr, debug = 0):
        """
        @param addr: the address the server should listen on
        @param debug: a debug flag to pass down internally

        @type addr: (host, port) tuple
        @type debug: 0, or 1
        """
        # This is where you set things for debugging
        _Server.__init__(self, addr, ServiceContainer(addr))
        
    def GetURLBase(self):
        """
        Return the base URL that represents this server.

        @return: the url of the server
        """
        return "https://%s:%s" % self._server.server_address
    
class InsecureServer(_Server):
    """
    The InsecureServer class derives from the ZSI server, but doesn't
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
        #_Server.__init__(self, addr, ServiceContainer(addr))
        _Server.__init__(self, addr, ThreadingServiceContainer(addr))

    def GetURLBase(self):
        """
        Return the base URL that represents this server.

        @return: the url of the server
        """
        return "http://%s:%s" % self._server.server_address
        
