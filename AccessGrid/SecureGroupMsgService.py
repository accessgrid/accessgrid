#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        SecureGroupMsgService.py
# Purpose:     A Secure Group Messaging service server.
# Created:     2005/10/10
# RCS-ID:      $Id: SecureGroupMsgService.py,v 1.2 2006-01-09 22:32:27 eolson Exp $
# Copyright:   (c) 2005 
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from GroupMsgService import GroupMsgService
from M2Crypto import SSL
import M2Crypto.SSL.TwistedProtocolWrapper as wrapper
from AccessGrid import Toolkit

class SecureContextFactory:
    def getContext(self):
        """Create an SSL context.
        """
        """
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_certificate_file('cert.pem')
        ctx.use_privatekey_file('key.pem')
        """
        return Toolkit.Service.instance().GetContext()

class SecureGroupMsgService(GroupMsgService):
    def Start(self):
        port = self.location[1]
        self.contextFactory = SecureContextFactory()
        #self.listenPort = reactor.listenSSL(port, self.factory, self.contextFactory)
        wrapper.listenSSL(port, self.factory, self.contextFactory)


def main():
    from AccessGrid.Toolkit import Service
    service = Service.instance()
    service.Initialize("SecureGroupMsgServiceTest")
    groupMsgService = SecureGroupMsgService(location=('localhost',7002))
    groupMsgService.CreateGroup("Test")
    groupMsgService.Start()

    from twisted.internet import reactor
    reactor.run()

if __name__ == '__main__':
    main()

