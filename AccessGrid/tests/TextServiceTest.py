#!/usr/bin/python2
#-----------------------------------------------------------------------------# Name:        EventServiceTest.py
# Purpose:     Test for text client and service.
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: TextServiceTest.py,v 1.3 2004-03-10 23:17:09 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#---------------------------------------------------------------------------

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid import Log
from AccessGrid.Utilities import GetHostname
from AccessGrid.TextServiceAsynch import TextService
from AccessGrid.TextClient import TextClient
from AccessGrid.GUID import GUID
import os, time
from AccessGrid.Platform import GetUserConfigDir
import threading
from AccessGrid.Utilities import ServerLock
from AccessGrid.ClientProfile import ClientProfile


class StartTest:
    '''
    Tests text service and client

    TextServiceController - Starts text service 
    TextServiceClient - Has a text client and sends/receives text messages
   
    Several TextServiceClients are created and are sending messages in separate threads.
            
    In order to show correct result, we are waiting for all TextServiceClients to receive
    all text messages sent. The result shows sent and received messages in the order
    they got sent/received.

    ISSUES:
    * If the text service has shut down before the event clients have properly disconnected,
    an exception will be raised. Solution; use sleep to make sure they have exited.
    * If the text clients try to disconnect while still receiving text messages, an exception
    will be raised. Solution: wait to show result and shut down until all clients have received
    all messages.
    * If the send threads are started before the text clients have properly connected, some
    events might not get received. Solution; use sleep to make sure clients have connected.
    '''
    def __init__(self, host, port, nrOfMessages, nrOfClients):
        '''
        Starts test

        **Arguments**
        *host* Machine where text service will run
        *port* Port used by text service on given host
        *nrOfMessages* Number of text messages sent by each client
        *nrOfClients* Number of clients sending/receiving messages
        '''
        print '**************************************************'
        print 'Test Started\nThis test will take about 30 sec. to finish'
        print '**************************************************\n'
        
        self.eventsOut = []
        self.eventsReceived = []
        self.sendLock = ServerLock("send")
        self.finishedLock = ServerLock("finished")
        self.nrOfMessages = nrOfMessages
        self.nrOfClients = nrOfClients
        self.totalNrOfMessages = self.nrOfClients * self.nrOfClients * self.nrOfMessages + 1
        self.clientsFinished = 1
        self.index = 1

        print "Nr of text clients used:", self.nrOfClients
        print "Nr of messages per client:", self.nrOfMessages
            
        self.ts = TextServiceController(host, port)
        self.StartClients()

        
    def StartClients(self):
        '''Creates text clients that send text messages in separate threads.'''

        # Create text clients
        self.tscList = []
        for i in range(self.nrOfClients):
            tsc = TextServiceClient(self)
            tsc.CreateTextClient(self.ts.GetChannelId(), self.ts.GetLocation())
            self.tscList.append(tsc)

        # Make sure the text client is properly started
        # else some events might not get received
        time.sleep(1)
                   
        # Start clients send method in threads
        print '\nStart sending text messages.'
        print "\nWait until all clients received all messages. If this hangs \nfor more than a minute, some messages did not get received.\n"

        self.threadList = []
        for tsc in self.tscList:
            thread = threading.Thread(target = tsc.SendText)
            self.threadList.append(thread)
        
        for thread in self.threadList:
            thread.start()
            
        # Join threads
        for thread in self.threadList:
            thread.join()

        # Shut down
        i = 1
        while i:
            if self.clientsFinished ==  self.totalNrOfMessages:
                self.ShutDown()
                i = 0
                     
    def ClientReceived(self):
        '''
        Is called by a text client when it has receives a message.
        When all messages are received, show the result.
        '''

        self.finishedLock.acquire()
        self.clientsFinished = self.clientsFinished + 1
        
                        
        if self.clientsFinished == self.totalNrOfMessages:
            # Each client gets each sent message
            # When all messages are received, show result and shut down
            self.finishedLock.release()
            self.ShowResult()
            
        else:
            self.finishedLock.release()
       
            
    def ShowResult(self):
        '''Prints the result'''
               
        print '--- RESULT ---'
        print "Sent text messages:\n %s\n"%(self.eventsOut)

        # Print all messages sent and received
        for client in self.tscList:
            print "%s received:\n %s\n"%(client.profile.name, client.receiveList)
                        
        receivedAllEvts = 1
        rightOrder = 1

        # For each client, check if it received all messages and if messages received
        # matches the order of messages sent.
        for client in self.tscList:
            notReceived = []
            
            for event in self.eventsOut:
                if event not in client.receiveList:
                    receivedAllEvts = 0
                    notReceived.append(event) 

            if len(notReceived)>0:
                print client.profile.name+ " did not receive messages: "+str(notReceived)

            if not self.eventsOut == client.receiveList:
                rightOrder = 0
                print client.profile.name + ' did not receive events in right order.\n'

        # Print result
        if receivedAllEvts:
            print '*** SUCCESS - All events sent got received. ***'
        else:
            print '*** FAIL - All events did not get received. ***'
            
        if rightOrder:
            print '*** SUCCESS - All events sent got received in right order. ***'
        else:
            print '*** FAIL - All events did NOT get received in right order. ***'

        print '--------------\n'

    def ShutDown(self):
        'shut down clients and service'
        
        for tsc in self.tscList:
            tsc.ShutDown()

        time.sleep(self.nrOfClients)
        # NOTE: If we don't sleep here, the service will start to shut down before
        # the clients have finished disconnecting. This will cause the text
        # service exit to raise an exception.
        
        self.ts.ShutDown()
            

