import gc, inspect, types, traceback, threading, time, pprint
from pyGlobus.io import GSITCPSocket
from AccessGrid.Security.Utilities import CreateTCPAttrAlwaysAuth

gc.set_debug(gc.DEBUG_LEAK)
print "GC Threshold: ", gc.get_threshold()
gc.set_threshold(1,1,1)

def Info(obj):
    if inspect.ismethod(obj):
        print "Method (%d): " % id(obj)
        print " Class: ", obj.im_class
        print " Name: ", obj.__name__
    elif isinstance(obj, types.InstanceType):
        print "Instance (%d): " % id(obj)
        pprint.pprint(obj)
    elif inspect.isframe(obj):
        print "Frame (%d): " % id(obj)
        traceback.print_stack(obj)
    else:
        print "Other (%d): " % id(obj)
        print type(obj)
#        pprint.pprint(obj)
    print " ---- "
    
class EventService:
    """
    The EventService provides a secure event layer. This might be more 
    scalable as a secure RTP or other UDP solution, but for now we use TCP.
    In the TCP case the EventService is the Server, GSI is our secure version.
    """
    def __init__(self, server_address):
        print "EventServiceAsynch: Event Service Started"

        self.active_sockets = dict()
        
        self.location = server_address
        #
        # The socket we're listening on.
        #
        self.socket = GSITCPSocket()
        self.socket.allow_reuse_address = 1
        self.attr = CreateTCPAttrAlwaysAuth()
        #
        # Initialize socket for listening.
        #
        port = self.socket.create_listener(self.attr, server_address[1])
        print "EventServiceAsynch: Bound to %s (server_address=%s)" % (port, server_address)

        self.lock = threading.Event()
        self.lock.clear()
        
    def start(self):
        """
        Start. Initialize the asynch io on accept.
        """

        print "EventServiceAsynch: Event service start"
        self.registerForListen()

        self.junk = map(lambda o: id(o), gc.get_objects())

        while (1):
            gc.collect()
            try:
                self.junk3 = gc.get_objects()
                junk = list()
                for o in self.junk3:
                    if id(o) not in self.junk and id(o) != id(self.junk) and id(o) != id(junk):
                        junk.append(o)
                print "JUNK REPORT: %d %d" % (len(self.junk), len(self.junk3))
                print " ************* "
                map(lambda o: Info(o), junk)
                print " ************* "
                del self.junk3
                del junk
            except:
                log.exception("Showing j3")

            time.sleep(0.1)
            
    def registerForListen(self):
        self.lock.clear()
        self.listenCallbackHandle = \
                      self.socket.register_listen(self.listenCallback, None)
        self.lock.set()
        
        print "EventServiceAsynch: register_listen returns '%s'" % (self.listenCallbackHandle)
        
    def listenCallback(self, arg, handle, result):
        self.lock.wait()
        try:
            self.socket.free_callback(self.listenCallbackHandle)
        except:
            log.exception("Listen Callback failed to free callback.")
            
        del self.listenCallbackHandle
        
        if result[0] != 0:
            print "EventServiceAsynch: listenCallback failed: %s %s" % \
                                                     (result[1], result[2])
            del result
            del arg
            return
        else:
            print "EventServiceAsynch: Listen Callback '%s' '%s' '%s'" % \
                                                     (arg, handle, result)
            del result
            del arg
        
        try:
            self.registerAccept(self.attr)
        except:
            log.exception("Listen Callback: registerForAccept.")

    def registerAccept(self, attr):
        self.lock.clear()
        print "EventServiceAsynch: registering accept"

        result = self.socket.register_accept(attr,
                                             self.acceptCallback,
                                             None)
        socket, self.acceptCallbackHandle = result
        self.lock.set()

        log.debug("EventServiceAsynch: register_accept returns result=(%s)",
                  self.acceptCallbackHandle)
        
        self.active_sockets[socket._handle] = socket
        del result
        
    def acceptCallback(self, arg, handle, result):
        self.lock.wait()
        try:
            self.socket.free_callback(self.acceptCallbackHandle)
            del self.acceptCallbackHandle
            del self.active_sockets[handle]
        except:
            log.exception("Accept Callback failed to free callback.")
            
        if result[0] != 0:
            print "EventServiceAsynch: acceptCB result failure: %s %s" % (result[1], result[2])
            return

        print "EventServiceAsynch: Accept Callback '%s' '%s' '%s'" % (arg, handle, result)

        del result
        del arg
        
        try:
            pass
#            sock = self.active_sockets[handle]
#            conn = ConnectionHandler(sock, self)
#            conn.registerForRead()
#            self.connectionMap[conn.GetId()] = None
#            del self.active_sockets[handle]
        except:
            log.exception("Accept failed to find socket for handle.")
            
        try:
            self.registerForListen()
        except:
            log.exception("acceptCallback failed")

if __name__ == "__main__":
  from AccessGrid import Toolkit

  Toolkit.CmdlineApplication().Initialize()

  port = 6500
  print "Creating new EventService at %d." % port
  eventService = EventService(('', port))
  evtThread = threading.Thread(target=eventService.start)
  evtThread.start()
  evtThread.join()
