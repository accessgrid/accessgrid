#-----------------------------------------------------------------------------
# Name:        CoherenceService.py
# Purpose:     This service provides coherence among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CoherenceService.py,v 1.15 2003-01-24 12:47:15 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket
import sys
import pickle
from threading import Thread

from SocketServer import ThreadingMixIn, StreamRequestHandler
from pyGlobus.io import GSITCPSocketServer

# This really should be defined in pyGlobus.io
class ThreadingGSITCPSocketServer(ThreadingMixIn, GSITCPSocketServer): pass

from AccessGrid.NetworkLocation import UnicastNetworkLocation
from AccessGrid.Utilities import formatExceptionInfo



class CoherenceRequestHandler(StreamRequestHandler):
    """
    The CoherenceRequestHandler is the object than handles a single coherence
    connection. This is an attempt to use the ThreadedTCPServer so that I can
    easily change to a GSI TCP solution.
    """
    def stop(self):
        self.running = 0
         
    def handle(self):
        
        # register setup stuff
        self.server.connections.append(self)
        
        # loop getting data and handing it to the server
        self.running = 1
        while(self.running == 1):
            try:
                # Get the size
                size = self.rfile.readline()
                # Get the data
                pdata = self.rfile.read(int(size))
                # Unpack the data
                data = pickle.loads(pdata)
                # Send it along to the rest
                self.server.distribute(data)
            except:
                print "Caught exception trying to read data", formatExceptionInfo()
                self.running = 0
                self.server.connections.remove(self)
                
class CoherenceService(ThreadingGSITCPSocketServer, Thread):
    """
    The CoherenceService provides a secure event layer. This might be more 
    scalable as a secure RTP or other UDP solution, but for now we use TCP.
    In the TCP case the CoherenceService is the Server.
    """
    def __init__(self, server_address, 
                 RequestHandlerClass=CoherenceRequestHandler):
        Thread.__init__(self)
        self.location = server_address
        self.connections = []
        ThreadingGSITCPSocketServer.__init__(self, server_address, RequestHandlerClass)

    def run(self):
        self.running = 1
        while(self.running):
            self.handle_request()

    def stop(self):
        self.running = 0
        
    def distribute(self, data):
        # This should be more generic
        pdata = pickle.dumps(data)
        for c in self.connections:
            c.wfile.write("%s\n" % len(pdata))
            c.wfile.write(pdata)
            
    def GetLocation(self):
        return UnicastNetworkLocation(self.location[0], self.location[1])
            
if __name__ == "__main__":
  import string
  host = string.lower(socket.getfqdn())
  port = 6500
  print "Creating new CoherenceService at %s %d." % (host, port)
  coherence = CoherenceService((host, port), CoherenceRequestHandler)
  coherence.start()
