from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.Descriptions import VenueDescription
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid.hosting.pyGlobus import Client
import sys

class VenueServerTest:
    def __init__(self, url):
        print " "
        print "------------------ CONNECTING TO SERVER"
        
        self.client = Client.Handle(url).get_proxy()
        print "------------------ CONNECT OK"
        
        name = "test venue"
        description = "this is a test venue"
        print " "
        print "------------------ INSERT VENUE"
        print "venue info -- "+"name: "+name+", description: "+description
        venue = VenueDescription(name, description, "", None)
        uri = self.client.AddVenue(venue)
        
        print " "
        print "------------------ All venues in server"
        
        venueList = self.client.GetVenues()
        
        for v in venueList:
            print "/n name: "+name+"/n "+description
            
        exit1 = VenueDescription("Exit1", "Exit1 description", "", None)
        exit2 = VenueDescription("Exit2", "Exit2 description", "", None)
        print " "
        print "------------------ Set connections"
        print "name: "+exit1.name+", description: "+ exit1.description
        print "name: "+exit2.name+", description: "+ exit2.description
        
        Client.Handle(uri).get_proxy().SetConnections([exit1, exit2])
        print " "
        print "------------------ Get connections"
         
        exitsList = Client.Handle(uri).get_proxy().GetConnections()

        for e in exitsList:
            print "name: "+e.name+", description: "+ e.description
            
        print " "  
        print "------------------ Modify The Venue"
        newName = "newName"
        newDescription = "newDescription"
        print "new venue has name: "+newName+" description: "+newDescription
        venue = VenueDescription(newName, newDescription, "", None)
        self.client.ModifyVenue(uri, venue)
        print " "
        print "------------------ All venues in server"
        venueList = self.client.GetVenues()
        for v in venueList:
            print "/n name: "+name+"/n "+description

        dnName = "dnName"
        print " "
        print "------------------ Add Administrator "+"dn: "+dnName

        self.client.AddAdministrator(dnName)
        adminList = self.client.GetAdministrators()
        print " "
        print "------------------ All administrators in server"
        for v in adminList:
            print "/n dnName: "+v
            
        print " "
        print "------------------ Remove the administrator"
        self.client.RemoveAdministrator(dnName)
        adminList = self.client.GetAdministrators()

        print " "
        print "------------------ All administrators in server"
        for v in adminList:
            print "/n dnName: "+v

        address = "225.224.224.224"
        print " "
        print "------------------ Set base address: "+address
        self.client.SetBaseAddress(address)
        address = self.client.GetBaseAddress()
        print " "
        print "------------------ Get base address: "+address

        mask = 20
        print " "
        print "------------------ Set mask: "+str(mask)
        self.client.SetAddressMask(mask)
        theMask = self.client.GetAddressMask()
        print " "
        print "------------------ Get mask: "+str(theMask)

        print ""
        print "------------------ Set allocator =  MulticastAddressAllocator.RANDOM"
        self.client.SetAddressAllocationMethod(MulticastAddressAllocator.RANDOM)
        method = self.client.GetAddressAllocationMethod()
        print " "
        if method == MulticastAddressAllocator.RANDOM:
            print "------------------ Get allocator: MulticastAddressAllocator.RANDOM"
        else:
            print "------------------ Get allocator: MulticastAddressAllocator.INTERVAL"

        print " "
        print "------------------ Set allocator =  MulticastAddressAllocator.INTERVAL"
        self.client.SetAddressAllocationMethod(MulticastAddressAllocator.INTERVAL)
        method = self.client.GetAddressAllocationMethod()
        print " "
        if method == MulticastAddressAllocator.RANDOM:
            print "------------------ Get allocator: MulticastAddressAllocator.RANDOM"
        else:
            print "------------------ Get allocator: MulticastAddressAllocator.INTERVAL"

        path = "/homes/"
        print " "
        print "------------------ SetStorageLocation: "+path
        self.client.SetStorageLocation(path)
        store = self.client.GetStorageLocation()
        print " "
        print "------------------ GetStorageLocation: "+store

        print " "
        print "------------------ Remove the venue"
        self.client.RemoveVenue(uri)
        self.client.GetVenues()
        print " "
        print "------------------ All venues in server"
        venueList = self.client.GetVenues()
        for v in venueList:
            print "/n name: "+name+"/n "+description
            
if __name__ == "__main__":       
    venueServerPort = 8000
    if len(sys.argv) > 1:
        venueServerPort = sys.argv[1]
    venueServerUri = 'https://localhost:%s/VenueServer' % ( venueServerPort )
    VenueServerTest(venueServerUri)
