#-----------------------------------------------------------------------------
# Name:        TextService.py
# Purpose:     This service provides events among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: TextServiceAsynch.py,v 1.29 2004-07-15 18:06:08 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: TextServiceAsynch.py,v 1.29 2004-07-15 18:06:08 turam Exp $"
__docformat__ = "restructuredtext en"

from AccessGrid.hosting import Client
import socket
import sys
import pickle
import Queue
import threading
import struct
import time

from pyGlobus.io import GSITCPSocketServer, GSIRequestHandler, GSITCPSocket
from pyGlobus.io import GSITCPSocketException, IOBaseException, Buffer
from pyGlobus.ioc import tcp_get_remote_address

from AccessGrid import Log
from AccessGrid.Events import HeartbeatEvent, ConnectEvent, TextEvent
from AccessGrid.Events import DisconnectEvent, MarshalledEvent
from AccessGrid.Events import TextPayload
from AccessGrid.Security.Utilities import CreateSubjectFromGSIContext
from AccessGrid.Security.Utilities import CreateTCPAttrAlwaysAuth
from AccessGrid.GUID import GUID

log = Log.GetLogger(Log.TextService)
Log.SetDefaultLevel(Log.TextService, Log.DEBUG)

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
        self.wfile = None

        self.dataBuffer = ''
        self.bufsize = 4096
        self.buffer= Buffer(self.bufsize)
        self.waitingLen = 0

	self.sender = "Not Connected"

        # New to try and make shutdown sane
        self.closing = 0
        
    def __del__(self):
        log.debug("TextServiceAsynch: ConnectionHandler delete")

    def GetId(self):
        return self.id

    def registerAccept(self, attr):
        log.info("conn handler registering accept")

        socket, cb = self.lsocket.register_accept(attr, self.acceptCallback, None)
        self.acceptCallbackHandle = cb

        log.info("register_accept returns socket=%s cb=%s", socket, cb)
        self.socket = socket

    def acceptCallback(self, arg, handle, result):
        try:
            if result[0] != 0:
                log.debug("TextServiceAsynch: acceptCallback returned failure: %d %s", result[0], result[1])
                self.server.registerForListen()
                return

            log.info("Accept Callback '%s' '%s' '%s'", arg, handle, result)
            self.lsocket.free_callback(self.acceptCallbackHandle)
            self.server.registerForListen()

            #
            # We can now start reading.
            #

            ctx = self.socket.get_security_context()
            self.sender = CreateSubjectFromGSIContext(ctx).GetName()

            self.wfile = self.socket.makefile("w")
            self.registerForRead()

        except:
            log.exception("acceptCallback failed")

    def registerForRead(self):
        if not self.closing:
            self.cbHandle = self.socket.register_read(self.buffer,
                                                      self.bufsize, 1,
                                                      self.readCallbackWrap,
                                                      None)

    def readCallbackWrap(self, arg, handle, result, buf, n):
        """
        Asynch read callback.

        We just use this to wrap the call to the readCallback itself,
        because the callback invocation mechanism silently ignores exceptions.
        """
        
        try:
            self.socket.free_callback(self.cbHandle)
            self.readCallback(arg, handle, result, buf, n)
            self.registerForRead()
        except:
            log.exception("readcallback failed")
            self.stop()
            return None

    def writeMarshalledEvent(self, mEvent):
        """
        Write this packet to the network.
        If the write fails for some reason, return 0.
        Otherwise, return 1. 
        """

	# if we have actually connected to something
	if self.wfile is not None:
	    try:
                ret = tcp_get_remote_address(self.wfile.sock._handle)
                if ret[0] == 0:
                    log.debug("Writing text event to %s", ret[1])
                    mEvent.Write(self.wfile)
                    return 1
                else:
                    log.error("Error writing to connection: %d %s", ret[0], ret[1])
            except:
                log.exception("writeMarshalledEvent write error!")
	else:
	    log.info("not sending text event, conn obj is none.")

        return 0

    def readCallback(self, arg, handle, result, buf, n):

        log.info("Got read handle=%s ret=%s  n=%s \n", handle, result, n)

        if result[0] != 0:
            log.debug("TextServiceAsynch: readCallback returned failure: %d %s", result[0], result[1])
            self.handleEOF()
            return

        if n == 0:
            log.debug("TextServiceAsynch: TextService got EOF")
            self.handleEOF()
            return

        self.dataBuffer += str(buf)

        if self.waitingLen == 0:

            sz = struct.calcsize('<i')
            
            if len(self.dataBuffer) < sz:
                return

            lenstr = self.dataBuffer[:sz]
            dlen = struct.unpack('<i', lenstr)

            self.dataBuffer = self.dataBuffer[sz:]

            self.waitingLen = dlen[0]

        if len(self.dataBuffer) >= self.waitingLen:
            log.info("finished reading packet, wait=%s buflen=%s",
                      self.waitingLen, len(self.dataBuffer))

            thedata = self.dataBuffer[:self.waitingLen]
            self.dataBuffer = self.dataBuffer[self.waitingLen:]

            self.handleData(thedata, None)

            self.waitingLen = 0

    def stop(self):
        try:
            if self.wfile is not None:
                self.wfile.close()
            self.socket.close()
        except:
            log.exception("TextServiceAsynch: IOBase exception on text service close (probably ok)")

    def handleData(self, pdata, event):
        """
        We have successfully read a data packet.
        """
        # Unpickle the data
        if event == None:
            try:
                event = pickle.loads(pdata)
            except EOFError:
                log.debug("TextServiceAsynch: TextConnection: read EOF.")
                self.handleEOF()
                return

        log.info("TextConnection: Got Event %s", event)

        # Drop this event on the event server's queue for processing
        # out of the asynch event handler.
        self.server.EnqueueEvent(event, self)

    def handleEOF(self):
        """
        We either got an EOF on the connection, or some other
        fatal error occurred (split these probably!).

        Close the socket,  and enqueue a "close" command.
        """
        self.stop()
        self.server.EnqueueEOF(self)

