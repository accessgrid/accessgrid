import os
import string
import sys
import threading
import time
import socket
import asyncore
import cPickle

from wxPython.wx import *
from AsyncoreEventService import XMLEvent 

from AccessGrid import Log
log = Log.GetLogger(Log.VenueClient)

class EventClient:
    '''
    Interface class.
    '''
    def __init__(self, location, id, channelId):
        log.debug('EventClient.__init__: Create event client, location: %s id %s' %(location, channelId))
        self.client = AsyncoreEventClient(location, id, channelId)
                
    def RegisterCallback(self, eventType, callback):
        '''
        Associates a method with an event type. You can register several
        callbacks for each event type.

        eventType - type of event
        callback - name of method that should be called when an event
        of type eventType is received
        '''
        self.client.register_callback(eventType, callback)

    def Send(self, eventType, data):
        '''
        Distribute an event of type eventType on the channel.

        eventType - type of event
        data - event data
        '''
        # create an event
        event = XMLEvent(eventType, self.client.channelId, self.client.id, data)
        self.client.send_a_line(event)
        
    def Start(self):
        '''
        Start the client.
        '''
        self.client.start()
       
    def Stop(self):
        '''
        Stop the client.
        '''
        self.client.stop()

    def IsRunning(self):
        '''
        Check if the client is still running.
        '''
        return self.client.is_running()

class NetworkClient (asyncore.dispatcher):
    '''
    The NetworkClient is an instances of class asyncore.dispatcher.
    This class takes care of read/write on the socket.
    '''
    def __init__ (self, location, handler=None):
        '''
        location - (host, port) location
        handler - callback for handling read and writes
        '''
        self.out_buffer = []
        self.in_buffer = []
               
        asyncore.dispatcher.__init__ (self)
        log.debug('NetworkClient.__init__: Connect to %s %s'%location)
        self.create_socket (socket.AF_INET, socket.SOCK_STREAM)
        self.connect(location)
        self.handler = handler
                  
    def handle_connect(self):
        pass

    def handle_read(self):
       try:
           self.in_buffer.append(self.recv(8192))
            
           if self.handler:
               self.handler(self.in_buffer[0])
               self.in_buffer = self.in_buffer[1:]
           else:
               log.warn('NetworkClient.handle_read:  Unhandled message %s' %self.out_buffer)
               
       except:
            log.exception('NetworkClient.handle_read: handle_read failed')
            
    def handle_write(self):
        try:
            sent = self.send(self.out_buffer[0])
            self.out_buffer = self.out_buffer[1:]
            
        except:
            log.exception('NetworkClient.handle_write error')
                
    def writable(self):
        return 0
             
# Adapted from class event_loop in Sam Rushing's async package
class EventLoop:

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
        log.debug("EventLoop.unschedule: unschedule %s"%callback)
        for k,v in self.events:
            if v is callback:
                del self.events[k]
                if not all:
                    break

class AsyncoreEventClient(threading.Thread):
    '''
    This thread runs in the background receiving commands via
    a socket, then sends the command back to the GUI as a "NetworkEvent"
    '''

    def __init__(self, location, id, channelId):
        threading.Thread.__init__(self)
        self.keep_going = true
        self.running    = false
        self.callbacks = {}
        self.id = id
        self.channelId = channelId
        self.client = NetworkClient(location, self.received_a_line)
        self.event_loop = EventLoop()
                
    def register_callback(self, eventType, callback):
        if not self.callbacks.has_key(eventType):
            existingCallbacks = []
        else:
            existingCallbacks = self.callbacks[eventType]

        existingCallbacks.append(callback)
        self.callbacks[eventType] = existingCallbacks
        
    def is_running(self):
        return self.running

    def stop(self):
        self.keep_going = 0

    def check_status(self,el,time):
        if not self.keep_going:
            asyncore.close_all()
        else:
            self.event_loop.schedule(1,self.check_status)
        
    def received_a_line(self, event):
        e = XMLEvent.CreateEvent(event)
              
        # Notify ui of the event
        self.send_event(event)
        
    def send_a_line(self, event):
        self.client.out_buffer.append((event.GetXML()))
        self.client.handle_write()

    def run(self):
        self.running = true
        self.event_loop.schedule(1,self.check_status)
        # loop here checking every 0.5 seconds for shutdowns etc..
        self.event_loop.go(0.5)
        time.sleep(1)
        self.running = false
    
    def send_event(self,event):
        '''
        send an event back to our GUI thread
        '''
        e = XMLEvent.CreateEvent(event)
        
        if self.callbacks.has_key(e.GetEventType()):
            log.debug("send_event: Callback found for event type %s"%e.GetEventType())
            for c in self.callbacks[e.GetEventType()]:
                wxCallAfter(c, e)
        else:
            log.debug("No callback registered for event %s. Can not update UI."%e.GetEventType())
            
