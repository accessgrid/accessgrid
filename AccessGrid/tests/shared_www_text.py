import sys
import logging

import AccessGrid.Types
from AccessGrid.Platform import GPI 
from AccessGrid import EventClient
from AccessGrid import VenueClient
from AccessGrid import Events

from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Types import *
from AccessGrid.hosting.pyGlobus import Client

log = logging.getLogger("watcher")

def init_logging(appName):
    logger = logging.getLogger("AG")
    logger.setLevel(logging.DEBUG)
    hdlr = logging.StreamHandler()
    fmt = logging.Formatter("%(name)-17s %(asctime)s %(levelname)-5s %(message)s")
    hdlr.setFormatter(fmt)
    logger.addHandler(hdlr)

    appLogger = logging.getLogger(appName)
    appLogger.setLevel(logging.DEBUG)
    appLogger.addHandler(hdlr)
    
def findBrowser(clientObj):
    """
    Look through the applications in the venue.

    Find the one that's named "SharedWeb", and return its
    data. If one does not exist, return None.

    """

    #
    # venueState.applications is a dictionary, where the keys are
    # the IDs of the applications and the values are the
    # application information structures. We construct
    # applicationList to be a list of the application information structures.
    #
    # Members of interest in these structures are
    #
    #      name - name of the application
    #      description - an application-defined description of the application
    #      id - the unique identifier for this application instance
    #      handle - the web service handle for this application object
    #      data - the application's data storage, itself a dictionary.
    #
    # Here, we just look at app.name.
    #
    
    applicationList = clientObj.venueState.applications.values()
    
    for  app in applicationList:
        if app.name == "Shared Browser":
            return app
    return None

def createBrowser(venueProxy, clientObj):
    """
    Create a new browser app.

    Creates the app object, joins to it, and initializes state.
    Returns a proxy to the application object, and its public and private IDs.
    """

    #
    # Use the Venue's CreateApplication() method to create a new application instance.
    # Name it "Shared Browser".
    #
    log.debug("creating browser app obj")
    appHandle = venueProxy.CreateApplication("Shared Browser", "shared web browser")

    #
    # Get a web service proxy on that new application
    #
    appProxy = Client.Handle(appHandle).GetProxy()

    #
    # and ask it for it's unique ID.
    #
    id = appProxy.GetId()
    
    log.debug("new app has id %s", id)

    #
    # Invoke the application's Join method, which returns to us our
    # public and private identifiers.
    #

    (publicId, privateId) = appProxy.Join("myprofile")

    log.debug("Joined app, pub=%s priv=%s", publicId, privateId)

    #
    # Create a new data channel
    #

    (channelId, loc) = appProxy.CreateDataChannel(privateId)

    log.debug("Created channel name=%s location=%s",
              channelId, loc._aslist)

    #
    # And save its identifier in the application data store.
    #

    appProxy.SetData(privateId, "channel", channelId)

    return (appProxy, publicId, privateId)

def browseCallback(myId, data):
    """
    Callback invoked when incoming browse events arrive.

    Determine if the sender of the event is this application or not.

    """

    #
    # Clear out the console prompt line.
    #
    print ""

    (senderId, url) = data
    if senderId == myId:
        print "Ignoring %s from myself" % (url)
    else:
        print "Browse to ", url

def browser(clientObj, url):
    """
    Main guts of the shared browser functionality.

    clientObj is a VenueClient instance for the venue we're connected to.
    url is the url to that venue.

    We first try to find a browser app in the venue.
    If one does not exist, call createBrowser() to set one up.
    Otherwise join to the one already there.

    """

    prox = Client.Handle(url).GetProxy()

    app = findBrowser(clientObj)

    if app is None:
        appProxy, publicId, privateId = createBrowser(prox, clientObj)
    else:
        appProxy = Client.Handle(app.handle).GetProxy()
        (publicId, privateId) = appProxy.Join("newprof")
        log.debug("Joined existing app, got pub=%s priv=%s",
                  publicId, privateId)

    #
    # Retrieve the channel id. We've stored it in the app object's
    # data store with a key of "channel".
    #

    channelId = appProxy.GetData(privateId, "channel")
    log.debug("Got channel id %s", channelId)

    # 
    # Subscribe to the event channel, using the event service
    # location provided by the app object.
    #

    eventServiceLocation = appProxy.GetEventServiceLocation()
    log.debug("Got event service location=%s", eventServiceLocation._asdict)

    eventClient = EventClient.EventClient(eventServiceLocation)
    eventClient.start()
    eventClient.Send(Events.ConnectEvent(channelId))


    #
    # Register our callback.
    #
    # The callback function is invoked with one argument, the data from the call.
    # We want that code to also have a handle on the current browser ID, so
    # register a lambda that defaults.
    #
    # Yah, it might be excessive language play but it's quite a useful idiom
    # to be familiar with.
    #

    eventClient.RegisterCallback("browse",
                                 lambda data, id=publicId: browseCallback(id, data))

    #
    # Loop reading URLs from the console. This takes the place of
    # getting actual data back from the browser.
    #

    while 1:
        sys.stdout.write("URL> ")
        l = sys.stdin.readline()

        if l == "":
            break
        
        l = l.strip()
        print "Sending URL ", l

        #
        # Send out the event, including our public ID in the message.
        #
        eventClient.Send(Events.Event("browse", channelId, (publicId, l)))
        

    #
    # All done. 
    #

    appProxy.Leave(privateId)
        
def main():
    venueServerPort = 8000
    if len(sys.argv) > 1:
        venueServerPort = sys.argv[1]
    venueServerUri = 'https://localhost:%s/Venues/default' % ( venueServerPort )

    #
    # Create a local venueclient object for handling the
    # client/venue protocol.
    #

    clientObj = VenueClient.VenueClient()
    profile = ClientProfile('userProfile')
    clientObj.SetProfile(profile)
    clientObj.EnterVenue(venueServerUri)

    browser(clientObj, venueServerUri)

    print "Exiting"
    clientObj.ExitVenue()

    
if __name__ == "__main__":
    init_logging("watcher")
    main()
