#-----------------------------------------------------------------------------
# Name:        SharedApplication.py
# Purpose:     Supports venue-coordinated applications.
#
# Created:     2003/02/27
# RCS-ID:      $Id: SharedApplication.py,v 1.15 2004-05-21 21:47:05 lefvert Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
Shared Application Support for the AGTk.

This module defines classes for the Shared Application implementation,
interface, and interface wrapper.
"""

__revision__ = "$Id: SharedApplication.py,v 1.15 2004-05-21 21:47:05 lefvert Exp $"
__docformat__ = "restructuredtext en"

from AccessGrid import Log
from AccessGrid import GUID
from AccessGrid import Events
from AccessGrid.Events import Event
from AccessGrid.Descriptions import ApplicationDescription, AppParticipantDescription, AppDataDescription
from AccessGrid.Descriptions import CreateClientProfile

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
        self.AddRequiredRole(Role.Everybody)
        
        self.authManager.AddRoles(self.GetRequiredRoles())

        admins = self.authManager.FindRole("Administrators")
        self.servicePtr = Service.instance()
        admins.AddSubject(self.servicePtr.GetDefaultSubject())
                                                                                
        # Default to admins
        self.authManager.SetDefaultRoles([admins])
        
        self.name = name
        self.description = description
        self.mimeType = mimeType
        self.eventService = eventService
        self.uri = None
        self.components = {}
        self.channels = []
        self.app_data = {}
        if id == None:
            self.id = str(GUID.GUID())
        else:
            self.id = id

        ai = SharedApplicationI(self)
        self.authManager.AddActions(ai._GetMethodActions())

        # Add roles to actions.
       
        # Default to giving administrators access to all app actions.
        admins = self.authManager.FindRole("Administrators")
        actions = self.authManager.GetActions()
        for action in actions:
            action.AddRole(admins)
        
        allowedConnectRole = self.authManager.FindRole("AllowedConnect")

        # For now, default to giving allowedConnect role access to all app actions.
        self.defaultConnectionActionNames = []
        for action in self.authManager.GetActions():
            self.defaultConnectionActionNames.append(action.name)
        
        everybodyRole = Role.Everybody
        
        for actionName in self.defaultConnectionActionNames:
            action = self.authManager.FindAction(actionName)
            if action != None:
                if not action.HasRole(allowedConnectRole):
                    action.AddRole(allowedConnectRole)
                if not action.HasRole(everybodyRole):
                    action.AddRole(everybodyRole)
            else:
                raise "DefaultActionNotFound %s" %actionName

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

    def GetState(self, private_token):
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

        if not self.components.has_key(private_token):
            raise InvalidPrivateToken
        
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
        # Remove the component
        if self.components.has_key(private_token):
            participant = self.components[private_token]

            # Distribute event
            for channelId in self.channels:
                evt = Event(Event.APP_PARTICIPANT_LEAVE, channelId,
                            participant)
                self.eventService.Distribute(channelId, evt)

            del self.components[private_token]
                
            return 1
            
        else:
            log.exception("AppService.Leave Trying to remove component that does not exist.")
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

    def GetParticipants(self, private_token):
        '''
        Returns a list of AppParticipantDescriptions that have client profile set.
        '''
        if not self.components.has_key(private_token):
            raise InvalidPrivateToken

        participants = []
        for c in self.components.values():
            if c.clientProfile != None:
                participants.append(c)

        return participants
    
    def SetData(self, private_token, key, value):
        if not self.components.has_key(private_token):
            raise InvalidPrivateToken

        

        self.app_data[key] = value

        participant = self.components[private_token]

        data = AppDataDescription(participant.appId, key, value)
        
        # Distribute event
        for channelId in self.channels:
            evt = Event(Event.APP_SET_DATA, channelId, data)
            self.eventService.Distribute(channelId, evt)

    def GetData(self, private_token, key):
        if not self.components.has_key(private_token):
            raise InvalidPrivateToken

        if self.app_data.has_key(key):
            return self.app_data[key]
        else:
            return ""

    def GetDataKeys(self, private_token):
        '''
        Access method for retreiving all keys for application data.

        **Returns**

        *[key]* List of all keys for application data
        
        '''
        if not self.components.has_key(private_token):
            raise InvalidPrivateToken

        return self.app_data.keys()

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
        
        if self.impl.servicePtr.GetOption("insecure"):
            return 1
        
        subject, action = self._GetContext()
        
        log.info("Authorizing action: %s for subject %s", action.name,
                 subject.name)

        authManager = self.impl.authManager

        isAuth = authManager.IsAuthorized(subject, action)
        
        return isAuth
   
    def GetId(self):
        return self.impl.GetId()
        
    def Join(self, clientProfile=None):
        if clientProfile is not None:
            cProfile = CreateClientProfile(clientProfile)
        else:
            cProfile = None
        return self.impl.Join(cProfile)

    def GetComponents(self, private_token):
        return self.impl.GetComponents(private_token)

    def GetParticipants(self, private_token):
        return self.impl.GetParticipants(private_token)

    def Leave(self, private_token):
        return self.impl.Leave(private_token)

    def SetData(self, private_token, key, value):
        return self.impl.SetData(private_token, key, value)

    def GetData(self, private_token, key):
        return self.impl.GetData(private_token, key)

    def GetDataKeys(self, private_token):
        return self.impl.GetDataKeys(private_token)

    def GetDataChannel(self, private_token):
        return self.impl.GetDataChannel(private_token)

    def GetVenueURL(self, private_token):
        return self.impl.GetVenueURL(private_token)

    def SetParticipantStatus(self, private_token, status):
        return self.impl.SetParticipantStatus(private_token, status)

    def SetParticipantProfile(self, private_token, profile):
        if profile is not None:
            cProfile = CreateClientProfile(profile)
        else:
            cProfile = None
        return self.impl.SetParticipantProfile(private_token, cProfile)

    def GetState(self, private_token):
        return self.impl.GetState(private_token)


class SharedApplicationIW(SOAPIWrapper, AuthorizationIWMixIn):
    """
    """
    def __init__(self, url):
        SOAPIWrapper.__init__(self, url)

    def GetId(self):
        return self.proxy.GetId()

    def Join(self, clientProfile=None):
        return self.proxy.Join(clientProfile)

    def GetComponents(self, private_token):
        return self.proxy.GetComponents(private_token)

    def GetParticipants(self, private_token):
        return self.proxy.GetParticipants(private_token)

    def Leave(self, private_token):
        return self.proxy.Leave(private_token)

    def SetData(self, private_token, key, value):
        return self.proxy.SetData(private_token, key, value)

    def GetData(self, private_token, key):
        return self.proxy.GetData(private_token, key)

    def GetDataKeys(self, private_token):
        return self.proxy.GetDataKeys(private_token)

    def GetDataChannel(self, private_token):
        return self.proxy.GetDataChannel(private_token)

    def GetVenueURL(self, private_token):
        return self.proxy.GetVenueURL(private_token)

    def SetParticipantStatus(self, private_token, status):
        return self.proxy.SetParticipantStatus(private_token, status)

    def SetParticipantProfile(self, private_token, profile):
        return self.proxy.SetParticipantProfile(private_token, profile)

    def GetState(self, private_token):
        return self.proxy.GetState(private_token)

    def GetParticipants(self, private_token):
        return self.proxy.GetParticipants(private_token)
