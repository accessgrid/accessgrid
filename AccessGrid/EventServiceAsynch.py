#-----------------------------------------------------------------------------
# Name:        EventServiceAsynch.py
# Purpose:     This service provides events among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson, Robert D. Olson
#
# Created:     2003/05/19
# RCS-ID:      $Id: EventServiceAsynch.py,v 1.34 2004-07-15 20:23:08 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: EventServiceAsynch.py,v 1.34 2004-07-15 20:23:08 turam Exp $"
__docformat__ = "restructuredtext en"

import sys
import pickle
import struct
import Queue
import threading
import time

from pyGlobus.io import GSITCPSocket
from pyGlobus.io import IOBaseException
from pyGlobus.util import Buffer
from pyGlobus import ioc, io

from AccessGrid import Log
from AccessGrid.Security.Utilities import CreateTCPAttrAlwaysAuth
from AccessGrid.Events import ConnectEvent, DisconnectEvent, MarshalledEvent
from AccessGrid.Events import Event, AddPersonalDataEvent
from AccessGrid.Events import RemovePersonalDataEvent, UpdatePersonalDataEvent
from AccessGrid.Events import AddDataEvent, RemoveDataEvent, UpdateDataEvent
from AccessGrid.Security.Utilities import CreateSubjectFromGSIContext
from AccessGrid.GUID import GUID

log = Log.GetLogger(Log.EventService)
Log.SetDefaultLevel(Log.EventService, Log.DEBUG)


class ConnectionRecord:
    def __init__(self,conn):
        self.connObj = conn
        self.start = time.time()
        
    def GetStart(self):
        return self.start


class ConnectionMonitor:

    def __init__(self, timeout):
        self.timeout = timeout
        
        self.connectionList = []
        
        self.listModLock = threading.Lock()
        
        self.running = threading.Event()
        self.running.clear()
        
        
    def Run(self):
        """
        Main loop for connection monitor
        Periodically check connections being monitored,
        closing them if they have timed out
        """
        log.debug("STARTING ConnectionMonitor.Run")
        self.running.set()
        while self.running.isSet():
            try:
                self.listModLock.acquire()
                now = time.time()
                index = 0
                while index < len(self.connectionList):
                    conn = self.connectionList[index]
                    tm = now - conn.GetStart()
                    log.debug( "ConnectionMonitor: conn,tm,timeout =%s %f %f", conn.connObj,tm,self.timeout)
                    if  tm > self.timeout:
                        log.info("Connection being terminated by connection monitor")
                        try:
                            conn.connObj.handleEOF()
                        except:
                            log.exception("ConnectionMonitor: Exception removing connection from list")
                        del self.connectionList[index]
                        continue
                    
                    index += 1
                        
                        
            except:
                log.exception("Exception in connection monitor")
               
            self.listModLock.release()
            
            # Sleep until it's time to check again
            time.sleep(self.timeout)
            
        log.debug("EXITING ConnectionMonitor.Run")
                
        
    def Start(self):
        """
        Start the connection monitor
        """
        threading.Thread(target=self.Run,name="ConnectionMonitor.Run").start()
        
    def Stop(self):
        self.running.clear()
        
    def AddConnection(self,connObj):
        """
        Add connection to list of connections to monitor
        """
        self.listModLock.acquire()
        try:
            c = ConnectionRecord(connObj)
            log.debug("ConnectionMonitor: Adding connection: %s start=%s", connObj, str(c.GetStart()))
            self.connectionList.append(c)
        except:
            log.exception("Error adding to connection list")
        self.listModLock.release()
        
    def RemoveConnection(self,connObj):
        """
        Remove connection from list of connections to monitor
        """
        self.listModLock.acquire()
        try:
            for conn in self.connectionList:
                if conn.connObj == connObj:
                    connTime = time.time()-conn.GetStart()
                    log.debug("ConnectionMonitor: Removing connection: %s duration=%s", connObj,str(connTime ))
                    self.connectionList.remove(conn)
                    break
        except:
            log.exception("Error removing from connection list")
        self.listModLock.release()
        
        

