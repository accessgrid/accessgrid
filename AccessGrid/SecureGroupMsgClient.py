#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        SecureGroupMsgClient.py
# Purpose:     A Secure Group Messaging service client.
# Created:     2005/10/10
# RCS-ID:      $Id: SecureGroupMsgClient.py,v 1.4 2006-10-19 22:01:54 turam Exp $
# Copyright:   (c) 2005 
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from GroupMsgClient import GroupMsgClient, TestMessages, GenerateRandomString
import M2Crypto.SSL.TwistedProtocolWrapper as wrapper

from M2Crypto import SSL

class ClientContextFactory:
    """A context factory for SSL clients."""
    isClient = 1
    method = "sslv23"
    context = None
    
    def getContext(self):
        if not self.context:
            self.context = SSL.Context(self.method)
        return self.context


class SecureGroupMsgClient(GroupMsgClient):

    def Start(self, wxapp=None):
        host = self.location[0]
        port = self.location[1]
        #reactor.connectSSL(host, port, self.factory, ssl.ClientContextFactory())
        wrapper.connectSSL(host, port, self.factory, ClientContextFactory(), postConnectionCheck=None)


def testMain(location, privateId, channel="Test", msgLength=13, numMsgs=1000, multipleClients=False):
    gmc = SecureGroupMsgClient(location, privateId, channel)
    gmc.measurePerformance = True
    tm = TestMessages(gmc=gmc, numMsgs=numMsgs, multipleClients=multipleClients)
    tm.SetMsgData(GenerateRandomString(length=msgLength))
    gmc.Start() # Connect

def main():
    location = ('localhost',7002)
    privateId = "some_id"

    """
    groupName = "Test"
    msgLength = 1000
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

