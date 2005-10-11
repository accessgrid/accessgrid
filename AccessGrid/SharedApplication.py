#-----------------------------------------------------------------------------
# Name:        SharedApplication.py
# Purpose:     Supports venue-coordinated applications.
#
# Created:     2003/02/27
# RCS-ID:      $Id: SharedApplication.py,v 1.27 2005-10-11 16:32:14 lefvert Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
Shared Application Support for the AGTk.

This module defines classes for the Shared Application implementation,
interface, and interface wrapper.
"""

__revision__ = "$Id: SharedApplication.py,v 1.27 2005-10-11 16:32:14 lefvert Exp $"
__docformat__ = "restructuredtext en"

from AccessGrid import Log
from AccessGrid.GUID import GUID
from AccessGrid import Events
from AccessGrid.Events import Event
from AccessGrid.VenueEventClient import VenueEventClient
from AccessGrid.Descriptions import ApplicationDescription, AppParticipantDescription, AppDataDescription
from AccessGrid.Descriptions import CreateClientProfile

from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper

from AccessGrid.Toolkit import Application, Service
from AccessGrid.Security.AuthorizationManager import AuthorizationManager, AuthorizationManagerI
from AccessGrid.Security import X509Subject, Role
from AccessGrid.interfaces.SharedApplication_interface import SharedApplication as SharedApplicationI
import re
log = Log.GetLogger(Log.SharedApplication)

class InvalidPrivateToken(Exception):
    """
    Raised if an attempt to call an SharedApplication method is made with
    an invalid private token.
    """
    pass

class SharedApplication:
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
        self.authManager = AuthorizationManager()
        
        # Add required roles and set parent auth Mgr
        self.authManager.AddRequiredRole(Role.Role("AllowedConnect"))
        # Do not keep track of connected users at this time.
        # self.AddRequiredRole(Role.Role("AppUsers"))
        self.authManager.AddRequiredRole(Role.Role("Administrators"))
        self.authManager.AddRequiredRole(Role.Everybody)

        self.authManager.AddRoles(self.authManager.GetRequiredRoles())
        
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
            self.id = str(GUID())
        else:
            self.id = id
            
        self.venueURL = ""

        ai = SharedApplicationI(self)
        self.authManagerI = AuthorizationManagerI(self.authManager)
        self.authManager.AddActions(ai._GetMethodActions() + self.authManagerI._GetMethodActions())
        
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

        # Save application authorization policy
        policy = self.authManager.ExportPolicy()
        # Don't store these control characters, but lets make sure we
        # bring them back
        policy = re.sub("\r\n", "<CRLF>", policy)
        policy = re.sub("\r", "<CR>", policy)
        policy = re.sub("\n", "<LF>", policy)
        string += 'authorizationPolicy : %s\n' % policy

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
            self.eventService.DestroyChannel(channel)

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

        public_id = str(GUID())
        private_id = str(GUID())

        # Create participant description
        participant = AppParticipantDescription(public_id, clientProfile,
                                                'connected')
        # Store description
        self.components[private_id] = participant

        # Distribute event
        for channelId in self.channels:
            evt = Event(Event.APP_PARTICIPANT_JOIN, channelId, participant)
            #self.eventService.Distribute(channelId, evt)
            self.eventClient.Send(Event.APP_PARTICIPANT_JOIN, participant)     

        return (public_id, private_id)

    def Leave(self, private_token):
        # Remove the component
        if self.components.has_key(private_token):
            participant = self.components[private_token]

            # Distribute event
            for channelId in self.channels:
                evt = Event(Event.APP_PARTICIPANT_LEAVE, channelId,
                            participant)
                #self.eventService.Distribute(channelId, evt)
                self.eventClient.Send(Event.APP_PARTICIPANT_LEAVE, participant)     


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
        
        return (channelId, location[0], location[1])

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
        key = key.lower() # Our .dat files use all lowercase keys

        if not self.components.has_key(private_token):
            raise InvalidPrivateToken

        # Only strings are encoded.
        if type(value) == type(""):
            # Get rid of endlines so server can store the data.
            codedData = value.replace("_", "__")   # escape underscores
            codedData = value.replace("\n", "z_z") # replace endlines using single underscores
        else:
            codedData = value

        self.app_data[key] = codedData

        participant = self.components[private_token]

        data = AppDataDescription(participant.appId, key, value)
        
        # Distribute event
        for channelId in self.channels:
            evt = Event(Event.APP_SET_DATA, channelId, data)
            #self.eventService.Distribute(channelId, evt)
            self.eventClient.Send(Event.APP_SET_DATA, data)
            
    def GetData(self, private_token, key):
        key = key.lower() # Our .dat files use all lowercase keys

        if not self.components.has_key(private_token):
            raise InvalidPrivateToken

        if self.app_data.has_key(key):
            # Only strings are encoded.
            if type("") == type(self.app_data[key]):
                decodedData = self.app_data[key].replace("z_z","\n") # restore endlines
                decodedData = decodedData.replace("__", "_")
            else:
                decodedData = self.app_data[key]
            return decodedData
        else:
            return ""

    def RemoveData(self, private_token, key):
        if not self.components.has_key(private_token):
            raise InvalidPrivateToken
        
        if self.app_data.has_key(key):
            del self.app_data[key]
        else:
            log.info("SharedApplication.RemoveData: Can not remove key=%s, data does not exist."%key)

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
                
        # Distribute event
        for channelId in self.channels:
            evt = Event(Event.APP_UPDATE_PARTICIPANT, channelId, participant)
            #self.eventService.Distribute(channelId, evt)
            self.eventClient.Send(Event.APP_UPDATE_PARTICIPANT, participant)     
                          
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
            #self.eventService.Distribute(channelId, evt)
            self.eventClient.Send(Event.APP_UPDATE_PARTICIPANT, participant)     
                        

    def __CreateDataChannel(self):
        """
        Create a new data channel.

        Returns the channel ID and the location of its event service.
        """
        channel_id = str(GUID())
        self.channels.append(channel_id)
        self.__InitializeDataChannel(channel_id)
        loc = self.eventService.GetLocation()
        log.debug("Returning channel_id='%s' loc='%s'", channel_id, loc)
        return (channel_id, loc)

    def __InitializeDataChannel(self, channel_id):
        handler = ChannelHandler(channel_id, self.eventService)
        self.eventService.CreateChannel(channel_id)
        evtLocation = self.eventService.GetLocation()
        evtLocation = ("localhost", 8002)
        self.eventClient = VenueEventClient(evtLocation, 
                                       1,
                                       channel_id)
        self.eventClient.Start()
                    
        #self.eventService.RegisterChannelCallback(channel_id,
        #                                          handler.handleEvent)

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
            #self.eventService.Distribute(self.channelId,
            #                             Events.Event(eventType, self.channelId, eventData))
            self.eventClient.Send(eventType, eventData)         
        except:
            log.exception("handleEvent threw exception")

#
# Create factory function
#

def CreateApplication(name, description, mimeType, eventService, id=None ):
    """
    Factory method for creating application objects
    """
    return SharedApplication(name, description, mimeType, eventService, id)


if __name__ == "__main__":

    import time

    from AccessGrid.Toolkit import Service
    from AccessGrid.hosting import SecureServer, InsecureServer
    from AccessGrid.SharedApplication import SharedApplication
    from AccessGrid.interfaces.SharedApplication_interface import SharedApplication as SharedApplicationI
    

    app = Service.instance()
    args = app.Initialize('SharedApplication')
    log = app.GetLog()
    hostname = app.GetHostname()
    port = 4000
    if app.GetOption("secure"):
        server = SecureServer((hostname, port))
    else:
        server = InsecureServer((hostname, port))
    
    # __init__(self, name, description, mimeType, eventService, id = None):
    sa = SharedApplication('name','description','application/x-sharedapp',None)
    sai = SharedApplicationI(impl=sa,auth_method_name=None)
    server.RegisterObject(sai,path="/SharedApplication")

    url = server.FindURLForObject(sa)    
    print "Starting Service Manager URL:", url

    # Start the service
    server.RunInThread()
    
    running = 1
    while running:
        try:
            time.sleep(1)
        except IOError, e:
            log.info("Sleep interrupted, exiting.")
    
    

