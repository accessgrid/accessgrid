#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        GroupMsgClient.py
# Purpose:     A Group Messaging service client.
# Created:     2005/09/09
# RCS-ID:      $Id: GroupMsgClient.py,v 1.2 2005-09-28 20:13:44 eolson Exp $
# Copyright:   (c) 2005 
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from AccessGrid import Log

log = Log.GetLogger(Log.GroupMsgClient)
Log.SetDefaultLevel(Log.GroupMsgClient, Log.DEBUG)

from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import Int32StringReceiver
from GroupMsgDefines import GroupDoesNotExistException, NotConnectedException, UnspecifiedErrorException, IncompatibleVersionException, UnpackUByte, ERROR, ServerUnableToSendException, ClientNotInGroupException, GeneralReceivedErrorException
import sys, time
import threading

class GroupMsgClientProtocol(Int32StringReceiver):
    def connectionMade(self):
        # send handshake info which includes the group we'd like to join
        self.factory.startHandshake(self)

    def stringReceived(self, line):
        self.factory.linesReceived += 1
        if self.factory.startedSending == False:
            self.ReceiveConnectResponse(line)
        else:
            self.factory.receivedMessages += 1
            if self.factory.receiveCallback != None:
                apply(self.factory.receiveCallback, [line])
            else:
                log.info("Group message: %s", line)
            
    def ReceiveConnectResponse(self, data):
        version = UnpackUByte(data[0])
        if version == "1":
            # versionIteration = UnpackUByte(data[1]) # Not used yet
            # Handshake finished
            self.factory.clientConnectionMade(connectionId=data[2:])
        elif version == "0":
            err = self.ReceiveError(data)
        else:
            raise IncompatibleVersionException("Client supports version 1 only.  Server is version " + str(version) )
        
    def ReceiveError(self, data):
        if len(data) < 2:
            raise UnspecifiedErrorException()
        errorCode = int(UnpackUByte(data[1]))
        if errorCode == ERROR.NO_SUCH_GROUP:
            raise GroupDoesNotExistException()
        elif errorCode == ERROR.SERVER_UNABLE_TO_SEND:
            raise ServerUnableToSendException()
        elif errorCode == ERROR.CLIENT_NOT_IN_GROUP:
            raise ClientNotInGroupException()
        else:
            raise GeneralReceivedErrorException(errorCode)

class ClientConnectionFailed(Exception):
    """
    This exception is used to indicate the client's attempt
    to connect the the group msg service have failed.
    """
    pass

class GroupMsgClientFactory(ClientFactory):
    protocol = GroupMsgClientProtocol

    def __init__(self):
        self.connection=None
        self.connectionId=None
        self.receiveCallback = None
        self.lostConnectionCallback = None
        self.madeConnectionCallback = None
        self.measurePerformance = False

    def startHandshake(self, connection):
        connection.sendString(str(self.group))
        self.startedSending = False
        self.connection = connection

    def setReceiveCallback(self, callback):
        self.receiveCallback = callback

    def setLostConnectionCallback(self, callback):
        self.lostConnectionCallback = callback

    def setMadeConnectionCallback(self, callback):
        self.madeConnectionCallback = callback

    def startFactory(self):
        self.linesReceived = 0
        self.receivedMessages = 0
        self.timeStart = 0
        self.timeFinish = 0
        self.connection=None

    def stopFactory(self):
        self.connection=None
        pass

    def setConnectionId(self, connectionId):
        self.connectionId = connectionId

    def setGroup(self, group):
        self.group = group

    def clientConnectionMade(self, connectionId):
        self.setConnectionId(connectionId)
        log.info("Connected.  Connection ID: %s", self.connectionId)
        self.startedSending = True
        self.timeStart = time.time()
        self.timeFinish = 0
        if self.madeConnectionCallback != None:
            apply(self.madeConnectionCallback)

    def clientConnectionFailed(self, connector, reason):
        log.error('connection failed: %s', reason.getErrorMessage())
        raise ClientConnectionFailed

    def clientConnectionLost(self, connector, reason):
        if self.measurePerformance:
            delta = self.timeFinish - self.timeStart
            if (delta > 0):
                print "msgs per sec:", self.receivedMessages * 1.0 / delta
                print "secs per msg:", delta * 1.0 / self.receivedMessages
            self.connection=None

        if self.lostConnectionCallback != None:
            apply(self.lostConnectionCallback, [connector, reason])
        else:
            log.info('connection lost: %s', reason.getErrorMessage())


