#-----------------------------------------------------------------------------
# Name:        EventService.py
# Purpose:     This service provides events among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: EventService.py,v 1.2 2003-02-05 21:36:46 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket
import sys
import pickle
from threading import Thread

from SocketServer import ThreadingMixIn, StreamRequestHandler
from pyGlobus.io import GSITCPSocketServer

# This really should be defined in pyGlobus.io
class ThreadingGSITCPSocketServer(ThreadingMixIn, GSITCPSocketServer): pass

from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.Events import HeartbeatEvent

class ConnectionHandler(StreamRequestHandler):
    """
    The ConnectionHandler is the object than handles a single event
    connection. The ConnectionHandler gets events from the client then
    passes them to registered callback functions based on event.eventType.
    """
    def stop(self):
        self.running = 0
         
    def handle(self):
        
        # register setup stuff
        self.server.connections.append(self)
        
        # loop getting data and handing it to the server
        self.running = 1
        while(self.running == 1):
            try:
                # Get the size of the pickled event data
                size = int(self.rfile.readline())
                # Get the pickled event data
                pdata = self.rfile.read(size)
                # Unpickle the event data
                event = pickle.loads(pdata)
                # Pass this event to the callback registered for this
                # event.eventType
                if self.server.callbacks.has_key(event.eventType):
                    self.server.callbacks[event.eventType](event.data)
                else:
                     print "Got event, but don't have a callback for %s events." % event.eventType   
            except:
                print "Client disconnected!"
                self.running = 0
                self.server.connections.remove(self)
                
class EventService(ThreadingGSITCPSocketServer, Thread):
    """
    The EventService provides a secure event layer. This might be more 
    scalable as a secure RTP or other UDP solution, but for now we use TCP.
    In the TCP case the EventService is the Server, GSI is our secure version.
    """
    def __init__(self, server_address, RequestHandlerClass=ConnectionHandler):
        Thread.__init__(self)
        self.location = server_address
        self.callbacks = {}
        self.connections = []
        ThreadingGSITCPSocketServer.__init__(self, server_address, 
                                                RequestHandlerClass)

    def run(self):
        """
        run is defined to override the Thread.run method so Thread.start works.
        """
        self.running = 1
        while(self.running):
            self.handle_request()

    def Stop(self):
        """
        Stop stops this thread, thus shutting down the service.
        """
        for c in self.connections:
            c.stop()
            
        self.running = 0
        
    def DefaultCallback(self, event):
        print "Got callback for %s event!" % event.eventType
        
    def RegisterCallback(self, eventType, callback):
        # Callbacks just take the event data as the argument
        self.callbacks[eventType] = callback
        
    def RegisterObject(self, object):
        """
        RegisterObject is short hand for registering multiple callbacks on the
        same object. The object being registered has to define a table named
        callbacks that has event types as keys, and self.methods as values.
        Then these are automatically registered.
        """
        for c in object.callbacks.keys():
            self.RegisterCallback(c, object.callbacks[c])
            
    def Distribute(self, data):
        """
        Distribute sends the data to all connections.
        """
        print "Sending Event %s" % data.eventType
        # This should be more generic
        pdata = pickle.dumps(data)
        for c in self.connections:
            c.wfile.write("%s\n" % len(pdata))
            c.wfile.write(pdata)
            
    def GetLocation(self):
        """
        GetLocation returns the (host,port) for this service.
        """
        return self.location
            
if __name__ == "__main__":
  import string
  host = string.lower(socket.getfqdn())
  port = 6500
  print "Creating new EventService at %s %d." % (host, port)
  eventChannel = EventService((host, port))
  eventChannel.start()
