#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        GroupMsgClientBase.py
# Purpose:     A base class for building more complex messaging services.
# Created:     2005/09/09
# RCS-ID:      $Id: GroupMsgClientBase.py,v 1.1 2005-09-23 22:08:17 eolson Exp $
# Copyright:   (c) 2005 
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from GroupMsgClient import GroupMsgClient

class GroupMsgClientBase:
    '''
    Helper Base class for classes that wish to use GroupMsgClient.
    Useful for adding layers on top of the base group messages.
    Inheriting this class mostly provides callback code.
    '''

    def __init__(self, location, privateId, channel, groupMsgClientClass=GroupMsgClient):
        self.receiveCallback = None
        self.lostConnectionCallback = None
        self.madeConnectionCallback = None
        self.groupMsgClient = apply(groupMsgClientClass, [location, privateId, channel])
        self.groupMsgClient.RegisterReceiveCallback(self.Receive)
        self.groupMsgClient.RegisterLostConnectionCallback(self.LostConnection)
        self.groupMsgClient.RegisterMadeConnectionCallback(self.MadeConnection)

    def RegisterLostConnectionCallback(self, callback):
        self.lostConnectionCallback = callback

    def RegisterMadeConnectionCallback(self, callback):
        self.madeConnectionCallback = callback

    def RegisterReceiveCallback(self, callback):
        self.receiveCallback = callback

    def LostConnection(self, connector, reason):
        if self.lostConnectionCallback != None:
            apply(self.lostConnectionCallback, [connector, reason])
        else:
            print 'GroupMsgClientBase: connection lost:', reason.getErrorMessage()

    def MadeConnection(self):
        if self.madeConnectionCallback != None:
            apply(self.madeConnectionCallback)
        else:
            print 'GroupMsgClientBase: made connection.'

    def Receive(self, data):
        if self.receiveCallback != None:
            apply(self.receiveCallback, [data])
        else:
            print "GroupMsgClientBase Received:", data

    def Send(self, data):
        self.groupMsgClient.Send(data)

    def Start(self):
        self.groupMsgClient.Start()

    def Stop(self):
        self.groupMsgClient.Stop()



class Layer1(GroupMsgClientBase):
    def Send(self, data):
        sendData = "|1|" + data + "|1|"
        print "Layer1 send:", sendData
        self.groupMsgClient.Send(sendData)

    def Receive(self, data):
        unpackedData = data.lstrip("|1|").rstrip("|1|")
        if self.receiveCallback != None:
            print "Layer1 GroupMsgClient Received:", unpackedData
            apply(self.receiveCallback, [unpackedData])
        else:
            print "Layer1 GroupMsgClient Received:", unpackedData


class Layer2(GroupMsgClientBase):
    def Send(self, data):
        sendData = "_2_" + data + "_2_"
        print "Layer2 send:", sendData
        self.groupMsgClient.Send(sendData)

    def Receive(self, data):
        unpackedData = data.lstrip("_2_").rstrip("_2_")
        if self.receiveCallback != None:
            apply(self.receiveCallback, [unpackedData])
        else:
            print "Layer2 MsgClient Received:", unpackedData
        reactor.stop()

class SingleMessageTester:
    '''
    Sends a single message once connected.
    Disconnects and Quits after receiving the message
    '''
    def __init__(self, gmc, message="message"):
        self.gmc = gmc
        self.message = message
        self.gmc.RegisterReceiveCallback(self.ReceiveOne)
        self.gmc.RegisterMadeConnectionCallback(self.StartSending)
        self.gmc.RegisterLostConnectionCallback(self.LostConnection)

    def StartSending(self):
        self.Send(self.message)

    def Send(self, message):
        print "Sending message:", message
        self.gmc.Send(message)

    def ReceiveOne(self, message):
        print "Received Message:", message
        self.gmc.Stop() # disconnect now that we received our one message

    def LostConnection(self, connector, reason):
        # quit
        if reactor.running:
            reactor.stop()


if __name__ == '__main__':
    # How to use multiple layers (example: first layer XML, second layer custom events)
    groupMsgLayer2 = Layer2(location=('localhost',8002), privateId="testId", channel="Test", groupMsgClientClass=Layer1)
    groupMsgLayer2.Start() # make connection

    tester = SingleMessageTester(groupMsgLayer2)

    from twisted.internet import reactor
    reactor.run()



