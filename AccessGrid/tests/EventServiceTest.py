#!/usr/bin/python2
#-----------------------------------------------------------------------------#
# Name:        EventServiceTest.py
# Purpose:     Test for event client and service.
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: EventServiceTest.py,v 1.4 2003-11-14 22:08:24 lefvert Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#---------------------------------------------------------------------------

from AccessGrid.Utilities import GetHostname
from AccessGrid.EventServiceAsynch import EventService
from AccessGrid.EventClient import EventClient
from AccessGrid.Events import Event, ConnectEvent
from AccessGrid import Events
from AccessGrid.Descriptions import DataDescription, ServiceDescription
from AccessGrid.Descriptions import ApplicationDescription, StreamDescription
from AccessGrid.Descriptions import ConnectionDescription
from AccessGrid.GUID import GUID
import logging, logging.handlers
import os, time
from AccessGrid.Platform import GetUserConfigDir
from AccessGrid.Utilities import ServerLock
from AccessGrid.ClientProfile import ClientProfile


class StartTest:
    '''
    Tests event service and client
    
    EventServiceController - Starts event service and distributes events
    EventServiceClient - Has an event client and receives events
     
    Several EventServiceClients can be started that will receive all distributed events.
    
    The result shows distributed events and which events got received by which client.
    '''
    
    def __init__(self, host, port, nrOfClients, nrOfEvents):
        '''
        Starts test

        *** Arguments ***
        *host* Machine where event service will run
        *port* Port used by event service on given host
        *nrOfClients* Number of clients receiving events
        *nrOfEvents* How many of each event will be sent (1 ~ 15 events)
        '''
        
        print '**************************************************'
        print 'Test Started\nThis test will take about 30 sec. to finish'
        print '**************************************************\n'
        
        self.eventsOut = []
        self.nrOfReceivedEvents = 0
        self.sendLock = ServerLock("send")
        self.receiveLock =  ServerLock("receive")
        self.nrOfEvent = nrOfEvents
        self.nrOfClients = nrOfClients
        self.clientList = []
        self.host = host 
        self.port = port 
        self.index = 1
        self.esc = EventServiceController(self)
                
        # Sleep to make sure the event client gets started before sending events.
        time.sleep(2)
        self.CreateEvents()
        self.StartClients()
        time.sleep(5)
        self.DistributeEvents()

        # Shut down
        i = 1
        while i:
            if self.nrOfReceivedEvents ==  self.totalEvents:
                self.ShutDown()
                i = 0
        
    def CreateEvents(self):
        dataDescription = DataDescription("")
        profile = ClientProfile()
        service = ServiceDescription("service", "desc", "uri", "mime")
        stream = StreamDescription("")
        conn = ConnectionDescription("")
        app = ApplicationDescription(1, 'app', 'desc', 'uri', 'mime')
        
        
        self.sendEvents = [Events.AddDataEvent(self.esc.GetChannelId(), dataDescription),
                      Events.UpdateDataEvent(self.esc.GetChannelId(), dataDescription),
                      Events.RemoveDataEvent(self.esc.GetChannelId(), dataDescription)]
                   
        self.distributeEvents = [Event( Event.ADD_DATA, self.esc.GetChannelId(), dataDescription ),
                            Event( Event.UPDATE_DATA, self.esc.GetChannelId(), dataDescription ),
                            Event( Event.REMOVE_DATA, self.esc.GetChannelId(), dataDescription ),
                            Event( Event.ENTER, self.esc.GetChannelId(), profile) ,
                            Event( Event.MODIFY_USER, self.esc.GetChannelId(), profile) ,
                            Event( Event.EXIT, self.esc.GetChannelId(), profile) ,
                            Event( Event.ADD_SERVICE, self.esc.GetChannelId(), service),
                            Event( Event.REMOVE_SERVICE, self.esc.GetChannelId(), service),
                            Event( Event.ADD_APPLICATION, self.esc.GetChannelId(), app),
                            Event( Event.REMOVE_APPLICATION, self.esc.GetChannelId(), app) ,
                            Event( Event.ADD_CONNECTION, self.esc.GetChannelId(), conn) ,
                            Event( Event.REMOVE_CONNECTION, self.esc.GetChannelId(), conn),
                            Event( Event.ADD_STREAM, self.esc.GetChannelId(), stream),
                            Event( Event.MODIFY_STREAM, self.esc.GetChannelId(), stream),
                            Event( Event.REMOVE_STREAM, self.esc.GetChannelId(), stream)]

        # Each client will receive all events.
        self.totalEvents = self.nrOfClients * len(self.distributeEvents) * self.nrOfEvent
        print 'Starting one event service and %s event clients' %(nrOfClients)
        

    def DistributeEvents(self):
        index = 0
        
        for i in range(self.nrOfEvent):
            index = index + 1
           
            for event in self.distributeEvents:
                event.data.name =" D-"+str(index)
                self.esc.DistributeEvents(event)
            
    def StartClients(self):
        print "\nWait until clients received all events. If this hangs \nfor more than a minute, some evemts did not get received.\n"

        for i in range(nrOfClients):
            client = EventServiceClient(self)
            client.CreateEventClient(self.esc.GetChannelId(), self.esc.GetLocation())
            self.clientList.append(client)
        
    def ReceivedEvent(self):
        self.receiveLock.acquire()
        self.nrOfReceivedEvents = self.nrOfReceivedEvents + 1
        
        if self.nrOfReceivedEvents == self.totalEvents:
            self.receiveLock.release()
          
            # All events are received
            self.ShowResult()
                                   
        else:
            self.receiveLock.release()
            

    def ShowResult(self):
        print '------------ RESULT --------------\n'
        print "['event type D/S-index'] where \nD = Distributed from event service\nS = Sent from event client\nindex = unique identifier\n"
        print "Sent/distributed events:\n %s\n"%(self.eventsOut)
        
        # Print all messages sent and received
        for client in self.clientList:
            print "Client%s received:\n %s\n"%(client.GetName(), client.eventReceivedList)

                        
        rightOrder = 1
        receivedAllEvts = 1
        
        for client in self.clientList:
            notReceived = []
            for event in self.eventsOut:
                if event not in client.eventReceivedList:
                    receivedAllEvts = 0
                    notReceived.append(event)

            if len(notReceived)>0:
                print 'client'+client.GetName()+ " did not receive messages: "+str(notReceived)

            if not self.eventsOut == client.eventReceivedList:
                rightOrder = 0
                print 'client'+client.GetName()+ ' did not receive events in right order.\n'
                
        if receivedAllEvts:
            print '*** SUCCESS - All events sent got received. ***'

        else:
            print '*** FAIL - All events did not get received. ***'


        if rightOrder:
            print '*** SUCCESS - All events sent got received in right order. ***'
        else:
            print '*** FAIL - All events did NOT get received in right order. ***'
                    
        print '--------------------------------------\n'


    def ShutDown(self):
        '''Shut down service and clients'''
        print 'Shut down'
        for client in self.clientList:
            client.ShutDown()
        self.esc.ShutDown()
     
       
