import traceback, random
from AccessGrid.VenueClient import VenueClient
from AccessGrid.GUID import GUID
import time

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
        VenueClient.__init__(self, profile=profile, app=app,pnode=0)
        #self.DoPostEnter = lambda x: 0
       
    def PrintVenueState( self ):
        print "--- Venue State ---"
        print " Description: ", self.venueState.description
        map( lambda listtuple: PrintList( listtuple[0], listtuple[1] ), 
             [ 
            ("Users", self.venueState.clients.values()),
            ("Connections", self.venueState.connections.values()),
            ("Data", self.venueState.data.values()),
            ("Services", self.venueState.services.values())
            ]  )

from M2Crypto import threading as m2threading
def RunClient(*args, **kw):
    m2threading.init()
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
                print "Entering Venue: %s" % venueUri
            ret = client.EnterVenue(venueUri)
            if ret:
                print '** EnterVenue ret = ', ret
            print "Client %d Entered %s %d times" % (id, venueUri,i)
        except:
            print traceback.print_exc()
            continue
        
        if verbose:
            client.PrintVenueState()

        # Pick next one
        if client.venueState is not None:
            exits = client.venueState.connections.values()
            if len(exits):
                next_index = random.randint(0, len(exits)-1)
                venueUri = exits[next_index].uri

        try:
            time.sleep(1)
            client.ExitVenue()
            if verbose:
                print "Exited venue !"
        except:
            print traceback.print_exc()

    client.Shutdown()
    m2threading.cleanup()
   
if __name__ == "__main__":
    import os, sys, threading, time
    from optparse import Option
    from AccessGrid.Toolkit import CmdlineApplication
    from AccessGrid.interfaces.VenueServer_client import VenueServerIW
    from AccessGrid.ClientProfile import ClientProfile

    m2threading.init()

    verbose =1
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
    venueUri = app.GetOption('url')

    vcList = list()

    print "Spawning venue clients"
    for id in range(app.GetOption("nc")):
       client = threading.Thread(target=RunClient, name="Venue Client %s" % id,
                                 kwargs = {'id':id, 'url': venueUri,
                                           'app' : app,
                                           'verbose' : verbose })
       client.start()

    while 1:
        numdaemonthreads = 0
        threads = threading.enumerate()
        numthreads = len(threads)
        print "Num Threads: ", numthreads
        for t in threads:
            print t
            if t.isDaemon():
                numdaemonthreads += 1

        # loop until only the main thread and daemon threads remain
        if numdaemonthreads == numthreads - 1:
            break
                
        time.sleep(1.0)

    m2threading.cleanup()
    sys.exit(0)

