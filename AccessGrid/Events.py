#-----------------------------------------------------------------------------
# Name:        Events.py
# Purpose:     Event classes for event infrastructure.
#
# Author:      Thomas D. Uram, Ivan R. Judson
#
# Created:     2003/31/01
# RCS-ID:      $Id: Events.py,v 1.10 2003-04-25 03:54:55 olson Exp $
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
    ADD_APPLICATION = "Add application"
    REMOVE_APPLICATION = "Remove application"
    ADD_CONNECTION = "Add connection"
    REMOVE_CONNECTION = "Remove connection"
    SET_CONNECTIONS = "Set connections"
    UPDATE_VENUE_STATE = "Update venue state"
    
    def __init__(self, eventType, venueId, data):
        self.eventType = eventType
        self.venue = venueId
        self.data = data

    def __repr__(self):
        string = "Event:\n"
        string += "\tType: %s" % (self.eventType, )
        string += "\tVenue: %s" % (self.venue, )
        string += "\tData: %s" % (self.data, )

        return string
    
class ConnectEvent(Event):
    CONNECT = "Connect"

    def __init__(self, venueId, privateId):
        Event.__init__(self, ConnectEvent.CONNECT, venueId, privateId)

class DisconnectEvent(Event):
    DISCONNECT = "Disconnect"

    def __init__(self, venueId, privateId):
        Event.__init__(self, DisconnectEvent.DISCONNECT, venueId, privateId)
        
class HeartbeatEvent(Event):
    HEARTBEAT = "Client Heartbeat"
    
    def __init__(self, venueId, privateId):
        Event.__init__(self, HeartbeatEvent.HEARTBEAT, venueId, privateId)

class TextPayload:
    """ """
    def __init__(self, sender, recipient, private, data):
        self.sender = sender
        self.recipient = recipient
        self.private = private
        self.data = data

    def __repr__(self):
        string = "Sender: %s, Recipient: %s, " % (self.sender, self.recipient)
        string += "Private: %d, Data: %s" % (self.private, self.data)

        return string
    
class TextEvent(Event):
    TEXT = "Text Event"
    def __init__(self, venue, recipient, private, data):

        self.venue = venue
        self.payload = TextPayload(None, recipient, private, data)
        Event.__init__(self, TextEvent.TEXT, self.venue, self.payload)

    def __repr__(self):
        string = "Text Event: Venue: %s, " % self.venue
        string += "Payload: %s" % self.payload

        return string

