#-----------------------------------------------------------------------------
# Name:        EventServiceAsynch.py
# Purpose:     This service provides events among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson, Robert D. Olson
#
# Created:     2003/05/19
# RCS-ID:      $Id: EventServiceAsynch.py,v 1.7 2003-05-28 13:25:45 olson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket
import sys
import pickle
import logging
import struct
import Queue
import threading

from SocketServer import ThreadingMixIn, StreamRequestHandler
from pyGlobus.io import GSITCPSocketServer, GSITCPSocketException, GSITCPSocket
from pyGlobus.io import IOBaseException
from pyGlobus.util import Buffer
from pyGlobus import ioc, io

from AccessGrid.hosting.pyGlobus.Utilities import CreateTCPAttrAlwaysAuth, CreateTCPAttrDefault
from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.Events import ConnectEvent, DisconnectEvent
from AccessGrid.GUID import GUID

log = logging.getLogger("AG.EventService")
log.setLevel(logging.DEBUG)


#
# Per-event debugging might be useful sometimes, but not usually.
# Leave the calls in the code via logEvent, but let them
# be disabled.
# 

detailedEventLogging = 0
if detailedEventLogging:
    logEvent = log.debug
else:
    logEvent = lambda *sh: 0

class ConnectionHandler:
    """
    The ConnectionHandler is the object than handles a single event
    connection. The ConnectionHandler gets events from the client then
    passes them to registered callback functions based on event.eventType.
    """

    def __init__(self, lsocket, eservice):
        self.id = str(GUID())
        self.lsocket = lsocket
        self.server = eservice

        self.dataBuffer = ''
        self.bufsize = 4096
        self.buffer= Buffer(self.bufsize)
        self.waitingLen = 0

    def __del__(self):
        log.debug("ConnectionHandler delete")

    def GetId(self):
        return self.id

    def registerAccept(self, attr):
        logEvent("conn handler registering accept")

        socket, cb = self.lsocket.register_accept(attr, self.acceptCallback, None)

        logEvent("register_accept returns socket=%s cb=%s", socket, cb)
        self.socket = socket

    def acceptCallback(self, arg, handle, result):
        try:
            logEvent("Accept Callback '%s' '%s' '%s'", arg, handle, result)
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

        logEvent("Got read handle=%s ret=%s  n=%s waiting=%s\n", handle, ret, n, self.waitingLen)

        if n == 0:
            event = DisconnectEvent(self.channel, self.privateId)
            self.handleData(None, event)
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
            logEvent("Finished reading packet, wait=%s buflen=%s",
                      self.waitingLen, len(self.dataBuffer))

            thedata = self.dataBuffer[:self.waitingLen]
            self.dataBuffer = self.dataBuffer[self.waitingLen:]

            self.handleData(thedata, None)

            self.waitingLen = 0

        self.registerForRead()
        
    def stop(self):
        self.wfile.close()
        self.socket.close()

    def handleData(self, pdata, event):

        # Unpickle the event data
        if event == None:
            try:
                event = pickle.loads(pdata)
            except EOFError, e:
                log.debug("EventService: unpickle got EOF.")
                self.running = 0
                return

        #
        # Snag the channel and private id out of the connect event.
        #
        
        if event.eventType == ConnectEvent.CONNECT:
            self.channel = event.venue
            self.privateId = event.data


        # Pass this event to the callback registered for this
        # event.eventType
        logEvent("EventConnection: Received event %s", event)

        self.server.EnqueueEvent(event, self, self.channel)

