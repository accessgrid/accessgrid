#-----------------------------------------------------------------------------
# Name:        EventService.py
# Purpose:     This service provides events among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: EventService.py,v 1.20 2003-05-16 04:17:26 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket
import sys
import pickle
from threading import Thread
import logging
import struct

from SocketServer import ThreadingMixIn, StreamRequestHandler
from pyGlobus.io import GSITCPSocketServer, GSITCPSocketException
from pyGlobus.io import IOBaseException

# This really should be defined in pyGlobus.io
class ThreadingGSITCPSocketServer(ThreadingMixIn, GSITCPSocketServer): pass

from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.Events import ConnectEvent, DisconnectEvent

log = logging.getLogger("AG.VenueServer")
log.setLevel(logging.INFO)

class ConnectionHandler(StreamRequestHandler):
    """
    The ConnectionHandler is the object than handles a single event
    connection. The ConnectionHandler gets events from the client then
    passes them to registered callback functions based on event.eventType.
    """
    def stop(self):
        self.running = 0
         
    def handle(self):
        # What channel is this connection for
        self.channel = None

        # Get a handle to the services logger
        log = self.server.log

        log.debug("EventConnection: New Handler!")
        
        # loop getting data and handing it to the server
        self.running = 1
        while(self.running):
            event = None
            try:
                # This is hardwired to 4 byte size for now
                data = self.rfile.read(4)
                log.debug("EventConnection: DataSizevenu: %d", len(data))
            except IOBaseException:
                data = None
                self.running = 0
                log.debug("EventConnection: Connection lost.")
                # this is an icky hack :-\
                event = DisconnectEvent(self.channel, self.privateId)

            if data != None and len(data) == 4:
                sizeTuple = struct.unpack('i', data)
                size = sizeTuple[0]
                log.debug("EventConnection: Read %d", size)
            else:
                size = 0
                self.running = 0
                log.debug("EventConnection: Connection lost.")
                # this is an icky hack :-\
                event = DisconnectEvent(self.channel, self.privateId)
                
            if size != 0:
                # Get the pickled event data
                try:
                    pdata = self.rfile.read(size)
                    log.debug("EventConnection: Read data.")
                except:
                    log.debug("EventConnection: Read data failed.")
                    self.running = 0
                    # this is an icky hack :-\
                    event = DisconnectEvent(self.channel, self.privateId)
            
            # Unpickle the event data
            if event == None:
                try:
                    event = pickle.loads(pdata)
                except EOFError, e:
                    log.debug("EventService: unpickle got EOF.")
                    self.running = 0
                    continue
            
            # Pass this event to the callback registered for this
            # event.eventType
            log.debug("EventConnection: Received event %s", event)
            
            if event.eventType == ConnectEvent.CONNECT:
                log.debug("EventConnection: Adding client %s to venue %s",
                          event.data, event.venue)
                self.channel = event.venue
                self.privateId = event.data
                self.server.connections[event.venue].append(self)
            
            # Disconnect Event
            if event.eventType == DisconnectEvent.DISCONNECT:
                log.debug("EventConnection: Removing client connection to %s",
                          event.venue)
                if self.channel != None:
                    self.server.connections[self.channel].remove(self)
                    self.running = 0
            
            # Pass this event to the callback registered for this
            # event.eventType
            if self.server.callbacks.has_key((event.venue,
                                              event.eventType)):
                cb = self.server.callbacks[(event.venue, event.eventType)]
                if cb != None:
                    log.debug("invoke callback %s", str(cb))
                    cb(event.data)
            elif self.server.callbacks.has_key((event.venue,)):
                # Default handler for this channel.
                cb = self.server.callbacks[(event.venue,)]
                if cb != None:
                    log.debug("invoke channel callback %s", cb)
                    cb(event.eventType, event.data)
                else:
                    log.info("EventService: No callback for %s, %s events.",
                             event.venue, event.eventType)

class EventService(ThreadingGSITCPSocketServer, Thread):
    """
    The EventService provides a secure event layer. This might be more 
    scalable as a secure RTP or other UDP solution, but for now we use TCP.
    In the TCP case the EventService is the Server, GSI is our secure version.
    """
    def __init__(self, server_address, RequestHandlerClass=ConnectionHandler):
        Thread.__init__(self)
        self.log = logging.getLogger("AG.EventService")
        self.log.debug("Event Service Started")
        
        self.location = server_address
        self.callbacks = {}
        self.connections = {}
        ThreadingGSITCPSocketServer.__init__(self, server_address, 
                                                RequestHandlerClass)
    def run(self):
        """
        run is defined to override the Thread.run method so Thread.start works.
        """
        self.log.debug("Event Service: Running")
        
        self.running = 1
        while(self.running):
            try:
                self.handle_request()
            except GSITCPSocketException:
                log.info("EventService: GSITCPSocket, interrupted I/O operation, most likely shutting down. ")
                pass

    def Stop(self):
        """
        Stop stops this thread, thus shutting down the service.
        """
        self.log.debug("EventService: Stopping")
        
        for v in self.connections.keys():
            for c in self.connections[v]:
                c.stop()
            
        self.running = 0
        self.server_close()
        
    def DefaultCallback(self, event):
        self.log.info("EventService: Got callback for %s event!",
                      event.eventType)
        
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
        self.log.debug("EventService: Sending Event %s", data)

        # This should be more generic
        pdata = pickle.dumps(data)
        size = struct.pack("i", len(pdata))
        if self.connections.has_key(channel):
            for c in self.connections[channel]:
                try:
                    c.wfile.write(size)
                    c.wfile.write(pdata)
                except:
                    self.log.exception("EventService.Distribute write error!")
                    self.connections[channel].remove(c)
            
    def GetLocation(self):
        """
        GetLocation returns the (host,port) for this service.
        """
        self.log.debug("EventService: GetLocation")
        
        return self.location

    def AddChannel(self, channelId):
        """
        This adds a new channel to the Event Service.
        """
        self.log.debug("EventService: AddChannel %s", channelId)
        
        self.connections[channelId] = []

    def RemoveChannel(self, channelId):
        """
        This removes a channel from the Event Service.
        """
        self.log.debug("EventService: Remove Channel %s", channelId)

        del self.connections[channelId]

if __name__ == "__main__":
  import string

  log.addHandler(logging.StreamHandler())
  log.setLevel(logging.DEBUG)
    
  port = 6500
  print "Creating new EventService at %d." % port
  eventService = EventService(('', port))
  eventService.AddChannel('Test')
  eventService.start()
