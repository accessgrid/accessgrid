#!/usr/bin/python2
#
#
import socket, threading, time, Queue, string, struct

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

class Client(threading.Thread):
    """
    """
    MSGSIZE = 8192
    def __init__(self, src_host, src_port, dst_host, dst_port, time, queue):
        """
        Create a new client, which could be either a unicast connection,
        or a multicast group.

        The time is the last time we heard from this client, in case
        we want to garbage collect silent clients.
        """
        super(Client, self).__init__()
        
        self.host = src_host
        self.port = src_port
        self.to_host = dst_host
        self.to_port = dst_port
        self.time = time
        self.queue = queue
        self.active = threading.Event()
        self.allowed = 1
        self.key = "%s:%s" % (self.host, self.port)
        self.socket = self.create_sock(self.host, self.port)


    def create_sock(self, host, port):
        if is_mcast(host):
            return openmcastsock(host, port)
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return sock

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

    def enable_send(self):
        self.allowed = 1

    def disable_send(self):
        self.allowed = 0
        
    def run(self):
        self.active.set()

        if not is_mcast(self.host):
            self.socket.bind((self.host, self.port))

        dst_addr = (self.host, self.port)
        while self.is_active():
            if self.allowed:
                data, src_addr = self.socket.recvfrom(self.MSGSIZE)
                k = "%s:%s" % (src_addr[0], src_addr[1])
                self.queue.put((data, src_addr, dst_addr))

    def stop(self):
        self.active.clear()

    def is_active(self):
        return self.active.isSet()

    def send(self, src, data, port_override=None):
        """
        Send data to this client, the client checks to make sure they
        don't send data to themselves.
        """
        if self.key != src and self.to_host != "":
            self.socket.sendto(data, (self.host, port_override))

class Receiver(threading.Thread):
    """
    """
    def __init__(self, host, port, timeout=None):
        """
        """
        super(Receiver, self).__init__()
        self.host = host; self.port = port; self.timeout = timeout
        self.active = threading.Event()
        self.active.set()
        self.clients = dict()
        self.queue = Queue.Queue(10)

        self.add_client(host, port, start=1)

    def add_client(self, src_host, src_port,
                   dst_host="", dst_port=0, start=0):
        c = Client(src_host, src_port, dst_host, dst_port,
                   time.time(), self.queue)
        c_key = "%s:%s" % (src_host, src_port)
        self.clients[c_key] = c

        if start:
            c.start()
        
    def run(self):
        """
        """
        while self.active.isSet():
            try:
                data, src, dst = self.queue.get()
                if is_mcast(dst[0]):
                    src_key = "%s:%s" % (dst[0], dst[1])
                    mcast = 1
                else:
                    src_key = "%s:%s" % (src[0], src[1])
                    mcast = 0

                if not self.clients.has_key(src_key):
                    # This is a new connection
                    self.add_client(src[0], src[1], dst[0], dst[1])
                else:
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

    def cleanup_clients(self):
        """
        """
        if self.timeout is not None:
            limit = time.time() - self.timeout
            for s in [k for (k,v) in self.clients.items()
                      if v.get_time() < limit]:
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
        
        super(RTPReceiver, self).__init__()
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
        self.data.add_client(addr, port, start=active)
        self.ctrl.add_client(addr, port+1, start=active)
                                    
def main():
    UDP_PORT = 43278; CHECK_PERIOD = 20; CHECK_TIMEOUT = 15
    host = socket.gethostbyname(socket.gethostname())
    rtp_bridge = RTPReceiver(host, UDP_PORT, CHECK_TIMEOUT)
    rtp_bridge.start()

    rtp_bridge.add_client("224.2.159.7", 57712, 1)
    
    print "Server on %s:%d" % (host, UDP_PORT)

    try:
        while rtp_bridge.is_active():
            pass
    except KeyboardInterrupt:
        print 'Exiting, please wait...'
        rtp_bridge.stop()

if __name__ == '__main__':
    main()
