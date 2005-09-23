#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        GroupMsgService.py
# Purpose:     A Group Messaging service server.
# Created:     2005/09/09
# RCS-ID:      $Id: GroupMsgService.py,v 1.1 2005-09-23 22:08:17 eolson Exp $
# Copyright:   (c) 2005 
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import time
from AccessGrid import Log

log = Log.GetLogger(Log.EventService)
Log.SetDefaultLevel(Log.EventService, Log.DEBUG)

import sys, struct
from twisted.internet.protocol import Protocol, ServerFactory
#from twisted.protocols.basic import LineOnlyReceiver
from twisted.protocols.basic import Int32StringReceiver
from twisted.internet import reactor
from GroupMsgDefines import GroupDoesNotExistException, NotConnectedException, PackUByte, ERROR, ClientNotInGroupException
from VenueServerService import VenueServerServiceInterface

#class GroupMsgServiceProtocol(LineOnlyReceiver):
class GroupMsgServiceProtocol(Int32StringReceiver):
    protocolVersion = 1
    protocolIteration = 0 # to identify updates

    def __init__(self):
        self.groups = {}
        self.connections = {}

    def connectionMade(self):
        self.factory.connectionMade(self.transport)

    #def lineReceived(self, data):
    def stringReceived(self, data):
        #print "lineReceived", data
        connection = self.transport

        sentOk = self.factory.sendGroupMessage(connection, data)
        if sentOk == False:
            if not self.factory.connectionHasGroup(connection):
                # new connection, so data is groupId
                groupId = data
                try:
                    self.factory.addConnection(connection, groupId)
                except GroupDoesNotExistException:
                    #self.transport.write("nosuchgroup" + "\r\n")
                    #self.sendString("nosuchgroup")
                    self.sendError(ERROR.NO_SUCH_GROUP)
                    self.transport.loseConnection()
                    #print "nosuchgroup:", groupId, "possibilities:", self.factory.getGroupNames()
                        
                #self.sendLine("ok") #self.transport.write("ok" + "\r\n")
                #self.sendString("ok")
                self.sendConnectResponse(connectionId=connection.connectionId)
                #print "Wrote version 1 response ack"
                assert True==self.factory.connectionHasGroup(connection)
            elif not self.factory.connectionHasGroup(connection):
                self.sendError(ERROR.CLIENT_NOT_IN_GROUP)
                self.transport.loseConnection()
            else:
                # Existing connection.  Unable to send for 
                #   unspecified reason.
                self.sendError(ERROR.SERVER_UNABLE_TO_SEND)
                self.transport.loseConnection()

        #print "lineReceived returning"

    # for testing between LineOnlyReceiver and intNNStringReceiver
    #lineReceived = stringReceived

    def connectionLost(self, reason):
        #print "Connection lost:", reason
        self.factory.removeConnection(self.transport)

    def sendError(self, errorCode):
        self.sendString(PackUByte(str(0)) + PackUByte(str(errorCode)))

    def sendConnectResponse(self, connectionId):
        self.sendString(PackUByte(str(self.protocolVersion)) + PackUByte(str(self.protocolIteration)) + str(connectionId) )

class GroupExistsException(Exception):
    """
    This exception is used to indicate the group/channel already
    exists in the Group Service.
    """
    pass

