#!/usr/bin/python2
#-----------------------------------------------------------------------------# Name:        EventServiceTest.py
# Purpose:     Test for event client and service.
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: EventServiceTest.py,v 1.2 2003-11-12 21:50:35 lefvert Exp $
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
import threading
from AccessGrid.Utilities import ServerLock
from AccessGrid.ClientProfile import ClientProfile

class EventServiceController:
    '''
    Starts event service and distributes events.
    '''
    
    def __init__(self, host, port, eventList, lock, nrOfEvent):
        '''
        Starts event service

        **Arguments**
        *host* host where event service is running
        *port* port that event service is using
        *eventList* buffer where to insert distributed events
        *lock* lock for eventList (also used by EventServiceSender)
        *nrOfEvents* how many events of each type should get sent
        '''
        self.uniqueId = str(GUID())
        self.eventList = eventList
        self.eventService = EventService((host, int(port)))
        self.eventService.start()
        self.eventService.AddChannel(self.uniqueId)
        self.lock = lock
        self.nrOfEvent = nrOfEvent
        
    def DistributeEvents(self, event):
        index = 0
               
        for i in range(self.nrOfEvent):
            index = index + 1
            event.data.name =" D-"+str(index)
            
            self.lock.acquire()
            self.eventList.append(event.eventType+event.data.name)
            self.lock.release()
            
            self.eventService.Distribute(self.uniqueId, event)
            time.sleep(0.01)

    def GetChannelId(self):
        return self.uniqueId

    def GetLocation(self):
        return self.eventService.GetLocation()

    def ShutDown(self):
        self.eventService.Stop()

   
class EventServiceSender:
    '''
    Sends events.
    '''
    def __init__(self, eventList, lock, nrOfEvent):
        '''
        Starts EventServiceSender

        **Arguments**
        *eventList* buffer where to insert sent events
        *lock* lock for eventList (also used by EventServiceController)
        *nrOfEvents* how many events of each type should get sent
        '''
        self.privateId = str(GUID())
        self.eventList = eventList
        self.lock = lock
        self.nrOfEvent = nrOfEvent
        
    def CreateEventClient(self, channelId, eventLocation):
        self.eventLocation = eventLocation
        self.channelId = channelId
        
        # Create event client and connect to event service.
        self.eventClient = EventClient(self.privateId,
                                       self.eventLocation,
                                       str(self.channelId))

        self.eventClient.start()
        self.eventClient.Send(ConnectEvent(self.channelId,self.privateId))

    def ShutDown(self):
        self.eventClient.Stop()

    def SendEvents(self, event):
        index = 0
        name = event.data.name
                
        for i in range(self.nrOfEvent):
            index = index + 1
            event.data.name = " S-" + str(index)

            self.lock.acquire()
            self.eventList.append(event.eventType+event.data.name)
            self.lock.release()
            
            self.eventClient.Send(event)
            time.sleep(0.02)

                         
