#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        EventService.py
# Purpose:     A secure version of the EventService.
# Created:     2006/01/10
# RCS-ID:      $Id: EventService.py,v 1.31 2006-01-19 23:30:38 eolson Exp $
# Copyright:   (c) 2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys

from SecureGroupMsgService import SecureGroupMsgService
from InsecureEventService import BaseEventService

class SecureEventService(BaseEventService):
    # An EventService with encryption.  Simply changes the default groupMsgService.
    def __init__(self, name, description, id, type, location, groupMsgService=SecureGroupMsgService):
        BaseEventService.__init__(self, name=name, description=description, id=id, type=type, 
                location=location, groupMsgService=groupMsgService)

EventService = SecureEventService

def main():
    from AccessGrid.Toolkit import Service
    # Initialize the toolkit so Access Grid certificates will be available.
    Service.instance().Initialize("SecureEventService")

    eventService = SecureEventService(name="test", description="atest", id="testId", type="event", location=('localhost',7002))
    eventService.CreateChannel("Test")
    eventService.Start()
    from twisted.internet import reactor
    reactor.run()


if __name__ == '__main__':
    main()

