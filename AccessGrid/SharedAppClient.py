import os

from AccessGrid import Log
from AccessGrid.EventClient import EventClient
from AccessGrid.Events import ConnectEvent, Event
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.hosting import Client

class SharedAppClient:
    '''
    The SharedAppClient may be used when building shared applications.
    This class encapsulates a handler to the application service and
    the event service associated with the application.  The SharedAppClient
    provides an interface to the Shared Application.
    '''
    
    def __init__(self, appName):
        '''
        Creates the client.

        **Arguments**
        
        *appName* The name of the application. Log file is by default named <appName>.log.
         '''
        self.__publicId = None
        self.__privateId = None
        self.__channelId = None
        self.__appProxy = None
        self.__appUrl = None
        self.__appName = appName

        self.__dataCache = {}
        self.__callbackTable = []

        
    def InitLogging(self, debug = 0, log = None):
        """
        This method sets up logging that prints debug and error messages.
        If you want to see more logging information use the appName 'AG',
        then you'll see logging information from the Access Grid Module.

        For more information about the logging module, check out:
        http://www.red-dove.com/python_logging.html

        **Arguments**
        
        *debug* If debug is set to 1, log messages will be printed to file
        and command window

        *log* Name of log file. If set to None, <appName>.log is used
        """

        # Set up a venue client log, too, since it's used by the event client
        self.log = Log.GetLogger(Log.VenueClient)
        
        hdlr = Log.StreamHandler()
        hdlr.setFormatter(Log.GetFormatter())
        Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())
        
        self.log = Log.GetLogger(self.__appName)
        Log.SetDefaultLevel(self.__appName, Log.DEBUG)
                
        # Log to file
        if log == None:
            logFile = self.__appName + ".log"
        else:
            logFile = log

        fileHandler = Log.FileHandler(logFile)
        fileHandler.setFormatter(Log.GetFormatter())
        Log.HandleLoggers(fileHandler, Log.GetDefaultLoggers())

        # If debug mode is on, log to command window too
        if debug:
            hdlr = Log.StreamHandler()
            hdlr.setFormatter(Log.GetFormatter())
            Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())

        return self.log
       
    def Join(self, appServiceUrl, clientProfile = None):
        '''
        Connect registers this client with the SharedApplication at
        specified URL.  The registration gives access to the
        EventService used for data communication among applications
        connected to this service.
        
        **Arguments**
        
        *appServiceUrl* location of application service.
        '''
      
        self.__appUrl = appServiceUrl
        
        # Get a handle to the application service in the venue
        self.__appProxy = Client.SecureHandle(appServiceUrl).GetProxy()
                

        try:
            # Join the application object with your client profile
            (self.__publicId, self.__privateId) = self.__appProxy.Join(clientProfile)
        except Client.MethodNotFound, e:
            try:
                (self.__publicId, self.__privateId) = self.__appProxy.Join()
                self.log.info("SharedAppClient.Connect: Service at %s is running old software"
                          %self.__appUrl)
            except:
                self.log.exception("SharedAppClient.Connect: Failed to join service at %s"%self.__appUrl)
        except:
            self.log.exception("SharedAppClient.Connect: Failed to join service at %s"%self.__appUrl)
        
        try:
            # Retrieve data/event channel id
            (self.__channelId, esl) = self.__appProxy.GetDataChannel(self.__privateId)
            
        except:
            self.log.exception("SharedAppClient.Connect: Failed to get data channel")
            raise "Failed to join application service at %s." %self.__appUrl
                    
        # Subscribe to the data/event channel
        self.eventClient = EventClient(self.__privateId, esl, self.__channelId)
        self.RegisterEventCallback(Event.APP_SET_DATA, self.__ReceiveDataUpdate)
        self.eventClient.start()
        self.eventClient.Send(ConnectEvent(self.__channelId, self.__privateId))

    def Shutdown(self):
        '''
        Exit from application service and shut down event client.
        '''
        try:
            self.eventClient.Stop()
        except:
            self.log.exception("SharedAppClient.Shutdown: Could not stop event client")

        try:
            self.__appProxy.Leave(self.__privateId)
        except:
            self.log.exception("SharedAppClient.Shutdown: Could not leave application service.")
                        
    def RegisterEventCallback (self, eventType, callback):
        '''
        Register callback for event. Several callbacks can be registered for each event.
        
        **Arguments**
        
        *eventType* Event to listen for.

        *callback* Method called when receiving event of type eventType.
        '''
        if not self.__EventIsRegistered(eventType):
            # Only register the event once since the same callback method is used.
            self.eventClient.RegisterCallback(eventType, self.HandleEvent)

        # Insert unique callback in table.
        self.__callbackTable.append((eventType, callback))

    def HandleEvent(self, event):
        '''
        This method is called when an event is distributed in the application service.
        NOTE: Used internally.
        '''
       
        if self.__EventIsRegistered(event.eventType):
            # Execute the callbacks.
            for e, callback in self.__callbackTable:
                if e == event.eventType:
                    try:
                        callback(event)
                        
                    except:
                        self.log.exception("SharedAppClient.HandleEvent: Callback failed for event %s" %(event.eventType))
                        raise "Callback failed for event '%s'" %event.eventType

        else:
            self.log.exception("SharedAppClient.HandleEvent: Callback has not been registered for this event %s" %(event.eventType))
            raise "Callback has not been registered for this event '%s'" %(event.eventType)
      
    def SendEvent(self, eventType, data):
        '''
        Post an event to all applications connected to the service.
        
        Note: This client will receive its own events.
        
        **Arguments**
        
        *eventType* Event to send

        *data* Data associated with this event 
        '''

        evt = Event(eventType, self.__channelId, data)
        self.eventClient.Send(evt)
        
    def SetData(self, dataKey, dataValue):
        '''
        Add data to application service.
        
        Note: If data with same dataKey is already present in the
        application service, the old dataValue will be overwritten.

        **Arguments**

        *dataKey* Unique id for this data

        *dataValue* The actual data
        '''
        try:
            self.__appProxy.SetData(self.__privateId, dataKey, dataValue)
            self.__dataCache[dataKey] = dataValue
        except:
            self.log.exception("SharedAppClient.SetData: Failed to set data, key: %s, value: %s" %(dataKey, dataValue))
            raise "Failed to set data"

    def GetData(self, dataKey):
        '''
        Get data from application service
        
        **Arguments**
        
        *dataKey* Unique id of data available in the service
        
        **Returns**
        
        *dataValue* The value associated with the specified dataKey
        '''
        # Check local cache first
        if self.__dataCache.has_key(dataKey):
            return self.__dataCache[dataKey]

        try:
            data = self.__appProxy.GetData(self.__privateId, dataKey)
            self.__dataCache[dataKey] = data
        except:
            self.log.exception("SharedAppClient.GetData: Failed to get data for key %s" %dataKey)
            raise "Failed to get data for key '%s'" %dataKey
        
        return data
  
    def GetPublicId(self):
        '''
        Access method for public ID.
        
        **Returns**
        
        *publicId* Id associated with this client.
        '''

        return self.__publicId
    
    def GetVenueURL(self):
        '''
        Access method for venue URL where the application service is running.

        **Returns**
        
        *url* URL to venue where the application service is running.
        '''
        try:
            url =  self.__appProxy.GetVenueURL(self.__privateId)
        except:
            self.log.exception("SharedAppClient.GetVenueURL: Failed to get venue URL")
            raise "Failed to get venue URL"

        return url
  
    def GetApplicationState(self):
        '''
        Access method for application state.

        **Returns**

        *state* Application state.
        '''

        try:
            state = self.__appProxy.GetState(self.__privateId)
        except Client.MethodNotFound, e:
            self.log.exception("SharedAppClient.GetApplicationState: Failed to get application state")
            raise "The server you are connecting to is running old software. This method is not implemented in that version." 
        except:
            self.log.exception("SharedAppClient.GetApplicationState: Failed to get state")
            raise "Failed to get application state" 

        return state

    def GetApplicationID(self):
        '''
        Access method for application service specific ID.
        
        **Returns**
        
        *appId* ID associated with the application service we are connected to.
        '''
        
        # Check GetState instead of GetId; GetId exists on old servers but with no
        # private id as argument.

        try:
            id = self.__appProxy.GetId(self.__privateId)
        except Client.MethodNotFound, e:
            self.log.exception("SharedAppClient.GetApplicationID: Failed to get application ID")
            raise "The server you are connecting to is running old software. This method is not implemented in that version." 
        except:
            self.log.exception("SharedAppClient.GetApplicationId: Failed to get application ID")
            raise "Failed to get application ID"

        return id
    
    def GetParticipants(self):
        '''
        Access method for participants.

        **Returns**
        
        *participants* List of AppParticipantDescriptions.
        '''

        try:
            participants = self.__appProxy.GetParticipants(self.__privateId)
        except Client.MethodNotFound, e:
            self.log.exception("SharedAppClient.GetParticipants: Failed to get participants")
            raise "The server you are connecting to is running old software. This method is not implemented in that version." 
                           
        except:
            self.log.exception("SharedAppClient.GetParticipants: Failed to participants")
            raise "Failed to get application participants" 

        return participants

    def GetComponents(self):
        '''
        Access method for all instances connected to the application service.

        **Returns**
        
        *components* List of public IDs for each instance connected to the application service.
        '''

        try:
            components = self.__appProxy.GetComponents(self.__privateId)
        except Client.MethodNotFound, e:
            self.log.exception("SharedAppClient.GetComponents: Failed to get components")
            raise "The server you are connecting to is running old software. This method is not implemented in that version." 
                           
        #except:
        #self.log.exception("SharedAppClient.GetComponents: Failed to get components")
        #   raise "Failed to get application components" 

        return components
        
    def GetDataKeys(self):
        '''
        Access method for data keys.

        **Returns**
        
        *keys* List of data keys.
        '''

        try:
            keys = self.__appProxy.GetDataKeys(self.__privateId)
        except Client.MethodNotFound, e:
            self.log.exception("SharedAppClient.GetDataKeys: Failed to get data keys")
            raise "The server you are connecting to is running old software. This method is not implemented in that version." 

        except:
            self.log.exception("SharedAppClient.GetDataKeys: Failed to get data keys")
            raise "Failed to get application data keys" 

        return keys

    def SetParticipantStatus(self, status):
        '''
        Set your status.

        **Arguments**

        *status* Status string
        '''

        try:
            self.__appProxy.SetParticipantStatus(self.__privateId, status)
        except Client.MethodNotFound, e:
            self.log.exception("SharedAppClient.SetParticipantStatus: Failed to set participant status")
            raise "The server you are connecting to is running old software. This method is not implemented in that version." 
        except:
            self.log.exception("SharedAppClient.SetParticipantStatus: Failed to set status")
            raise "Failed to set participant status" 

    def SetParticipantProfile(self, profile):
        '''
        Set your profile.

        **Arguments**

        *profile* Your ClientProfile.
        '''

        try:
            self.__appProxy.SetParticipantProfile(self.__privateId, profile)
        except Client.MethodNotFound, e:
            self.log.exception("SharedAppClient.SetParticipantProfile: Failed to set participant profile")
            raise "The server you are connecting to is running old software. This method is not implemented in that version." 
        except:
            self.log.exception("SharedAppClient.SetParticipantProfile: Failed to set profile")
            raise "Failed to set participant profile"

    def __ReceiveDataUpdate(self, event):
        '''
        This method is called when data has been set in the application service.
        
        **Arguments**
        
        *event* Received event.
        '''
        # Update data cache.
        self.__dataCache[event.data.key] = event.data.value

    def __EventIsRegistered(self, eventType):
        '''
        Check if event is registered locally in callback table.
        '''
        for e, callback in self.__callbackTable:
            
            if e == eventType:
                return 1
            
        return 0

