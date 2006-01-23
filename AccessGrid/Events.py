#-----------------------------------------------------------------------------
# Name:        Events.py
# Purpose:     Event classes for event infrastructure.
# Created:     2003/31/01
# RCS-ID:      $Id: Events.py,v 1.27 2006-01-23 06:56:30 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Events.py,v 1.27 2006-01-23 06:56:30 turam Exp $"
__docformat__ = "restructuredtext en"

import pickle
import struct

class Event:
    ALL = "ALL"
    ENTER = "Enter"
    EXIT = "Exit"
    MODIFY_USER = "Modify user"
    ADD_DATA = "Add data"
    UPDATE_DATA = "Update data"
    REMOVE_DATA = "Remove data"
    ADD_SERVICE = "Add service"
    UPDATE_SERVICE = "Update service"
    REMOVE_SERVICE = "Remove service"
    ADD_APPLICATION = "Add application"
    UPDATE_APPLICATION = "Update application"
    REMOVE_APPLICATION = "Remove application"
    ADD_CONNECTION = "Add connection"
    REMOVE_CONNECTION = "Remove connection"
    SET_CONNECTIONS = "Set connections"
    UPDATE_VENUE_STATE = "Update venue state"
    ADD_STREAM = "Add stream"
    MODIFY_STREAM = "Modify stream"
    REMOVE_STREAM = "Remove stream"
    OPEN_APP = "Start application"
       
    APP_PARTICIPANT_JOIN = 'Join application'
    APP_PARTICIPANT_LEAVE = 'Leave application'
    APP_UPDATE_PARTICIPANT = 'Update application participant status'
    APP_SET_DATA = 'Set application data'
    
    def __init__(self, eventType, venueId, data):
        self.eventType = eventType
        self.venue = venueId
        self.data = data
        self.id = None

    def __repr__(self):
        string = "Event:\n"
        string += "\tType: %s" % (self.eventType, )
        string += "\tVenue: %s" % (self.venue, )
        # Commenting this out, it gets really spammy -- IRJ 7/29/04
        #string += "\tData: %s" % (self.data, )

        return string

class ConnectEvent(Event):
    CONNECT = "Connect"

    def __init__(self, venueId, privateId):
        Event.__init__(self, ConnectEvent.CONNECT, venueId, privateId)

class OpenAppEvent(Event):
    '''
    Event for opening a shared application client for all participants.
    '''
    OPEN_APP = 'Open application'
    
    def __init__(self, venueId, privateId):
        Event.__init__(self, OpenAppEvent.OPEN_APP, venueId, privateId)

class AddDataEvent(Event):
    '''
    Event for adding data
    '''
    ADD_DATA = "Add data"
    
    def __init__(self, venueId, d):
        Event.__init__(self, AddDataEvent.ADD_DATA , venueId, d)

class RemoveDataEvent(Event):
    '''
    Event for removing data
    '''
    REMOVE_DATA = "Remove data"
    
    def __init__(self, venueId, d):
        Event.__init__(self, RemoveDataEvent.REMOVE_DATA , venueId, d)
  
class UpdateDataEvent(Event):
    '''
    Event for updating data
    '''

    UPDATE_DATA = "Update data"
    
    def __init__(self, venueId, d):
        Event.__init__(self, UpdateDataEvent.UPDATE_DATA , venueId, d)
        


# Have to stay for 2.0 clients
# -----------------------------
class AddPersonalDataEvent(Event):
    '''
    Event for adding personal data
    '''
    ADD_PERSONAL_DATA = "Add data"
    
    def __init__(self, venueId, d):
        Event.__init__(self, AddPersonalDataEvent.ADD_PERSONAL_DATA , venueId, d)

class RemovePersonalDataEvent(Event):
    '''
    Event for removing personal data
    '''
    REMOVE_PERSONAL_DATA = "Remove data"
    
    def __init__(self, venueId, d):
        Event.__init__(self, RemovePersonalDataEvent.REMOVE_PERSONAL_DATA , venueId, d)
  
class UpdatePersonalDataEvent(Event):
    '''
    Event for updating personal data
    '''

    UPDATE_PERSONAL_DATA = "Update data"
    
    def __init__(self, venueId, d):
        Event.__init__(self, UpdatePersonalDataEvent.UPDATE_PERSONAL_DATA , venueId, d)
        
# -----------------------------

class DisconnectEvent(Event):
    DISCONNECT = "Disconnect"

    def __init__(self, venueId, privateId):
        Event.__init__(self, DisconnectEvent.DISCONNECT, venueId, privateId)
        
class ClientExitingEvent(Event):
    CLIENT_EXITING = "ClientExiting"

    def __init__(self, venueId, privateId):
        Event.__init__(self, ClientExitingEvent.CLIENT_EXITING, venueId, privateId)
        
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