class ConnectionHandler:
    """
    The ConnectionHandler is the object that handles a single event
    connection. The ConnectionHandler gets events from the client then
    passes them to registered callback functions based on event.eventType.
    """

    def __init__(self, lsocket, eservice):
        self.id = str(GUID())
        self.lsocket = lsocket
        self.server = eservice
        self.wfile = None

	self.sender = "Not Connected"

        self.dataBuffer = ''
        self.bufsize = 4096
        self.buffer= Buffer(self.bufsize)
        self.waitingLen = 0

    def __del__(self):
        log.debug("EventServiceAsynch: ConnectionHandler delete")

    def GetId(self):
        return self.id 


    def registerAccept(self, attr):
        log.info("EventServiceAsynch: conn handler registering accept")

        socket, cb = self.lsocket.register_accept(attr, self.acceptCallback,
                                                  None)
        self.acceptCallbackHandle = cb
        
        log.info("EventServiceAsynch: register_accept returns socket=%s cb=%s", socket, cb)
        self.socket = socket

    def acceptCallback(self, arg, handle, result):
        try:
            if result[0] != 0:
                log.debug("EventServiceAsynch: acceptCallback returned failure: %d %s", result[0], result[1])
                self.server.registerForListen()
                return

            log.info("EventServiceAsynch: Accept Callback '%s' '%s' '%s'",
                     arg, handle, result)
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
        h = self.socket.register_read(self.buffer, self.bufsize, 1,
                                      self.readCallbackWrap, None)
        self.cbHandle = h

    def readCallbackWrap(self, arg, handle, result, buf, n):
        """
        Asynch read callback.

        We just use this to wrap the call to the readCallback itself,
        because the callback invocation mechanism silently ignores exceptions.
        """
        
        try:
            self.socket.free_callback(self.cbHandle)
            return self.readCallback(arg, handle, result, buf, n)
        except:
            log.exception("readcallback failed")
            return None

    def writeMarshalledEvent(self, mEvent):
        """
        Write this packet to the network.
        If the write fails for some reason, return 0.
        Otherwise, return 1.
        """

	if self.wfile is not None:        
	    try:
                self.server.connectionMonitor.AddConnection(self)
                mEvent.Write(self.wfile)
                #time.sleep(12)
                self.server.connectionMonitor.RemoveConnection(self)
                return 1
            except:
                self.server.connectionMonitor.RemoveConnection(self)
                log.exception("writeMarshalledEvent write error!")
        else:
	    log.info("not sending event, conn obj is none.")

	return 0

    def readCallback(self, arg, handle, result, buf, n):

        log.info("EventServiceAsynch: Got read handle=%s result=%s  n=%s waiting=%s\n",
                 handle, result, n, self.waitingLen)

        if result[0] != 0:
            log.debug("EventServiceAsynch: readCallback returned failure: %s %s", result[0], result[1])
            self.handleEOF()
            return

        if n == 0:
            self.handleEOF()
            return

        dstr = str(buf)
        self.dataBuffer += dstr

        if self.waitingLen == 0:

            sz = struct.calcsize('<i')
            
            if len(self.dataBuffer) < sz:
                return

            lenstr = self.dataBuffer[:sz]
            dlen = struct.unpack('<i', lenstr)

            self.dataBuffer = self.dataBuffer[sz:]

            self.waitingLen = dlen[0]

        if len(self.dataBuffer) >= self.waitingLen:
            log.info("EventServiceAsynch: Finished reading packet, wait=%s buflen=%s",
                      self.waitingLen, len(self.dataBuffer))

            thedata = self.dataBuffer[:self.waitingLen]
            self.dataBuffer = self.dataBuffer[self.waitingLen:]

            self.handleData(thedata, None)

            self.waitingLen = 0

        self.registerForRead()
        
    def stop(self):
        try:
            if self.wfile is not None:
                self.wfile.close()
            self.socket.close()
        except IOBaseException:
            log.info("EventServiceAsynch: IOBase exception on event service close (probably ok)")

    def handleData(self, pdata, event):
        """
        We have successfully read a data packet.

        """
        
        # Unpickle the event data
        if event == None:
            try:
                event = pickle.loads(pdata)
            except EOFError:
                log.debug("EventServiceAsynch: unpickle got EOF.")
                self.handleEOF()
                return

        log.info("EventServiceAsynch: EventConnection: Received event %s", event)

        #
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

