#-----------------------------------------------------------------------------
# Name:        AppService.py
# Purpose:     Supports venue-coordinated applications.
#
# Author:      Robert Olson
#
# Created:     2003/02/27
# RCS-ID:      $Id: AppService.py,v 1.2 2003-03-19 16:50:31 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
An AG Application Service.

AppService is the web service interface for the Application Service.
AppServiceImpl is the actual implementation of the Application Service.

AppObject is the web service interface for the Application object.
AppObjectImpl is its implementation.

Likewise with DataChannel and DataChannelImpl.

"""

import logging

from AccessGrid import GUID
from AccessGrid import Events
from AccessGrid.hosting.pyGlobus import ServiceBase

log = logging.getLogger("AG.AppService")

class AppService(ServiceBase.ServiceBase):
    def __init__(self, impl):
        self.impl = impl
        
    def CreateApplication(self, description):
        return self.impl.CreateApplication(description)

    CreateApplication.soap_export_as = "CreateApplication"

class AppObject(ServiceBase.ServiceBase):
    def __init__(self, impl):
        self.impl = impl
        
    def GetId(self):
        return self.impl.GetId()
    GetId.soap_export_as = "GetId"
        
    def GetEventServiceLocation(self):
        return self.impl.GetEventServiceLocation()
    GetEventServiceLocation.soap_export_as = "GetEventServiceLocation"

    def Join(self, profile):
        return self.impl.Join(profile)
    Join.soap_export_as = "Join"

    def GetComponents(self):
        return self.impl.GetComponents()
    GetComponents.soap_export_as = "GetComponents"

    def Leave(self, private_token):
        return self.impl.Leave(private_token)
    Leave.soap_export_as = "Leave"

    def SetData(self, private_token, key, value):
        return self.impl.SetData(private_token, key, value)
    SetData.soap_export_as = "SetData"

    def GetData(self, private_token, key):
        return self.impl.GetData(private_token, key)
    GetData.soap_export_as = "GetData"

    def CreateDataChannel(self, private_token):
        return self.impl.CreateDataChannel(private_token)
    CreateDataChannel.soap_export_as = "CreateDataChannel"

class DataChannel(ServiceBase.ServiceBase):
    def __init__(self, impl):
        self.impl = impl

    def Register(self, eventTypes):
        return self.impl.Register(eventTypes)
    Register.soap_export_as = "Register"

    def Send(self, eventType, eventData):
        return self.impl.Send(eventType, eventData)
    Send.soap_export_as = "Send"

#
# End of interfaces. Start the implementation classes.
# 


class AppServiceImpl:
    def __init__(self, hostingEnvironment, eventService):
        self.hostingEnvironment = hostingEnvironment
        self.eventService = eventService
        
    def CreateApplication(self, name, description):
        appImpl = AppObjectImpl(name, description, self.eventService)
        app = AppObject(appImpl)
        obj = self.hostingEnvironment.create_service_object()
        app._bind_to_service(obj)
        return obj.GetHandle()

class InvalidPrivateToken(Exception):
    """
    Raised if an attempt to call an AppObject method is made with
    an invalid private token.
    """
    pass

class AppObjectImpl:
    def __init__(self, name, description, eventService):
        """
        An application object.

        Member variables:
            name - The name of this application.

            description - Description of the application. Format chosen by the app.

            eventService - Handle to the local event service objec.t

            components - Dictionary of application components. key is the private
            id of the component. Value is the (public_id, profile) for the component.

            channels - List of channels that have been created for this app.

            app_data - Dictionary containing application's internal data.

            id - Unique identifier for this application.

        Persistence policy.

        We do not keep the list of components in persistent storage. However, we do
        keep the set of channel names. When the app object is reawakened, it will
        recreate event channels for each of the channels that were registered.
        """
            
        self.name = name
        self.description = description
        self.eventService = eventService

        self.components = {}
        self.channels = []
        self.app_data = {}
        self.id = str(GUID.GUID())

    def __getstate__(self):
        """
        Retrieve the state of object attributes for pickling.

        We don't pickle any object instances, except for the
        uniqueId and description.

        """
        odict = self.__dict__.copy()
        # We don't save things in this list
        keys = ("eventService", "components", "handle")
        for k in odict.keys():
            if k in keys:
                del odict[k]

        return odict

    def __setstate__(self, pickledDict):
        """
        Set the new state of the object after unpickling.
        """

        for k, v in pickledDict.items():
            self.__dict__[k] = v

    def Awaken(self, eventService):
        self.eventService = eventService
        self.components = {}
        self.__AwakenChannels()
        
    def SetHandle(self, handle):
        """
        Sets the web service handle that this app is listening on.
        """

        self.handle = handle

    def GetHandle(self):
        return self.handle

    def GetId(self):
        return self.id

    def GetEventServiceLocation(self):
        return self.eventService.GetLocation()
        
    def Join(self, profile):
        public_id = str(GUID.GUID())
        private_id = str(GUID.GUID())

        self.components[private_id] = (public_id, profile)

        return (public_id, private_id)

    def GetComponents(self):
        comps = self.components.values()
        return comps
    
    def Leave(self, private_token):
        if self.components.has_key(private_token):
            del self.components[private_token]
            return 1
        else:
            raise InvalidPrivateToken

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

    def CreateDataChannel(self, private_token):
        """
        Create a new data channel.

        Returns the channel ID and the location of its event service.
        """
        
        if not self.components.has_key(private_token):
            raise InvalidPrivateToken

        channel_id = str(GUID.GUID())

        self.channels.append(channel_id)

        self.__InitializeDataChannel(channel_id)

        loc = self.eventService.GetLocation()
        log.debug("Returning channel_id='%s' loc='%s'", channel_id, loc)
        return (channel_id, loc)

    def __InitializeDataChannel(self, channel_id):

        handler = ChannelHandler(channel_id, self.eventService)

        self.eventService.RegisterChannelCallback(channel_id,
                                                  handler.handleEvent)

        self.eventService.AddChannel(channel_id)

    def __AwakenChannels(self):
        """
        Reinitialize  the data channels after a persistent restore.
        """

        for channel_id in self.channels:
            self.__InitializeDataChannel(channel_id)

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
           handle - the web service handle for this application object
           data - the application's data storage, itself a dictionary.

        """
        
        state = {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'handle': self.handle,
            'data': self.app_data,
            }
        return state

class ChannelHandler:
    def __init__(self, channelId, eventService):
        self.eventService = eventService
        self.channelId = channelId

    def handleEvent(self, eventType, eventData):
        try:
            log.debug("handling event type='%s' data='%s'", eventType, eventData)
            self.eventService.Distribute(self.channelId,
                                         Events.Event(eventType, self.channelId, eventData))
        except:
            log.exception("handleEvent threw exception")

class DataChannelImpl:
    def __init__(self):
        pass

    def Register(self, eventTypes):
        pass

    def Send(self, eventType, eventData):
        pass


