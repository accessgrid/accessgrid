#-----------------------------------------------------------------------------
# Name:        EventClient.py
# Purpose:     This is the client side object for maintaining  in a
#               virtual venue via the event service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: EventClient.py,v 1.18 2003-05-22 20:15:47 olson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from threading import Thread
import Queue
import pickle
import logging
import struct

from pyGlobus.io import GSITCPSocket, TCPIOAttr, AuthData, IOBaseException
from pyGlobus.util import Buffer
from pyGlobus import ioc

from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.Events import HeartbeatEvent, ConnectEvent, DisconnectEvent
from AccessGrid.hosting.pyGlobus.Utilities import CreateTCPAttrAlwaysAuth

log = logging.getLogger("AG.VenueClient")
log.setLevel(logging.INFO)

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
        
        self.queue = Queue.Queue()

        self.qThread = Thread(target = self.queueThreadMain)
        self.qThread.start()

        attr = CreateTCPAttrAlwaysAuth()
        self.sock = GSITCPSocket()
        try:
            self.sock.connect(location[0], location[1], attr)
            self.connected = 1
        except:
            log.exception("Couldn't connect to event service.")
            raise EventClientConnectionException
        
        # self.rfile = self.sock.makefile('rb', -1)

    def __del__(self):
        log.debug("EventClient destructor")
        if self.running:
            self.Stop()
        
        log.debug("EventClient.del: closing queue")
        self.queue.put(("quit",))
        self.qThread.join()

    def queueThreadMain(self):
        print "In queue thread"

        while 1:
            log.debug("Queue waiting for data")
            dat = self.queue.get()
            log.debug("Queue got data %s", dat)
            if dat[0] == "quit":
                log.debug("Queue exiting")
                return
            elif dat[0] == "call":
                try:
                    dat[1](dat[2])
                except:
                    log.exception("callback invocation failed")

    def start(self):
        """
        Register for asynch io.
        """

        self.dataBuffer = ''
        self.waitingLen = 0
        
        h = self.sock.register_read(self.buffer, EventClient.bufsize, 1,
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
            
        h = self.sock.register_read(self.buffer, EventClient.bufsize, 1,
                                    self.readCallbackWrap, None)
        self.cbHandle = h

    def thr_run(self):
        """
        The run method starts this thread actively getting and
        processing event data provided by a EventService.
        """
        self.running = 1
        while self.running:
            event = None
            data = None
            try:
                data = self.rfile.read(4)
                log.debug("EventClient: DataSize: %d", len(data))
            except IOBaseException:
                data = None
                self.running = 0
                log.exception("EventClient: ReadDataException.")
                raise EventClientReadDataException

            if data != None and len(data) == 4:
                sizeTupe = struct.unpack('i', data)
                size = sizeTupe[0]
                log.debug("EventClient: Read size: %d", size)
            else:
                size = 0
                self.running = 0
                log.exception("EventClient: Connection Lost.")
                raise EventClientReadDataException
            
            # Read the data
            try:
                pdata = self.rfile.read(size)
                log.debug("EventClient: Read data.")
            except:
                self.running = 0
                log.exception("EventClient: Read data failed.")
                raise EventClientReadDataException

            self.handleData(pdata)

        self.sock.close()

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
                        self.queue.put(("call", callback, event.data))
                        print "FOOOO"
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
            self.sock.write(size, 4)
            self.sock.write(pdata, len(pdata))
        except:
            self.running = 0
            self.connected = 0
            self.sock.close()
            log.exception("EventClient.Send Error: socket write failed.")
            raise EventClientWriteDataException
        
    def Stop(self):
#         try:
#             self.Send(DisconnectEvent(self.channel, self.privateId))
#         except:
#             #
#             # This may well fail, if the server side has already disconnected us.
#             #
#             pass
        
        self.running = 0
        log.debug("EventClient.Stop: closing socket")
        self.sock.close()
        self.connected = 0

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
    # command line arguments are:
    # 1) host for event service
    # 2) port for event service
    # 3) channel for event service
    log.addHandler(logging.StreamHandler())
    log.setLevel(logging.DEBUG)
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
        port = int(sys.argv[2])
        channel = sys.argv[3]
    else:
        host = ''
        port = 6500
        channel = 'Test'
        
        eventClient = EventClient('privId', (host, port), channel)

    eventClient.Start()
    
    eventClient.Send(ConnectEvent(channel, 'privId'))
        
    for i in range(1,5):
        eventClient.Send(HeartbeatEvent(channel, "foo"))
        time.sleep(1)

    time.sleep(1)
    
#    eventClient.Stop()

    os._exit(0)
