#-----------------------------------------------------------------------------
# Name:        EventClient.py
# Purpose:     This is the client side object for maintaining  in a
#               virtual venue via the event service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: EventClient.py,v 1.45 2004-09-09 22:12:12 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: EventClient.py,v 1.45 2004-09-09 22:12:12 turam Exp $"
__docformat__ = "restructuredtext en"

import sys
from threading import Thread, Lock
import Queue
import pickle
import struct

from AccessGrid import Log
from pyGlobus.io import GSITCPSocket, TCPIOAttr, AuthData, IOBaseException
from pyGlobus.util import Buffer
from pyGlobus import ioc

from AccessGrid.Events import HeartbeatEvent, ConnectEvent, DisconnectEvent
from AccessGrid.Security.Utilities import CreateTCPAttrAlwaysAuth

log = Log.GetLogger(Log.EventClient)
Log.SetDefaultLevel(Log.EventClient, Log.DEBUG)

class EventClientConnectionException(Exception):
    """
    This exception is used to indicate a problem connecting to an
    Event Service.
    """
    pass

class EventClientReadDataException(Exception):
    """
    This exception is used to indicate a read error.

    This is usually thrown when an IOBaseException has occured on the
    underlying GSITCPSocket. It can also be thrown if the read succeeds,
    but the data resulting is bad.
    """
    pass

class EventClientWriteDataException(Exception):
    """
    This exception is used to indicate a write error.

    This is usually thrown when an IOBaseException has occured on the
    underlying GSITCPSocket.
    """
    pass

def readCallbackWrap(arg, handle, result, buf, n):
    log.debug("wrap: arg=%s", arg)
    obj = arg()
    if obj:
        log.debug("Got obj %s", obj)
        obj.readCallbackWrap(None, handle, result, buf, n)

class EventClient:
    """
    The Event Client maintains a client side connection to the Event
    Service to maintain state among a set of clients. This is done by sending
    events through the event service.
    """
    bufsize = 4096
    def __init__(self, privateId, location, channel):
        """
        The EventClient constructor takes a host, port.
        """
        # Standard initialization
        self.privateId = privateId
        self.channel = channel
        self.buffer = Buffer(EventClient.bufsize)
        self.location = location
        self.callbacks = []
        self.connected = 0
        self.cbHandle = None

        #
        # clientLock is used to ensure serialization between the
        # started/stopped state of the event client and
        # any asynchronously-received incoming events.
        #
        self.clientLock = Lock()
        
        self.queue = Queue.Queue()

        self.qThread = Thread(target = self.QueueThreadMain,
                              name = "EventClient.QueueThreadMain")
        self.qThread.start()

        attr = CreateTCPAttrAlwaysAuth()
        self.sock = GSITCPSocket()
        try:
            self.sock.connect(location[0], location[1], attr)
            self.connected = 1
        except:
            log.exception("Couldn't connect to event service.")
            raise EventClientConnectionException
        
    def __del__(self):
        if self.running:
            self.Stop()
        

    def QueueThreadMain(self):
        """
        Event processing thread.

        This thread blocks on a read from the client-local event queue
        (self.queue). Commands on the form are tuples where tuple[0]
        is the name of the command.

        Commands we process are

        quit:  Terminate the event processing thread.
        call:  Invoke a callback. The callback is tuple[1], the event to
        pass to it is tuple[2].

        """

        while 1:
#            log.debug("Queue waiting for data")
            dat = self.queue.get()
#            log.debug("Queue got data %s", dat)

            if dat[0] == "quit":