class EventServiceReceiver:
    '''
    Receives events.
    '''    
    def __init__(self, eventList):
        '''
        Starts EventServiceSender

        **Arguments**
        *eventList* buffer where to insert received events
        '''
        self.privateId = str(GUID())
        self.eventList = eventList
        self.lock = ServerLock()
        
    def CreateEventClient(self, channelId, eventLocation):
        self.eventLocation = eventLocation
        self.channelId = channelId
       
        # Create and connect to event client.
        self.eventClient = EventClient(self.privateId,
                                       self.eventLocation,
                                       str(self.channelId))

        self.ReceiveEvents()
        self.eventClient.start()
        self.eventClient.Send(ConnectEvent(self.channelId,
                                           self.privateId))
       
    def ShutDown(self):
        self.eventClient.Stop()

    def ReceiveEvents(self):
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

    def AddUserEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)
            
    def RemoveUserEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)

    def ModifyUserEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)
                    
    def AddDataEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)
        
    def UpdateDataEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)
        
    def RemoveDataEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)
                    
    def AddServiceEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)
            
    def RemoveServiceEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)
            
    def AddApplicationEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)
              
    def RemoveApplicationEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)
         
    def AddConnectionEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)
             
    def RemoveConnectionEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)
            
    def SetConnectionsEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)

    def AddStreamEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)
            
    def ModifyStreamEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)
            
    def RemoveStreamEvent(self, event):
        self.eventList.append(event.eventType+event.data.name)
        
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

    '''
    Tests event service and client

    EventServiceController - Starts event service and distributes events
    EventServiceSender - Has an event client and sends events
    EventServiceReceiver - Has an event client and receives events

    Separate threads for sending/distributing different events
    are started, events are saved in the eventsOut list.
    
    Received events are saved in the eventsReceived list.


    Compare the eventsOut list to eventsReceived to see if all events
    are received and in what order.
    '''
    
    SetLogging()

    eventsOut = []
    eventsReceived = []
    sendLock = ServerLock("send")
    nrOfEvent = 2
    
    esc = EventServiceController(GetHostname(), 8899, eventsOut,
                                 sendLock, nrOfEvent)
    ess = EventServiceSender(eventsOut, sendLock, nrOfEvent)
    esr = EventServiceReceiver(eventsReceived)

    esr.CreateEventClient(esc.GetChannelId(), esc.GetLocation())
    ess.CreateEventClient(esc.GetChannelId(), esc.GetLocation())

    print '**************************************************'
    print 'Test Started\nThis test will take about 30 sec. to finish'
    print '**************************************************\n'

    # Create data for events
    dataDescription = DataDescription("")
    profile = ClientProfile()
    service = ServiceDescription("service", "desc", "uri", "mime")
    stream = StreamDescription("")
    conn = ConnectionDescription("")
    app = ApplicationDescription(1, 'app', 'desc', 'uri', 'mime')
        
    #
    # Send threads
    #

    # -- Add data
    event = Events.AddDataEvent(esc.GetChannelId(), dataDescription)
    sendThread1 = threading.Thread(target = ess.SendEvents, args = [event])
    
    #
    # Distribute threads
    #

    # -- Add data
    event = Event( Event.ADD_DATA, esc.GetChannelId(), dataDescription ) 
    distributeThread1 = threading.Thread(target = esc.DistributeEvents,
                                        args = [event])
    # -- Update data
    event = Event( Event.UPDATE_DATA, esc.GetChannelId(), dataDescription ) 
    distributeThread2 = threading.Thread(target = esc.DistributeEvents,
                                        args = [event])
    # -- Remove data
    event = Event( Event.REMOVE_DATA, esc.GetChannelId(), dataDescription ) 
    distributeThread3 = threading.Thread(target = esc.DistributeEvents,
                                        args = [event])
    # -- Add user
    event = Event( Event.ENTER, esc.GetChannelId(), profile) 
    distributeThread4 = threading.Thread(target = esc.DistributeEvents,
                                         args = [event])
    # -- Modify user
    event = Event( Event.MODIFY_USER, esc.GetChannelId(), profile) 
    distributeThread5 = threading.Thread(target = esc.DistributeEvents,
                                         args = [event])
    # -- Remove user
    event = Event( Event.EXIT, esc.GetChannelId(), profile) 
    distributeThread6 = threading.Thread(target = esc.DistributeEvents,
                                         args = [event])
    # -- Add service
    event = Event( Event.ADD_SERVICE, esc.GetChannelId(), service) 
    distributeThread7 = threading.Thread(target = esc.DistributeEvents,
                                         args = [event])
    # -- Remove service
    event = Event( Event.REMOVE_SERVICE, esc.GetChannelId(), service) 
    distributeThread8 = threading.Thread(target = esc.DistributeEvents,
                                         args = [event])
    # -- Add application
    event = Event( Event.ADD_APPLICATION, esc.GetChannelId(), app) 
    distributeThread9 = threading.Thread(target = esc.DistributeEvents,
                                         args = [event])
    # -- Remove application
    event = Event( Event.REMOVE_APPLICATION, esc.GetChannelId(), app) 
    distributeThread9 = threading.Thread(target = esc.DistributeEvents,
                                         args = [event])
    # -- Add connection
    event = Event( Event.ADD_CONNECTION, esc.GetChannelId(), conn) 
    distributeThread10 = threading.Thread(target = esc.DistributeEvents,
                                         args = [event])
    # -- Remove connection
    event = Event( Event.REMOVE_CONNECTION, esc.GetChannelId(), conn) 
    distributeThread11 = threading.Thread(target = esc.DistributeEvents,
                                         args = [event])
    # -- Add stream
    event = Event( Event.ADD_STREAM, esc.GetChannelId(), stream) 
    distributeThread12 = threading.Thread(target = esc.DistributeEvents,
                                         args = [event])
    # -- Modify stream
    event = Event( Event.MODIFY_STREAM, esc.GetChannelId(), stream) 
    distributeThread13 = threading.Thread(target = esc.DistributeEvents,
                                         args = [event])
    # -- Remove stream
    event = Event( Event.REMOVE_STREAM, esc.GetChannelId(), stream) 
    distributeThread14 = threading.Thread(target = esc.DistributeEvents,
                                         args = [event])
    sendThread1.start()
    distributeThread1.start()
    distributeThread2.start()
    distributeThread3.start()
    distributeThread4.start()
    distributeThread5.start()
    distributeThread6.start()
    distributeThread7.start()
    distributeThread8.start()
    distributeThread9.start()
    distributeThread10.start()
    distributeThread11.start()
    distributeThread12.start()
    distributeThread13.start()
    distributeThread14.start()
    
    #
    # Join threads
    #
    sendThread1.join()
    distributeThread1.join()
    distributeThread2.join()
    distributeThread3.join()
    distributeThread4.join()
    distributeThread5.join()
    distributeThread6.join()
    distributeThread7.join()
    distributeThread8.join()
    distributeThread9.join()
    distributeThread10.join()
    distributeThread11.join()
    distributeThread12.join()
    distributeThread13.join()
    distributeThread14.join()

    # Make sure all events are received before showing result.
    time.sleep(20)

    #
    # Show results
    #
    print "['event type D/S-index'] where \nD = Distributed from event service\nS = Sent from event client\nindex = unique identifier\n"
    print "Sent/distributed events:\n %s\n"%(eventsOut)
    print "Received events:\n %s\n"%(eventsReceived)
   
    print '--- RESULT ---'
    
    for event in eventsOut:
        if event not in eventsReceived:
            print event + " was not received"

    if not eventsOut == eventsReceived:
        print '\nThe events were not received in the same order as they were sent\n'

    print '--------------'

    #
    # Shut down service and clients
    #
    esc.ShutDown()
    ess.ShutDown()
    esr.ShutDown()