class EventService:
    """
    The EventService provides a secure event layer. This might be more 
    scalable as a secure RTP or other UDP solution, but for now we use TCP.
    In the TCP case the EventService is the Server, GSI is our secure version.
    """
    def __init__(self, server_address):
        self.log = logging.getLogger("AG.EventService")
        self.log.debug("Event Service Started")
        
        self.location = server_address
        self.callbacks = {}
        self.connections = {}

        self.socket = GSITCPSocket()
        self.socket.allow_reuse_address = 1
        self.attr = CreateTCPAttrAlwaysAuth()

        self.queue = Queue.Queue()
        self.queueThread = threading.Thread(target = self.QueueHandler)
        self.queueThread.start()

        port = self.socket.create_listener(self.attr, server_address[1])
        log.debug("Bound to %s (server_address=%s)", port, server_address)

    def start(self):
        """
        Start. Initialize the asynch io on accept.
        """

        log.debug("Event service start")
        self.registerForListen()

    def registerForListen(self):
        ret = self.socket.register_listen(self.listenCallback, None)
        log.debug("register_listen returns '%s'", ret)

    def listenCallback(self, arg, handle, result):
        try:
            logEvent("Listen Callback '%s' '%s' '%s'", arg, handle, result)

            self.waiting_socket = GSITCPSocket(handle)

            conn = ConnectionHandler(self.waiting_socket, self)
            conn.registerAccept(self.attr)

        except:
            log.exception("listenCallback failed")

    def Stop(self):
        """
        Stop stops this thread, thus shutting down the service.
        """
        self.log.debug("EventService: Stopping")
        
        for v in self.connections.keys():
            for c in self.connections[v]:
                c.stop()
            
        self.running = 0
        self.socket.close()
        self.EnqueueQuit()
        self.queueThread.join()

    def EnqueueQuit(self):
        self.queue.put(("quit",))
        
    def EnqueueEvent(self, event, conn, channel):
        logEvent("Enqueue event for %s %s...", conn, channel)
        self.queue.put(("event", event, conn, channel))
        logEvent("Enqueue event for %s %s...done (size=%s)", conn, channel, self.queue.qsize())

    def QueueHandler(self):
        """
        Thread main routine for event queue handling.
        """

        try:

            while 1:
                logEvent("Queue handler waiting for data")
                cmd = self.queue.get()
                logEvent("Queue handler received %s", cmd)
                if cmd[0] == "quit":
                    log.debug("Queue handler exiting")
                    return
                elif cmd[0] != "event":
                    log.error("QueueHandler received unknown command %s", cmd[0])
                    continue

                try:
                    self.HandleEvent(cmd[1], cmd[2], cmd[3])
                except:
                    log.exception("HandleEvent threw an exception")
        except:
            log.exception("Body of QueueHandler threw exception")

    def HandleEvent(self, event, conn, channel):

        logEvent("Handle event type %s", event.eventType)
        if event.eventType == ConnectEvent.CONNECT:
            log.debug("EventConnection: Adding client %s to venue %s",
                      event.data, event.venue)
            self.AddChannelConnection(event.venue, conn)

        if event.eventType == DisconnectEvent.DISCONNECT:

            log.debug("EventConnection: Removing client connection to %s",
                      event.venue)
            if channel != None:
                self.RemoveChannelConnection(channel, conn)

        # Pass this event to the callback registered for this
        # event.eventType
        if self.callbacks.has_key((event.venue, event.eventType)):
            cb = self.callbacks[(event.venue, event.eventType)]
            logEvent("Specific event callback=%s", cb)
            if cb != None:
                logEvent("invoke callback %s", str(cb))
                cb(event)
        elif self.callbacks.has_key((event.venue,)):
            # Default handler for this channel.
            cb = self.callbacks[(event.venue,)]
            logEvent("Default channel event callback=%s", cb)
            if cb != None:
                logEvent("invoke channel callback %s", cb)
                cb(event)
            else:
                log.info("EventService: No callback for %s, %s events.",
                         event.venue, event.eventType)

        logEvent("HandleEvent returns")

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
        logEvent("EventService: Sending Event %s", data)

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
                    self.RemoveChannelConnection(channel, c)
            
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

    def AddChannelConnection(self, channelId, conn):
        log.debug("Adding channel %s conn %s", channelId, conn)
        self.connections[channelId].append(conn)
        
    def RemoveChannelConnection(self, channelId, conn):
        clist = self.connections[channelId]
        if conn in clist:
            clist.remove(conn)
        else:
            log.info("RemoveChannelConnection: conn %s not in channel %s",
                     conn, channelId)

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
