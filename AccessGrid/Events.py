#-----------------------------------------------------------------------------
# Name:        Events.py
# Purpose:     Event classes for event infrastructure.
#
# Author:      Thomas D. Uram, Ivan R. Judson
#
# Created:     2003/31/01
# RCS-ID:      $Id: Events.py,v 1.6 2003-02-21 21:42:10 judson Exp $
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

class ConnectEvent(Event):
    CONNECT = "Connect"

    def __init__(self, venueId):
        Event.__init__(self, ConnectEvent.CONNECT, venueId, None)
        
class HeartbeatEvent(Event):
    HEARTBEAT = "Client Heartbeat"
    
    def __init__(self, venueId, data):
        Event.__init__(self, HeartbeatEvent.HEARTBEAT, venueId, data)

class TextPayload:
    """ """
    def __init__(self, sender, recipient, private, data):
        self.sender = sender
        self.recipient = recipient
        self.private = private
        self.data = data
    
class TextEvent(Event):
    TEXT = "Text Event"
    def __init__(self, venue, recipient, private, data):

        payload = TextPayload(None, recipient, private, data)

        Event.__init__(self, TextEvent.TEXT, venue, payload)
        

