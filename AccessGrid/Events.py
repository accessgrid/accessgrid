#-----------------------------------------------------------------------------
# Name:        Events.py
# Purpose:     Event classes for event infrastructure.
#
# Author:      Thomas D. Uram, Ivan R. Judson
#
# Created:     2003/31/01
# RCS-ID:      $Id: Events.py,v 1.5 2003-02-21 16:10:29 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
class Event:
    ENTER = "Enter"
    EXIT = "Exit"
    MODIFY_USER = "Modify user"
    ADD_DATA = "Add data"
    UPDATE_DATA = "Update data"
    REMOVE_DATA = "Remove data"
    ADD_SERVICE = "Add service"
    REMOVE_SERVICE = "Remove service"
    ADD_CONNECTION = "Add connection"
    REMOVE_CONNECTION = "Remove connection"
    SET_CONNECTIONS = "Set connections"
    UPDATE_VENUE_STATE = "Update venue state"
    
    def __init__( self, eventType, venueId, data ):
        self.eventType = eventType
        self.venue = venueId
        self.data = data

class HeartbeatEvent(Event):
    HEARTBEAT = "Client Heartbeat"
    
    def __init__(self, venueId, data):
        Event.__init__(self, HeartbeatEvent.HEARTBEAT, venueId, data)
        

