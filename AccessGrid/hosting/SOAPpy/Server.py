#-----------------------------------------------------------------------------
# Name:        Server.py
# Purpose:     
#
# Author:      Ivan R. Judson, Robert D. Olson
#
# Created:     2003/29/01
# RCS-ID:      $Id: Server.py,v 1.4 2004-02-27 22:38:21 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Server.py,v 1.4 2004-02-27 22:38:21 judson Exp $"
__docformat__ = "restructuredtext en"

from SOAPpy.GSIServer import ThreadingGSISOAPServer, GSIConfig
from SOAPpy.Server import ThreadingSOAPServer, GetSOAPContext
from SOAPpy.Config import SOAPConfig

from threading import Thread, Event

class Server:
    def __init__(self, addr, server):
        self._server = server
        self._running = Event()
        self._serving = dict()
        
    def IsRunning(self):
        """
        This is simply an accessor that returns the value of the running flag.
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
        if self._running.isSet():
           self._running.clear()
           self._server.server_close()

    def GetPort(self):
        """Return the port on which this server is listening. """
        return self._server.port

    def GetURLBase(self):
        """Return the base URL that represents this server. """
        return "https://%s:%s" % self._server.server_address

    # Convenient encapsulations
    def RegisterObject(self, object, namespace = '', path = ''):
        # by convention path is always /<somethin>
        uri = "%s%s" % (self.GetURLBase(), path)
        if self._serving.has_key(uri):
            print "Warning! Registering two objects at the same endpoint!"
            print "Endpoint: ", uri
            print "Object 1: ", self._serving[uri]
            print "Object 2: ", object

        self._serving[uri] = object

        self._server.registerObject(object, namespace=namespace, path = path)

    def UnregisterObject(self, object):
        for u,o in self._serving.items():
            if object == o:
                del self._serving[u]
        self._server.unregisterObject(object)

    # Don't forget we expose interfaces, so
    # interfaces.impl == passed in object
    def FindObject(self, object):
        for u,o in self._serving.items():
            if object == o.impl:
                return u,o
        return None,None
            
    def GetURLForObject(self, object):
        for u,o in self._serving.items():
            if object == o.impl:
                return u
        return None

    def FindObjectForURL(self, url):
        for u,o in self._serving.items():
            if u == url:
                return o
        return None

    def FindObjectForPath(self, path):
        match_url = "%s%s" % (self.GetURLBase(), path)
        return self.FindObjectForURL(match_url)
        
class SecureServer(Server):
    def __init__(self, addr, debug = 0):
        # This is where you set things for debugging
        self.config = GSIConfig()
        self.config.debug = debug
        self.config.simplify_objects = 1
        if debug:
            self.config.dumpFaultInfo = 1

        s = ThreadingGSISOAPServer(addr, config = self.config)
        Server.__init__(self, addr, s)
        
class InsecureServer(Server):
    def __init__(self, addr, debug = 0):
        # This is where you set things for debugging
        self.config = SOAPConfig()
        self.config.debug = debug
        if debug:
            self.config.dumpFaultInfo = 1

        s = ThreadingSOAPServer(addr, config = self.config)
        Server.__init__(self, addr, s)
        
