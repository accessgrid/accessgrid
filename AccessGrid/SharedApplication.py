#-----------------------------------------------------------------------------
# Name:        SharedApplication.py
# Purpose:     Supports venue-coordinated applications.
#
# Created:     2003/02/27
# RCS-ID:      $Id: SharedApplication.py,v 1.11 2004-04-16 22:27:40 eolson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
Shared Application Support for the AGTk.

This module defines classes for the Shared Application implementation,
interface, and interface wrapper.
"""

__revision__ = "$Id: SharedApplication.py,v 1.11 2004-04-16 22:27:40 eolson Exp $"
__docformat__ = "restructuredtext en"

from AccessGrid import Log
from AccessGrid import GUID
from AccessGrid import Events
from AccessGrid.Events import Event
from AccessGrid.Descriptions import ApplicationDescription, AppParticipantDescription

from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper

from AccessGrid.Toolkit import Application, Service
from AccessGrid.Security.AuthorizationManager import AuthorizationManager
from AccessGrid.Security.AuthorizationManager import AuthorizationIMixIn
from AccessGrid.Security.AuthorizationManager import AuthorizationIWMixIn
from AccessGrid.Security.AuthorizationManager import AuthorizationMixIn
from AccessGrid.Security.AuthorizationManager import AuthorizationMixIn
from AccessGrid.Security import X509Subject, Role

log = Log.GetLogger(Log.SharedApplication)

class InvalidPrivateToken(Exception):
    """
    Raised if an attempt to call an SharedApplication method is made with
    an invalid private token.
    """
    pass

class SharedApplication(AuthorizationMixIn):
    """
    SharedApplication is the implementation class for an application
    """
    def __init__(self, name, description, mimeType, eventService, id = None):
        """
        An application object.

        Member variables:
            name - The name of this application.

            description - Description of the application. Format chosen by the app.

            eventService - Handle to the local event service object

            components - Dictionary of application components. key is the private
            id of the component. Value is the profile for the component.

            channels - List of channels that have been created for this app.

            app_data - Dictionary containing application's internal data.

            id - Unique identifier for this application.

        Persistence policy.

        We do not keep the list of components in persistent
        storage. However, we do keep the set of channel names. When
        the app object is reawakened, it will recreate event channels
        for each of the channels that were registered.
        """
        AuthorizationMixIn.__init__(self)
        # Add required roles and set parent auth Mgr
        self.AddRequiredRole(Role.Role("AllowedConnect"))
        # Do not keep track of connected users at this time.
        # self.AddRequiredRole(Role.Role("AppUsers"))
        self.AddRequiredRole(Role.Role("Administrators"))

        self.authManager.AddRoles(self.GetRequiredRoles())

        admins = self.authManager.FindRole("Administrators")
        admins.AddSubject(Service.instance().GetDefaultSubject())
                                                                                
        # Default to admins
        self.authManager.SetDefaultRoles([admins])

        self.name = name
        self.description = description
        self.mimeType = mimeType
        self.eventService = eventService

        self.components = {}
        self.channels = []
        self.app_data = {}
        if id == None:
            self.id = str(GUID.GUID())
        else:
            self.id = id

        ai = SharedApplicationI(self)
        self.authManager.AddActions(ai._GetMethodActions())

        # Create the data channel
        self.__CreateDataChannel()

    def AsINIBlock(self):
        # Got the basic description
        string = self.AsApplicationDescription().AsINIBlock()

        # Now to save data (state)
        for key, value in self.app_data.items():
            string += "%s : %s\n" % (key, value)

        return string
    
    def AsApplicationDescription(self):
        """
        Return an application description, used in the rollup of
        venue state for the return from the Venue.Enter call.
        """
        appDesc = ApplicationDescription(self.id, self.name,
                                         self.description,
                                         self.handle,
                                         self.mimeType)
        return appDesc

    def Awaken(self, eventService):
        self.eventService = eventService
        self.components = {}
        self.__AwakenChannels()
        
    def Shutdown(self):
        """
        Shut down the applications before it is destroyed.
        """

        for channel in self.channels:
            self.eventService.RemoveChannel(channel)

    def GetState(self):
        """
        Return the state of this application, used in the rollup of
        venue state for the return from the Venue.Enter call.

        The state is a dictionary with the following keys defined:

           name - name of the application
           description - an application-defined description of the application
           id - the unique identifier for this application instance
           mimeType - description of data type handled by this application
           url - the web service endpoint for this application object
           data - the application's data storage, itself a dictionary.

        """

        appState = {
            'name' : self.name,
            'description' : self.description,
            'id' : self.id,
            'mimeType' : self.mimeType,
            'uri' : self.uri,
            'data' : self.app_data
            }
            
        return appState

    def SetVenueURL(self, url):
        self.venueURL = url

    def GetVenueURL(self):
        return self.venueURL
    
    def GetEventServiceLocation(self):
        return self.eventService.GetLocation()
        
    def SetHandle(self, handle):
        """
        Sets the web service handle that this app is listening on.
        """

        self.handle = handle

    def GetHandle(self):
        return self.handle

    def GetId(self):
        return self.id

    def Join(self, clientProfile=None):

        # Takes a client profile until venue client has been refactored
        # to include  a connection ID.

        public_id = str(GUID.GUID())
        private_id = str(GUID.GUID())

        # Create participant description
        participant = AppParticipantDescription(public_id, clientProfile,
                                                'connected')
        # Store description
        self.components[private_id] = participant

        # Distribute event
        for channelId in self.channels:
            evt = Event(Event.APP_PARTICIPANT_JOIN, channelId, participant)
            self.eventService.Distribute(channelId, evt)

        return (public_id, private_id)

    def Leave(self, private_token):
        if self.components.has_key(private_token):
            del self.components[private_token]
            return 1
        else:
            raise InvalidPrivateToken

    def GetDataChannel(self, private_token):
        """
        Return the channel id and location of the
        application object's data channel 
        """
        if not self.components.has_key(private_token):
            raise InvalidPrivateToken

        channelId = self.channels[0]
        location = self.eventService.GetLocation()
        log.info( "channel = " + self.channels[0] )
        log.info( "location = " +  location[0] + ":" + str(location[1]) )
        
        return (channelId, location)

    def GetVenueURL(self, private_token):
        """
        Return the url of the venue this app object is in.
        """
        if not self.components.has_key(private_token):
            raise InvalidPrivateToken

        return self.venueURL
    
    def GetComponents(self, private_token):
        if not self.components.has_key(private_token):
            raise InvalidPrivateToken

        comps = self.components.values()
        return comps
    
    def SetData(self, private_token, key, value):
        if not self.components.has_key(private_token):
            raise InvalidPrivateToken

        self.app_data[key] = value

    def GetData(self, private_token, key):
        if not self.components.has_key(private_token):
            raise InvalidPrivateToken

        if self.app_data.has_key(key):
            return self.app_data[key]
        else:
            return ""

    def SetParticipantProfile(self, private_token, profile):
        '''
        Sets profile of participant associated with private_token

        **Arguments**
        
        *profile* New client profile.
        '''
        if not self.components.has_key(private_token):
            raise InvalidPrivateToken
        
        participant = self.components[private_token]
        participant.clientProfile = profile
        self.components[private_token] = participant

        for p in self.components.values():
            if p.clientProfile != 'None' and p.clientProfile != None:
                p.clientProfile.name
                
        # Distribute event
        for channelId in self.channels:
            evt = Event(Event.APP_UPDATE_PARTICIPANT, channelId, participant)
            self.eventService.Distribute(channelId, evt)
                          
    def SetParticipantStatus(self, private_token, status):
        '''
        Sets status of participant associated with private_token

        **Arguments**
        
        *status* New status value.
        '''

        if not self.components.has_key(private_token):
            raise InvalidPrivateToken

        
        participant = self.components[private_token]
        participant.status = status
        self.components[private_token] = participant
        
        # Distribute event
        for channelId in self.channels:
            evt = Event(Event.APP_UPDATE_PARTICIPANT, channelId, participant)
            self.eventService.Distribute(channelId, evt)

    def __CreateDataChannel(self):
        """
        Create a new data channel.

        Returns the channel ID and the location of its event service.
        """
        
        channel_id = str(GUID.GUID())

        self.channels.append(channel_id)

        self.__InitializeDataChannel(channel_id)

        loc = self.eventService.GetLocation()
        log.debug("Returning channel_id='%s' loc='%s'", channel_id, loc)
        return (channel_id, loc)

    def __InitializeDataChannel(self, channel_id):

        handler = ChannelHandler(channel_id, self.eventService)

        self.eventService.AddChannel(channel_id)

        self.eventService.RegisterChannelCallback(channel_id,
                                                  handler.handleEvent)

    def __AwakenChannels(self):
        """
        Reinitialize the data channels after a persistent restore.
        """

        for channel_id in self.channels:
            self.__InitializeDataChannel(channel_id)

class ChannelHandler:
    def __init__(self, channelId, eventService):
        self.eventService = eventService
        self.channelId = channelId

    def handleEvent(self, event):
        try:
            eventType = event.eventType
            eventData = event.data
            log.debug("handling event type='%s' data='%s'", eventType, eventData)
            self.eventService.Distribute(self.channelId,
                                         Events.Event(eventType, self.channelId, eventData))
        except:
            log.exception("handleEvent threw exception")

#
# Create factory function
#

def CreateApplication(name, description, mimeType, eventService, id=None ):
    """
    Factory method for creating application objects
    """
    return SharedApplicationImpl(name, description, mimeType, eventService, id)

class SharedApplicationI(SOAPInterface, AuthorizationIMixIn):
    """
    SharedApplication is the interface class for an application
    """

    def __init__(self, impl):
        """
        """
        SOAPInterface.__init__(self, impl)

    def _authorize(self, *args, **kw):
        """
        """
        subject, action = self._GetContext()

        return 1
    
    def GetId(self):
        return self.impl.GetId()
        
    def Join(self, clientProfile=None):
        return self.impl.Join(clientProfile)

    def GetComponents(self):
        return self.impl.GetComponents()

    def Leave(self, private_token):
        return self.impl.Leave(private_token)

    def SetData(self, private_token, key, value):
        return self.impl.SetData(private_token, key, value)

    def GetData(self, private_token, key):
        return self.impl.GetData(private_token, key)

    def GetDataChannel(self, private_token):
        return self.impl.GetDataChannel(private_token)

    def GetVenueURL(self, private_token):
        return self.impl.GetVenueURL(private_token)

    def SetParticipantStatus(self, private_token, status):
        return self.impl.SetParticipantStatus(private_token, status)

    def SetParticipantProfile(self, private_token, profile):
        return self.impl.SetParticipantProfile(private_token, profile)

class SharedApplicationIW(SOAPIWrapper, AuthorizationIWMixIn):
    """
    """
    def __init__(self, url):
        SOAPIWrapper.__init__(self, url)

    def GetId(self):
        return self.proxy.GetId()

    def Join(self, clientProfile=None):
        return self.proxy.Join(clientProfile)

    def GetComponents(self):
        return self.proxy.GetComponents()

    def Leave(self, private_token):
        return self.proxy.Leave(private_token)

    def SetData(self, private_token, key, value):
        return self.proxy.SetData(private_token, key, value)

    def GetData(self, private_token, key):
        return self.proxy.GetData(private_token, key)

    def GetDataChannel(self, private_token):
        return self.proxy.GetDataChannel(private_token)

    def GetVenueURL(self, private_token):
        return self.proxy.GetVenueURL(private_token)

    def SetParticipantStatus(self, private_token, status):
        return self.proxy.SetParticipantStatus(private_token, status)

    def SetParticipantProfile(self, private_token, profile):
        return self.proxy.SetParticipantProfile(private_token, profile)


