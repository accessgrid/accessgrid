#!/usr/bin/python2
#
#
import sys
import optparse
import socket, threading, time, Queue, string, struct

debug = 0

def is_mcast(host):
    # Check the first byte of the address, if it's between 224 and 239
    # we make it a multicast socket.
    first_byte = int(host.split('.')[0])
    
    if first_byte > 223 and first_byte < 240:
        return 1
    else:
        return 0
    
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

class BaseClient(threading.Thread):
    """
    """
    MSGSIZE = 8192
    def __init__(self, src_host, src_port, queue):
        super(BaseClient, self).__init__(name=self.__class__)
        self.host = src_host
        self.port = src_port
        self.queue = queue
        self.active = threading.Event()
        self.key = "%s:%s" % (self.host, self.port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
       
    def listen(self):
        self.socket.bind((self.host, self.port))
       
    def disable(self):
        self.active.clear()
        
    def get_key(self):
        """
        Return the unique (ish) key for this client.
        """
        return self.key

    def get_socket(self):
        """
        return the actual socket for this client.
        """
        return self.socket

    def set_time(self, time):
        """
        Set the last time heard from this client.
        """
        self.time = time

    def get_time(self, now=None):
        """
        Get the last time heard from this client, or if specified, the
        length of time since the now parameter.
        """
        if now is None:
            return self.time
        else:
            return now - self.time
        
    def run(self):
        self.active.set()
        
        dst_addr = (self.host, self.port)
        while self.is_active():
            data, src_addr = self.socket.recvfrom(self.MSGSIZE)
            #print "received data from ", src_addr
            self.time = time.time()
            k = "%s:%s" % (src_addr[0], src_addr[1])
            self.queue.put((data, src_addr, dst_addr))

    def stop(self):
        self.active.clear()
        try:
            self.socket.shutdown(2)
        except Exception,e:
            #print "Exception in shutdown:", e
            pass

    def is_active(self):
        return self.active.isSet()
    
    def send(self, src, data, port_override=None):
        pass

class Client(BaseClient):
    """
    """
    MSGSIZE = 8192
    def __init__(self, src_host, src_port, dst_host, dst_port, time, queue):
        super(Client, self).__init__(src_host, src_port, queue)
        self.to_host = dst_host
        self.to_port = dst_port
        self.time = time
        self.allowed = 1

    def set_time(self, time):
        """
        Set the last time heard from this client.
        """
        self.time = time

    def get_time(self, now=None):
        """
        Get the last time heard from this client, or if specified, the
        length of time since the now parameter.
        """
        if now is None:
            return self.time
        else:
            return now - self.time

    def enable_send(self):
        self.allowed = 1

    def disable_send(self):
        self.allowed = 0
        
    def run(self):
        pass
        
    def send(self, src, data, port_override=None):
        """
        Send data to this client, the client checks to make sure they
        don't send data to themselves.
        """
        if self.key != src and self.to_host != "":
            #print "sending data to ", self.host, port_override
            self.socket.sendto(data, (self.host, port_override))

class MulticastClient(Client):
    """
    """
    MSGSIZE = 8192
    def __init__(self, src_host, src_port,time, queue):
        """
        Create a new client, which could be either a unicast connection,
        or a multicast group.

        The time is the last time we heard from this client, in case
        we want to garbage collect silent clients.
        """
        super(MulticastClient, self).__init__(src_host,src_port,"",0,time,queue)
        self.socket = openmcastsock(src_host,src_port)
        

    def create_sock(self, host, port):
        return openmcastsock(host, port)

    def run(self):
        self.active.set()
        
        dst_addr = (self.host, self.port)
        while self.is_active():
            if self.allowed:
                data, src_addr = self.socket.recvfrom(self.MSGSIZE)
                #print "Received data from",src_addr
                k = "%s:%s" % (src_addr[0], src_addr[1])
                self.queue.put((data, src_addr, dst_addr))

    def send(self, src, data, port_override=None):
        """
        Send data to this client, the client checks to make sure they
        don't send data to themselves.
        """
        if self.key != src:
            #print "sending data to ", self.host, port_override
            self.socket.sendto(data, (self.host, self.port))

class Receiver(threading.Thread):
    """
    """
    MSGSIZE = 8192
    def __init__(self, host, port, timeout=None):
        """
        """
        super(Receiver, self).__init__(name=self.__class__)
        self.host = host; self.port = port; self.timeout = timeout
        self.active = threading.Event()
        self.active.set()
        self.clients = dict()
        self.queue = Queue.Queue(10)

        c = BaseClient(self.host, self.port, self.queue)
        c.listen()
        self.add_client(c)

    def add_client(self, client):
        self.clients[client.key] = client

        client.start()
            
    def run(self):
        """
        """
        while self.active.isSet():
            try:
                data, src, dst = self.queue.get()
                if data == 'quit':
                    break
                if is_mcast(dst[0]):
                    src_key = "%s:%s" % (dst[0], dst[1])
                    mcast = 1
                else:
                    src_key = "%s:%s" % (src[0], src[1])
                    mcast = 0

                if not self.clients.has_key(src_key):
                    if debug: print "adding client src_key = ", src_key
                    # This is a new connection
                    c = Client(src[0], src[1], self.host, self.port,
                               time.time(), self.queue)
                    self.add_client(c)

                # Update the time on this client
                self.clients[src_key].set_time(time.time())
                
                # Then send the data
                for c in self.clients.values():
                    c.send(src_key, data, self.port)

            except socket.timeout:
                print "Socket timeout"
                pass
                
        for l in self.clients.values():
            l.stop()
            
    def stop(self):
        """
        """
        self.active.clear()
        self.queue.put(('quit','',''))

    def cleanup_clients(self):
        """
        """
        if self.timeout is not None:
            limit = time.time() - self.timeout
            for s in [k for (k,v) in self.clients.items()
                      if v.get_time() < limit]:
                if debug: print "Removing client ", self.clients[s].host, self.clients[s].port
                del self.clients[s]

    def is_active(self):
        """
        """
        return self.active.isSet()
        
class RTPReceiver(threading.Thread):
    """
    """
    def __init__(self, host, port, timeout=None):
        """
        """
        if port % 2:
            raise "RTP Port must be even."
        
        super(RTPReceiver, self).__init__(name=self.__class__)
        self.host = host; self.port = port; self.timeout = timeout
        self.data = Receiver(host, port, timeout)
        self.ctrl = Receiver(host, port+1, timeout)

    def run(self):
        """
        """
        self.data.start()
        self.ctrl.start()
        
    def stop(self):
        """
        """
        self.data.stop()
        self.ctrl.stop()
        self.data.join()
        self.ctrl.join()

    def is_active(self):
        """
        """
        return self.data.is_active() or self.ctrl.is_active()

    def add_client(self, addr, port, active):
        """
        """
        if is_mcast(addr):
            if debug: print "Adding mcast client", addr, port
            dataClient = MulticastClient(addr,port,time.time(),self.data.queue)
            ctrlClient = MulticastClient(addr,port+1,time.time(),self.ctrl.queue)
        else:
            if debug: print "Adding ucast client", addr, port
            dataClient = Client(addr,port,self.host,self.port,time.time(),self.data.queue)
            ctrlClient = Client(addr,port+1,self.host,self.port+1,time.time(),self.ctrl.queue)
        self.data.add_client(dataClient)
        self.ctrl.add_client(ctrlClient)
                                    
def main():

    global debug

    parser = optparse.OptionParser()
    parser.add_option("-g", "--group",
                      dest="group",
                      help="The multicast group to bridge.")
    parser.add_option("-m", "--mport",
                      dest="mport",type='int',
                      help="The multicast port to bridge.")
    parser.add_option("-u", "--uport",
                      dest="uport",type='int',default=0,
                      help="The unicast port for the bridge.")
    parser.add_option("-d", "--debug", action="store_true",
                      help="The debug level.")
    (options, args) = parser.parse_args()
    
    if not options.group:
        print "Error: A multicast group must be specified"
        parser.print_help()
        sys.exit(1)
    if not options.mport:
        print "Error: A multicast port must be specified"
        parser.print_help()
        sys.exit(1)
    if not options.uport:
        print "Error: A unicast port must be specified"
        parser.print_help()
        sys.exit(1)
        
    group = options.group
    mport = options.mport
    uport = options.uport
    debug = options.debug
    
    CHECK_TIMEOUT = 15
    host = socket.gethostbyname(socket.gethostname())
    rtp_bridge = RTPReceiver(host, uport, CHECK_TIMEOUT)
    rtp_bridge.start()

    rtp_bridge.add_client(group, mport, 1)
    
    print "Server on %s:%d" % (host, uport)

    try:
        while rtp_bridge.is_active():
            pass
    except KeyboardInterrupt:
        print 'Exiting, please wait...'
        rtp_bridge.stop()
        
#     for t in threading.enumerate():
#         print "t = ", t

if __name__ == '__main__':
    main()
