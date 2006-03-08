import os

from AccessGrid.Platform.Config import UserConfig, AGTkConfig
from AccessGrid import Log
from AccessGrid.Platform import IsWindows, IsOSX
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Utilities import LoadConfig, SaveConfig
from AccessGrid.Descriptions import BridgeDescription, QUICKBRIDGE_TYPE
from AccessGrid.Descriptions import NodeConfigDescription
from AccessGrid.GUID import GUID
from AccessGrid.BridgeCache import BridgeCache
from AccessGrid.interfaces.AGNodeService_client import AGNodeServiceIW

log = Log.GetLogger(Log.VenueClient)

class Preferences:
    '''
    Class including accessors to user preferences.
    '''
    RECONNECT = "reconnect"
    MAX_RECONNECT = "maxReconnect"
    RECONNECT_TIMEOUT = "reconnectTimeout"
    STARTUP_MEDIA = "startupMedia"
    NODE_URL = "defaultNodeServiceUrl"
    NODE_BUILTIN = "nodeBuiltin"
    NODE_CONFIG = "defaultNodeConfig"
    NODE_CONFIG_TYPE = "defaultNodeConfigType"
    MULTICAST = "multicast"
    BEACON = "beacon"
    LOG_TO_CMD = "logToCmd"
    ENABLE_DISPLAY = "enableDisplay"
    ENABLE_VIDEO = "enableVideo"
    ENABLE_AUDIO = "enableAudio"
    DISPLAY_MODE = "displayMode"
    EXITS = "exits"
    MY_VENUES = "my venues"
    ALL_VENUES = "all venues"
    BRIDGE_REGISTRY = "bridgeRegistry"
    PROXY_HOST = "proxyHost"
    PROXY_PORT = "proxyPort"
                
    def __init__(self):
        '''
        Initiate preferences class. Simple client configuration
        parameters are saved in preferences dictionary. More
        complicated data structures are added as separate class
        objects and are saved to separate config file, for example
        client profile.
        '''
        
        self.preferences = {}
        
        # Default preferences
        self.default = { self.RECONNECT : 1,
                         self.MAX_RECONNECT : 3,
                         self.RECONNECT_TIMEOUT : 10,
                         self.STARTUP_MEDIA: 1,
                         self.NODE_BUILTIN: "1",
                         self.NODE_URL: "",
                         self.NODE_CONFIG_TYPE : NodeConfigDescription.SYSTEM,
                         self.NODE_CONFIG: "default",
                         self.MULTICAST: 1,
                         self.BEACON: 1,
                         self.LOG_TO_CMD: 0,
                         self.ENABLE_DISPLAY: 1,
                         self.ENABLE_VIDEO: 1,
                         self.ENABLE_AUDIO: 1,
                         self.DISPLAY_MODE: self.EXITS,
                         self.BRIDGE_REGISTRY: "http://www.accessgrid.org/registry/peers.txt",
                         self.PROXY_HOST: "",
                         self.PROXY_PORT: "",
                         }

        # Set default log levels to Log.DEBUG.
        # Keys used for log preferences
        # are the same as listed in Log.py.
        # Save log levels as
        # Log.VenueClient=Log.DEBUG.
        categories = Log.GetCategories()
        for category in categories:
            self.default[category] = Log.DEBUG
        self.default[Log.RTPSensor] = Log.CRITICAL

        # Use the already implemented parts of
        # client profile. Save client profile
        # to separate profile file.
        self.profile = ClientProfile()

        # Use the bridge cache object. Save bridges
        # to separate file
        self.bridgeCache = BridgeCache()
        
        # Use already implemented parts of
        # node service. Default node service
        # config will get saved using the node
        # service.
        self.nodeConfigs = []
        self.config = UserConfig.instance(initIfNeeded=0)
        self.__bridges = {} # Stores current bridges to display in UI
        self.LoadPreferences()
        
        self.venueClient = None
        
    def SetVenueClient(self,venueClient):
        self.venueClient = venueClient
     
    def GetPreference(self, preference):
        '''
        Accessor for client preferences. If the preference
        is not set, the method returns default value.
        
        ** Arguments **

        *preference* Preference you want to know value of

        ** Returns **

        *value* Value for preference
        '''
        r = None
        if self.preferences.has_key(preference):
            r = self.preferences[preference]
            
        elif self.default.has_key(preference):
            r = self.default[preference]
        else:
            return Exception, "Preferences.GetPreference: %s does not exist in preferences" %preference
        return r
                
    def SetPreference(self, preference, value):
        '''
        Set value for preference.
        
        ** Arguments **

        *preference* Preference to set

        *value* Value for preference
        '''
        self.preferences[preference] = value
        
    def StorePreferences(self):
        '''
        Save preferences to config file using INI file format.
        Client profile is saved separately.
        '''
        tempDict = {}

        # Add category to preference
        for key in self.preferences.keys():
            tempDict["Preferences."+key] = self.preferences[key]
                   
        # Save preference
        try:
            log.debug("Preferences.StorePreferences: open file")
            SaveConfig(self.config.GetPreferences(), tempDict)
        
        except:
            log.exception("Preferences.StorePreferences: store file error")

        # Save client profile in separate file.
        try:
            profileFile = os.path.join(self.config.GetConfigDir(),
                                       "profile" )
            self.profile.Save(profileFile)
        except:
            log.exception("Preferences.StorePreferences: store profile file error")

        # Save bridge information in separate file
        self.bridgeCache.StoreBridges(self.__bridges.values())
        
            
    def LoadPreferences(self):
        '''
        Read preferences from configuration file.
        '''
        try:
            log.debug("Preferences.LoadPreferences: open file")
            preferences = LoadConfig(self.config.GetPreferences())

            # Remove category from preference
            for p in preferences.keys():
                category = p.split(".")[0]
                pref = p.split(".")[1]

                if category == "Preferences":
                    self.preferences[pref] = preferences[p]

            # Add any default preferences that are missing
            for key in self.default:
                if not self.preferences.has_key(key):
                    self.preferences[key] = self.default[key]
             
        except:
            log.exception("Preferences.LoadPreferences: open file error")
            self.preferences = {}
                
        # Load client profile separately
        try:
            profileFile = os.path.join(self.config.GetConfigDir(),
                                       "profile" )
            self.profile = ClientProfile(profileFile)
                   
        except IOError:
            log.exception("Preferences.LoadPreferences: open file io error")

        # Load bridges separately
        for b in self.bridgeCache.GetBridges():
            self.__bridges[b.guid] = b
    
    def ResetPreferences(self):
        '''
        Reset all preferences to default values. The preferences will
        also get stored in configuration file.
        '''
        for key in self.default.GetKeys():
            self.preferences[key] = self.default[key]

        self.StorePreferences()

    def GetDefaultNodeConfig(self):
        configs = self.GetNodeConfigs()
        defaultName = self.GetPreference(self.NODE_CONFIG)
        defaultType = self.GetPreference(self.NODE_CONFIG_TYPE)
        
        for c in configs:
            if c.name == defaultName and c.type == defaultType:
                return c
            
        return None

    def SetBridges(self, bridges):
        self.__bridges = bridges
                       
    def GetBridges(self):
        return self.__bridges
                                    
    def GetNodeConfigs(self):
        '''
        Get all available node configuration from a node service.

        ** Returns **
        *configs* list of node configurations [string]
        '''
        if self.GetPreference(self.NODE_BUILTIN):
            nodeService = self.venueClient.builtInNodeService
        else:
            nodeServiceUrl = self.GetPreference(self.NODE_URL)
            nodeService = AGNodeServiceIW(nodeServiceUrl)

        configs = []
        try:
            configs = nodeService.GetConfigurations() 
        except:
            log.exception('Failed to retrieve node configurations')
              
        return configs

    def SetProfile(self, profile):
        '''
        Set client profile describing your personal information.

        ** Arguments **
        
        * profile * ClientProfile with your information.
        '''
        # To avoid storing redundant information, save
        # client preferences in profile file.
        if type(profile) != ClientProfile:
            return Exception, "Invalid Type: SetProfile takes a ClientProfile as argument"
        self.profile = profile
        
    def GetProfile(self):
        '''
        Get client profile describing your personal information.

        **Returns**

        * clientProfile * ClientProfile with your information. 
        '''
        return self.profile
    

    
