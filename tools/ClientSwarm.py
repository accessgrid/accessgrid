import traceback, random
from AccessGrid.VenueClient import VenueClient
from AccessGrid.GUID import GUID


def PrintList( listname, thelist ):
    print " ",listname," ------"
    for item in thelist:
        print "  ", item.name
        if "uri" in item.__dict__.keys(): print "   uri = ", item.uri

class MyVenueClient(VenueClient):
    """
    MyVenueClient is a wrapper for the base VenueClient.
    It prints the venue state when it enters a venue or 
    receives a coherence event.  A real client would probably
    update its UI instead of printing the venue state as text.
    """
    def __init__(self, profile, app):
        VenueClient.__init__(self, profile=profile, app=app)
       
    def EnterVenue(self, URL):
        """
        Note: Overloaded from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client enters a venue.
        """
        VenueClient.EnterVenue( self, URL )
        
    def ExitVenue(self):
        """
        Note: Overloaded from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client exits a venue.
        """
        VenueClient.ExitVenue( self )

    def PrintVenueState( self ):
        print "--- Venue State ---"
        print " Name: ", self.venueState.name
        print " Description: ", self.venueState.description
        map( lambda listtuple: PrintList( listtuple[0], listtuple[1] ), 
             [ 
            ("Users", self.venueState.clients.values()),
            ("Connections", self.venueState.connections.values()),
            ("Data", self.venueState.data.values()),
            ("Services", self.venueState.services.values())
            ]  )

def RunClient(*args, **kw):
    id = kw['id']
    venueUri = kw['url']
    app = kw['app']
    iter = app.GetOption("rt")
    verbose = kw['verbose']

    profile = ClientProfile()
    profile.name = "Test Client %s" % id
    profile.publicId = str(GUID())

    client = MyVenueClient(profile, app)
    
    for i in range(iter):
        try:
            if verbose:
                print "Entering Venue: %s" % URL
            client.EnterVenue(venueUri)
            print "Client %d Entered %s" % (id, client.venueState.name)
        except:
            print traceback.print_exc()
        
        if verbose:
            client.PrintVenueState()

        # Pick next one
        if client.venueState is not None:
            exits = client.venueState.connections.values()
            if len(exits):
                next_index = random.randint(0, len(exits)-1)
                venueUri = exits[next_index]

        try:
            client.ExitVenue()
            if verbose:
                print "Exited venue !"
        except:
            print traceback.print_exc()

    client.Shutdown()
   
if __name__ == "__main__":
    import os, sys, threading, time
    from optparse import Option
    from AccessGrid.Toolkit import CmdlineApplication
    from AccessGrid.VenueServer import VenueServerIW
    from AccessGrid.ClientProfile import ClientProfile

    verbose = 0
    random.seed(time.time())
    
    app = CmdlineApplication()

    urlOption = Option("-u", "--url", dest="url",
                       default="https://localhost/VenueServer",
                       help="URL to the venue server to test.")
    app.AddCmdLineOption(urlOption)

    nvcOption = Option("-n", "--num-clients", dest="nc", type="int",
                       default=1, help="number of clients to use.")
    app.AddCmdLineOption(nvcOption)

    rtOption = Option("-t", "--traverse", dest="rt", type="int",
              default=10, help="number of venues each client will traverse.")
    app.AddCmdLineOption(rtOption)
    
    try:
       app.Initialize("ClientSwarm")
    except:
       print "Application initialize failed, exiting."
       sys.exit(-1)
       
    print "Getting default venue"
    venueUri = VenueServerIW(app.GetOption("url")).GetDefaultVenue()

    vcList = list()

    print "Spawning venue clients"
    for id in range(app.GetOption("nc")):
       client = threading.Thread(target=RunClient, name="Venue Client %s" % id,
                                 kwargs = {'id':id, 'url': venueUri,
                                           'app' : app,
                                           'verbose' : verbose })
       client.start()

    while len(threading.enumerate()) > 1:
        #print "Num Threads: %d" % len(threading.enumerate())
        #for t in threading.enumerate():
        #    print t
        time.sleep(1.0)

    sys.exit(0)

