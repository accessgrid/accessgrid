#-----------------------------------------------------------------------------
# Name:        CoherenceService.py
# Purpose:     This service provides coherence among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CoherenceService.py,v 1.5 2003-01-13 05:16:28 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket
import select
import sys
import time
import struct
from threading import Thread

from NetworkLocation import UnicastNetworkLocation

class ConnectionHandler(Thread):
    def __init__(self, server, connection, address):
        Thread.__init__(self)
        self.server = server
        self.connection = connection
        self.address = address
        self.running = 0
        
    def stop(self):
        self.running = 0

    def send(self, data):
        self.connection.send(data)
        
    def run(self):
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
    def __init__(self, server, socket):
        Thread.__init__(self)
        self.server = server
        self.socket = socket
        self.running = 0

    def stop(self):
        self.running = 0
        
    def run(self):
        self.running = 1
        while(self.running == 1):
            sys.stderr.write("AH Running\n")
            rr,rw,re = select.select([self.socket], [], [], 30)
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
    connections = {}
    location = None
    sock = None
    acceptThread = None
    
    def __init__(self, location):
        Thread.__init__(self)
        self.location = location
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.location.GetHost(), self.location.GetPort()))
    
    def run(self):
        self.running = 1
        self.sock.listen(1)
        self.acceptThread = AcceptHandler(self, self.sock)
        self.acceptThread.start()
        while(self.running == 1):
            print "Still running"
            time.sleep(1)
            
    def stop(self):
        """ """
        print "Stopping acceptor"
        self.acceptThread.stop()
        print "Shutting down active connections"
        for c in self.connections.keys():
            self.connections[c].stop()
        print "Closing listening socket"
        self.sock.close()
        self.running = 0
        
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

  time.sleep(30)
  coherence.stop()