if __name__=='__main__':

    # Test for the event client/service. After starting the event service,
    # run this client. A UI will open which allows you to transmit key values.
    # The same key value is received in an event and printed in the window.
    # This is a good example on how to interact with the wx main thread from
    # the network thread.
 
    class NetworkEvent(wxPyEvent):
        '''
        the network thread communicates back to the main GUI thread via
        this sythetic event
        '''
        def __init__(self,msg=""):
            wxPyEvent.__init__(self)
            self.SetEventType(wxEVT_NETWORK)
            self.msg = msg
    wxEVT_NETWORK = 2000

    def EVT_NETWORK(win, func):
        win.Connect(-1, -1, wxEVT_NETWORK, func)

    class MyApp(wxApp):
        '''
        main wx ui app.
        '''
        def OnInit(self):
            self.frame = frame = MainFrame(NULL, -1, 
                                           "wxPython+threading")
            self.SetTopWindow(frame)
            frame.Show(true)
            return true
  
    class MainFrame(wxFrame):
        '''
        all the ui components.
        '''
        ID_EXIT  = 102

        def __init__(self, parent, ID, title):
            wxFrame.__init__(self, parent, ID,
                             title,
                             wxDefaultPosition, # position
                             wxSize(512,512))
            self.SetAutoLayout(true)
            self.CreateStatusBar()
            menuBar = wxMenuBar()
            menu    = wxMenu()
            menu.AppendSeparator()
            menu.Append(self.ID_EXIT, "E&xit", "Terminate the program")
            menuBar.Append(menu, "&File");
            self.SetMenuBar(menuBar)
            EVT_MENU(self,self.ID_EXIT,self.TimeToQuit)
            
            sizer = wxBoxSizer(wxVERTICAL)
            self.SetSizer(sizer)
            
            # a logging window
            self.log = wxTextCtrl(self,-1,style = wxTE_MULTILINE)
            wxLog_SetActiveTarget(wxLogTextCtrl(self.log))
            sizer.Add(self.log,1,wxEXPAND|wxALL,1)
            
            # trap characters
            EVT_CHAR(self.log, self.OnChar)
            
            # start the event server thread
            eventHost = "localhost"
            eventPort = 8002
            self.eventClient = EventClient((eventHost, eventPort), 1, 1)
            self.eventClient.RegisterCallback("test", self.OnTest)
            self.eventClient.Start()
            self.eventClient.Send("connect", "")    
                        
            # cleanup
            EVT_CLOSE(self, self.OnCloseWindow)
            
            self.show_status("Connecting to %s on port %d." % 
                             (eventHost, eventPort))
            
        def OnCloseWindow(self, event):
            self.shutdown_network()
            self.Destroy()

        def OnChar(self, event):
            key = event.KeyCode()
            
            if key == 27:
                self.Close(true)
          
            else:
                self.eventClient.Send("test", chr(key))
                return

        def TimeToQuit(self, event):
            self.Close(true)

        def OnTest(self, evt):
            string = "channelId = %s, senderId = %s, data = %s"%(evt.GetChannelId(), evt.GetSenderId(), evt.GetData())
            wxLogMessage("Received: \"%s\"." % string)

        def shutdown_network(self):
            wxLogMessage('Shutting down event client.')
            # wait for network thread to die
            if self.eventClient.IsRunning():
                self.eventClient.Stop()
                nd = 1
            while self.eventClient.IsRunning():
                self.show_status("Shutting down network service" + nd*'.')
                time.sleep(0.3)
                nd = nd + 1

        def show_status(self,t):
            self.SetStatusText(t)

    # Start the ui main thread.
    app = MyApp(0)
    app.MainLoop()
     



