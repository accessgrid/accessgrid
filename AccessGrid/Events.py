#-----------------------------------------------------------------------------
# Name:        Events.py
# Purpose:     Event classes for event infrastructure.
#
# Author:      Thomas D. Uram, Ivan R. Judson
#
# Created:     2003/31/01
# RCS-ID:      $Id: Events.py,v 1.1 2003-02-03 17:30:17 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
class Event:
    ENTER = "Enter"
    EXIT = "Exit"
    MODIFY_USER = "Modify user"
    ADD_DATA = "Add data"
    REMOVE_DATA = "Remove data"
    ADD_SERVICE = "Add service"
    REMOVE_SERVICE = "Remove service"
    ADD_CONNECTION = "Add connection"
    REMOVE_CONNECTION = "Remove connection"
    UPDATE_VENUE_STATE = "Update venue state"
    
    def __init__( self, eventType, data ):
        self.eventType = eventType
        self.data = data

class TestEvent(Event):
    TEST = "Test Event"
    
    def __init__(self, data):
        Event.__init__(self, TestEvent.TEST, data)
        
class HeartbeatEvent(Event):
    HEARTBEAT = "Client Heartbeat"
    
    def __init__(self, data):
        Event.__init__(self, HeartbeatEvent.HEARTBEAT, data)
        
class TextEvent(Event):
    TEXT = "Text"
    
    def __init__(self, data):
        Event.__init__(self, TextEvent.TEXT, data)