#-----------------------------------------------------------------------------
# Name:        CoherenceClient.py
# Purpose:     This is the client side object for maintaining coherence in a 
#               virtual venue via the coherence service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CoherenceClient.py,v 1.14 2003-01-27 20:57:33 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from threading import Thread
import socket
import string
import pickle

from pyGlobus.io import GSITCPSocket,TCPIOAttr,AuthData
from pyGlobus import ioc

from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.Types import Event

class CoherenceClient(Thread):
    """
    The Coherence Client maintains a client side connection to the Coherence
    Service to maintain state among a set of clients. This is done by sending
    coherence events through the event service.
    """
    rbufsize = -1
    wbufsize = 0
    
    def __init__(self, host = 'localhost', port = 6500, 
                 callback = None, id = ''):
        """
        The CoherenceClient constructor takes a host, port and a
        callback for coherence data.
        """
        # Standard initialization

        Thread.__init__(self)
        self.host = host
        self.port = port
        self.id = id
        if callback == None:
            self.callback = self.__TestCallback
        else:
            self.callback = callback
            
        # Setup socket stuff
        self.__SetupSocket(host, port)
        
        # Start the heartbeat thread
        self.heartbeat = Heartbeat(self, 10)
        self.heartbeat.start()
        
    def __SetupSocket(self, host, port):
        """
        __setupSocket is a private method used to consolidate socket
        initialization code so that it can be easily modified without having
        to delve into the rest of the coherence client implementation.
        """        
        attr = TCPIOAttr()
        attr.set_authentication_mode(ioc.GLOBUS_IO_SECURE_AUTHENTICATION_MODE_GSSAPI)
        authData = AuthData()
        attr.set_authorization_mode(ioc.GLOBUS_IO_SECURE_AUTHORIZATION_MODE_SELF, authData)
        attr.set_channel_mode(ioc.GLOBUS_IO_SECURE_CHANNEL_MODE_GSI_WRAP)
        attr.set_delegation_mode(ioc.GLOBUS_IO_SECURE_DELEGATION_MODE_LIMITED_PROXY)
        self.sock = GSITCPSocket()
        self.sock.connect(host, port, attr)
            
        # Open the socket part
        #self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.sock.connect((host, port))
        
        # Some cool trick for IO from SocketServer.py
        self.rfile = self.sock.makefile('rb', self.rbufsize)
        self.wfile = self.sock.makefile('wb', self.wbufsize)
        
    def run(self):
        """
        The run method starts this thread actively getting and
        processing Coherence data provided by a CoherenceService.
        """
        self.running = 1
        while self.sock != None and self.running:
            try:
                # Read the size
                size = self.rfile.readline()
                # Then read the event
                pdata = self.rfile.read(int(size))
                # Unpack the data
                event = pickle.loads(pdata)
                # Send it on its way
                self.callback(event)

            except:
                print "Server closed connection!", formatExceptionInfo()
                self.sock.close()
                self.heartbeat.stop()

    def send(self, data):
        """
        This method sends data to the Coherence Service.
        """
        if self.sock != None:
            # Pickle the data
            pdata = pickle.dumps(data)
            # Send the size on it's own line
            self.wfile.write("%s\n" % len(pdata))
            # Then send the pickled data
            self.wfile.write(pdata)
         
    def __TestCallback(self, event):
        """
        The __TestCallback method is used to test the CoherenceService, it
        simply prints out Coherence Events received over the CoherenceService.
        This is kept private since it really isn't for general use.
        """
        print "Got Event: ", event.eventType, "Data: " + event.data

    def stop(self):
        self.running = 0

    
class Heartbeat(Thread):
    """
    This class is derived from Thread and provides the CoherenceClient with a
    constant periodic heartbeat sent to the Virtual Venue.
    """
    def __init__(self, coherenceClient = None, period = 15):
        """
        The constructor takes the CoherenceClient and the number of seconds
        between heartbeats. The default period for heartbeats is 15 seconds.
        """
        Thread.__init__(self)
        self.client = coherenceClient
        self.period = period
        self.running = 0

    def run(self):
        """
        The run method starts the thread looping sending a heartbeat then
        sleeping until the next time.
        """
        import time
        self.running = 1
        while self.running:
            data = "%s-%s" % (self.client.id,
                              string.join(map(str, time.localtime()), ':'))
            self.client.send(Event(Event.HEARTBEAT, data))
            time.sleep(self.period)
            
    def stop(self):
        """ This method stops the VenueClientHeartbeat."""
        self.running = 0
        
if __name__ == "__main__":
    import sys
    # command line arguments are: 
    # 1) host to connect to (we'll use the default port)
    # 2) a unique identifier for this coherenceclient
    coherenceClient = CoherenceClient(host = sys.argv[1], id = sys.argv[2])
    coherenceClient.start()