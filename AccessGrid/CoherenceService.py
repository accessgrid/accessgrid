#-----------------------------------------------------------------------------
# Name:        CoherenceService.py
# Purpose:     This service provides coherence among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CoherenceService.py,v 1.9 2003-01-17 16:56:05 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket
import select
import sys
import time
import struct
import pickle
from threading import Thread

from NetworkLocation import UnicastNetworkLocation

class ConnectionHandler(Thread):
    """
    ConnectionHandler class is a thread-derived class that is
    responsible for handling a coherence client connection.
    """
    def __init__(self, server, connection, address):
        """
        The ConnectionHandler constructor maintains a smalls set of
        state for keeping a connection alive to a specific
        coherenceclient.
        """
        Thread.__init__(self)
        self.server = server
        self.connection = connection
        self.address = address
        self.running = 0
        
    def stop(self):
        """
        stop stops the coherence service.
        """
        self.running = 0

    def send(self, data):
        """
        send sends data do the coherence client at the other end of
        this connection handler.
        """
        self.connection.send(data)
        
    def run(self):
        """
        run is the overloaded Thread.run which starts this connection handler.
        """
        self.running = 1
        while(self.running == 1):
            try:
                data = self.connection.recv(1024)
            except:
                self.connection.close()
                self.running = 0
            if not data: break 
            self.server.distribute(data)
        self.connection.close()
        sys.stderr.write("Connection Handler Exiting\n")
        
class AcceptHandler(Thread):
    """
    The AcceptHandler is a thread based object to handle the TCP
    socket connection acceptance. This makes it possible to have a
    simple service that handles the entire connection accepting,
    handling and servicing responsibilities.
    """
    def __init__(self, server, socket):
        """
        The AcceptHander class needs to know about the listening
        socket and the server object this is a thread inside of.
        """
        Thread.__init__(self)
        self.server = server
        self.socket = socket
        self.running = 0

    def stop(self):
        """
        stop stops the AcceptHandler thread.
        """
        self.running = 0
        
    def run(self):
        """
        run starts the AcceptHandler thread. The accept handler loops
        on a select to find out if there are new incoming
        connections. If there is a new incoming connection it accepts
        the connection, creates a ConnectionHandler (passing it the
        connection) then starts the ConnectionHandler thread.
        """
        self.running = 1
        while(self.running == 1):
            rr,rw,re = select.select([self.socket], [], [], 1)
            if(len(rr) != 0 and self.running):
                print rr
                connection, address = rr[0].accept()
                addressString = "%s:%d" % (address[0], address[1])
                self.server.connections[addressString] = ConnectionHandler(self.server, 
                                                                           connection, 
                                                                           addressString)
                self.server.connections[addressString].start()
        sys.stderr.write("Accept Handler Exiting\n")
        
class CoherenceService(Thread):
    """
    The CoherenceService maintains coherence by providing a
    distributed event channel among a set of CoherenceClients. The
    service is used by each venue to provide coherence within the
    Virtual Venue.
    """
    def __init__(self, location):
        """
        The CoherenceService contstructor only takes a location (which
        is a host, port pair) to listen for CoherenceClient
        connection.
        """
        Thread.__init__(self)
        self.location = location
        self.connections = {}
        self.acceptThread = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.location.GetHost(), self.location.GetPort()))
    
    def run(self):
        """
        The run method is the overloaded Thread.run which allows the
        CoherenceService to run within a thread. The coherence service
        starts an AcceptHandler thread then waits for the service to
        stop.
        """
        self.running = 1
        self.sock.listen(1)
        self.acceptThread = AcceptHandler(self, self.sock)
        self.acceptThread.start()
            
    def stop(self):
        """
        The stop method stops the CoherenceService and it's sub-threads.
        """
        self.acceptThread.stop()
        for c in self.connections.keys():
            self.connections[c].stop()
        self.sock.close()
        self.running = 0
        
    def SetLocation(self, location):
        """
        SetLocation sets the network location of the CoherenceService.
        """
        self.location = location
        
    def GetLocation(self):
        """
        GetLocation returns the network location of the CoherenceService.
        """
        return self.location
         
    def distribute(self, data):
        """
        distribute sends coherence data to all of the CoherenceClients
        of this CoherenceService.
        """
        pickledData = pickle.dumps( data )
        for c in self.connections.keys():
            if self.connections[c].isAlive():
                self.connections[c].send( pickledData )
            else:
                del self.connections[c]
            
if __name__ == "__main__":
  import string
  nl = UnicastNetworkLocation(string.lower(socket.getfqdn()), 6500)
  print "Creating new CoherenceService at %s %d." % (nl.GetHost(), nl.GetPort())
  coherence = CoherenceService(nl)
  coherence.start()

  time.sleep(30)
  coherence.stop()
