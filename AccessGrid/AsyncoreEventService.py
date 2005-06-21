
import os
import string
import sys
import threading
import time
import socket
import asyncore
import signal

from AccessGrid import Log

log = Log.GetLogger(Log.EventService)
Log.SetDefaultLevel(Log.EventService, Log.DEBUG)

from ZSI.writer import SoapWriter
from ZSI.parse import ParsedSoap
from AccessGrid.interfaces.AccessGrid_Types import www_accessgrid_org_v3_0

class XMLEvent:
    '''
    Event class. This will eventually be built using xml.
    '''
    def __init__(self, type, channelId, senderId, data):
        '''
        channelId - which channel this event should be sent on
        senderId - unique id of sender
        data - event data
        '''
        self.channelId = str(channelId)
        self.senderId = str(senderId)
        self.data = data
        self.time = "here goes time later..."
        self.eventType = str(type)

        self.soapWriter = SoapWriter()
        
    def GetChannelId(self):
        return self.channelId

    def GetSenderId(self):
        return self.senderId

    def GetData(self):
        return self.data

    def GetEventType(self):
        return self.eventType 

    def GetXML(self):
        xml = self.soapWriter.serialize(self, www_accessgrid_org_v3_0.Event_('qwe'))
        xml = str(xml)
        return xml

    def CreateEvent(xml):
        ps = ParsedSoap(xml)
        p = www_accessgrid_org_v3_0.Event_('qwe').parse(ps.body_root, ps)
        ret = XMLEvent(p.eventType, p.channelId, p.senderId,  p.data)
        return ret

    # Makes it possible to access the method without an instance.
    CreateEvent = staticmethod(CreateEvent)

class VenueServerServiceDescription:
    '''
    Describes a venue server service.
    '''
    def __init__(self, id, name, description, type, location, channels):
        '''
        id - unique id for this service
        name - name of service
        description - description of service
        type - which type of service (e.g. event, text, etc)
        location - host, port information
        channels - list of all channel ids for channels in this service 
        '''
        self.__id = str(id)
        self.__name = str(name)
        self.__description = str(description)
        self.__type = str(type)
        self.__location = location
        self.__channels = channels

    def HasChannel(self, channelId):
        '''
        Check if a specific channel exists for this service.
        '''
        for channel in self.__channels:
            if channel == channelId:
                return 1
        return 0
            
    def GetChannels(self):
        '''
        Get all channels associated with this service
        '''
        return self.__channels
        
    def GetType(self):
        '''
        Get type of service.
        '''
        return self.__type

    def GetLocation(self):
        '''
        Get location (host, port) information for
        this service.
        '''
        return self.__location
   
    def GetId(self):
        '''
        Get unique id for this service.
        '''
        return str(self.__id)
    
      
class Channel:
    '''
    The channel class represents a group of network connections
    that belongs to the same session. Channels help us decide wich
    connections should receive which events.
    '''
    
    def __init__(self, id):
        self.__channelId = str(id)
        self.__connections = {}
      
    def GetId(self):
        return self.__channelId

    def AddConnection(self, networkConnection):
        log.debug("Channel.AddConnection: Add connection %s to channel %s"%(networkConnection.get_id(), self.__channelId))
        self.__connections[networkConnection.get_id()] = networkConnection

    def GetConnections(self):
        return self.__connections.values()

    def HasConnection(self, networkConnection):
        return self.__connections.has_key(networkConnection.get_id())


