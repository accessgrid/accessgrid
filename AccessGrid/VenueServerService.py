
from ZSI.writer import SoapWriter
from ZSI.parse import ParsedSoap
from AccessGrid.interfaces.AccessGrid_Types import www_accessgrid_org_v3_0

class VenueServerServiceDescription:
    '''
    Describes a venue server service.
    '''
    def __init__(self, id, name, description, type, location, channels):
        '''
        id - unique id for this service
        name - name of service
        description - description of service
        type - which type of service (e.g. event, text, etc)
        location - host, port information
        channels - list of all channel ids for channels in this service 
        '''
        self.__id = str(id)
        self.__name = str(name)
        self.__description = str(description)
        self.__type = str(type)
        self.__location = location
        self.__channels = channels

    def HasChannel(self, channelId):
        '''
        Check if a specific channel exists for this service.
        '''
        for channel in self.__channels:
            if channel == channelId:
                return 1
        return 0
            
    def GetChannels(self):
        '''
        Get all channel ids associated with this service
        '''
        return self.__channels
        
    def GetType(self):
        '''
        Get type of service.
        '''
        return self.__type

    def GetLocation(self):
        '''
        Get location (host, port) information for
        this service.
        '''
        return self.__location
   
    def GetId(self):
        '''
        Get unique id for this service.
        '''
        return str(self.__id)

class UnimplementedException(Exception):
    pass

class VenueServerServiceInterface:
    '''
    An interface class, services should inherit from this class. This class 
    has methods for handling channels. 
    '''
    def __init__(self, name, description, id, type, location):
        raise UnimplementedException

    def Start(self):
        raise UnimplementedException

    def GetId(self):
        raise UnimplementedException

    def GetDescription(self):
        '''
        Returns a VenueServerServiceDescription.
        '''
        raise UnimplementedException

    def GetChannelNames(self):
        raise UnimplementedException

    def CreateChannel(self, channelId):
        raise UnimplementedException

    def DestroyChannel(self, channelId):
        raise UnimplementedException

    def GetChannel(self, channelId):
        raise UnimplementedException

    def HasChannel(self, channelId):
        raise UnimplementedException

    def GetLocation(self):
        '''
        A tuple of (host, port)
        '''
        raise UnimplementedException

class VenueServerServiceBasic(VenueServerServiceInterface):
    '''
    A basic implementation of a VenueServerService. This class 
    has methods for handling channels. 
    '''
    def __init__(self, name, description, id, type, location):
        self.name = name
        self.description = description
        self.id = id
        self.type = type
        self.location = location
        self.channels = {}

    def Start(self):
        log.error("VenueServerService.Start: This method should only be called from sub class.")
       
    def GetId(self):
        return self.id
       
    def GetDescription(self):
        return VenueServerServiceDescription(self.id, self.name,
                                             self.description, self.type,
                                             self.location, self.GetChannelNames())

    def GetChannelNames(self):
        return self.channels.keys()
        
    def CreateChannel(self, channelId):
        channel = Channel(channelId)
        self.channels[channelId] = channel
                       
    def DestroyChannel(self, channelId):
        del self.channels[channelId]

    def GetChannel(self, channelId):
        channel = None
        if self.channels.has_key(channelId):
            channel = self.channels[channelId]

        return channel

    def HasChannel(self, channelId):
        channel = self.channels.has_key(channelId)
        return channel

    def GetLocation(self):
        return self.location

class Channel:
    '''
    The channel class represents a group of network connections
    that belongs to the same session. Channels help us decide wich
    connections should receive which events.
    '''
    
    def __init__(self, id):
        self.__channelId = str(id)
        self.__connections = {}
      
    def GetId(self):
        return self.__channelId

    def AddConnection(self, networkConnection):
        log.debug("Channel.AddConnection: Add connection %s to channel %s"%(networkConnection.get_id(), self.__channelId))
        self.__connections[networkConnection.get_id()] = networkConnection

    def GetConnections(self):
        return self.__connections.values()

    def HasConnection(self, networkConnection):
        return self.__connections.has_key(networkConnection.get_id())

