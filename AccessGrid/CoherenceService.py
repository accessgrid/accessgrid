#-----------------------------------------------------------------------------
# Name:        CoherenceService.py
# Purpose:     This service provides coherence among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CoherenceService.py,v 1.10 2003-01-21 11:50:55 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket
from SocketServer import ThreadingTCPServer, StreamRequestHandler
import sys

from NetworkLocation import UnicastNetworkLocation

class CoherenceService(ThreadingTCPServer):
    """
    The CoherenceService provides a secure event layer. This might be more 
    scalable as a secure RTP or other UDP solution, but for now we use TCP.
    In the TCP case the CoherenceService is the Server.
    """
    def __init__(self, server_address, RequestHandlerClass):
        self.connections = []
        ThreadingTCPServer.__init__(self, server_address, RequestHandlerClass)

    def distribute(self, data):
        for c in self.connections:
            c.wfile.write(data)
            
class CoherenceRequestHandler(StreamRequestHandler):
    """
    The CoherenceRequestHandler is the object than handles a single coherence
    connection. This is an attempt to use the ThreadedTCPServer so that I can
    easily change to a GSI TCP solution.
    """
    
    def stop(self):
        self.running = 0
    
    def send(self, data):
        self.request.send(data)
        
    def handle(self):
        # register setup stuff
#        print "Saving connection!"
        self.server.connections.append(self)
        
        # loop getting data and handing it to the server
        self.running = 1
        while(self.running == 1):
#            print "Reading data!"
            try:
                data = self.rfile.readline()
#               print "Read %s" % data[:-1]
                self.server.distribute(data)
            except:
                print "Caught exception trying to read data"
                self.running = 0
                self.server.connections.remove(self)
            
if __name__ == "__main__":
  import string
  host = string.lower(socket.getfqdn())
  port = 6500
  print "Creating new CoherenceService at %s %d." % (host, port)
  coherence = CoherenceService((host, port), CoherenceRequestHandler)
  while(1):
      coherence.handle_request()
