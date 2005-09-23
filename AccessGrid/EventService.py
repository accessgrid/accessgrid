#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        EventService.py
# Purpose:     A group messaging service with an AccessGrid
#                 VenueServerServiceInterface.
# Created:     2005/09/09
# RCS-ID:      $Id: EventService.py,v 1.26 2005-09-23 22:09:36 eolson Exp $
# Copyright:   (c) 2005 
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
from GroupMsgService import GroupMsgService
from VenueServerService import VenueServerServiceDescription

class EventService(GroupMsgService):
    def __init__(self, name, description, id, type, location):
        GroupMsgService.__init__(self, location)
        self.name = name
        self.description = description
        self.id = id
        self.type = type

    def Start(self):
        GroupMsgService.Start(self)

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
        return GroupMsgService.GetGroupNames(self)

    def CreateChannel(self, channelId):
        return GroupMsgService.CreateGroup(self, channelId)

    def DestroyChannel(self, channelId):
        return GroupMsgService.RemoveGroup(self, channelId)

    #def GetChannel(self, channelId):
    #    raise UnimplementedException

    def HasChannel(self, channelId):
        return GroupMsgService.HasGroup(self, channelId)

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
    eventService.CreateGroup("Test")
    eventService.Start()
    from twisted.internet import reactor
    reactor.run()


if __name__ == '__main__':
    if "--psyco" in sys.argv:
        import psyco
        psyco.full()
    main()

