#!/usr/bin/python2
#-----------------------------------------------------------------------------# Name:        EventServiceTest.py
# Purpose:     Test for event client and service.
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: EventServiceTest.py,v 1.1 2003-11-12 17:59:08 lefvert Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#---------------------------------------------------------------------------
from AccessGrid.Utilities import GetHostname
from AccessGrid.EventServiceAsynch import EventService
from AccessGrid.EventClient import EventClient
from AccessGrid.Events import Event, ConnectEvent
from AccessGrid import Events
from AccessGrid.Descriptions import DataDescription
from AccessGrid.GUID import GUID
import logging, logging.handlers
import os, time
from AccessGrid.Platform import GetUserConfigDir

class EventServiceController:
    def __init__(self, host, port):
        self.uniqueId = str(GUID())

        self.eventService = EventService((host, int(port)))
        self.eventService.start()
        self.eventService.AddChannel(self.uniqueId)

    def DistributeEvents(self):
        dataDescription  = DataDescription("Data")
        
        for i in range(10):
            print '--- distribute add data event'
            self.eventService.Distribute( self.uniqueId,
                                          Event( Event.ADD_DATA,
                                                 self.uniqueId,
                                                 dataDescription ) )
                
    def GetChannelId(self):
        return self.uniqueId

    def GetLocation(self):
        return self.eventService.GetLocation()

    def ShutDown(self):
        self.eventService.Stop()

   
class EventServiceSender:
    def __init__(self):
        self.privateId = str(GUID())
        
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

    def SendEvents(self):
        # Create DataDescription
        dataDescription = DataDescription("Data")
                        
        # Send data event
        self.eventClient.Send(Events.AddDataEvent(self.channelId, 
                                                  dataDescription))    
                  
class EventServiceReceiver:
    def __init__(self):
        self.privateId = str(GUID())
        
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
        print 'Recieved Add User Event'
    
    def RemoveUserEvent(self, event):
        print 'Recieved Remove User Event'

    def ModifyUserEvent(self, event):
        print 'Recieved Modify User Event'
            
    def AddDataEvent(self, event):
        print 'Recieved Add Data Event'

    def UpdateDataEvent(self, event):
        print 'Recieved Update Data Event'
    
    def RemoveDataEvent(self, event):
        print 'Recieved Remove Data Event'
    
    def AddServiceEvent(self, event):
        print 'Recieved Add Service Event'
    
    def RemoveServiceEvent(self, event):
        print 'Recieved Remove Service Event'
    
    def AddApplicationEvent(self, event):
        print 'Recieved Add Application Event'
    
    def RemoveApplicationEvent(self, event):
        print 'Recieved Remove Application Event'
    
    def AddConnectionEvent(self, event):
        pass
    
    def RemoveConnectionEvent(self, event):
        pass
    
    def SetConnectionsEvent(self, event):
        pass
    
    def AddStreamEvent(self, event):
        pass
    
    def ModifyStreamEvent(self, event):
        pass
    
    def RemoveStreamEvent(self, event):
        pass

def SetLogging():
    debugMode = 1
    logFile = None
    
    log = logging.getLogger("AG.VenueClient")
    log = logging.getLogger("AG")
    log.setLevel(logging.DEBUG)
    
    if logFile is None:
        logname = os.path.join(GetUserConfigDir(), "VenueClient.log")
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
    
    esc = EventServiceController(GetHostname(), 8899)
    
    ess = EventServiceSender()
    esr = EventServiceReceiver()

    esr.CreateEventClient(esc.GetChannelId(), esc.GetLocation())
   
    
    ess.CreateEventClient(esc.GetChannelId(), esc.GetLocation())
    ess.SendEvents()

    esc.DistributeEvents()
    
    time.sleep(2)
    esc.ShutDown()
    ess.ShutDown()
    esr.ShutDown()