class GroupMsgServiceFactory(ServerFactory):
    def __init__(self):
        # FIXME -- move these to the correct startup method
        self.groups = {}
        self.connections = {}

    def connectionMade(self, connection):
        # Setup a connection id for each connection
        peer = connection.getPeer()
        id = peer.host + ":" + str(peer.port)
        connection.connectionId = id
        # add connection to list, but it has no group yet
        self.connections[id] = (connection, None)

    def hasGroup(self, groupName):
        return id in self.groups.keys()

    def hasConnection(self, connection):
        id = connection.connectionId 
        if id in self.connections.keys():
            return True
        else:
            return False

    def connectionHasGroup(self, connection):
        if connection.connectionId in self.connections.keys():
            connectionTuple = self.connections[connection.connectionId]
            groupName = connectionTuple[1]
            if groupName in self.groups.keys():
                return True
            #print "connection Has no group.  Listed groupName:", groupName
        return False

    def createGroup(self, id):
        if self.hasGroup(id):
            raise GroupExistsException
        self.groups[id] = list()

    def removeGroup(self, id):
        if not self.hasGroup(self, id):
            raise GroupDoesNotExistException
        for connection in self.groups[id]:
            self.removeConnection(connection)
        del self.groups[id]

    def getGroupNames(self):
        return self.groups.keys()

    def addConnection(self, connection, groupName):
        '''
        returns connectionId
        '''
        if not groupName in self.groups.keys():
            raise GroupDoesNotExistException
        # note the group in the connection's infomartion
        self.connections[connection.connectionId] = (connection, groupName)
        # add the connection to the group's infomartion
        self.groups[groupName].append(connection)
        #print "AddedConnection", id, groupName
        assert self.connectionHasGroup(connection)

    def removeConnection(self, connection):
        connectionId = connection.connectionId
        connectionTuple = self.connections.pop(connectionId)
        groupName = connectionTuple[1]
        self.groups[groupName].remove(connection)
        #print "Removed connection:", connectionId

    def sendGroupMessage(self, connection, data):
        #print "Sending Group Message", data
        # look up group name
        groupName = self.connections[connection.connectionId][1]
        if None == groupName:
            return False  # user doesn't have a group yet

        #connectionTuple = self.connections[connection.connectionId]
        #groupName = connectionTuple[1]
        #for conn in self.groups[groupName]:
        for conn in self.groups[groupName]:
            #conn.write(data + "\r\n")  # sendLine
            #conn.write(struct.pack("!h",len(data))+data) # sendString Int16
            conn.write(struct.pack("!i",len(data))+data) # sendString Int32
        return True

class GroupMsgService:
    def __init__(self, location):
        self.location = location
        self.factory = GroupMsgServiceFactory()
        self.factory.protocol = GroupMsgServiceProtocol

    def Start(self):
        port = self.location[1]
        reactor.listenTCP(port, self.factory)
        #reactor.run()

    def Stop(self):
        reactor.stop()

    start=Start
    stop=Stop

    def CreateGroup(self, id):
        self.factory.createGroup(id)

    def RemoveGroup(self, id):
        self.factory.removeGroup(id)

    def GetGroupNames(self):
        return self.factory.getGroupNames

class GroupMsgServiceFactoryWithPerformance(GroupMsgServiceFactory):
    def __init__(self):
        GroupMsgServiceFactory.__init__(self)
        self.numMsgsReceived = 0
        self.numMsgsSent = 0
        self.performanceDisplayDelay = 2
        self.lastDisplay = time.time()

    def sendGroupMessage(self, connection, data):
        """ The same function as in superclass, but count the messages
        """ 
        groupName = self.connections[connection.connectionId][1]
        if None == groupName:
            return False  # user doesn't have a group yet

        for conn in self.groups[groupName]:
            conn.write(struct.pack("!i",len(data))+data) # sendString Int32

        self.numMsgsReceived += 1
        self.numMsgsSent += len(self.groups[groupName])
        return True

    def displayPerformance(self):
        delta = time.time() - self.lastDisplay
        if delta > 0:
            print "Received Msgs/sec:", self.numMsgsReceived / delta
            print "Sent Msgs/sec:", self.numMsgsSent / delta
        # reset for next iteration
        self.numMsgsReceived = 0
        self.numMsgsSent = 0
        reactor.callLater(self.performanceDisplayDelay, self.displayPerformance)
        self.lastDisplay = time.time()

class GroupMsgServiceWithPerformance(GroupMsgService):
    """
    A group messages service that displays performance throughput.
    """
    def __init__(self, location):
        GroupMsgService.__init__(self, location=location)
        self.factory = GroupMsgServiceFactoryWithPerformance()
        self.factory.protocol = GroupMsgServiceProtocol
        reactor.callLater(self.factory.performanceDisplayDelay, self.factory.displayPerformance)

def main():
    """
    f = GroupMsgServiceFactory()
    f.protocol = GroupMsgServiceProtocol
    f.createGroup("Test")
    reactor.listenTCP(8002, f)
    reactor.run()
    """
    showPerformance = False
    for arg in sys.argv:
        if arg.startswith("--perf"):
            showPerformance = True

    if showPerformance == True:
        groupMsgService = GroupMsgServiceWithPerformance(location=('localhost',8002))
    else:
        groupMsgService = GroupMsgService(location=('localhost',8002))
    groupMsgService.CreateGroup("Test")
    groupMsgService.Start()
    reactor.run()


if __name__ == '__main__':
    if "--psyco" in sys.argv:
        import psyco
        psyco.full()
    main()
