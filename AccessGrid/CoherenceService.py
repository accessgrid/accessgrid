#-----------------------------------------------------------------------------
# Name:        CoherenceService.py
# Purpose:     This service provides coherence among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CoherenceService.py,v 1.1.1.1 2002-12-16 22:25:37 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from threading import Thread
import SocketServer
import CoherenceConnectionHandler

class CoherenceService(Thread):
    __doc__ = """
    This coherence service provides coherence among a set of listening
    endpoints by sending events, and perhaps periodic state updates.
    """
    server = None
    location = None
    connections = ()
    
    def __init__(self, location):
        Thread.__init__(self)
        self.allow_reuse_address = 1
        self.location = location
        self.server = SocketServer.TCPServer((location.GetHost(), 
                                              location.GetPort()), 
                                              CoherenceConnectionHandler)
    
    def SetLocation(self, location):
        self.location = location
        
    def GetLocation(self):
        return self.location
        
    def run(self):
        self.server.serve_forever()
        
    def handle(self, data):
        __doc__ = """
        The handle method is used to emit data to coherence clients. The
        each connection calls this when they recieve data from the their
        client. The Virtual Venue calls this to emit coherence data to the 
        clients.
        """ 
        print "Got Data: " + data
        for c in connections:
            c.request.send(data)
            
class CoherenceConnectionhandler(SocketServer.BaseRequestHandler):
    def handle(self):
        __doc__ = """
        The CoherenceConnection handler takes the TCP connection, puts it in
        the servers list of connections, then it proceeds to listen for data.
        If there is data it sends the data to all the listening endpoints.
        """
        
        self.server.connections.append(self)
        
        while 1:
            dataRecieved = self.request.recv(1024)
            print "Got Data: " + dataRecieved
            if not dataRecieved: break
            self.server.handle(dataRecieved) 
                       
if __name__ == "__main__":
  # just print out a for testing
  import socket
  import string
  import NetworkLocation
  nl = NetworkLocation.UnicastNetworkLocation(string.lower(socket.getfqdn()), 
                                              6500)
  print "Creating new CoherenceService."
  coherence = CoherenceService(nl)
  print "Starting the CoherenceService."
  coherence.start()
  