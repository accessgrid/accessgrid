#-----------------------------------------------------------------------------
# Name:        CoherenceClient.py
# Purpose:     This is the client side object for maintaining coherence in a 
#               virtual venue via the coherence service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CoherenceClient.py,v 1.2 2002-12-18 04:37:21 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket

class CoherenceClient:
    __doc__ = """
    The Coherence Client maintains a client side connection to the Coherence
    Service to maintain state among a set of clients. This is done by sending
    coherence events through the event service.
    """
    host = ''
    port = 0
    callback = None
    sock = None
    run = 0
    
    def __init__(self, host, port, callback):
        self.host = host
        self.port = port
        self.callback = callback
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        
    def start(self):
        self.run = 1
                    
    def stop(self):
        self.run = 0
        
    def serve(self):
        while self.run:
            data = self.sock.recv(1024)
            self.callback(data)   
            
    def test_serve(self):
        import time
        while self.run:
            data = "%s %s" % (socket.getfqdn(), time.asctime())
            self.sock.send(data)
            data = self.sock.recv(1024)
            self.callback(data)
            time.sleep(1)
            
def test(data):
    print "Got Data from Coherence: " + data
    
if __name__ == "__main__":
  coherenceClient = CoherenceClient('buffalojump.mcs.anl.gov', 6500, test)
  coherenceClient.start()
  coherenceClient.test_serve()