class TextServiceController:
    '''
    Starts text service.
    '''
    
    def __init__(self, host, port):
        '''
        Starts text service

        **Arguments**
        *host* host where text service is running
        *port* port that text service is using
        '''
        self.uniqueId = str(GUID())
        self.textService = TextService((host, int(port)))
        self.textService.start()
        self.textService.AddChannel(self.uniqueId)
             
    def GetChannelId(self):
        return self.uniqueId

    def GetLocation(self):
        return self.textService.GetLocation()

    def ShutDown(self):
        print 'stop text service'
        self.textService.Stop()


class TextServiceClient:
    '''
    Sends/receives text messages.
    '''
    def __init__(self, parent):
        '''
        Starts TextServiceSender

        **Arguments**
        *eventList* buffer where to insert sent events
        *lock* lock for eventList (also used by EventServiceController)
        *nrOfEvents* how many events of each type should get sent
        '''
        self.parent = parent
        self.privateId = str(GUID())
        self.eventList = parent.eventsOut
        self.receiveList = []
        self.lock = parent.sendLock
        self.nrOfEvent = parent.nrOfMessages
        self.profile = ClientProfile()
        self.profile.name = "client"+str(self.parent.index)
        self.parent.index = self.parent.index + 1

    def GetName(self):
        return self.profile.name
               
    def CreateTextClient(self, channelId, textLocation):
        self.textLocation = textLocation
        self.channelId = channelId
        
        # Create text client and connect to text service.
        self.textClient = TextClient(self.profile,
                                     self.textLocation)
        self.textClient.Connect(self.channelId, self.privateId)

        self.textClient.RegisterOutputCallback(self.ReceiveText)

    def ReceiveText(self, name, message):
        self.receiveList.append(message)
        self.parent.ClientReceived()

    def SendText(self):
        i = 0
        
        for i in range(self.nrOfEvent):
            i = i + 1
            text = self.profile.name + "-"+str(i)        
            self.lock.acquire()
            self.eventList.append(text)
            self.lock.release()

            self.textClient.Input(text)
                                
    def ShutDown(self):
        print 'stop text client'
        self.textClient.Disconnect(self.channelId,
                                   self.privateId)
        
def SetLogging():
    debugMode = 1
    logFile = None
    
    if logFile is None:
        logname = os.path.join(GetUserConfigDir(), "Test.log")
    else:
        logname = logFile
        
    hdlr = Log.FileHandler(logname)
    hdlr.setLevel(Log.DEBUG)
    hdlr.setFormatter(Log.GetFormatter())
    Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())
    
    if debugMode:
        hdlr = Log.StreamHandler()
        hdlr.setFormatter(Log.GetLowDetailFormatter())
        Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())
       
if __name__ == "__main__":
    SetLogging()
    
    host = GetHostname()
    port = 8899
    nrOfMessages = 5
    nrOfClients = 5

    StartTest(host, port, nrOfMessages, nrOfClients)
    
