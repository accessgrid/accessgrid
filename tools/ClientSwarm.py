from AccessGrid.VenueClient import VenueClient

def PrintList( listname, thelist ):
   print " ",listname," ------"
   for item in thelist:
      print "  ", item.name
      if "uri" in item.__dict__.keys(): print "   uri = ", item.uri

class MyVenueClient( VenueClient ):
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
        self.PrintVenueState()

    def ExitVenue(self):
        """
        Note: Overloaded from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client exits a venue.
        """
        VenueClient.ExitVenue( self )
        print "Exited venue ! "

    def PrintVenueState( self ):
       venueState = self.venueState
       print "--- Venue State ---"
       print " Name: ", venueState.name
       print " Description: ", venueState.description
       map( lambda listtuple: PrintList( listtuple[0], listtuple[1] ), 
          [ 
          ("Users", venueState.clients.values()),
          ("Connections", venueState.connections.values()),
          ("Data", venueState.data.values()),
          ("Services", venueState.services.values())
          ]  )

if __name__ == "__main__":
    import os, sys
    from optparse import Option
    from AccessGrid.Toolkit import CmdlineApplication
    from AccessGrid.VenueServer import VenueServerIW
    from AccessGrid.ClientProfile import ClientProfile

    app = CmdlineApplication()

    urlOption = Option("-u", "--url", dest="url",
                       default="https://localhost:8000/VenueServer",
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
       
    # Get default venue from venue server
    print "Getting default venue"
    venueUri = VenueServerIW(app.GetOption("url")).GetDefaultVenue()

    vcList = list()

    print "Creating venue clients"
    for id in range(app.GetOption("nc")):
        profile = ClientProfile('userProfile')
        profile.name = "User"+str(id)
        profile.publicId = profile.publicId + str(id)
        vcList.append( MyVenueClient(profile, app))

    for i in range(app.GetOption("rt")):
        print "Roundtrip: ", i
        print "Clients entering: "
        for vc in vcList:
            print "  ", vc.profile.name
            try:
                vc.EnterVenue( venueUri )
            except:
                print sys.exc_type
                print sys.exc_value
                print sys.exc_info()

        print "Clients exiting: "
        for vc in vcList:
            print "  ", vc.profile.name
            try:
                vc.ExitVenue()
            except:
                print sys.exc_type
                print sys.exc_value
                print sys.exc_info()

    os._exit(1)