class VenueServerService:
    '''
    The VenueServerService is an interface class, services should
    inherit from this class. This class has methods for handling
    channels. 
    '''
    def __init__(self, name, description, id, type, location):
        self.name = name
        self.description = description
        self.id = id
        self.type = type
        self.location = location
        self.channels = {}

    def Start(self):
        log.error("VenueServerService.Start: This method should only be called from sub class.")
       
    def GetId(self):
        return self.id
       
    def GetDescription(self):
        return VenueServerServiceDescription(self.id, self.name,
                                             self.description, self.type,
                                             self.location, self.channels.keys())
        
    def CreateChannel(self, channelId):
        channel = Channel(channelId)
        self.channels[channelId] = channel
                       
    def DestroyChannel(self, channelId):
        del self.channels[channelId]

    def GetChannel(self, channelId):
        channel = None
        if self.channels.has_key(channelId):
            channel = self.channels[channelId]

        return channel

    def HasChannel(self, channelId):
        channel = self.channels.has_key(channelId)
        return channel

    def GetLocation(self):
        return self.location


class NetworkService (asyncore.dispatcher):
    '''
    The NetworkService accepts incoming network connections. 
    '''
    def __init__ (self,port,handler=None):
        '''
        Create a socket and listen for connections. Bind socket
        to address localhost and port.
        '''
        asyncore.dispatcher.__init__ (self)
        self.port = port

        log.debug('NetworkService: Bind to localhost on port %s'
                  %(port))
        
        self.create_socket (socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(('', port))
        self.listen(5) # maximum number of queued connections
        self.handler = handler
      
    def handle_accept (self):
        '''
        Accept incoming connections. 
        '''
        try:
            conn, addr = self.accept()
        

            log.debug('NetworkService: Incoming connection from %s:%d'
                      %(addr[0], addr[1]))
            # create a connection
            NetworkConnection(conn, addr, self.handler)
        except:
            print '---------------- accept error -----why?'
            

class NetworkConnection (asyncore.dispatcher):
    '''
    A network connection is an instances of class asyncore.dispatcher.
    This class takes care of read/write on the socket.
    '''
    def __init__ (self, conn, addr,handler=None):
        asyncore.dispatcher.__init__(self, conn)
        self.__handler = handler
        self.__buffer = []
        self.__data = ''

        # the connection object is the unique id for this class.
        self.__id = conn

    def get_id(self):
        return self.__id

    def add_to_buffer(self, data):
        """
        Add data to submit.
        """
        try:
            self.__buffer.append(data)
        except:
            log.exception("NetworkConnection.add_to_buffer: Failed %s"%(data))
                       
    def handle_read(self):
        """
        Called when the asynchronous loop detects that a read()
        call on the connection's socket will succeed. 
        """
        try:
            self.__data = self.recv(8192)
            if self.__handler:
                self.__handler(self, self.__data)
            else:
                log.warn("NetworkConnection.handle_read: Unhandled message %s"(self.__buffer))
        except:
            log.exception("NetworkConnection.handle_read: Failed %s"
                          %(self.__data))
            
    def writable(self):
        """
        Method used to determine whether the connection's socket
        should be added to the list of connections polled for write
        events. 
        """
        return (len(self.__buffer) > 0)

    def handle_write(self):
        """
        Called when the asynchronous loop detects that a writable
        socket can be written. Implements buffering.
        """
        try:
            sent = self.send(self.__buffer[0])
            self.__buffer = self.__buffer[1:]
            
        except:
            log.exception("NetworkConnection.handle_write: Failed %s"
                          %(self.__buffer))
            
    def handle_close(self):
        """
        Called when socket is closed.
        """
        try:
            self.close()
        except:
            log.exception("NetworkConnection.handle_close: Failed")

           
class EventLoop:
    """
    Adapted from class event_loop in Sam Rushing's async package
    """
    
    socket_map = asyncore.socket_map
    
    def __init__ (self):
        self.events = {}

    def go (self, timeout=5.0):
        events = self.events
        while self.socket_map:
            now = int(time.time())
            for k,v in events.items():
                if now >= k:
                    v (self, now)
                    del events[k]
            asyncore.poll (timeout)

    def schedule (self, delta, callback):
        now = int (time.time())
        self.events[now + delta] = callback

    def unschedule (self, callback, all=1):
        "unschedule a callback"
        for k,v in self.events:
            if v is callback:
                del self.events[k]
                if not all:
                    break


class EventService(threading.Thread, VenueServerService):
    '''
    This thread runs in the background receiving commands via
    a socket. The EventService inherits VenueServerService to
    expose a set of methods that can be used in the venue server. 
    '''
    
    def __init__(self, name, description, id, type, location):
        threading.Thread.__init__(self)
        VenueServerService.__init__(self, name, description, id, type, location)
        self.keep_going = 1
        self.running    = 0
        host, port = location
        log.debug("EventServcie.__init__: Starting event service at %s %s"
                  %(host, port))

        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
               
        self.server = NetworkService(port,self.received_event)
        self.event_loop = EventLoop()
        
        self.buffer = ''

    def Start(self):
        self.start()

    def handle_signal(self, arg1, arg2):
        self.shutdown()

    def is_running(self):
        return self.running

    def stop(self):
        self.keep_going = 0

    def check_status(self,el,time):
        if not self.keep_going:
            asyncore.close_all()
        else:
            self.event_loop.schedule(1,self.check_status)
            
    def received_event(self,networkConnection,event):
        eventList = []
        
        self.buffer += event
        
        envelopeEndTag = '</SOAP-ENV:Envelope>'
        while 1:
            i = string.find(self.buffer,envelopeEndTag,1)
            if i < 0:
                break
                
            msgEnd = i + len(envelopeEndTag)
            ev = self.buffer[0:msgEnd]
            self.buffer = self.buffer[msgEnd:]
            
            eventList.append(ev)
            
        for ev in eventList:
            self._received_event(networkConnection,ev)
            
    def _received_event(self, networkConnection, event):
        '''
        Event callback for reading. Distribute the event
        to all connections in a channel. A connection is added
        to a channel when first event is received. This method is
        triggered by a client sending an event over the network.
        '''
        # deserialize the event
        event = XMLEvent.CreateEvent(str(event))
                         
        try:
            # Does the channel exist? 
            if not self.HasChannel(event.GetChannelId()):
                log.error("EventService.received_event: Trying to send an event on a channel that does not exist %s" %(event.GetChannelId()))
                    
                self.CreateChannel(event.GetChannelId())
                return

            channel = self.GetChannel(event.GetChannelId())

            log.debug('EventService.received_event: Send event %s to channel %s'
                      %(event.GetEventType(), event.GetChannelId()))

            # Is the connection associated with the channel?
            # Otherwise, add the connection to the channel.
            if not channel.HasConnection(networkConnection):
                channel.AddConnection(networkConnection)
                           
            # distribute the event to all connections in the
            # channel.
            log.debug('EventService.received_event: Distribute this event %s to all connection on all channels %s'%(event.GetEventType(), len(channel.GetConnections())))

           
            for connection in channel.GetConnections():
                connection.add_to_buffer(event.GetXML())
        except:
            log.exception("EventService.received_event: Caught exception.")
            

    def run(self):
        self.running = 1
        self.event_loop.schedule(1,self.check_status)
        # loop here checking every 0.5 seconds for shutdowns etc..
        self.event_loop.go(0.5)
        # server has shutdown
        log.debug("EventServcie.run: Closed down network")
        time.sleep(1)
        self.running = 0
        
    def shutdown(self):
        # wait for network thread to die
        if self.is_running():
            self.stop()
        nd = 1
        while self.is_running():
            log.debug("EventService.shutdown: Shutting down network service %s"%(nd*'.'))
            time.sleep(0.3)
            nd = nd + 1

if __name__=='__main__':

    network = EventService("Event Service",
                           "asyncore based service for distributing events",
                           1, "AsyncoreEvent", ('localhost', 8002))
    network.CreateChannel(1)
    network.start()
    
    print "started event service on host: localhost port: 8002"

    #Loop main thread to catch signals
    while network.is_running():
        time.sleep(1)
        

