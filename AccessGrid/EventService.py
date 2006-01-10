#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        EventService.py
# Purpose:     A group messaging service with an AccessGrid
#                 VenueServerServiceInterface.
# Created:     2005/09/09
# RCS-ID:      $Id: EventService.py,v 1.28 2006-01-10 20:30:09 eolson Exp $
# Copyright:   (c) 2005 
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
from GroupMsgService import GroupMsgService
from VenueServerService import VenueServerServiceDescription

class EventService:
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

    def GetId(self):
        return self.id

    def GetDescription(self):
        '''
        Returns a VenueServerServiceDescription.
        '''
        return VenueServerServiceDescription(self.id, self.name,
                                             self.description, self.type,
                                             self.location, self.GetChannelNames())
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
        return self.location

def main():
    for arg in sys.argv:
        if arg.startswith("--perf"):
            showPerformance = True

    eventService = EventService(name="test", description="atest", id="testId", type="event", location=('localhost',8002))
    eventService.CreateChannel("Test")
    eventService.Start()
    from twisted.internet import reactor
    reactor.run()


if __name__ == '__main__':
    if "--psyco" in sys.argv:
        import psyco
        psyco.full()
    main()

