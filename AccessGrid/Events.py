#-----------------------------------------------------------------------------
# Name:        Events.py
# Purpose:     Event classes for event infrastructure.
#
# Author:      Thomas D. Uram, Ivan R. Judson
#
# Created:     2003/31/01
# RCS-ID:      $Id: Events.py,v 1.22 2004-02-13 22:02:59 lefvert Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Events.py,v 1.22 2004-02-13 22:02:59 lefvert Exp $"
__docformat__ = "restructuredtext en"

import pickle
import struct

class Event:
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

    APP_PARTICIPANT_JOIN = 'Join application'
    APP_PARTICIPANT_LEAVE = 'Leave application'
    APP_UPDATE_PARTICIPANT = 'Update application participant status'
    APP_SET_DATA = 'Set application data'
    
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

class MarshalledEvent:
    """
    Class to contain an event marshalled into the wire form.

    Typical uses:

    App reads data according to a wire protocol that matches
    the protocol used here (pkt size + pickling). (This is a flaw
    in the design of this, but as this is an attempt to partially
    encapsulate something that's currently not at all encapsulated
    it is sufficient if used with care):

    myData = (get the data somehow)
    me = MarshalledEvent()
    me.SetData(myData)
    myEvent = me.GetEvent()

    App has an event that it wants to send to multiple file handles:

    me = MarshalledEvent()
    me.SetEvent(myEvent)
    for fh in handles():
        me.Write(fh)
        
    """

    def SetEvent(self, event):
        """
        Create the marshalled form of the event and hold it internally.
        """

        self.pdata = pickle.dumps(event)
        self.sizeStr = struct.pack("<i", len(self.pdata))

    def GetEvent(self):
        """
        Unmarshall the event object from the binary data held internally.
        """

        try:
            event = pickle.loads(self.pdata)
            return event
        except EOFError:
            log.exception("MarshalledEvent: could not unpickle")
            return None

    def SetData(self, data):
        """
        Set the binary data of the event.
        """

        self.pdata = data

    def Write(self, fh):
        """
        Write the binary data out to the specified filehandle.
        """

        fh.write(self.sizeStr)
        fh.write(self.pdata)
