#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        InsecureEventService.py
# Purpose:     A group messaging service with an AccessGrid
#                 VenueServerServiceInterface.
# Created:     2005/09/09
# RCS-ID:      $Id: InsecureEventService.py,v 1.3 2006-01-23 17:21:29 turam Exp $
# Copyright:   (c) 2005, 2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
from GroupMsgService import GroupMsgService
from VenueServerService import VenueServerServiceDescription

class BaseEventService:
    def __init__(self, name, description, id, type, location, groupMsgService=GroupMsgService):
        self.groupMsgService = groupMsgService(location)
        self.name = name
        self.description = description
        self.id = id
        self.type = type

    def Start(self):
        self.groupMsgService.Start()

    def Stop(self):
        self.groupMsgService.Stop()

    shutdown = Stop
    start = Start

    def GetId(self):
        return self.id

    def GetDescription(self):
        '''
        Returns a VenueServerServiceDescription.
        '''
        return VenueServerServiceDescription(self.id, self.name,
                                             self.description, self.type,
                                             self.groupMsgService.location, self.GetChannelNames())
        return self.description

    def GetChannelNames(self):
        return self.groupMsgService.GetGroupNames()

    def CreateChannel(self, channelId):
        return self.groupMsgService.CreateGroup(channelId)

    def DestroyChannel(self, channelId):
        return self.groupMsgService.RemoveGroup(channelId)

    #def GetChannel(self, channelId):
    #    raise UnimplementedException

    def HasChannel(self, channelId):
        return self.groupMsgService.HasGroup(channelId)

    def GetLocation(self):
        '''
        A tuple of (host, port)
        '''
        return self.groupMsgService.location

InsecureEventService = BaseEventService

def main():
    eventService = InsecureEventService(name="test", description="atest", id="testId", type="event", location=('localhost',8002))
    eventService.CreateChannel("Test")
    eventService.Start()
    from twisted.internet import reactor
    reactor.run()


if __name__ == '__main__':
    if "--psyco" in sys.argv:
        import psyco
        psyco.full()
    main()

