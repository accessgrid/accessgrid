#-----------------------------------------------------------------------------
# Name:        TextService.py
# Purpose:     This service provides events among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: TextService.py,v 1.15 2003-04-21 14:07:26 eolson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket
import sys
import pickle
from threading import Thread
import logging
import struct

from SocketServer import ThreadingMixIn, StreamRequestHandler
from pyGlobus.io import GSITCPSocketServer, GSIRequestHandler
from pyGlobus.io import GSITCPSocketException, IOBaseException

# This really should be defined in pyGlobus.io
class ThreadingGSITCPSocketServer(ThreadingMixIn, GSITCPSocketServer): pass

from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.Events import HeartbeatEvent, ConnectEvent, TextEvent
from AccessGrid.Events import DisconnectEvent
from AccessGrid.Events import TextPayload
from AccessGrid.hosting.AccessControl import CreateSubjectFromGSIContext

class ConnectionHandler(StreamRequestHandler):
    """
    The ConnectionHandler is the object than handles a single event
    connection. The ConnectionHandler gets events from the client then
    passes them to registered callback functions based on event.eventType.
    """
    def stop(self):
        self.running = 0
         
    def handle(self):
        # Grab a handle to the log
        log = self.server.log
        
        # loop getting data and handing it to the server
        self.running = 1
        while(self.running == 1):
            self.channel = None

            log = self.server.log
            
            log.debug("TextConnection: New Handler!")
            
            try:
                data = self.rfile.read(4)
                sizeTuple = struct.unpack("i", data)
                size = sizeTuple[0]
                log.debug("TextConnection: Read %d", size)
            except IOBaseException:
                size = 0
                self.disconnect()
                log.debug("TextConnection: Connection Lost.")
                continue
            
            # Get the pickled event data
            try:
                pdata = self.rfile.read(size)
                log.debug("TextConnection: Read data.")
            except:
                log.debug("TextConnection: Read data failed.")
                self.disconnect()
                continue
            
            # Unpickle the data
            event = pickle.loads(pdata)

            log.debug("TextConnection: Got Event %s", event)
            
            if event.eventType == ConnectEvent.CONNECT:
                # Connection Event
                self.channel = event.venue
                self.server.connections[self.channel].append(self)
                continue

            if event.eventType == DisconnectEvent.DISCONNECT:
                # Disconnection Event
                self.disconnect()
                continue
            
            # Tag the event with the sender, which is obtained
            # from the security layer to avoid spoofing
            ctx = self.connection.get_security_context()
            payload = event.data
            payload.sender = CreateSubjectFromGSIContext(ctx).GetName()
            
            # Parse the text structure
            # When this is advanced you can route things, for now
            # this is a simple text reflector
            # However we assign the from address in the server, so
            # there is some notion of security :-)
            self.server.Distribute(event)

    def disconnect(self):
        """
        This is the disconnect method that cleans up the connection.
        """
        # First turn off the connection loop
        self.running = 0

        # Clean up
#        self.server.connections[self.channel].remove(self)
        
class TextService(ThreadingGSITCPSocketServer, Thread):
    """
    The TextService provides a secure event layer. This might be more 
    scalable as a secure RTP or other UDP solution, but for now we use TCP.
    In the TCP case the TextService is the Server, GSI is our secure version.
    """
    def __init__(self, server_address, RequestHandlerClass=ConnectionHandler):
        Thread.__init__(self)
        self.log = logging.getLogger("AG.TextService")
        self.log.debug("Text Service Started")
        
        self.location = server_address
        self.connections = {}
        ThreadingGSITCPSocketServer.__init__(self, server_address, 
                                                RequestHandlerClass)

    def run(self):
        """
        run is defined to override the Thread.run method so Thread.start works.
        """
        self.log.debug("Text Service: Running")
        
        self.running = 1
        while(self.running):
            try:
                self.handle_request()
            except GSITCPSocketException:
                self.log.info("TextService: GSITCPSocket, interrupted I/O operation, most likely shutting down. ")

    def Stop(self):
        """
        Stop stops this thread, thus shutting down the service.
        """
        self.log.debug("TextService: Stopping")
        
        for v in self.connections.keys():
            for c in self.connections[v]:
                c.stop()
            
        self.running = 0
        self.server_close()
            
    def GetLocation(self):
        """
        GetLocation returns the (host,port) for this service.
        """
        self.log.debug("TextService: GetLocation")

        return self.location

    def Distribute(self, data):
        """
        Send the data to all the connections in this server.
        """
        self.log.debug("TextService: Sending Event %s", data)
        
        pdata = pickle.dumps(data)
        size = struct.pack("i", len(pdata))
        for c in self.connections[data.venue]:
            try:
                c.wfile.write(size)
                c.wfile.write(pdata)
            except:
                self.log.exception("TextService: Client disconnected!")
#                self.connections[channel].remove(c)
        
    def AddChannel(self, channelId):
        self.log.debug("Text Service: Adding Channel: %s", channelId)
        
        self.connections[channelId] = []

    def RemoveChannel(self, channelId):
        self.log.debug("Text Service: Removing Channel: %s", channelId)
        
        del self.connections[channelId]

if __name__ == "__main__":
  import string

  log.addHandler(StreamHandler())
  log.setLevel(logging.DEBUG)

  host = string.lower(socket.getfqdn())
  port = 6600
  self.log.debug("Creating new TextService at %s %d.", host, port)
  textChannel = TextService((host, port))
  textChannel.start()