#                log.debug("Queue exiting")
                return
            elif dat[0] == "call":
                try:
                    #
                    # Invoke the callback.
                    #
                    
                    callback = dat[1]
                    event = dat[2]
                    callback(event)
                except:
                    log.exception("callback invocation failed")
                    
    def start(self):
        """
        Register for asynch io.
        """

        self.dataBuffer = ''
        self.waitingLen = 0

        self.running = 1

        # h = self.sock.register_read(self.buffer, EventClient.bufsize, 1,
        #                            readCallbackWrap, weakref.ref(self))
        h = self.sock.register_read(self.buffer, EventClient.bufsize, 1,
                                    self.readCallbackWrap, None)
        self.cbHandle = h
        log.debug("Have callback handle %s", self.cbHandle)

    def readCallbackWrap(self, arg, handle, result, buf, n):
        """
        Asynch read callback.

        We just use this to wrap the call to the readCallback itself,
        because the callback invocation mechanism silently ignores exceptions.
        """
        
        try:
            return self.readCallback(arg, handle, result, buf, n)
        except Exception:
            log.exception("readcallback failed")
                
    def readCallback(self, arg, handle, result, buf, n):

        log.debug("Got read handle=%s result=%s  n=%s \n", handle, result, n)

        if result[0] != 0:
            log.debug("readCallback gets failure in result: %s %s", result[0], result[1])
            try:
                self.sock.close()
            except IOBaseException:
                log.exception("IOBaseException while closing socket due to failure in read callback")

            self.connected = 0
            return
                

        if n == 0:
            log.debug("EventClient got EOF")
            try:
                self.sock.close()
            except IOBaseException:
                # we may get here because the socket was already closed
                log.exception("IOBaseException while closing socket due to failure in read callback")
            self.connected = 0
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
            log.debug("finally read enough data, wait=%s buflen=%s",
                      self.waitingLen, len(self.dataBuffer))

            thedata = self.dataBuffer[:self.waitingLen]
            self.dataBuffer = self.dataBuffer[self.waitingLen:]

            self.handleData(thedata)
            log.debug("handleData returns")

            self.waitingLen = 0

        if self.running:
            log.debug("Freeing callback %s within callback", self.cbHandle)
            if self.cbHandle:
                self.sock.free_callback(self.cbHandle)
                
            #h = self.sock.register_read(self.buffer, EventClient.bufsize, 1,
            #                            readCallbackWrap, weakref.ref(self))
            h = self.sock.register_read(self.buffer, EventClient.bufsize, 1,
                                        self.readCallbackWrap, None)
            self.cbHandle = h
            log.debug("Have new callback handle %s", self.cbHandle)
        
    def handleData(self, pdata):
        try:
            # Unpack the data
            event = pickle.loads(pdata)

            # Invoke registered callbacks
            calls = []
            for (evt, callback) in self.callbacks:
                if evt == event.eventType:
                    calls.append(callback)

            if len(calls) != 0:
                for callback in calls:
                    log.debug("Invoking callback %s...", callback)
                    try:
                        #callback(event.data)
                        self.queue.put(("call", callback, event))
                    except:
                        log.exception("Callback fails")
                    log.debug("Invoking callback %s...done", callback)
                else:
                    log.info("No callback for %s!", event.eventType)
                    self.DefaultCallback(event)
        except ImportError:
            exc, value = sys.exc_info()[:2]
            valueStrList = str(value).lower().split()
            first_words = valueStrList[:2]
            module_name = valueStrList[-1:]
            if first_words == ['no', 'module'] and module_name == ['pyglobus.aggsisoap']:
                log.warning("handleData unable to import pyGlobus.AGGSISOAP")
            else:
                log.exception("handleData failed due to ImportError")
        except:
            log.exception("handleData failed")

    def Send(self, data):
        """
        This method sends data to the Event Service.
        """
        # log.info("Sending data: %s", data)
        if not self.connected:
            log.error("Attempting to send on a disconnected EventClient")
            raise EventClientWriteDataException
        try:
            pdata = pickle.dumps(data)
            size = struct.pack("<i", len(pdata))
            self.sock.write(size, 4)
            self.sock.write(pdata, len(pdata))
        except:
# tdu - Don't disconnect the event client just because a
#       send failed
#             self.running = 0
#             self.connected = 0
#             try:
#                 self.sock.close()
#             except IOBaseException:
#                 pass
            log.exception("EventClient.Send Error: socket write failed.")
            raise EventClientWriteDataException
        
    def Stop(self):
        self.running = 0

        log.debug("Cancel pending callbacks")
        try:
            self.sock.cancel(1)
        except IOBaseException:
            pass
        if self.cbHandle:
            log.debug("Free callback %s", self.cbHandle)
            try:
                self.sock.free_callback(self.cbHandle)
            except ValueError:
                log.exception("EventClient.Stop: callback already gone.")
        
        log.debug("EventClient.Stop: closing socket")
        try:
            self.sock.close()
        except IOBaseException:
            pass
        
        self.connected = 0

        log.debug("EventClient.Stop: closing queue")
        self.queue.put(("quit",))
        self.qThread.join()
        self.qThread = None

    def DefaultCallback(self, event):
        log.info("Got callback for %s event!", event.eventType)

    def RegisterCallback(self, eventType, callback):
        # Callbacks just take the event data as the argument
        self.callbacks.append((eventType, callback))

    def RegisterObject(self, object):
        """
        RegisterObject is short hand for registering multiple callbacks on the
        same object. The object being registered has to define a table named
        callbacks that has event types as keys, and self.methods as values.
        Then these are automatically registered.
        """
        for c in object.callbacks.keys():
            self.RegisterCallback(c, object.callbacks[c])

    def Start(self):
        self.start()
        
if __name__ == "__main__":
    import os, time
    from AccessGrid import Toolkit
    from AccessGrid import ClientProfile
    from AccessGrid.GUID import GUID

    host = ''
    port = 6500
    channel = "Test"
    count = 10
    last_one = 0
    
    app = Toolkit.CmdlineApplication()
    try:
        app.Initialize("EventClient-Main")
    except:
        print "Toolkit initialization failed."
        sys.exit(-1)

    if len(sys.argv) > 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
        channel = sys.argv[3]
        count = int(sys.argv[4])
    elif len(sys.argv) > 2:
        channel = sys.argv[1]
        count = int(sys.argv[2])
    elif len(sys.argv) == 2:
        count = int(sys.argv[1])

    privId = str(GUID())
    eventClient = EventClient(privId, (host, port), channel)
    eventClient.Start()
    
    eventClient.Send(ConnectEvent(channel, privId))
        
    for i in range(1,count):
        print "sending heartbeat %d" % i
        eventClient.Send(HeartbeatEvent(channel, "%s -- %d" % (privId, i)))
#        time.sleep(1)

    eventClient.Stop()
