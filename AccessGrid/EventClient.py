#-----------------------------------------------------------------------------
# Name:        EventClient.py
# Purpose:     This is the client side object for maintaining  in a
#               virtual venue via the event service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: EventClient.py,v 1.4 2003-02-14 20:43:32 olson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from threading import Thread
import socket
import string
import pickle

from pyGlobus.io import GSITCPSocket,TCPIOAttr,AuthData
from pyGlobus.util import Buffer
from pyGlobus import ioc

from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.Events import HeartbeatEvent
from AccessGrid.hosting.pyGlobus.Utilities import CreateTCPAttrAlwaysAuth
class EventClient(Thread):
    """
    The Event Client maintains a client side connection to the Event
    Service to maintain state among a set of clients. This is done by sending
    events through the event service.
    """
    bufsize = 128
    def __init__(self, location = ('localhost', 6500)):
        """
        The EventClient constructor takes a host, port.
        """
        # Standard initialization
        self.buffer = Buffer(EventClient.bufsize)
        self.location = location
        self.id = id
        self.callbacks = []
        Thread.__init__(self)
        
        attr = CreateTCPAttrAlwaysAuth()
        self.sock = GSITCPSocket()
        self.sock.connect(location[0], location[1], attr)
        self.rfile = self.sock.makefile('rb', -1)
        self.wfile = self.sock.makefile('wb', 0)

    def run(self):
        """
        The run method starts this thread actively getting and
        processing event data provided by a EventService.
        """
        self.running = 1
        while self.sock != None and self.running:
            try:
##                str = ""
##                while self.running:
##                    bytesRead = self.sock.try_read(self.buffer, 1)
##                    if bytesRead > 0:
##                        bString = self.buffer.as_string()
##                        if bString[0] == '\n':
##                            break
##                        else:
##                            str = str + bString[0]
##                    
##                # Read the size
##                if len(str) == 0:
##                    str = "0"
##                    
                str = self.rfile.readline()
                size = int(str)
                
                if size > 0:
                    # Then read the event
                    pdata = self.rfile.read(size)
                    
                    # Unpack the data
                    event = pickle.loads(pdata)
#                    print "Got Event: %s" % event.eventType
                    if self.running:
                        # Send it on its way
                        calls = []
                        for (evt, callback) in self.callbacks:
                            if evt == event.eventType:
                                calls.append(callback)
                        
                        if len(calls) != 0:
                            for callback in calls:
                                callback(event.data)
                        else:
                            print "No callback for %s!" % event.eventType
                            self.DefaultCallback(event)                            
                    else:
                        self.sock.close()
                        break
            except:
                print "Server closed connection!", formatExceptionInfo()
                self.sock.close()

    def Send(self, data):
        """
        This method sends data to the Event Service.
        """
        try:
            # Pickle the data
            pdata = pickle.dumps(data)
            size = "%d\n" % len(pdata)
            # Send the size on it's own line
            self.sock.write(size, len(size))
            # Then send the pickled data
            self.sock.write(pdata, len(pdata))
        except:
            (name, args, tb) = formatExceptionInfo()
            print "EventClient.Send Error: %s, %s" % (name, args)

    def Stop(self):
        self.running = 0

    def DefaultCallback(self, event):
        print "Got callback for %s event!" % event.eventType

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

if __name__ == "__main__":
    import sys
    # command line arguments are:
    # 1) host for event service
    # 2) port for event service
    if len(sys.argv) > 1:
        eventClient = EventClient(location = ( sys.argv[1], sys.argv[2]) )
    else:
        eventClient = EventClient()
    eventClient.start()
