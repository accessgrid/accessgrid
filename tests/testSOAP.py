#
#
#
#
#

import AccessGrid.hosting.pyGlobus.Client as Client

ServerURL = "https://vv2.mcs.anl.gov:8020/VenueServer"
#ServerURL = "https://localhost:8000/VenueServer"

server = Client.Handle(ServerURL).get_proxy()

defVenueURL = server.GetDefaultVenue()

print "Default Venue: ", defVenueURL

#v = Client.Handle(defVenueURL).get_proxy()

#print "Def Venue is Valid: ", v._IsValid()

print "Calling GetVenues"

#venues = server.GetVenues()

print "Got Venues."

#for v in venues:
#    print "Venue: ", v
#    dv = Client.Handle(v.uri).get_proxy()
#    dv._IsValid()

print "Finished"
