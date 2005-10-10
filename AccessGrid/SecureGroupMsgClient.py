#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        SecureGroupMsgClient.py
# Purpose:     A Secure Group Messaging service client.
# Created:     2005/10/10
# RCS-ID:      $Id: SecureGroupMsgClient.py,v 1.1 2005-10-10 22:01:35 eolson Exp $
# Copyright:   (c) 2005 
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from GroupMsgClient import GroupMsgClient, TestMessages
from twisted.internet import ssl

class SecureGroupMsgClient(GroupMsgClient):

    def Start(self, wxapp=None):
        host = self.location[0]
        port = self.location[1]
        # late import to allow for selecting type of reactor
        from twisted.internet import reactor
        reactor.connectSSL(host, port, self.factory, ssl.ClientContextFactory())

def main():
    location = ('localhost',7002)
    privateId = "some_id"
    groupName = "Test"
    numMsgs = 1000
    msgLength = 1000

    gmc = SecureGroupMsgClient(location, privateId, channel=groupName)
    gmc.measurePerformance = True

    tm = TestMessages(gmc=gmc, numMsgs=numMsgs)
    import random, string
    msgData = "".join([random.choice(string.letters) for x in xrange(msgLength)])
    tm.SetMsgData(msgData)
    gmc.Start()

    from twisted.internet import reactor
    reactor.run()

if __name__ == '__main__':
    main()

