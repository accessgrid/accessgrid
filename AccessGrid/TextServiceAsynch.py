#-----------------------------------------------------------------------------
# Name:        TextService.py
# Purpose:     This service provides events among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: TextServiceAsynch.py,v 1.1 2003-05-20 19:40:55 olson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket
import sys
import pickle
from threading import Thread
import logging
import struct

log = logging.getLogger("AG.TextService")
log.setLevel(logging.INFO)

from pyGlobus.io import GSITCPSocketServer, GSIRequestHandler, GSITCPSocket
from pyGlobus.io import GSITCPSocketException, IOBaseException, Buffer

from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.Events import HeartbeatEvent, ConnectEvent, TextEvent
from AccessGrid.Events import DisconnectEvent
from AccessGrid.Events import TextPayload
from AccessGrid.hosting.AccessControl import CreateSubjectFromGSIContext
from AccessGrid.hosting.pyGlobus.Utilities import CreateTCPAttrAlwaysAuth

class ConnectionHandler:
    """
    The ConnectionHandler is the object than handles a single event
    connection. The ConnectionHandler gets events from the client then
    passes them to registered callback functions based on event.eventType.
    """

    def __init__(self, lsocket, eservice):
        self.lsocket = lsocket
        self.server = eservice

        self.dataBuffer = ''
        self.bufsize = 4096
        self.buffer= Buffer(self.bufsize)
        self.waitingLen = 0

    def registerAccept(self, attr):
        log.debug("conn handler registering accept")

        socket, cb = self.lsocket.register_accept(attr, self.acceptCallback, None)

        log.debug("register_accept returns socket=%s cb=%s", socket, cb)
        self.socket = socket

    def acceptCallback(self, arg, handle, result):
        try:
            log.debug("Accept Callback '%s' '%s' '%s'", arg, handle, result)
            self.server.registerForListen()

            #
            # We can now start reading.
            #

            self.wfile = self.socket.makefile("w")
            self.registerForRead()

        except:
            log.exception("acceptCallback failed")

    def registerForRead(self):
        h = self.socket.register_read(self.buffer, self.bufsize, 1,
                                      self.readCallbackWrap, None)
        self.cbHandle = h

    def readCallbackWrap(self, arg, handle, ret, buf, n):
        """
        Asynch read callback.

        We just use this to wrap the call to the readCallback itself,
        because the callback invocation mechanism silently ignores exceptions.
        """
        
        try:
            return self.readCallback(arg, handle, ret, buf, n)
        except Exception, e:
            log.exception("readcallback failed")
                

    def readCallback(self, arg, handle, ret, buf, n):

        log.debug("Got read handle=%s ret=%s  n=%s \n", handle, ret, n)

        if n == 0:
            log.debug("TextService got EOF")
            return

        dstr = str(buf)
        self.dataBuffer += dstr

        if self.waitingLen == 0:

            sz = struct.calcsize('i')
            
            if len(self.dataBuffer) < sz:
                return

            lenstr = self.dataBuffer[:sz]
            dlen = struct.unpack('i', lenstr)

            self.dataBuffer = self.dataBuffer[sz:]

            self.waitingLen = dlen[0]

        if len(self.dataBuffer) >= self.waitingLen:
            log.debug("finally read enough data, wait=%s buflen=%s",
                      self.waitingLen, len(self.dataBuffer))

            thedata = self.dataBuffer[:self.waitingLen]
            self.dataBuffer = self.dataBuffer[self.waitingLen:]

            self.handleData(thedata)

            self.waitingLen = 0

        self.registerForRead()
        
    def stop(self):
        self.wfile.close()
        self.socket.close()

    def handleData(self, pdata):
        # Unpickle the data
        try:
            event = pickle.loads(pdata)
        except EOFError:
            log.debug("TextConnection read EOF.")
            return

        log.debug("TextConnection: Got Event %s", event)

        if event.eventType == ConnectEvent.CONNECT:
            # Connection Event
            self.channel = event.venue
            self.server.connections[self.channel].append(self)
            return

        if event.eventType == DisconnectEvent.DISCONNECT:
            # Disconnection Event
            return

        # Tag the event with the sender, which is obtained
        # from the security layer to avoid spoofing
        ctx = self.socket.get_security_context()
        payload = event.data
        payload.sender = CreateSubjectFromGSIContext(ctx).GetName()

        # Parse the text structure
        # When this is advanced you can route things, for now
        # this is a simple text reflector
        # However we assign the from address in the server, so
        # there is some notion of security :-)
        self.server.Distribute(event)

        
class TextService:
    """
    The TextService provides a secure event layer. This might be more 
    scalable as a secure RTP or other UDP solution, but for now we use TCP.
    In the TCP case the TextService is the Server, GSI is our secure version.
    """
    def __init__(self, server_address):
        self.log = logging.getLogger("AG.TextService")
        self.log.debug("Text Service Started")
        
        self.location = server_address
        self.connections = {}

        self.socket = GSITCPSocket()
        self.socket.allow_reuse_address = 1
        self.attr = CreateTCPAttrAlwaysAuth()

        port = self.socket.create_listener(self.attr, server_address[1])
        log.debug("Bound to %s (server_address=%s)", port, server_address)

    def start(self):
        """
        Start. Initialize the asynch io on accept.
        """

        self.registerForListen()

    def registerForListen(self):
        ret = self.socket.register_listen(self.listenCallback, None)
        log.debug("register_listen returns '%s'", ret)

    def listenCallback(self, arg, handle, result):
        try:
            log.debug("Listen Callback '%s' '%s' '%s'", arg, handle, result)

            self.waiting_socket = GSITCPSocket(handle)

            conn = ConnectionHandler(self.waiting_socket, self)
            conn.registerAccept(self.attr)


        except:
            log.exception("listenCallback failed")

        
    def Stop(self):
        """
        Stop stops this thread, thus shutting down the service.
        """
        self.log.debug("TextService: Stopping")
        
        for v in self.connections.keys():
            for c in self.connections[v]:
                c.stop()
            
        self.socket.close()
            
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

  log.addHandler(logging.StreamHandler())
  log.setLevel(logging.DEBUG)

  host = string.lower(socket.getfqdn())
  port = 6600
  log.debug("Creating new TextService at %s %d.", host, port)
  textChannel = TextService((host, port))
  textChannel.start()
