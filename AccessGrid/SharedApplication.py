from AccessGrid import VenueClient
from AccessGrid import EventClient
from AccessGrid import Events

from AccessGrid.hosting.pyGlobus import Client


class SharedApplication:

    def __init__(self, appName, venueUri, profile ):

        self.appName = appName

        # Create the venue client object and enter the venue
        self.clientObj = VenueClient.VenueClient()
        self.clientObj.SetProfile(profile)
        self.clientObj.EnterVenue(venueUri)

        
        # We first try to find an app in the venue.
        # If one does not exist, call CreateApplication() to set one up.
        # Otherwise join to the one already there.
        app = self.FindApplication()
        if app is None:
            prox = Client.Handle(venueUri).GetProxy()
            appProxy, self.publicId, self.privateId = self.CreateApplication(prox)
        else:
            appProxy = Client.Handle(app.handle).GetProxy()
            (self.publicId, self.privateId) = appProxy.Join("newprof")

        #
        # Retrieve the channel id. We've stored it in the app object's
        # data store with a key of "channel".
        #
        self.channelId = appProxy.GetData(self.privateId, "channel")

        # 
        # Subscribe to the event channel, using the event service
        # location provided by the app object.
        #
        eventServiceLocation = appProxy.GetEventServiceLocation()
        self.eventClient = EventClient.EventClient(eventServiceLocation)
        self.eventClient.start()
        self.eventClient.Send(Events.ConnectEvent(self.channelId))

    def FindApplication(self):
        """
        Look through the applications in the venue.

        Find this application and return its data. 
        If one does not exist, return None.
        """
        print self.clientObj.venueState.applications.items()
        for id, app in self.clientObj.venueState.applications.items():
            if app.name == self.appName:
                return app
        return None

    def CreateApplication(self,venueProxy):
        """
        Creates the app object, joins to it, and initializes state.
        Returns a proxy to the application object, and its public and private IDs.
        """
        appHandle = venueProxy.CreateApplication(self.appName, "have to figure this out")
        appProxy = Client.Handle(appHandle).GetProxy()
        id = appProxy.GetId()

        #
        # Join the app
        #
        (publicId, privateId) = appProxy.Join("myprofile")

        #
        # Set up the event channel.
        #
        (channel, loc) = appProxy.CreateDataChannel(privateId)
        appProxy.SetData(privateId, "channel", channel)

        return (appProxy, publicId, privateId)