class EventChannel:
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
        log.debug("EventServiceAsynch: Delete EventChannel %s", self.id)

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
            log.info("EventServiceAsynch: Callback %s already in handler list for type %s",
                     callback, eventType)
        else:
            cbList.append(callback)

    def RegisterChannelCallback(self, callback):
        """
        Register callback as a handler for all events on this channel.
        """

        if callback in self.channelHandlers:
            log.info("EventServiceAsynch: Callback %s already in channel handler list", callback)
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

        log.debug("EventServiceAsynch: Attempting authorization on event %s", event.eventType)


        if event.eventType != ConnectEvent.CONNECT:
            log.debug("EventServiceAsynch: Channel refusing authorization, %s is not a connect event",
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
                log.debug("EventServiceAsynch: Auth callback %s returns %s", self.authCallback,
                          authorized)
            except:
                log.exception("EventServiceAsynch: Authorization callback failed")
                authorized = 0
        else:
            log.debug("EventServiceAsynch: Default authorization (no callback registered)")
            authorized = 1
        return authorized

    def HandleEvent(self, event, connObj):
        """
        Handle an incoming event from connObj.
        """

        if event.eventType == DisconnectEvent.DISCONNECT:

            log.debug("EventServiceAsynch: EventConnection: Removing client connection to %s",
                      event.venue)
            self.RemoveConnection(connObj)
            self.server.CloseConnection(connObj)

        # Pass this event to the callback registered for this
        # event.eventType
        if self.typedHandlers.has_key(event.eventType):
            for cb in self.typedHandlers[event.eventType]:
                log.debug("EventServiceAsynch: Specific event callback=%s", cb)
                if cb != None:
                    log.info("EventServiceAsynch: invoke callback %s", str(cb))
                    try:
                        cb(event)
                    except:
                        log.exception("Event callback failed")

        for cb in self.channelHandlers:
            log.debug("EventServiceAsynch: invoke channel callback %s", cb)
            try:
                cb(event)
            except:
                log.exception("Event callback failed")

        log.info("EventServiceAsynch: HandleEvent returns")


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
            success = c.writeMarshalledEvent(me)
            if not success:
                removeList.append(c)
        #
        # These guys failed. Bag 'em.
        #

        for r in removeList:
            log.debug("EventServiceAsynch: Removing connection %s due to write error", r.GetId())
            self.RemoveConnection(r)

    def RemoveConnection(self, connObj):
        if connObj.GetId() in self.connections:
            del self.connections[connObj.GetId()]
        else:
            log.error("RemoveConnection: connection %s not in connection list",
                      connObj.GetId())

    def AddConnection(self, event, connObj):
        self.connections[connObj.GetId()] = connObj


    def GetId(self):
        return self.id

class EventService:
    """
    The EventService provides a secure event layer. This might be more 
    scalable as a secure RTP or other UDP solution, but for now we use TCP.
    In the TCP case the EventService is the Server, GSI is our secure version.
    """
    def __init__(self, server_address):
        log.debug("EventServiceAsynch: Event Service Started")
        
        self.location = server_address

        # self.channels is a dictionary keyed on the channel id
        #
        # self.connectionMap is a dict keyed on the ConnectionHandler
        # id (assigned when the connection comes in). The value is
        # the EventChannel that the connection is registered with, or
        # None if it is not (yet) registered.
        #
        # self.allConnections is a list of all the active connections
        # that we know about.
        self.channels = {}
        self.connectionMap = {}
        self.allConnections = []

        # The socket we're listening on.
        self.socket = GSITCPSocket()
        self.socket.allow_reuse_address = 1
        self.attr = CreateTCPAttrAlwaysAuth()

        # Our incoming message queue. We don't handle messages
        # in the asynch IO threads, in order that they don't block
        # on the Globus side.
        self.outQueue = Queue.Queue()
	self.outQEvt = threading.Event()
	self.outQEvt.set()
        self.outQThread = threading.Thread(target = self.RecvHandler, 
				name = "EventService Recieve Queue Handler")
        self.outQThread.start()

	# Create a queue and thread to distribute events asynchronously
	# This alleviates proportional calls (to the number of clients)
	self.inQueue = Queue.Queue()
	self.inQEvt = threading.Event()
	self.inQEvt.set()
	self.inQThread = threading.Thread(target = self.SendHandler,
				name = "EventService Send Queue Handler")
	self.inQThread.start()

        # Initialize socket for listening.
        port = self.socket.create_listener(self.attr, server_address[1])
        log.debug("EventServiceAsynch: Bound to %s (server_address=%s)", port, server_address)
        
        
        self.connectionMonitor = ConnectionMonitor(2)
        self.connectionMonitor.Start()

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

        log.debug("EventServiceAsynch: Event service start")
        self.registerForListen()

    def registerForListen(self):
        ret = self.socket.register_listen(self.listenCallback, None)
        self.listenCallbackHandle = ret
        log.info("EventServiceAsynch: register_listen returns '%s'", ret)

    def listenCallback(self, arg, handle, result):
        try:
            if result[0] != 0:
                log.debug("EventServiceAsynch: listenCallback returned failure: %d %s", result[0], result[1])
                self.registerForListen()
                return
            
            log.info("EventServiceAsynch: Listen Callback '%s' '%s' '%s'", arg, handle, result)
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

        log.debug("EventServiceAsynch: Removing connection %s", cid)
        connObj.stop()

        channel = self.findConnectionChannel(cid)
        if channel is not None:
            log.debug("EventServiceAsynch: Removing connection %s from channel %s", cid, channel.GetId())
            channel.RemoveConnection(connObj)
        try:
            self.allConnections.remove(connObj)
        except ValueError:
            #
            # We can get this if we lose the race on a shutdown.
            #
            pass
        
    def SendHandler(self):
	log.info("Entering SendHandler")

	try:
	    while self.inQEvt.isSet():
		try:
		    (channel, data) = self.inQueue.get()
                    if channel == 'quit':
                        self.inQEvt.clear()
                        break
		except Queue.Empty:
		    log.info("Didn't get anything to distribute.")
		    data = None
	
		if data is not None:
                    log.info("Calling _Distribute, in SendHandler.")
                    self._Distribute(channel, data)         
	except:
	    log.exception("Body of event distribution queue handler threw.")

	log.info("Exiting SendHandler")

    def Stop(self):
        """
        Stop the event service.

        Close our listener socket and all the active connections; this should
        clear out any lingering state.
        """
        
        log.debug("EventServiceAsynch: Stopping")

        try:
            self.socket.close()
        except IOBaseException:
            log.exception("EventServiceAsynch: socket close failed")
            pass
        
        self.EnqueueQuit()
        self.inQueue.put(("quit",))

        for c in self.allConnections:
            c.stop()
        self.allConnections = []
        
        for ch in self.channels.keys():
            self.RemoveChannel(ch)
            
	self.outQEvt.clear()
	self.inQEvt.clear()
        
        self.connectionMonitor.Stop()

    def EnqueueQuit(self):
        self.outQueue.put(("quit",))
        
    def EnqueueEvent(self, event, conn):
        log.info("EventServiceAsynch: Enqueue event %s for %s...", event.eventType, conn)
        self.outQueue.put(("event", event, conn))

    def EnqueueEOF(self, conn):
        log.info("EventServiceAsynch: Enqueue EOF for %s...", conn)
        self.outQueue.put(("eof", conn))

    def RecvHandler(self):
        """
        Thread main routine for event queue handling.
        """

        while self.outQEvt.isSet():
            try:
                log.info("EventServiceAsynch: recv handler waiting for data")
                cmd = self.outQueue.get()
                log.info("EventServiceAsynch: recv handler received %s", cmd)
                if cmd[0] == "quit":
                    log.debug("EventServiceAsynch: recv handler exiting")
                    return
                elif cmd[0] == "eof":
                    connObj = cmd[1]
                    log.debug("EventServiceAsynch: recv handler got EOF %s", 
			      connObj.GetId())
                    self.HandleEOF(connObj)
                elif cmd[0] == "event":

                    try:
                        event = cmd[1]
                        connObj = cmd[2]
                        self.HandleEvent(event, connObj)
                    except:
                        log.exception("recv handler threw an exception")

                else:
                    log.error("QueueHandler received unknown command %s", cmd[0])
                    continue

            except:
                log.exception("Body of QueueHandler threw exception")

    def HandleEvent(self, event, connObj):
        """
        Handle an incoming event.

        This is executed in the message handling thread after an event
        has been received by the async reader.

        Exactly what happens with this event depends on whether
        the connection object has been connected to a channel or not.

        If it has not, the only events that will be processed are Connect
        and Disconnect.

        If it has, the event is passed along to the EventChannel for
        processing.

        """

        connId = connObj.GetId()

        connChannel = self.findConnectionChannel(connId)

        if connChannel is None:
            self.HandleEventForDisconnectedChannel(event, connObj)
        else:
            if event.eventType == AddDataEvent.ADD_DATA:
                log.debug("EventServiceAsynch: ConnectionHandlet: ADD_DATA, venue id: %s, data: %s",
                          event.venue, event.data)

                #if self.channel != None:
                self.Distribute(event.venue,
                                Event( Event.ADD_DATA,
                                       event.venue,
                                       event.data))

                
            elif event.eventType == UpdateDataEvent.UPDATE_DATA:
                log.debug("EventServiceAsynch: ConnectionHandlet: UPDATE_DATA, venue id: %s, data: %s",
                          event.venue, event.data)

                #if self.channel != None:
              
                self.Distribute(event.venue,
                                Event( Event.UPDATE_DATA,
                                       event.venue,
                                       event.data))

              
            elif event.eventType == RemoveDataEvent.REMOVE_DATA:
                log.debug("EventServiceAsynch: EventService.ConnectionHandlet: REMOVE_DATA, venue id: %s, data: %s",
                          event.venue, event.data)

                #if self.channel != None:
                self.Distribute(event.venue,
                                Event( Event.REMOVE_DATA,
                                       event.venue,
                                       event.data))
                         
            #else:
                #print 'the event does not exist'

            connChannel.HandleEvent(event, connObj)

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

        if connChannel:
            log.debug("EventServiceAsynch: EventConnection: Removing client connection to %s",
                  connChannel.id)
            connChannel.RemoveConnection(connObj)
        else:
            log.debug("EventServiceAsynch: EOF on connection that doesn't belong to a channel")

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
            log.info("EventServiceAsynch: EventService receives event type %s for nonexistent channel %s",
                     event.eventType, event.venue)
            self.CloseConnection(connObj)
            return
        
        allowed = channel.AuthorizeNewConnection(event, connObj)

        if allowed:
            log.debug("EventServiceAsynch: Adding connObj %s to channel %s", connObj.GetId(),
                      event.venue)
            channel.AddConnection(event, connObj)
            self.connectionMap[connObj.GetId()] = channel

        else:
            log.debug("EventServiceAsynch: Rejected adding connObj %s to channel %s", connObj.GetId(),
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
            
    def Distribute(self, channelId, data):
	log.info("Calling Distribute")
	self.inQueue.put((channelId, data))

    def _Distribute(self, channelId, data):
        """
        Distribute sends the data to all connections.
        """

        log.info("EventServiceAsynch: _Distributing Event %s", data)

        channel = self.GetChannel(channelId)

        if channel is None:
            log.error("Distribute invoked on nonexistent channel %s", channelId)
            return

        channel.Distribute(data)
        log.info("EventServiceAsynch: Sent Event ")
            
    def GetLocation(self):
        """
        GetLocation returns the (host,port) for this service.
        """
        log.debug("EventServiceAsynch: GetLocation")
        
        return self.location

    def AddChannel(self, channelId, authCallback = None):
        """
        This adds a new channel to the Event Service.
        """
        log.debug("EventServiceAsynch: AddChannel %s", channelId)

        if self.GetChannel(channelId) is not None:
            log.info("EventServiceAsynch: Channel %s already exists", channelId)
            return

        channel = EventChannel(self, channelId, authCallback)
        self.channels[channelId] = channel

    def RemoveChannel(self, channelId):
        """
        This removes a channel from the Event Service.
        """
        log.debug("EventServiceAsynch: Remove Channel %s", channelId)

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
  level_hdlr = Log.HandleLoggers(hdlr)

  port = 6500
  print "Creating new EventService at %d." % port
  eventService = EventService(('', port))
  eventService.AddChannel('Test')
  eventService.start()
