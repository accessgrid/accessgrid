#-----------------------------------------------------------------------------
# Name:        EventClient.py
# Purpose:     This is the client side object for maintaining  in a
#               virtual venue via the event service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: EventClient.py,v 1.30 2003-09-25 20:50:18 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: EventClient.py,v 1.30 2003-09-25 20:50:18 judson Exp $"
__docformat__ = "restructuredtext en"

from threading import Thread, Lock
import Queue
import pickle
import logging
import struct
import types

from pyGlobus.io import GSITCPSocket, TCPIOAttr, AuthData, IOBaseException
from pyGlobus.util import Buffer
from pyGlobus import ioc

from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.Events import HeartbeatEvent, ConnectEvent, DisconnectEvent
from AccessGrid.hosting.pyGlobus.Utilities import CreateTCPAttrAlwaysAuth

log = logging.getLogger("AG.VenueClient")
log.setLevel(logging.DEBUG)

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

def readCallbackWrap(arg, handle, ret, buf, n):
    log.debug("wrap: arg=%s", arg)
    obj = arg()
    if obj:
        log.debug("Got obj %s", obj)
        obj.readCallbackWrap(None, handle, ret, buf, n)

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

        self.qThread = Thread(target = self.queueThreadMain)
        self.qThread.start()

        self.lock = Lock()

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
        

    def queueThreadMain(self):
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

    def readCallbackWrap(self, arg, handle, ret, buf, n):
        """
        Asynch read callback.

        We just use this to wrap the call to the readCallback itself,
        because the callback invocation mechanism silently ignores exceptions.
        """
        
        try:
            return self.readCallback(arg, handle, ret, buf, n)
        except Exception:
            log.exception("readcallback failed")
                
    def readCallback(self, arg, handle, ret, buf, n):

        log.debug("Got read handle=%s ret=%s  n=%s \n", handle, ret, n)

        #
        # Check for new-style status returns
        # 

        if type(ret) == types.TupleType:
            if ret[0] != 0:
                log.debug("readCallback gets failure in result: %s %s", ret[1], ret[2])
                try:
                    self.sock.close()
                except IOBaseException:
                    pass

                self.connected = 0
                return
                

        if n == 0:
            log.debug("EventClient got EOF")
            try:
                self.sock.close()
            except IOBaseException:
                # we may get here because the socket was already closed
                pass
            self.connected = 0
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
            size = struct.pack("i", len(pdata))
            self.lock.acquire()
            self.sock.write(size, 4)
            self.sock.write(pdata, len(pdata))
            self.lock.release()
        except:
            self.running = 0
            self.connected = 0
            try:
                self.sock.close()
            except IOBaseException:
                pass
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
    import sys, os, time
    from AccessGrid import Toolkit
    from AccessGrid import ClientProfile
    from AccessGrid.GUID import GUID

    host = ''
    port = 6500
    channel = "Test"
    count = 10
    last_one = 0
    
    app = Toolkit.CmdlineApplication()
    app.Initialize()
    app.InitGlobusEnvironment()

    certMgr = app.GetCertificateManager()
    if not certMgr.HaveValidProxy():
        certMgr.CreateProxy()

    log = logging.getLogger("AG.TextClient")
    log.addHandler(logging.StreamHandler())
    log.setLevel(logging.DEBUG)
    
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
