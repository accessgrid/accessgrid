#-----------------------------------------------------------------------------
# Name:        EventClient.py
# Purpose:     This is the client side object for maintaining  in a
#               virtual venue via the event service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: EventClient.py,v 1.14 2003-04-26 06:43:09 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from threading import Thread
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

class EventClientConnectionException(Exception):
    """
    This exception is used to indicate a problem connecting to an
    Event Service.
    """
    pass

class EventClient(Thread):
    """
    The Event Client maintains a client side connection to the Event
    Service to maintain state among a set of clients. This is done by sending
    events through the event service.
    """
    bufsize = 128
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
        Thread.__init__(self)
        
        attr = CreateTCPAttrAlwaysAuth()
        self.sock = GSITCPSocket()
        try:
            self.sock.connect(location[0], location[1], attr)
        except:
            log.exception("Couldn't connect to event service.")
            raise EventClientConnectionException
        
        self.rfile = self.sock.makefile('rb', -1)

    def run(self):
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
                log.debug("EventClient: Connection Lost.")
                continue

            if data != None and len(data) == 4:
                sizeTupe = struct.unpack('i', data)
                size = sizeTupe[0]
                log.debug("EventClient: Read size: %d", size)
            else:
                size = 0
                self.running = 0
                log.debug("EventClient: Connection Lost.")
                continue
            
            # Read the data
            try:
                pdata = self.rfile.read(size)
                log.debug("EventClient: Read data.")
            except:
                log.debug("EventClient: Read data failed.")
                self.running = 0
                continue

            # Unpack the data
            event = pickle.loads(pdata)

            # Invoke registered callbacks
            calls = []
            for (evt, callback) in self.callbacks:
                if evt == event.eventType:
                    calls.append(callback)
                    
                    if len(calls) != 0:
                        for callback in calls:
                            callback(event.data)
                        else:
                            log.info("No callback for %s!", event.eventType)
                            self.DefaultCallback(event)

        self.sock.close()

    def Send(self, data):
        """
        This method sends data to the Event Service.
        """
        log.info("Sending data: %s", data)
        
        try:
            pdata = pickle.dumps(data)
            size = struct.pack("i", len(pdata))
            self.sock.write(size, 4)
            self.sock.write(pdata, len(pdata))
        except:
            self.running = 0
            log.exception("EventClient.Send Error.")
            
    def Stop(self):
        self.running = 0

        self.Send(DisconnectEvent(self.channel, self.privateId))

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
