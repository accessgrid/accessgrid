#-----------------------------------------------------------------------------
# Name:        CoherenceClient.py
# Purpose:     This is the client side object for maintaining coherence in a 
#               virtual venue via the coherence service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CoherenceClient.py,v 1.8 2003-01-17 16:49:32 judson Exp $
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
    def __init__(self, host = '', port = 0, callback = None):
        """
        The CoherenceClient constructor takes a host, port and a
        callback for coherence data.
        """
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.callback = callback
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        
    def run(self):
        """
        The run method starts this thread actively getting and
        processing Coherence data provided by a CoherenceService.
        """
        while self.sock != None:
#FIXME - bad: assumed message length limit
            pickledData = self.sock.recv(10000)
            data = pickle.loads( pickledData )
            self.callback( data )

    def send(self, ):
        """
        This method sends data to the Coherence Service.
        """
        if self.sock != None:
            self.sock.send(data)
        
    def TestServe(self, label):
        """
        test_serve is used to send a constant stream of events with a user
        supplied text label, a timestamp and a hostname of the CoherenceClient.
        """
        import time
        while self.sock != None:
            data = "%s : %s : %s" % (label, socket.getfqdn(),
                                     time.asctime())
            self.send(data)
            time.sleep(1)
            
    def TestCallback(data):
        """
        The testCallback function is used to test the CoherenceService, it
        simply prints out Coherence Events received over the CoherenceService.
        """
        print "Got Data from Coherence: " + data
    
if __name__ == "__main__":
    import sys
    coherenceClient = CoherenceClient(sys.argv[1], int(sys.argv[2]),
                                      CoherenceClient.TestCallback)
    coherenceClient.start()

    if len(sys.argv) > 3:
        coherenceClient.test_serve(sys.argv[1])
