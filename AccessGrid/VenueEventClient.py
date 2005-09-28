#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        EventService.py
# Purpose:     A group messaging service client that handles Access Grid
#                 venue events.
# Created:     2005/09/09
# RCS-ID:      $Id: VenueEventClient.py,v 1.2 2005-09-28 20:14:43 eolson Exp $
# Copyright:   (c) 2005 
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys, time

from AccessGrid import Log
log = Log.GetLogger(Log.EventClient)
Log.SetDefaultLevel(Log.EventClient, Log.DEBUG)

from AccessGrid.Descriptions import EventDescription
from AccessGrid.XMLGroupMsgClient import XMLGroupMsgClient

class VenueEventClient:
    '''
    Sends and Receives Venue group events.

    Doesn't inherit from GroupMsgClientBase since RegisterEventCallback
       is different and uses different arguments than a standard Receive.
    '''
    defaultGroupMsgClientClass = XMLGroupMsgClient
    def __init__(self, location, privateId, channel, groupMsgClientClass=None):
        self.id = privateId
        self.location = location
        self.channelId = channel
        self.eventCallbacks = {}
        self.madeConnectionCallback = None
        self.lostConnectionCallback = None
        if groupMsgClientClass != None:
            self.groupMsgClientClass = groupMsgClientClass
        else:
            self.groupMsgClientClass = self.defaultGroupMsgClientClass

        #self.groupMsgClient = apply(XMLGroupMsgClient, [location, privateId, channel] )
        self.groupMsgClient = apply(self.groupMsgClientClass, [location, privateId, channel])

        self.groupMsgClient.RegisterReceiveCallback(self.Receive)
        self.groupMsgClient.RegisterLostConnectionCallback(self.LostConnection)
        self.groupMsgClient.RegisterMadeConnectionCallback(self.MadeConnection)

    def MadeConnection(self):
        if self.madeConnectionCallback != None:
            apply(self.madeConnectionCallback)
        else:
            log.info("VenueEventClient made connection.")

    def Send(self, eventType, data):
        event = EventDescription(eventType, self.channelId, self.id, data)
        #reactor.callLater(0, self.groupMsgClient.Send, [event])
        self.groupMsgClient.Send(event)

    def Receive(self, event):
        eventDesc = event
        if eventDesc.eventType in self.eventCallbacks.keys():
            for callback in self.eventCallbacks[eventDesc.eventType]:
                apply(callback, [eventDesc])

    def LostConnection(self, connector, reason):
        if self.lostConnectionCallback != None:
            apply(self.lostConnectionCallback, [connector, reason])
        else:
            log.info("VenueEventClient lost connection.")

    def RegisterEventCallback(self, eventType, callback):
        self.eventCallbacks.setdefault(eventType, list())
        self.eventCallbacks[eventType].append(callback)

    def RegisterMadeConnectionCallback(self, callback):
        self.madeConnectionCallback = callback

    def RegisterLostConnectionCallback(self, callback):
        self.lostConnectionCallback = callback

    def Start(self):
        self.groupMsgClient.Start()

    def Stop(self):
        self.groupMsgClient.Stop()

# For testing
def GenerateRandomString(length=6):
    import string, random
    random.seed(99)
    letterList = [random.choice(string.letters) for x in xrange(length)]
    retStr = "".join(letterList)
    return retStr

class TestMessages:
    '''
    Class for sending test messages on a VenueEventClient.
    Starts sending test messages after a connection is made.
    '''
    numMsgsDefault=10000

    def __init__(self, vec=None, numMsgs=None, multipleClients=False):
        self.msgData = "1234567890123"
        if numMsgs == None:
            self.numExpectedMsgs = numMsgsDefault
        else:
            self.numExpectedMsgs = numMsgs
        self.numMessagesReceived = 0
        self.numSentMessages = 0
        self.startTime = 0
        self.finishTime = 0
        self.venueEventClient = vec
        self.maxMessagesPerSend = 15
        self.multiClient = multipleClients
        self.multiClientTimeout = 15
        if self.venueEventClient != None:
            self.venueEventClient.RegisterEventCallback("Test", self.Receive)
            self.venueEventClient.RegisterLostConnectionCallback(self.LostConnection)
            self.venueEventClient.RegisterMadeConnectionCallback(self.StartSending)

    def StartSending(self):
        reactor.callLater(0, self.Send)

    def SetMsgData(self, data):
        self.msgData = data

    def SetVenueEventClient(self, vec):
        self.venueEventClient = vec

    def Send(self):
        # Send one message to eliminate any python setup times from measurements.
        if self.numSentMessages == 0:
            self.venueEventClient.Send("Test", self.msgData)
            self.numSentMessages += 1
        else:
        
            if self.numMessagesReceived == 1:
                self.startTime = time.time()

            if self.numMessagesReceived >= 1:
                numToSend = min( self.maxMessagesPerSend, (self.numExpectedMsgs - self.numSentMessages))
                for i in range(numToSend):
                    self.venueEventClient.Send("Test", self.msgData)
                self.numSentMessages += numToSend

        # Prepare to call again until all messages are sent
        if self.numSentMessages < self.numExpectedMsgs:
            reactor.callLater(0, self.Send) 
        else:
            print "Finished sending test messages."

    def Receive(self, msg):    
        self.numMessagesReceived += 1
        if self.multiClient: # finish after a timeout
            if time.time() - self.startTime > self.multiClientTimeout:
                print "Finished (allotted time)"
                reactor.stop()
        else:                # finish after i receive all my own messages
            if self.numMessagesReceived >= self.numExpectedMsgs:
                self.finishTime = time.time()
                print "Finished receiving test messages."
                # Use numMessagesReceived - 1 since first msg was not measured
                print "  Msgs / sec = ", (self.numMessagesReceived - 1) / (self.finishTime - self.startTime)
                self.venueEventClient.Stop()

    def LostConnection(self, connector, reason):
        print 'TestMessages client connection lost:', reason.getErrorMessage()
        print "Stopping."
        if reactor.running:
            reactor.stop()
     