class TextChannel:
    def __init__(self, server, id, authCallback):
        self.server = server
        self.id = id

        #
        # connections is the set of active connections on this
        # channel. It is a dictionary keyed on the connection ID.
        #

        self.connections = {}
        #
        # typedHandlers is the set of handlers for specific message types.
        # it is keyed by the event type string. Each value is the list
        # of handlers receiving that message type.
        #
        
        self.typedHandlers = {}

        #
        # channelHandlers is the set of handlers wishing to receive
        # all events on the channel. It is a simple list.
        #
        self.channelHandlers = []

        self.authCallback = authCallback

    def __del__(self):
        log.debug("TextServiceAsynch: Delete EventChannel %s", self.id)

    def RegisterCallback(self, eventType, callback):
        """
        Register callback as a handler for events of type eventType.
        """

        try:
            cbList = self.typedHandlers[eventType]
        except KeyError:
            cbList = []
            self.typedHandlers[eventType] = cbList

        if callback in cbList:
            log.info("TextServiceAsynch: Callback %s already in handler list for type %s",
                     callback, eventType)
	    pass
        else:
            cbList.append(callback)

    def RegisterChannelCallback(self, callback):
        """
        Register callback as a handler for all events on this channel.
        """

        if callback in self.channelHandlers:
            log.info("TextServiceAsynch: Callback %s already in channel handler list", callback)
	    pass
        else:
            self.channelHandlers.append(callback)

    def AuthorizeNewConnection(self, event, connObj):
        """
        An event has come in on a previously unconnected connection
        object connObj. See if we want to allow this connection to be
        attached to this channel.
        """

        #
        # We only allow a CONNECT event to attempt authorization.
        #

        log.debug("TextServiceAsynch: Attempting authorization on event %s", event.eventType)


        if event.eventType != ConnectEvent.CONNECT:
            log.debug("TextServiceAsynch: Channel refusing authorization, %s is not a connect event",
                      event.eventType)
            return 0

        #
        # Invoke the authorization callback. If we don't have one,
        # allow the connection.
        #

        authorized = 0
        if self.authCallback is not None:
            try:
                authorized = self.authCallback(event, connObj)
                log.debug("TextServiceAsynch: Auth callback %s returns %s",
                          self.authCallback,
                          authorized)
            except:
                log.info("TextServiceAsynch: Authorization callback failed")
                authorized = 0
        else:
            log.debug("TextServiceAsynch: Default authorization (no callback registered)")
            authorized = 1
        return authorized

    def HandleEvent(self, event, connObj):
        """
        Handle an incoming event from connObj.
        """

        if event.eventType == DisconnectEvent.DISCONNECT:
            connObj.closing = 1
            log.debug("TextServiceAsynch: EventConnection: Removing client \
                       connection to %s", event.venue)
            self.RemoveConnection(connObj)
            self.server.CloseConnection(connObj)
            return
            
        # Pass this event to the callback registered for this
        # event.eventType
        if self.typedHandlers.has_key(event.eventType):
            for cb in self.typedHandlers[event.eventType]:
                log.debug("TextServiceAsynch: Specific event callback=%s", cb)
                if cb != None:
                    log.info("invoke callback %s", str(cb))
                    try:
                        cb(event)
                    except:
                        log.exception("TextEvent callback failed")

        for cb in self.channelHandlers:
            log.debug("TextServiceAsynch: invoke channel callback %s", cb)
            try:
                cb(event)
            except:
                log.exception("TexftEvent callback failed")

        log.info("HandleEvent returns")

    def Distribute(self, data):
        """
        Distribute the event contained in data to the connections in this channel.
        """

        connections = self.connections.values()

        #
        # Quick path out if we don't have anyone to send to.
        #
        if len(connections) == 0:
            return

        removeList = []
        me = MarshalledEvent()
        me.SetEvent(data)
        for c in connections:
            if not c.closing:
                success = c.writeMarshalledEvent(me)
                if not success:
                    removeList.append(c)
        
        #
        # These guys failed. Bag 'em.
        #

        for r in removeList:
            log.debug("TextServiceAsynch: Removing connection %s due to write error", r.GetId())
            self.RemoveConnection(r)

    def RemoveConnection(self, connObj):
        if connObj.GetId() in self.connections:
            del self.connections[connObj.GetId()]
        else:
            log.info("TextServiceAsynch: RemoveConnection: connection %s not in connection list.  (okay, could have been removed twice)",
                      connObj.GetId())
        
    def AddConnection(self, event, connObj):
        self.connections[connObj.GetId()] = connObj

    def GetId(self):
        return self.id


