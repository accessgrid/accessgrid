#-----------------------------------------------------------------------------
# Name:        TextService.py
# Purpose:     This service provides events among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: TextService.py,v 1.13 2003-04-18 17:18:35 eolson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket
import sys
import pickle
from threading import Thread
import logging

from SocketServer import ThreadingMixIn, StreamRequestHandler
from pyGlobus.io import GSITCPSocketServer, GSIRequestHandler, GSITCPSocketException

# This really should be defined in pyGlobus.io
class ThreadingGSITCPSocketServer(ThreadingMixIn, GSITCPSocketServer): pass

from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.Events import HeartbeatEvent, ConnectEvent, TextEvent
from AccessGrid.Events import DisconnectEvent
from AccessGrid.Events import TextPayload
from AccessGrid.hosting.AccessControl import CreateSubjectFromGSIContext

log = logging.getLogger("AG.VenueServer")

class ConnectionHandler(GSIRequestHandler):
    """
    The ConnectionHandler is the object than handles a single event
    connection. The ConnectionHandler gets events from the client then
    passes them to registered callback functions based on event.eventType.
    """
    def stop(self):
        self.running = 0
         
    def handle(self):
        # loop getting data and handing it to the server
        self.running = 1
        while(self.running == 1):
            try:
                # Get the size of the text message
                evtSize = int(self.rfile.readline())
                # Get the real text message
                pdata = self.rfile.read(evtSize, evtSize)
                # Parse the text structure
                # When this is advanced you can route things, for now
                # this is a simple text reflector
                # However we assign the from address in the server, so
                # there is some notion of security :-)
                event = pickle.loads(pdata)

                if event.eventType == ConnectEvent.CONNECT:
                    # Connection Event
                    self.server.connections[event.venue].append(self)
                    continue
                elif event.eventType == DisconnectEvent.DISCONNECT:
                    # Disconnection Event
                    self.server.connections[event.venue].remove(self)
                    continue
                else:
                    # Tag the event with the sender, which is obtained
                    # from the security layer to avoid spoofing
                    ctx = self.connection.get_security_context()
                    payload = event.data
                    payload.sender = CreateSubjectFromGSIContext(ctx).GetName()

                    # For now we send all messages to everyone
                    self.server.Distribute(event)
            except:
                log.exception("ConnectionHandler.handle: Client disconnected!")
                self.running = 0
                # Find the connection and remove it
                for v in self.server.connections.keys():
                    if self in self.server.connections[v]:
                        self.server.connections[v].remove(self)
                                         
class TextService(ThreadingGSITCPSocketServer, Thread):
    """
    The TextService provides a secure event layer. This might be more 
    scalable as a secure RTP or other UDP solution, but for now we use TCP.
    In the TCP case the TextService is the Server, GSI is our secure version.
    """
    def __init__(self, server_address, RequestHandlerClass=ConnectionHandler):
        Thread.__init__(self)
        self.location = server_address
        self.connections = {}
        ThreadingGSITCPSocketServer.__init__(self, server_address, 
                                                RequestHandlerClass)

    def run(self):
        """
        run is defined to override the Thread.run method so Thread.start works.
        """
        self.running = 1
        while(self.running):
            try:
                self.handle_request()
            except GSITCPSocketException:
                log.info("TextService: GSITCPSocket, interrupted I/O operation, most likely shutting down. ")

    def Stop(self):
        """
        Stop stops this thread, thus shutting down the service.
        """
        for v in self.connections.keys():
            for c in self.connections[v]:
                c.stop()
            
        self.running = 0
        self.server_close()
            
    def GetLocation(self):
        """
        GetLocation returns the (host,port) for this service.
        """
        return self.location

    def Distribute(self, data):
        """
        Send the data to all the connections in this server.
        """
        log.debug("Sending Event (%s) %s", data.venue, data.data.recipient)
        pdata = pickle.dumps(data)
        lenStr = "%s\n" % len(pdata)
        for c in self.connections[data.venue]:
            try:
                c.wfile.write(lenStr)
                c.wfile.write(pdata)           
            except:
                log.exception("EventService.Distribute: Client disconnected!")
        
    def AddChannel(self, channelId):
        self.connections[channelId] = []

    def RemoveChannel(self, channelId):
        del self.connections[channelId]

if __name__ == "__main__":
  import string
  host = string.lower(socket.getfqdn())
  port = 6600
  print "Creating new TextService at %s %d." % (host, port)
  textChannel = TextService((host, port))
  textChannel.start()
