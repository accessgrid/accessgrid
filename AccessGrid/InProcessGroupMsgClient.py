#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        SecureGroupMsgClient.py
# Purpose:     A Secure Group Messaging service client.
# Created:     2005/10/10
# RCS-ID:      $Id: InProcessGroupMsgClient.py,v 1.1 2006-01-24 17:18:19 eolson Exp $
# Copyright:   (c) 2005 
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import struct
from GroupMsgClient import TestMessages, GenerateRandomString
from twisted.internet import address
from twisted.protocols.basic import Int32StringReceiver
from twisted.internet.error import ConnectionDone
from twisted.python.failure import Failure

class DummyAddress:
    def __init__(self):
        self.host = None
        self.port = None
        self.type = None

class DummyConnectionInt32String:
    def __init__(self, parent, receiveCallback):
        self.address = DummyAddress()
        self.receiveCallback = receiveCallback
        self.parent = parent

    def write(self, recvd_strng):
        # simply decode the string and call the receive callback.

        length ,= struct.unpack("!i",recvd_strng[:4])
        if length > Int32StringReceiver.MAX_LENGTH:
            if self.parent.lostConnectionCallback != None:
                self.parent.lostConnectionCallback() # self.transport.loseConnection()
            return

        packet = recvd_strng[4:length+4]
        self.receiveCallback(packet)

    def getPeer(self):
        return self.address


class InProcessGroupMsgClient:
    def __init__(self, eventService, privateId, groupId):
        self.eventService = eventService
        self.id = privateId
        self.location = None
        self.groupId = groupId
        self.receiveCallback = None
        self.lostConnectionCallback = None
        self.madeConnectionCallback = None
        self.connection = DummyConnectionInt32String(self, self.Receive)

        self.eventService.factory.connectionMade(self.connection)
        self.eventService.factory.addConnection(self.connection, groupId)

    def Start(self):
        self.madeConnectionCallback()

    def Stop(self):
        self.eventService.factory.removeConnection(self.connection)
        self.lostConnectionCallback(None, reason=Failure(ConnectionDone))

    def Send(self, data):
        self.eventService.factory.sendGroupMessage(self.connection, data)

    def Receive(self, data):

        if self.receiveCallback != None:
            self.receiveCallback(data)

    def RegisterReceiveCallback(self, callback):
        '''
        Called when a msg is received.
        arguments: (data)
        '''
        self.receiveCallback = callback

    def RegisterLostConnectionCallback(self, callback):
        '''
        Called when a connection is lost.
        arguments (connector, reason)
        '''
        self.lostConnectionCallback = callback

    def RegisterMadeConnectionCallback(self, callback):
        '''
        Called when a full connection is made.
        arguments (connector, reason)
        '''
        self.madeConnectionCallback = callback


def testMain(location, privateId, channel="Test", msgLength=13, numMsgs=1000, multipleClients=False):
    gmc = SecureGroupMsgClient(location, privateId, channel)
    gmc.measurePerformance = True
    tm = TestMessages(gmc=gmc, numMsgs=numMsgs, multipleClients=multipleClients)
    tm.SetMsgData(GenerateRandomString(length=msgLength))
    gmc.Start() # Connect

def main():
    location = ('localhost',7002)
    privateId = "some_id"
    groupName = "Test"
    numMsgs = 1000
    msgLength = 1000

    """
    gmc = SecureGroupMsgClient(location, privateId, channel=groupName)
    gmc.measurePerformance = True

    tm = TestMessages(gmc=gmc, numMsgs=numMsgs)
    import random, string
    msgData = "".join([random.choice(string.letters) for x in xrange(msgLength)])
    tm.SetMsgData(msgData)
    gmc.Start()
    """

    group = "Test"
    testMessageSize = 13
    numMsgs = 1000
    testMain(location=location, privateId=privateId, channel=group, msgLength=testMessageSize, numMsgs=numMsgs, multipleClients=False)

    from twisted.internet import reactor
    reactor.run()

if __name__ == '__main__':
    main()