class TextService:
    """
    The TextService provides a secure event layer. This might be more 
    scalable as a secure RTP or other UDP solution, but for now we use TCP.
    In the TCP case the TextService is the Server, GSI is our secure version.
    """
    def __init__(self, server_address):
        log.debug("TextServiceAsynch: Text Service Started")
        
        self.location = server_address

        #
        # self.channels is a dictionary keyed on the channel id
        #
        # self.connectionMap is a dict keyed on the ConnectionHandler
        # id (assigned when the connection comes in). The value is
        # the EventChannel that the connection is registered with, or
        # None if it is not (yet) registered.
        #
        # self.allConnections is a list of all the active connections
        # that we know about.
        #

        self.channels = {}
        self.connectionMap = {}
        self.allConnections = []

        self.socket = GSITCPSocket()
        self.socket.allow_reuse_address = 1
        self.attr = CreateTCPAttrAlwaysAuth()

        #   
        # Our incoming message queue. We don't handle messages
        # in the asynch IO threads, in order that they don't block
        # on the Globus side.
        #
        self.queue = Queue.Queue()
        self.queueThread = threading.Thread(target = self.QueueHandler,
				name="TextService Queue Handler")
        self.queueThread.start()

        port = self.socket.create_listener(self.attr, server_address[1])
        log.debug("TextServiceAsynch: Bound to %s (server_address=%s)", port, server_address)

    def findConnectionChannel(self, id):
        try:
            return self.connectionMap[id]
        except KeyError:
            return None

    def GetChannel(self, id):
        try:
            return self.channels[id]
        except KeyError:
            return None

    def start(self):
        """
        Start. Initialize the asynch io on accept.
        """

        log.debug("TextServiceAsynch: Text service start")
        self.registerForListen()

    def registerForListen(self):
        ret = self.socket.register_listen(self.listenCallback, None)
        self.listenCallbackHandle = ret
        log.debug("TextServiceAsynch: register_listen returns '%s'", ret)

    def listenCallback(self, arg, handle, result):
        try:
            if result[0] != 0:
                log.debug("TextServiceAsynch: listenCallback returned failure: %d %s", result[0], result[1])
                self.registerForListen()
                return

            log.info("Listen Callback '%s' '%s' '%s'", arg, handle, result)
            self.socket.free_callback(self.listenCallbackHandle)

            #
            # Don't do this! the handle that is passed in here is the
            # handle that is bound to self.socket. 
            #
            # By creating this new wrapper, the listening socket is
            # prematurely destroyed (when teh new wrapper is destroyed).
            #
            # At some point the namespace needs to be cleaned up a bit (remove
            # referenes to waiting_socket).
            #self.waiting_socket = GSITCPSocket(handle)
            #

            self.waiting_socket = self.socket

            conn = ConnectionHandler(self.waiting_socket, self)
            conn.registerAccept(self.attr)
            self.connectionMap[conn.GetId()] = None
            self.allConnections.append(conn)

        except:
            log.exception("listenCallback failed")

    def CloseConnection(self, connObj):

        cid = connObj.GetId()

        log.debug("TextServiceAsynch: Removing connection %s", cid)
        connObj.stop()

