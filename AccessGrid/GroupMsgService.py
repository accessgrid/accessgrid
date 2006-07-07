#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        GroupMsgService.py
# Purpose:     A Group Messaging service server.
# Created:     2005/09/09
# RCS-ID:      $Id: GroupMsgService.py,v 1.6 2006-07-07 18:29:40 turam Exp $
# Copyright:   (c) 2005 
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import time
from AccessGrid import Log

log = Log.GetLogger(Log.EventService)
Log.SetDefaultLevel(Log.EventService, Log.DEBUG)

import sys, struct
from AccessGrid.GUID import GUID
from twisted.internet.protocol import Protocol, ServerFactory
from twisted.protocols.basic import Int32StringReceiver
from twisted.internet import reactor
from GroupMsgDefines import GroupDoesNotExistException, NotConnectedException, PackUByte, ERROR, ClientNotInGroupException

class GroupMsgServiceProtocol(Int32StringReceiver):
    protocolVersion = 1
    protocolIteration = 0 # to identify updates
    
    def __init__(self):
        self.groups = {}
        self.connections = {}

    def connectionMade(self):
        self.factory.connectionMade(self.transport)

    def stringReceived(self, data):
        #print "lineReceived", data
        connection = self.transport

        sentOk = self.factory.sendGroupMessage(connection, data)
        if sentOk == False:
            if not self.factory.connectionHasGroup(connection):
                # Client is not in any group; treat data as connect string
                # parse connection string:  grouplen,groupid,connectionlen,connectionid
                
                try:
                    if len(data) == 32:
                        # do beta1 compatibility handling
                        groupId = data
                        connectionId = GUID()
                        log.info('beta1 compat: group=%s  conn=%s' % (groupId, connectionId))
                    else:
                        grouplen = int(data[:2])
                        groupId = data[2:grouplen+2]
                        connectionlen = int(data[grouplen+2:grouplen+4])
                        connectionId = data[grouplen+4:grouplen+4+connectionlen]
                        log.info('beta2+: groupid=%s; connectionid=%s' % (groupId,connectionId))
                    self.factory.addConnection(connection, groupId, connectionId)
                except GroupDoesNotExistException:
                    self.sendError(ERROR.NO_SUCH_GROUP)
                    self.transport.loseConnection()
                except:
                    log.exception('Exception in group msg service connect')
                    self.sendError(ERROR.UNKNOWN)
                    self.transport.loseConnection()
                        
                self.sendConnectResponse(connectionId=connection.connectionId)
                #print "Wrote version 1 response ack"
                #assert True==self.factory.connectionHasGroup(connection)
            else:
                # Existing connection.  Unable to send for unspecified reason.
                log.debug('Client in group, but send failed')
                self.sendError(ERROR.SERVER_UNABLE_TO_SEND)
                self.transport.loseConnection()

    def connectionLost(self, reason):
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
        connection.connectionId = GUID()
        # add connection to list, but it has no group yet
        self.connections[connection.connectionId] = (connection, None)
        log.info("connectionMade %s:%s", connection.getPeer().host, connection.getPeer().port)

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
        if not self.hasGroup(id):
            raise GroupDoesNotExistException
        for connection in self.groups[id]:
            self.removeConnection(connection)
        del self.groups[id]

    def getGroupNames(self):
        return self.groups.keys()

    def addConnection(self, connection, groupName, connectionId):
        '''
        returns connectionId
        '''
        if not groupName in self.groups.keys():
            raise GroupDoesNotExistException
        # note the group in the connection's infomartion
        self.connections[connection.connectionId] = (connection, groupName, connectionId)
        # add the connection to the group's infomartion
        self.groups[groupName].append(connection)
        assert self.connectionHasGroup(connection)
        log.info("addedConnection %s:%s id:%s", connection.getPeer().host, connection.getPeer().port, connection.connectionId)

    def removeConnection(self, connection):
        connectionId = connection.connectionId
        if self.connections.has_key(connectionId):
            connectionTuple = self.connections.pop(connectionId)
            groupName = connectionTuple[1]
            self.groups[groupName].remove(connection)
            log.info("removedConnection %s:%s id:%s", connection.getPeer().host, connection.getPeer().port, connection.connectionId)

    def sendGroupMessage(self, connection, data):
        groupName = self.connections[connection.connectionId][1]
        if None == groupName:
            return False  # user doesn't have a group yet

        for conn in self.groups[groupName]:
            try:
                conn.write(struct.pack("!i",len(data))+data) # sendString Int32
            except:
                log.exception("Error sending message to connection %s", str(conn))
        return True

class GroupMsgService:
    def __init__(self, location):
        self.location = location
        self.factory = GroupMsgServiceFactory()
        self.factory.protocol = GroupMsgServiceProtocol
        self.listenPort = None

    def Start(self):
        port = self.location[1]
        self.listenPort = reactor.listenTCP(port, self.factory)

    def Stop(self):
        if self.listenPort != None:
            self.listenPort.stopListening()

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