class EventServiceController:
    '''
    Starts event service and distributes events.
    '''
    
    def __init__(self, parent):
        '''Starts event service'''
        self.uniqueId = str(GUID())
        self.eventList = parent.eventsOut
        self.eventService = EventService((parent.host, int(parent.port)))
        self.eventService.start()
        self.eventService.AddChannel(self.uniqueId)
        self.lock = parent.sendLock
        self.nrOfEvent = parent.nrOfEvent
        
    def DistributeEvents(self, event):
        '''Distributes event'''
        self.lock.acquire()
        self.eventList.append(event.eventType+event.data.name)
        self.lock.release()
        
        self.eventService.Distribute(self.uniqueId, event)
        
    def GetChannelId(self):
        '''Returns channel id'''
        return self.uniqueId

    def GetLocation(self):
        '''Returns location (host, port)'''
        return self.eventService.GetLocation()

    def ShutDown(self):
        '''Stops event service '''
        self.eventService.Stop()

   
class EventServiceClient:
    '''
    Sends events.
    '''
    def __init__(self, parent):
        '''
        Starts EventServiceSender
        '''
        self.privateId = str(GUID())
        self.eventOutList = parent.eventsOut
        self.eventReceivedList = []
        self.lock = parent.sendLock
        self.nrOfEvent = parent.nrOfEvent
        self.parent = parent
        self.name = parent.index
        parent.index = parent.index + 1

    def GetName(self):
        '''Returns unique name of client'''
        return str(self.name)
                
    def CreateEventClient(self, channelId, eventLocation):
        '''Create event client and register events'''
        self.eventLocation = eventLocation
        self.channelId = channelId

        # Create event client and connect to event service.
        self.eventClient = EventClient(self.privateId,
                                       self.eventLocation,
                                       str(self.channelId))
        self.ReceiveEvents()
        self.eventClient.start()
        self.eventClient.Send(ConnectEvent(self.channelId,self.privateId))

    def ShutDown(self):
        '''Stop event client'''
        self.eventClient.Stop()

    def SendEvents(self, event):
        '''Send events'''
        index = 0

        for i in range(self.nrOfEvent):
            index = index + 1
            event.data.name = " S-" + str(index)
            
            self.lock.acquire()
            self.eventOutList.append(event.eventType+event.data.name)
            self.lock.release()
            
            self.eventClient.Send(event)

    def ReceiveEvents(self):
        '''Registers event callbacks'''
        coherenceCallbacks = {
            Event.ENTER: self.AddUserEvent,
            Event.EXIT: self.RemoveUserEvent,
            Event.MODIFY_USER: self.ModifyUserEvent,
            Event.ADD_DATA: self.AddDataEvent,
            Event.UPDATE_DATA: self.UpdateDataEvent,
            Event.REMOVE_DATA: self.RemoveDataEvent,
            Event.ADD_SERVICE: self.AddServiceEvent,
            Event.REMOVE_SERVICE: self.RemoveServiceEvent,
            Event.ADD_APPLICATION: self.AddApplicationEvent,
            Event.REMOVE_APPLICATION: self.RemoveApplicationEvent,
            Event.ADD_CONNECTION: self.AddConnectionEvent,
            Event.REMOVE_CONNECTION: self.RemoveConnectionEvent,
            Event.SET_CONNECTIONS: self.SetConnectionsEvent,
            Event.ADD_STREAM: self.AddStreamEvent,
            Event.MODIFY_STREAM: self.ModifyStreamEvent,
            Event.REMOVE_STREAM: self.RemoveStreamEvent
            }

        for e in coherenceCallbacks.keys():
            self.eventClient.RegisterCallback(e, coherenceCallbacks[e])

    #
    # Event callbacks
    #

    def AddUserEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()
            
    def RemoveUserEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()

    def ModifyUserEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()
                    
    def AddDataEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()
        
    def UpdateDataEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()
        
    def RemoveDataEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()
                    
    def AddServiceEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()
            
    def RemoveServiceEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()
            
    def AddApplicationEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()
              
    def RemoveApplicationEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()
         
    def AddConnectionEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()
             
    def RemoveConnectionEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()
            
    def SetConnectionsEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()

    def AddStreamEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()
            
    def ModifyStreamEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()
                    
    def RemoveStreamEvent(self, event):
        self.eventReceivedList.append(event.eventType+event.data.name)
        self.parent.ReceivedEvent()

                         

def SetLogging():
    debugMode = 1
    logFile = None
    
    log = logging.getLogger("AG")
    log.setLevel(logging.DEBUG)
    
    if logFile is None:
        logname = os.path.join(GetUserConfigDir(), "Test.log")
    else:
        logname = logFile
        
    hdlr = logging.FileHandler(logname)
    extfmt = logging.Formatter("%(asctime)s %(thread)s %(name)s %(filename)s:%(lineno)s %(levelname)-5s %(message)s", "%x %X")
    fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
    hdlr.setFormatter(extfmt)
    log.addHandler(hdlr)
    
    if debugMode:
        hdlr = logging.StreamHandler()
        hdlr.setFormatter(fmt)
        log.addHandler(hdlr)

       
if __name__ == "__main__":

    SetLogging()

    host = GetHostname()
    port = 8889
    nrOfClients = 4
    nrOfEvents = 1

    StartTest(host, port, nrOfClients, nrOfEvents)
      

























