#-----------------------------------------------------------------------------
# Name:        EventService.py
# Purpose:     This service provides events among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: EventService.py,v 1.10 2003-03-24 20:26:12 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket
import sys
import pickle
from threading import Thread
import logging

from SocketServer import ThreadingMixIn, StreamRequestHandler
from pyGlobus.io import GSITCPSocketServer

# This really should be defined in pyGlobus.io
class ThreadingGSITCPSocketServer(ThreadingMixIn, GSITCPSocketServer): pass

from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.Events import ConnectEvent, DisconnectEvent

log = logging.getLogger("AG.VenueServer")

class ConnectionHandler(StreamRequestHandler):
    """
    The ConnectionHandler is the object than handles a single event
    connection. The ConnectionHandler gets events from the client then
    passes them to registered callback functions based on event.eventType.
    """
    def stop(self):
        self.running = 0
         
    def handle(self):
        log.debug("In request Handler!")
        
        # loop getting data and handing it to the server
        self.running = 1
        while(self.running == 1):
            try:
                # Get the size of the pickled event data
                size = int(self.rfile.readline())

                # Get the pickled event data
                pdata = self.rfile.read(size, size)
                
                # Unpickle the event data
                event = pickle.loads(pdata)
                
                # Pass this event to the callback registered for this
                # event.eventType
                log.debug("Received event %s %s", event.eventType, event.venue)

                if event.eventType == ConnectEvent.CONNECT:
                    log.debug("EventService: Adding connection to venue %s",
                              event.venue)
                    self.server.connections[event.venue].append(self)
                    continue
                
                # Disconnect Event
                if event.eventType == DisconnectEvent.DISCONNECT:
                    log.debug("EventService: Removing client connection to %s",
                              event.venue)
                    self.server.connections[event.venue].remove(self)
                    continue
                
                # Pass this event to the callback registered for this
                # event.eventType
                if self.server.callbacks.has_key((event.venue,
                                                    event.eventType)):
                    cb = self.server.callbacks[(event.venue, event.eventType)]
                    if cb != None:
                        log.debug("invoke callback %s", str(cb))
                        cb(event.data)
                elif self.server.callbacks.has_key((event.venue,)):
                    #
                    # Default handler for this channel.
                    cb = self.server.callbacks[(event.venue,)]
                    if cb != None:
                        log.debug("invoke channel callback %s", cb)
                        cb(event.eventType, event.data)
                else:
                    log.info("EventService: No callback for %s, %s events.",
                             event.venue, event.eventType)
            except:
                log.debug("ConnectionHandler.handle Client disconnected!")
                self.running = 0
                # Find the connection and remove it
                for v in self.server.connections.keys():
                    if self in self.server.connections[v]:
                        self.server.connections[v].remove(self)
                    
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
        self.connections = {}
        ThreadingGSITCPSocketServer.__init__(self, server_address, 
                                                RequestHandlerClass)


#     def ConnectCallback(self, cv, handle, result):
#         print "In connect callback"
#         return

#     def WriteCallback(self, cv, handle, result, buf, length):
#         print "In write callback"
#         return

#     def ReadCallBack(self, cv, handle, result, buf, length):
#         return

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

        for v in self.connections.keys():
            for c in self.connections[v]:
                c.stop()
            
        self.running = 0
        
    def DefaultCallback(self, event):
        log.info("EventService: Got callback for %s event!", event.eventType)
        
    def RegisterCallback(self, channel, eventType, callback):
        # Callbacks just take the event data as the argument
        self.callbacks[(channel, eventType)] = callback
        
    def RegisterChannelCallback(self, channel, callback):
        """
        Register a callback for all events on this channel.
        """
        # Callbacks just take the event data as the argument
        self.callbacks[(channel,)] = callback
        
    def RegisterObject(self, channel, object):
        """
        RegisterObject is short hand for registering multiple callbacks on the
        same object. The object being registered has to define a table named
        callbacks that has event types as keys, and self.methods as values.
        Then these are automatically registered.
        """
        for c in object.callbacks.keys():
            self.RegisterCallback(c, channel, object.callbacks[c])
            
    def Distribute(self, channel, data):
        """
        Distribute sends the data to all connections.
        """
        log.debug("EventService: Sending Event %s", data.eventType)

        # This should be more generic
        pdata = pickle.dumps(data)
        lenStr = "%s\n" % len(pdata)
        if self.connections.has_key(channel):
            for c in self.connections[channel]:
                try:
                    log.debug("write length '%s'", lenStr)
                    c.wfile.write(lenStr)
                    log.debug("write data")
                    c.wfile.write(pdata)           
                except:
                    log.exception("EventService.Distribute Client disconnected!")
            
    def GetLocation(self):
        """
        GetLocation returns the (host,port) for this service.
        """
        return self.location

    def AddChannel(self, channelId):
        self.connections[channelId] = []

    def RemoveChannel(self, channelId):
        del self.connections[channelId]

if __name__ == "__main__":
  import string

  log.addHandler(logging.StreamHandler())
  log.setLevel(logging.DEBUG)
    
  host = string.lower(socket.getfqdn())
  port = 6500
  print "Creating new EventService at %s %d." % (host, port)
  eventService = EventService((host, port))
  eventService.AddChannel('Test')
  eventService.start()
