import os
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
    

    def EnterVenue(self, URL):
        """
        Note: Overloaded from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client enters a venue.
        """
        VenueClient.EnterVenue( self, URL )
        #self.PrintVenueState()


    def ExitVenue(self ):
        """
        Note: Overloaded from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client exits a venue.
        """
        VenueClient.ExitVenue( self )
        #print "Exited venue ! "


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

def Enter( venueUri, profile ):
    
    print "Entering venue: name = ", profile.name
    vc = MyVenueClient( profile )
    vc.EnterVenue( venueUri )



if __name__ == "__main__":

    import sys
    from AccessGrid.hosting.pyGlobus.Server import Server
    from AccessGrid.hosting.pyGlobus import Client
    from AccessGrid.ClientProfile import ClientProfile
    from AccessGrid.Types import *

    NUM_VENUE_CLIENTS = 1
    NUM_ROUNDTRIPS = 260

    #
    # process arguments
    venueServerUri = "https://localhost:8000/VenueServer"
    if len(sys.argv) > 1:
        venueServerUri = sys.argv[1]

    #
    # Get default venue from venue server
    #
    print "Getting default venue"
    venueUri = Client.Handle( venueServerUri ).get_proxy().GetDefaultVenue()

    print "Reading profile"

    vcList = []

    print "Creating venue clients"
    for id in range(NUM_VENUE_CLIENTS):
        profile = ClientProfile('userProfile')
        profile.name = "User"+str(id)
        profile.publicId = profile.publicId + str(id)
        vcList.append( MyVenueClient( profile ) )


    for i in range(NUM_ROUNDTRIPS):
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



    #
    # Create VenueClient and enter venue
    #os._exit(1)

    """

    #profile.name = "Changed name"
    #Client.Handle( venueUri ).get_proxy().UpdateClientProfile( profile )


    # 
    # Create web service for venue client
    server = Server( 8700 )
    service = server.create_service_object("VenueClient")
    vc._bind_to_service( service )


    #
    # Update venue client with venue client uri
    #
    vc.profile.venueClientUri = vc.get_handle()

    #vc.coherenceClient.stop()


    #
    # Start service
    #
    print "Starting service; URI: ", vc.get_handle()
    server.run()
    """