def testMain(location, privateId, channel="Test", msgLength=13, numMsgs=100, groupMsgClientClass=None, multipleClients=False):
    #from PickleGroupMsgClient import PickleGroupMsgClient
    vec = VenueEventClient(location, privateId, channel, groupMsgClientClass=groupMsgClientClass)
    tm = TestMessages(vec=vec, numMsgs=numMsgs, multipleClients=multipleClients)
    tm.SetMsgData(GenerateRandomString(length=msgLength))
    vec.Start()
    #reactor.callLater(0, tm.Send) # wait 2 secs

def mainWithUI(group="Test", groupMsgClientClass=None):

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
            frame.Show(1)
            return 1
  
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
            self.SetAutoLayout(1)
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
            channelId = group
            self.eventClient = VenueEventClient((eventHost, eventPort), 1, channelId, groupMsgClientClass=groupMsgClientClass)
            self.eventClient.RegisterEventCallback("test", self.OnTest)
            self.eventClient.RegisterMadeConnectionCallback(self.MadeConnection)
            self.eventClient.RegisterLostConnectionCallback(self.LostConnection)
            self.eventClient.Start()

            #timeout = 3
            #timeStart = time.time()
            #while (not self.eventClient.IsConnected()) and (timeout > time.time() - timeStart):
            #    print "Waiting for connection"
            #    time.sleep(1)
            #self.eventClient.Send("connect", "")    
                        
            # cleanup
            EVT_CLOSE(self, self.OnCloseWindow)
            
            self.show_status("Connecting to %s on port %d." % 
                             (eventHost, eventPort))

            reactor.interleave(wxCallAfter)

        def MadeConnection(self):
            eventHost = self.eventClient.location[0]
            eventPort = self.eventClient.location[1]
            self.show_status("Connected to %s on port %d." % 
                             (eventHost, eventPort))

        def OnCloseWindow(self, event):
            self.shutdown_network()
            # Do rest of shutdown when LostConnection callback is called.

        def OnChar(self, event):
            key = event.KeyCode()
            
            if key == 27:
                self.Close(1)
          
            else:
                self.eventClient.Send("test", chr(key))
                return

        def TimeToQuit(self, event):
            print "TimeToQuit"
            self.Close(1)

        def OnTest(self, evt):
            string = "channelId = %s, senderId = %s, data = %s"%(evt.GetChannelId(), evt.GetSenderId(), evt.GetData())
            wxCallAfter(wxLogMessage,"Received: \"%s\"." % string)

        def shutdown_network(self):
            wxLogMessage('Shutting down event client.')
            self.eventClient.Stop()

        def LostConnection(self, connector, reason):
            print "wx Test: Lost connection", reason
            reactor.addSystemEventTrigger('after', 'shutdown', self.Destroy)
            reactor.stop()

        def show_status(self,t):
            self.SetStatusText(t)

    # Start the ui main thread.
    app = MyApp(0)
    #app.MainLoop()
    return app

def main():
    wxapp = None
    if "--psyco" in sys.argv:
        print "optimizing with psyco."
        import psyco
        psyco.full()
    group = "Test"
    testMessageSize = 13
    useUI = True
    multipleClients = False
    location = ('localhost',8002)
    privateId = GenerateRandomString(length=6)
    format='xml' # or 'pickle'
    numMsgs = 10
    for arg in sys.argv:
        if arg.startswith("--group="):
            group = arg.lstrip("--group=")
            print "Setting group:", group
        if arg.startswith("--perf"):
            print "Measuring performance for single client."
            useUI = False 
        if arg.startswith("--largeMsg"):
            print "Using large messages (1000 bytes)"
            testMessageSize = 1000
        if arg.startswith("--format="):
            format = arg.lstrip("--format=")
        if arg.startswith("--multiClient"):
            multipleClients = True
        if arg.startswith("--numMsgs="):
            numMsgs = int(arg.lstrip("--numMsgs="))
            print "Setting number of messages:", numMsgs

    if format=='xml':
        from AccessGrid.XMLGroupMsgClient import XMLGroupMsgClient
        groupMsgClientClass = XMLGroupMsgClient
    elif format=='pickle':
        from AccessGrid.PickleGroupMsgClient import PickleGroupMsgClient
        groupMsgClientClass = PickleGroupMsgClient
    else:
        raise Exception("Unknown format")

    if useUI:
        wxapp = mainWithUI(group=group, groupMsgClientClass=groupMsgClientClass)
        wxapp.MainLoop()
    else:
        testMain(location=location, privateId=privateId, channel=group, msgLength=testMessageSize, numMsgs=numMsgs, groupMsgClientClass=groupMsgClientClass, multipleClients=multipleClients)
        reactor.run()

if __name__ == '__main__':
    # need to parse for wx here to be able to get wx imports 
    #    and the threadedselectreactor that wx requires.
    useUI = True
    for arg in sys.argv:
        if arg.startswith("--perf"):
            useUI = False
    if useUI:
        from wxPython.wx import *
        from twisted.internet import threadedselectreactor
        threadedselectreactor.install()
    from twisted.internet import reactor

    main()

from twisted.internet import reactor

