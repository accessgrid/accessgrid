#-----------------------------------------------------------------------------
# Name:        CoherenceService.py
# Purpose:     This service provides coherence among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CoherenceService.py,v 1.4 2003-01-06 20:50:22 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket
import struct
from threading import Thread

from NetworkLocation import UnicastNetworkLocation

class ConnectionHandler(Thread):
    server = None
    connection = None
    address = ''
    run = 0
    
    def __init__(self, server, connection, address):
        Thread.__init__(self)
        self.server = server
        self.connection = connection
        self.address = address
        
    def Stop(self):
        self.run = 0
        
    def send(self, data):
        self.connection.send(data)
        
    def run(self):
        self.run = 1
        while(self.run):
            try:
                data = self.connection.recv(1024)
            except:
                self.connection.close()
                self.run = 0
            if not data: break 
            self.server.distribute(data)
            
class AcceptHandler(Thread):
    socket = None
    server = None
    run = 0
    
    def __init__(self, server, socket):
        Thread.__init__(self)
        self.server = server
        self.socket = socket
    
    def Stop(self):
        self.run = 0
        
    def run(self):
        self.run = 1
        while(self.run == 1):
            connection, address = self.socket.accept()
            addressString = "%s:%d" % (address[0], address[1])
            self.server.connections[addressString] = ConnectionHandler(self.server, 
                                                                 connection, 
                                                                 addressString)
            self.server.connections[addressString].start()    

class CoherenceService(Thread):
    connections = {}
    location = None
    sock = None
    acceptThread = None
    
    def __init__(self, location):
        Thread.__init__(self)
        self.location = location
    
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.location.GetHost(), self.location.GetPort()))
        sock.listen(1)
        acceptThread = AcceptHandler(self, sock)
        acceptThread.start()
        
    def SetLocation(self, location):
        self.location = location
        
    def GetLocation(self):
        return self.location
         
    def distribute(self, data):
        for c in self.connections.keys():
            if self.connections[c].isAlive():
                self.connections[c].send(data)
            else:
                del self.connections[c]
            
if __name__ == "__main__":
  # just print out a for testing
  import string
  nl = UnicastNetworkLocation(string.lower(socket.getfqdn()), 6500)
  print "Creating new CoherenceService at %s %d." % (nl.GetHost(), nl.GetPort())
  coherence = CoherenceService(nl)
  coherence.start()
