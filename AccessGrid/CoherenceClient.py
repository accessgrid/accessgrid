#-----------------------------------------------------------------------------
# Name:        CoherenceClient.py
# Purpose:     This is the client side object for maintaining coherence in a 
#               virtual venue via the coherence service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CoherenceClient.py,v 1.5 2003-01-13 18:24:32 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from threading import Thread
import socket

class CoherenceClient(Thread):
    """
    The Coherence Client maintains a client side connection to the Coherence
    Service to maintain state among a set of clients. This is done by sending
    coherence events through the event service.
    """
    host = ''
    port = 0
    callback = None
    sock = None
    
    def __init__(self, host, port, callback):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.callback = callback
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        
    def run(self):
        while self.sock != None:
            data = self.sock.recv(1024)
            print "Received coherence event !"
            self.callback(data)   

    def test_serve(self, label):
        import time
        while self.sock != None:
            data = "%s : %s : %s" % (label, socket.getfqdn(),
                                     time.asctime())
            self.sock.send(data)
            time.sleep(1)
            
def test(data):
    print "Got Data from Coherence: " + data
    
if __name__ == "__main__":
    import sys
    coherenceClient = CoherenceClient(sys.argv[1], int(sys.argv[2]), test)
    coherenceClient.start()
    if len(sys.argv)>3:
        coherenceClient.test_serve(sys.argv[1])
