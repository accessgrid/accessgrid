#-----------------------------------------------------------------------------
# Name:        AsyncService.py
# Purpose:     Abstracted out the parts of the asynchronous services to be a 
#              single copy of the code.
# Created:     2004/07/14
# RCS-ID:      $Id: AsyncService.py,v 1.1 2004-07-16 01:05:37 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
This module contains the common code that is used for the Event and
Text Services. These services both use the pyGlobus asynchronous IO,
but implement slight different dispatch handlers. So we've combined
them and cleaned this up.
"""

__revision__ = "$Id: AsyncService.py,v 1.1 2004-07-16 01:05:37 judson Exp $"

import Queue
import threading
import pickle
import struct

from pyGlobus.io import GSITCPSocket
from pyGlobus.ioc import tcp_get_remote_address
from pyGlobus.util import GlobusException, Buffer

from AccessGrid import Log
from AccessGrid.GUID import GUID
from AccessGrid.Events import ConnectEvent, DisconnectEvent, MarshalledEvent
from AccessGrid.Security.Utilities import CreateTCPAttrAlwaysAuth
from AccessGrid.Security.Utilities import CreateSubjectFromGSIContext

log = Log.GetLogger(Log.AsyncService)
Log.SetDefaultLevel(Log.EventService, Log.DEBUG)

class AsyncConnectionHandler:
    """
    A connection endpoint for a connected asynchonous socket.
    """
    def __init__(self, lsocket, eservice):
        """
        The constructor.
        """
        self.id = str(GUID())
        self.lsocket = lsocket
        self.server = eservice
        self.wfile = None
        self.dataBuffer = ''
        self.bufsize = 4096
        self.buffer = Buffer(self.bufsize)
        self.waitingLen = 0
        self.sender = "Not Connected"
        self.closing = 0
        self.cbHandle = None
        self.acceptCallbackHandle = None
        self.socket = None

        log.debug("Created AsynchConnectionHandler.")
        
    def __del__(self):
        """
        Null destructor, might be useful for logging.
        """
        log.debug("Destroyed AsyncConnectionHandler.")
    
    def GetId(self):
        """
        Simple accessor to retrieve the connection id.
        """
        return self.id
    
    def registerAccept(self, attr):
        """
        Method to register an accept callback, this is step 2 in the process
        of Listen, Accept, etc.
        """
        log.debug("Registering accept callback.")

        socket, callback = self.lsocket.register_accept(attr,
                                                        self.acceptCallback,
                                                        None)
        self.acceptCallbackHandle = callback
        self.socket = socket
    
    def acceptCallback(self, arg, handle, result):
        """
        Docstring to fill in later.
        """
        log.debug("Invoking accept callback (arg=%s handle=%s and result=%s)",
                  arg, handle, result)

        try:
            if result[0] != 0:
                self.server.registerForListen()
                return
            
            self.lsocket.free_callback(self.acceptCallbackHandle)
            self.server.registerForListen()
            ctx = self.socket.get_security_context()
            self.sender = CreateSubjectFromGSIContext(ctx).GetName()
            self.wfile = self.socket.makefile("w")
            self.registerForRead()
        except:
            pass
    
    def registerForRead(self):
        """
        Docstring to fill in later.
        """
        log.debug("registering read callback.")
        
        if not self.closing:
            self.cbHandle = self.socket.register_read(self.buffer,
                                                      self.bufsize, 1,
                                                      self.readCallbackWrap,
                                                      None)
    
    def readCallbackWrap(self, arg, handle, result, buf, buf_len):
        """
        Docstring to fill in later.
        """
        log.debug("Invoking read callback (arg=%s handle=%s result=%s)",
                  arg, handle, result)
        try:
            self.socket.free_callback(self.cbHandle)
            return self.readCallback(arg, handle, result, buf, buf_len)
        except:
            return None
    
    def writeMarshalledEvent(self, mEvent):
        """
        Docstring to fill in later.
        """
        log.debug("writing marshalled event.")

        if self.wfile is not None:
            try:
                ret = tcp_get_remote_address(self.wfile.sock._handle)
                if ret[0] == 0:
                    log.debug("Writing text event to %s", ret[1])
                    mEvent.Write(self.wfile)
                    return 1
                else:
                    log.error("Error writing to %s (%d %s).",
                              self.__class__, ret[0], ret[1])
            except:
                log.exception("writeMarshalledEvent write error.")
        else:
            log.info("Not writing marshalled event, %s is None.",
                     self.__class__)
        
        return 0
    
    def readCallback(self, arg, handle, result, buf, buf_len):
        """
        Docstring to fill in later.
        """
        log.debug("In read callback.")
        
        if result[0] != 0:
            log.debug("Read callback result %d, calling handleEOF", result[0])
            self.handleEOF()
            return
        
        if buf_len == 0:
            log.debug("buffer length 0, calling handleEOF")
            self.handleEOF()
            return
        
        self.dataBuffer += str(buf)
        if self.waitingLen == 0:
            data_size = struct.calcsize('<i')
            if len(self.dataBuffer) < data_size:
                return
            
            lenstr = self.dataBuffer[:data_size]
            dlen = struct.unpack('<i', lenstr)
            self.dataBuffer = self.dataBuffer[data_size:]
            self.waitingLen = dlen[0]
        
        if len(self.dataBuffer) >= self.waitingLen:
            thedata = self.dataBuffer[:self.waitingLen]
            self.dataBuffer = self.dataBuffer[self.waitingLen:]
            self.handleData(thedata, None)
            self.waitingLen = 0
        
        self.registerForRead()
    
    def stop(self):
        """
        Docstring to fill in later.
        """
        log.debug("calling %s stop.", self.__class__)

        try:
            if self.wfile is not None:
                self.wfile.close()
            self.socket.close()
        except GlobusException, globus_exc:
            pass
    
    def handleData(self, pdata, event):
        """
        Docstring to fill in later.
        """
        log.debug("calling %s handleData.", self.__class__)

        if event == None:
            try:
                event = pickle.loads(pdata)
            except EOFError:
                self.handleEOF()
                return
        
        self.server.EnqueueEvent(event, self)
    
    def handleEOF(self):
        """
        Docstring to fill in later.
        """
        log.debug("calling %s handleEOF.", self.__class__)

        self.stop()
        self.server.EnqueueEOF(self)

class AsyncChannel:
    """
    Docstring to fill in later.
    """
    def __init__(self, server, channel_id, authCallback):
        """
        Docstring to fill in later.
        """
        self.server = server
        self.channel_id = channel_id
        self.connections = dict()
        self.typedHandlers = dict()
        self.channelHandlers = list()
        self.authCallback = authCallback

        log.debug("Creating AsyncChannel %s", self.channel_id)
        
    def __del__(self):
        """
        Docstring to fill in later.
        """
        log.debug("Destroying AsyncChannel %s", self.channel_id)

    def __repr__(self):
        str_self = "<AsyncChannel address=(h='%s' p=%d) id=%s>" % (
            self.server.location[0], self.server.location[1], self.channel_id)
        return str_self

    def RegisterCallback(self, eventType, callback):
        """
        Docstring to fill in later.
        """
        log.debug("Registering a callback.")
        
        try:
            cbList = self.typedHandlers[eventType]
        except KeyError:
            cbList = []
            self.typedHandlers[eventType] = cbList
        
        if callback in cbList:
            pass
        else:
            cbList.append(callback)
    
    def RegisterChannelCallback(self, callback):
        """
        Docstring to fill in later.
        """
        log.debug("Registering a channel callback.")
        
        if callback in self.channelHandlers:
            pass
        else:
            self.channelHandlers.append(callback)
    
    def AuthorizeNewConnection(self, event, connObj):
        """
        Docstring to fill in later.
        """
        log.debug("Authorizing a connection for %s", connObj)
        
        if event.eventType != ConnectEvent.CONNECT:
            return 0
        
        authorized = 0
        if self.authCallback is not None:
            try:
                authorized = self.authCallback(event, connObj)
            except:
                authorized = 0
        else:
            authorized = 1
        
        return authorized
    
    def HandleEvent(self, event, connObj):
        """
        Docstring to fill in later.
        """
        log.debug("Handling an event %s", event.eventType)
        
        if event.eventType == DisconnectEvent.DISCONNECT:
            connObj.closing = 1
            self.RemoveConnection(connObj)
            self.server.CloseConnection(connObj)
            return
        
        if self.typedHandlers.has_key(event.eventType):
            for callback in self.typedHandlers[event.eventType]:
                if callback != None:
                    try:
                        callback(event)
                    except:
                        pass
        
        for callback in self.channelHandlers:
            try:
                callback(event)
            except:
                pass
    
    def Distribute(self, data):
        """
        Docstring to fill in later.
        """
        log.debug("Distributing an event.")

        connections = self.connections.values()
        
        if len(connections) == 0:
            return
        
        removeList = []
        m_event = MarshalledEvent()
        m_event.SetEvent(data)
        for conn in connections:
            if not conn.closing:
                success = conn.writeMarshalledEvent(m_event)
                if not success:
                    removeList.append(conn)

        map(self.RemoveConnection, removeList)
    
    def RemoveConnection(self, connObj):
        """
        Docstring to fill in later.
        """
        log.debug("Removing connection %s", connObj)
        
        if connObj.GetId() in self.connections:
            del self.connections[connObj.GetId()]
        else:
            log.warn("Connection not found.")
    
    def AddConnection(self, event, connObj):
        """
        Docstring to fill in later.
        """
        log.debug("Adding connection %s", connObj)
        
        self.connections[connObj.GetId()] = connObj
    
    def GetId(self):
        """
        Docstring to fill in later.
        """
        return self.channel_id

class AsyncService:
    """
    Docstring to fill in later.
    """
    def __init__(self, server_address):
        """
        Docstring to fill in later.
        """
        self.location = server_address
        self.channels = dict()
        self.connectionMap = dict()
        self.allConnections = list()

        self.socket = GSITCPSocket()
        self.socket.allow_reuse_address = 1
        self.attr = CreateTCPAttrAlwaysAuth()
        self.waiting_socket = None
        self.listenCallbackHandle = None
        
        self.outQueue = Queue.Queue()
        self.outQEvt = threading.Event()
        self.outQEvt.set()
        self.outQThread = threading.Thread(target = self.RecvHandler, 
                                 name = "AsyncService Recieve Queue Handler")

        self.inQueue = Queue.Queue()
        self.inQEvt = threading.Event()
        self.inQEvt.set()
        self.inQThread = threading.Thread(target = self.SendHandler,
                                    name = "AsyncService Send Queue Handler")

        self.inQThread.start()
        self.outQThread.start()

        self.listenPort = self.socket.create_listener(self.attr,
                                                      server_address[1])
        log.debug("Created AsyncService.")
        
    def findConnectionChannel(self, conn_id):
        """
        Docstring to fill in later.
        """
        log.debug("Finding channel for connection %s", conn_id)
        
        try:
            return self.connectionMap[conn_id]
        except KeyError:
            return None
    
    def GetChannel(self, channel_id):
        """
        Docstring to fill in later.
        """
        log.debug("Getting channel object for id %s", channel_id)
        
        if self.channels.has_key(channel_id):
            return self.channels[channel_id]
        else:
            return None
    
    def start(self):
        """
        Docstring to fill in later.
        """
        log.debug("Starting the AsyncService.")
        
        self.registerForListen()
    
    def registerForListen(self):
        """
        Docstring to fill in later.
        """
        log.debug("Registering for listen.")
        
        ret = self.socket.register_listen(self.listenCallback, None)
        self.listenCallbackHandle = ret
    
    def listenCallback(self, arg, handle, result):
        """
        Docstring to fill in later.
        """
        log.debug("Invoking listen callback.")
        
        try:
            if result[0] != 0:
                self.registerForListen()
                return
            
            self.socket.free_callback(self.listenCallbackHandle)
            self.waiting_socket = self.socket
            conn = AsyncConnectionHandler(self.waiting_socket, self)
            conn.registerAccept(self.attr)
            self.connectionMap[conn.GetId()] = None
            self.allConnections.append(conn)
        except:
            log.exception("Listen callback raised exception.")
    
    def CloseConnection(self, connObj):
        """
        Docstring to fill in later.
        """
        log.debug("Closing connection %s", connObj)
        
        connObj.stop()
        channel = self.findConnectionChannel(connObj.GetId())
        if channel is not None:
            channel.RemoveConnection(connObj)
        try:
            self.allConnections.remove(connObj)
        except ValueError:
            log.exception("CloseConnection.")
    
    def SendHandler(self):
        """
        Docstring to fill in later.
        """
        log.debug("SendHandler.")
        
        while self.inQEvt.isSet():
            try:
                try:
                    (channel, data) = self.inQueue.get()
                    if channel == 'quit':
                        self.inQEvt.clear()
                        break
                except:
                    data = None
                        
                if data is not None:
                    self._Distribute(channel, data)         
            except:
                log.exception("SendHandler loop.")
    
    def Stop(self):
        """
        Docstring to fill in later.
        """
        log.debug("AsyncService stop.")
        
        try:
            self.socket.close()
        except GlobusException, globus_exc:
            log.exception("Error closing socket.")
        
        self.outQueue.put(("quit",))
        self.inQueue.put(("quit",))
        
        for conn in self.allConnections:
            conn.stop()
        self.allConnections = []
        
        for channel in self.channels.keys():
            self.RemoveChannel(channel)

        self.outQEvt.clear()
        self.inQEvt.clear()
    
    def EnqueueQuit(self):
        """
        Docstring to fill in later.
        """
        log.debug("Enqueuing quit.")
        self.outQueue.put(("quit",))
    
    def EnqueueEvent(self, event, conn):
        """
        Docstring to fill in later.
        """
        log.debug("Enqueuing event %s.", event)
        self.outQueue.put(("event", event, conn))
    
    def EnqueueEOF(self, conn):
        """
        Docstring to fill in later.
        """
        log.debug("Enqueuing eof.")
        self.outQueue.put(("eof", conn))
    
    def RecvHandler(self):
        """
        Docstring to fill in later.
        """
        while self.outQEvt.isSet():
            try:
                cmd = self.outQueue.get()
                if cmd[0] == "quit":
                    return
                elif cmd[0] == "eof":
                    connObj = cmd[1]
                    self.HandleEOF(connObj)
                elif cmd[0] == "event":
                    try:
                        event = cmd[1]
                        connObj = cmd[2]
                        self.HandleEvent(event, connObj)
                    except:
                        log.exception("Error calling HandleEvent.")
                else:
                    continue
            except:
                log.exception("RecvHandler loop.")

    def HandleEvent(self, event, connObj):
        """
        Handle Event method, to be over-ridden.
        """
        log.warn("This should have been overridden.")
    
    def HandleEOF(self, connObj):
        """
        Docstring to fill in later.
        """
        log.debug("Closing connection %s", connObj)
        
        self.CloseConnection(connObj)
    
    def HandleEventForDisconnectedChannel(self, event, connObj):
        """
        Docstring to fill in later.
        """
        log.debug("Handlig event for disconnected channel %s", connObj)
        
        channel = self.GetChannel(event.venue)
        if channel is None:
            self.CloseConnection(connObj)
            return
        
        allowed = channel.AuthorizeNewConnection(event, connObj)
        
        if allowed:
            channel.AddConnection(event, connObj)
            self.connectionMap[connObj.GetId()] = channel
        else:
            self.CloseConnection(connObj)
    
    def RegisterCallback(self, channelId, eventType, callback):
        """
        Docstring to fill in later.
        """
        log.debug("Registering callback.")
        
        channel = self.GetChannel(channelId)
        if channel is None:
            return
        
        channel.RegisterCallback(eventType, callback)
    
    def RegisterChannelCallback(self, channelId, callback):
        """
        Docstring to fill in later.
        """
        log.debug("Registering a channel callback.")

        channel = self.GetChannel(channelId)
        if channel is None:
            return
        
        channel.RegisterChannelCallback(callback)
    
    def RegisterObject(self, channel, obj):
        """
        Docstring to fill in later.
        """
        log.debug("Registering methods on object.")

        for callback in obj.callbacks.keys():
            self.RegisterCallback(callback, channel, obj.callbacks[callback])
    
    def Distribute(self, channelId, data):
        """
        Docstring to fill in later.
        """
        log.debug("Putting event on queue.")

        self.inQueue.put((channelId, data))
    
    def _Distribute(self, channelId, data):
        """
        Docstring to fill in later.
        """
        log.debug("Distributing event.")

        channel = self.GetChannel(channelId)
        
        if channel is None:
            return
        
        channel.Distribute(data)
    
    def GetLocation(self):
        """
        Docstring to fill in later.
        """
        return self.location
    
    def AddChannel(self, channelId, authCallback = None):
        """
        Docstring to fill in later.
        """
        log.debug("Adding channel %s with callback %s", channelId,
                  authCallback)
        if self.GetChannel(channelId) is not None:
            return
        
        channel = AsyncChannel(self, channelId, authCallback)
        self.channels[channelId] = channel
    
    def RemoveChannel(self, channelId):
        """
        Docstring to fill in later.
        """
        log.debug("Removing channel %s", channelId)
        
        del self.channels[channelId]