#         channel = self.findConnectionChannel(cid)
#         if channel is not None:
#             log.debug("TextServiceAsynch: Removing connection %s from channel %s", cid, channel.GetId())
#             channel.RemoveConnection(connObj)
        try:
            self.allConnections.remove(connObj)
        except ValueError:
            # We can get this if we lose the race on a shutdown.
            pass

    def Stop(self):
        """
        Stop the text service.

        Close our listener socket and all the active connections; this should
        clear out any lingering state.
        """

        log.debug("TextServiceAsynch: Stopping")
        
        try:    
            self.socket.close()
        except:
            log.exception("TextServiceAsynch: socket close failed")
            pass

        self.EnqueueQuit()

        for c in self.allConnections:
            c.stop()
            self.allConnections.remove(c)

        for ch in self.channels.keys():
            self.RemoveChannel(ch)
            if self.channels.has_key(ch):
                del self.channels[ch]
            
        self.running = 0
        self.queueThread.join()

    def EnqueueQuit(self):
        self.queue.put(("quit",))

    def EnqueueEvent(self, event, conn):
        log.info("Enqueue event %s for %s...", event.eventType, conn)
        self.queue.put(("event", event, conn))

    def EnqueueEOF(self, conn):
        log.info("Enqueue EOF for %s...", conn)
        self.queue.put(("eof", conn))

    def QueueHandler(self):
        """
        Thread main routine for event queue handling.
        """

        try:

            while 1:
                log.info("Queue handler waiting for data")
                cmd = self.queue.get()
                log.info("Queue handler received %s", cmd)
                if cmd[0] == "quit":
                    log.debug("TextServiceAsynch: Queue handler exiting")
                    return
                elif cmd[0] == "eof":
                    connObj = cmd[1]
                    log.debug("TextServiceAsynch: EOF on connection %s", connObj.GetId())
                    self.HandleEOF(connObj)
                elif cmd[0] == "event":
                    try:
                        event = cmd[1]
                        connObj = cmd[2]
                        self.HandleEvent(event, connObj)
                    except:
                        log.exception("HandleEvent threw an exception")

                else:
                    log.error("QueueHandler received unknown command %s", cmd[0])
                    continue

        except:
            log.exception("Body of QueueHandler threw exception")

    def HandleEvent(self, event, connObj ):
        """
        Handle an incoming event.

        This is executed in the message handling thread after an event
        has been received by the async reader.

        Exactly what happens with this event depends on whether
        the connection object has been connected to a channel or not.

        If it has not, the only events that will be processed are Connect
        and Disconnect.

        If it has, the event is passed along to the TextChannel for
        processing.

        """
        connId = connObj.GetId()

        connChannel = self.findConnectionChannel(connId)

        log.info("Handle event type %s", event.eventType)

        if connChannel is None:
            self.HandleEventForDisconnectedChannel(event, connObj)
        else:
            connChannel.HandleEvent(event, connObj)

        if event.eventType == ConnectEvent.CONNECT:
            # Connection Event
            return
       
        if event.eventType == DisconnectEvent.DISCONNECT:
            # Disconnection Event
            return

        # Tag the event with the sender, which is obtained
        # from the security layer to avoid spoofing
        payload = event.data
        payload.sender = connObj.sender

        # Parse the text structure
        # When this is advanced you can route things, for now
        # this is a simple text reflector
        # However we assign the from address in the server, so
        # there is some notion of security :-)
        self.Distribute(connChannel.id, event)

    def HandleEOF(self, connObj):
        """
        Handle an EOF on a connection.

        If this connection doesn't yet have a channel assignment,
        we can just delete it from our list of all channels.

        If it does have a channel assignment, remove from there then delete
        from all-channels.
        """

        connId = connObj.GetId()
        connChannel = self.findConnectionChannel(connId)
        self.CloseConnection(connObj)

    def HandleEventForDisconnectedChannel(self, event, connObj):
        """
        We've received an event for a connection which hasn't
        yet been connected to a channel.

        Pass the event to the channel to allow it to decide whether
        to allow the connection or not. If it allows it, add the
        connection to the channel. If not, close the channel.
        """

        channel = self.GetChannel(event.venue)
        if channel is None:
            log.debug("TextServiceAsynch: received event type %s for nonexistent channel %s", event.eventType, event.venue)
            self.CloseConnection(connObj)
            return

        allowed = channel.AuthorizeNewConnection(event, connObj)

        if allowed:
            log.debug("TextServiceAsynch: Adding connObj %s to channel %s", connObj.GetId(),
                      event.venue)
            channel.AddConnection(event, connObj)
            self.connectionMap[connObj.GetId()] = channel

        else:
            log.debug("TextServiceAsynch: Rejected adding connObj %s to channel %s", connObj.GetId(),
                      event.venue)
            self.CloseConnection(connObj)

    def RegisterCallback(self, channelId, eventType, callback):
        # Callbacks just take the event data as the argument

        channel = self.GetChannel(channelId)
        if channel is None:
            log.error("RegisterCallback on a nonexistent channel %s", channelId)
            return

        channel.RegisterCallback(eventType, callback)

    def RegisterChannelCallback(self, channelId, callback):
        """
        Register a callback for all events on this channel.
        """

        channel = self.GetChannel(channelId)
        if channel is None:
            log.error("RegisterCallback on a nonexistent channel %s", channelId)
            return

        channel.RegisterChannelCallback(callback)

    def RegisterObject(self, channel, object):
        """
        RegisterObject is short hand for registering multiple callbacks on the
        same object. The object being registered has to define a table named
        callbacks that has event types as keys, and self.methods as values.
        Then these are automatically registered.
        """
        for c in object.callbacks.keys():
            self.RegisterCallback(c, channel, object.callbacks[c])


            
    def GetLocation(self):
        """
        GetLocation returns the (host,port) for this service.
        """
        log.debug("TextServiceAsynch: GetLocation")

        return self.location

    def Distribute(self, channelId, data):
        """
        Distribute sends the data to all connections.
        """

        log.info("TextServiceAsynch: Sending Event %s", data)
  
        channel = self.GetChannel(channelId)
  
        if channel is None:
            log.error("Distribute invoked on nonexistent channel %s", channelId)
            return

        channel.Distribute(data)

        log.info("TextServiceAsynch: Sent Event")
        
    def AddChannel(self, channelId, authCallback = None):
        """
        This adds a new channel to the Text Service.
        """
        log.debug("TextServiceAsynch: AddChannel %s", channelId)

        if self.GetChannel(channelId) is not None:
            log.warn("TextServiceAsynch: Channel %s already exists", channelId)
            return

        channel = TextChannel(self, channelId, authCallback)
        self.channels[channelId] = channel

    def RemoveChannel(self, channelId):
        """
        This removes a channel from the Text Service.
        """
        log.debug("TextServiceAsynch: Text Service: Removing Channel: %s", channelId)
        
        del self.channels[channelId]

if __name__ == "__main__":
  import string
  from AccessGrid import Toolkit

  app = Toolkit.CmdlineApplication()
  app.Initialize()
  app.InitGlobusEnvironment()

  certMgr = app.GetCertificateManager()
  if not certMgr.HaveValidProxy():
      certMgr.CreateProxy()
  
  hdlr = Log.StreamHandler()
  hdlr.setLevel(Log.DEBUG)
  Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())
  

  port = 6600
  log.debug("TextServiceAsynch: Creating new TextService at %d.", port)
  textService = TextService(('', port))
  textService.AddChannel("Test")
  textService.start()

