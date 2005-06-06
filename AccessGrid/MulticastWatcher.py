#-----------------------------------------------------------------------------
# Name:        MulticastWatcher.py
# Purpose:     Class to watch a multicast address for traffic and report status
# Created:     2005/06/06
# RCS-ID:      $Id: MulticastWatcher.py,v 1.1 2005-06-06 21:30:27 turam Exp $
# Copyright:   (c) 2005
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
"""
__revision__ = "$Id: MulticastWatcher.py,v 1.1 2005-06-06 21:30:27 turam Exp $"

import socket, threading, string, struct
import time
import select


def openmcastsock(group, port):
    # Create a socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Allow multiple copies of this program on one machine
    # (not strictly needed)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind it to the port
    # IRJ -- This needs to be fixed
    s.bind(('', port))
    
    # Look up multicast group address in name server
    # (doesn't hurt if it is already in ddd.ddd.ddd.ddd format)
    group = socket.gethostbyname(group)
    
    # Construct binary group address
    bytes = map(int, string.split(group, "."))
    grpaddr = long(0)
    for byte in bytes:
        grpaddr = (grpaddr << 8) | byte
        
    # Construct struct mreq from grpaddr and ifaddr
    ifaddr = socket.INADDR_ANY
    mreq = struct.pack('ll', socket.htonl(grpaddr), socket.htonl(ifaddr))
    
    # Add group membership
    s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    
    return s

class MulticastWatcher:

    MSGSIZE = 5192

    def __init__(self,host='233.4.200.19',port=10002,
                 statusChangeCB=None,
                 timeout=5):
        self.host = host
        self.port = port
        self.statusChangeCB = statusChangeCB
        self.timeout = timeout
        
        self.sock = openmcastsock(self.host,self.port)
        
        self.mcastStatus = threading.Event()
        self.mcastStatus.clear()
        
        self.lastRecvTime = 0
        
        self.running = threading.Event()
        self.listeningThread = threading.Thread(target=self.Listen)
        
    def Start(self):
        self.running.set()
        self.listeningThread.start()
        
    def Stop(self):
        self.running.clear()
        
    def Listen(self):
        while self.running.isSet():
            fdList = select.select([self.sock.fileno()],[],[],self.timeout)
            if fdList[0] and self.sock.fileno() in fdList[0]:
                data,src_addr = self.sock.recvfrom(self.MSGSIZE)
                self.lastRecvTime = time.time()
                self.SetStatus(1)
            else:
                self.SetStatus(0)
            
    def SetStatus(self,status):
    
        # check for change in status
        newStatus = 0
        if status != self.mcastStatus.isSet():
            newStatus = 1
        
        # set new status
        if status:
            self.mcastStatus.set()
        else:
            self.mcastStatus.clear()

        # call change callback
        if newStatus and self.statusChangeCB:
            self.statusChangeCB(self)
            
    def GetStatus(self):
        return self.mcastStatus.isSet()


if __name__ == '__main__':


    import signal

    def signalHandler(e,f):
        print "caught signal", e, "; shutting down"
        global mw
        mw.Stop()
        global running
        running.clear()

    def myStatusChangedCB(obj):
        print "Status: ", obj.GetStatus()

    signal.signal(signal.SIGINT, signalHandler)

    mw = MulticastWatcher(statusChangeCB=myStatusChangedCB)
    mw.Start()

    running = threading.Event()
    running.set()
    while running.isSet():
        time.sleep(0.5)