if __name__ == "__main__":
    appUrl = "https://zuz-10:8000/102"
  
    def Callback(event):
        print '**** Received event (first)', event.data

    def Callback2(event):
        print '**** Received event (second)', event.data
    
    # Create shared application c  print "get data keys ", self.sharedAppClient.GetDataKeys()lient
    sharedAppClient = SharedAppClient("Test Client")
    sharedAppClient.InitLogging()

    # Get client profile
    clientProfileFile = os.path.join(UserConfig.instance().GetConfigDir(),
                                     "profile")
    clientProfile = ClientProfile(clientProfileFile)
    
    # Connect to shared application service. 
    sharedAppClient.Join(appUrl, clientProfile)
    
    # Register callback
    sharedAppClient.RegisterEventCallback("event1", Callback )
    sharedAppClient.RegisterEventCallback("event1", Callback2)
       
    print "\n--set data; dataKey1:data1, dataKey2:data2"
    sharedAppClient.SetData("key1", "data1")
    sharedAppClient.SetData("key2", "data2")
    print "\n--get data keys; "
    keys = sharedAppClient.GetDataKeys()
    for k in keys:
        print "   ", k
   
    print "\n--get data for dataKey1;",  sharedAppClient.GetData("dataKey1")
    print "\n--get public ID; ",  sharedAppClient.GetPublicId()
    print "\n--get app ID; ",  sharedAppClient.GetApplicationID()
    print "\n--get venue URL; ",  sharedAppClient.GetVenueURL()
    print "\n--get application state; "
    state = sharedAppClient.GetApplicationState()
    print '  ', state.name
    print '  ', state.description
    print '  ', state.id
    print '  ', state.mimeType
    print '  ', state.uri
    print '  ', state.data

    print "\n--send event event1:2"
    sharedAppClient.SendEvent('event1', '2')
    print "event got sent"
                        
    print "\n--get participants; "
    for p in sharedAppClient.GetParticipants():
        if p.clientProfile != 'None' and p.clientProfile != None:
            print p.clientProfile.name

    print "\n--get components;"
    for p in sharedAppClient.GetComponents():
        print p
    
    clientProfileFile = os.path.join(UserConfig.instance().GetConfigDir(),
                                     "profile")
    clientProfile = ClientProfile(clientProfileFile)
    clientProfile.name = "new name"
    print "\n--set profile with name 'new name'"
    sharedAppClient.SetParticipantProfile(clientProfile)

    sharedAppClient.SetData("newKey", 15)
    sharedAppClient.SetData("newKey", 16)
               
    print "\n--set status to 'ready' "
    sharedAppClient.SetParticipantStatus('ready') 
    
    print "\n--participants; "
    for p in sharedAppClient.GetParticipants():
        if p.clientProfile != "None" and p.clientProfile != None:
            print p.clientProfile.name, p.status
    
    sharedAppClient.Shutdown()
  