class GroupMsgClient:
    def __init__(self, location, privateId, channel):
        self.id = privateId
        self.location = location
        self.channelId = channel
        self.factory = GroupMsgClientFactory()
        self.factory.setGroup(channel)
        self.factory.setReceiveCallback(self.Receive)
        self.factory.setLostConnectionCallback(self.LostConnection)
        self.factory.setMadeConnectionCallback(self.MadeConnection)
        self.receiveCallback = None
        self.lostConnectionCallback = None

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

    def Start(self, wxapp=None):
        host = self.location[0]
        port = self.location[1]
        # late import to allow for selecting type of reactor
        from twisted.internet import reactor
        reactor.connectTCP(host, port, self.factory)

    def Stop(self):
        if self.factory.connection != None:
            self.factory.connection.transport.loseConnection()
            self.factory.connection = None

    def Send(self, data):
        if self.factory.connection == None:
            raise NotConnectedException
        self.factory.connection.sendString(data) # for Int32StringReceiver

    def Receive(self, data):
        if self.receiveCallback != None:
            apply(self.receiveCallback, [data])

    def LostConnection(self, connector, reason):
        if self.lostConnectionCallback != None:
            apply(self.lostConnectionCallback, [connector, reason])
        else:
            log.info('GroupMsgClient: connection lost: %s', reason.getErrorMessage())

    def MadeConnection(self):
        if self.madeConnectionCallback != None:
            apply(self.madeConnectionCallback)
        else:
            log.info('GroupMsgClient: made connection.')

    def IsConnected(self):
        if self.factory.connection==None:
            return False
        elif self.factory.connection.transport.connected == 1:
            return True
        return False

#
# Test Code Below
#

class TestMessages:
    '''
    Class for sending test messages on a VenueEventClient.
    Starts sending test messages after a connection is made.
    '''
    numMsgsDefault=10000

    def __init__(self, gmc=None, numMsgs=None, multipleClients=False):
        self.msgData = "1234567890123"
        if numMsgs == None:
            self.numExpectedMsgs = numMsgsDefault
        else:
            self.numExpectedMsgs = numMsgs
        self.numMessagesReceived = 0
        self.numSentMessages = 0
        self.startTime = 0
        self.finishTime = 0
        self.groupMsgClient = gmc
        self.maxMessagesPerSend = 15
        self.multiClient = multipleClients
        self.multiClientTimeout = 15
        if self.groupMsgClient != None:
            self.groupMsgClient.RegisterReceiveCallback(self.Receive)
            self.groupMsgClient.RegisterLostConnectionCallback(self.LostConnection)
            self.groupMsgClient.RegisterMadeConnectionCallback(self.StartSending)

    def StartSending(self):
        reactor.callLater(0, self.Send)

    def SetMsgData(self, data):
        self.msgData = data

    def SetVenueEventClient(self, vec):
        self.groupMsgClient = vec

    def Send(self):
        # Send one message to eliminate any python setup times from measurements.
        if self.numSentMessages == 0:
            self.groupMsgClient.Send(self.msgData)
            self.numSentMessages += 1
        else:
        
            if self.numMessagesReceived == 1:
                self.startTime = time.time()

            if self.numMessagesReceived >= 1:
                numToSend = min( self.maxMessagesPerSend, (self.numExpectedMsgs - self.numSentMessages))
                for i in range(numToSend):
                    self.groupMsgClient.Send(self.msgData)
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
                print "  Msgs (%d bytes)/ sec = " % (len(self.msgData)), (self.numMessagesReceived - 1) / (self.finishTime - self.startTime)
                self.groupMsgClient.Stop()

    def LostConnection(self, connector, reason):
        print 'TestMessages client connection lost:', reason.getErrorMessage()
        print "Stopping."
        if reactor.running:
            reactor.stop()

# for testing
def GenerateRandomString(length=6):
    import string, random
    random.seed(99)
    letterList = [random.choice(string.letters) for x in xrange(length)]
    retStr = "".join(letterList)
    return retStr

def testMain(location, privateId, channel="Test", msgLength=13, numMsgs=1000, multipleClients=False):
    gmc = GroupMsgClient(location, privateId, channel)
    gmc.measurePerformance = True
    tm = TestMessages(gmc=gmc, numMsgs=numMsgs, multipleClients=multipleClients)
    tm.SetMsgData(GenerateRandomString(length=msgLength))
    gmc.Start() # Connect

def simpleMain(group="Test"):
    factory = GroupMsgClientFactory()
    factory.setGroup(group)
    reactor.connectTCP('localhost', 8002, factory)

if __name__ == '__main__':
    if "--psyco" in sys.argv:
        import psyco
        psyco.full()
    group = "Test"
    testMessageSize = 13
    numMsgs = 1000
    for arg in sys.argv:
        if arg.startswith("--group="):
            group = arg.lstrip("--group=")
            print "Setting group:", group
        if arg.startswith("--msgSize="):
            testMessageSize = int(arg.lstrip("--msgSize="))
            #print "Using messages size(%d bytes)" % testMessageSize
        if arg.startswith("--numMsgs="):
            numMsgs = int(arg.lstrip("--numMsgs="))
            print "Setting number of messages:", numMsgs

    from twisted.internet import reactor
    #simpleMain(group=group)
    location = ('localhost',8002)
    privateId = GenerateRandomString(length=6)
    testMain(location=location, privateId=privateId, channel=group, msgLength=testMessageSize, numMsgs=numMsgs, multipleClients=False)
    reactor.run()

