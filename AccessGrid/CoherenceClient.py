#-----------------------------------------------------------------------------
# Name:        CoherenceClient.py
# Purpose:     This is the client side object for maintaining coherence in a 
#               virtual venue via the coherence service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CoherenceClient.py,v 1.6 2003-01-15 22:03:40 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from threading import Thread
import socket
import pickle

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
        self.callbacks = dict()
        
    def run(self):
        while self.sock != None:
            pickledData = self.sock.recv(10000)
            print "pickled data ", pickledData
            event = pickle.loads( pickledData )
            callback = self.callbacks[event.eventType]
            callback( event.data )

    def add_callback( self, eventType, callback ):
        self.callbacks[eventType] = callback

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
