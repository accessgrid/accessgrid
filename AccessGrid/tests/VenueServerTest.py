#-----------------------------------------------------------------------------
# Name:        VenueServerTest.py
# Purpose:     
#
# Author:      Susanne Lefvert
#
# Created:     2003/08/02
# RCS-ID:      $Id: VenueServerTest.py,v 1.10 2003-03-25 17:57:56 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.Descriptions import ConnectionDescription, StreamDescription
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.Types import Capability
from AccessGrid.NetworkLocation import MulticastNetworkLocation
import sys

class VenueServerTest:
    def __init__(self, url):
        print "\n------------------ CONNECTING TO SERVER"
        
        self.client = Client.Handle(url).get_proxy()
        print "------------------ CONNECT OK"
        
        name = "test venue"
        description = "this is a test venue"
     
        print "\n------------------ INSERT VENUE"
        print "name: "+name+"\n"+description
        uri = self.client.AddVenue(name, description)
        
        print "\n------------------ All venues in server"
        
        venueList = self.client.GetVenues()
        
        for v in venueList:
            print "\n name: "+v['name']+"\n "+v['description']
            
        exit1 = ConnectionDescription("Exit1", "Exit1 description", "")
        exit2 = ConnectionDescription("Exit2", "Exit2 description", "")
      
        print "\n------------------ Set connections"
        print "name: "+exit1.name+", description: "+ exit1.description
        print "name: "+exit2.name+", description: "+ exit2.description
        
        Client.Handle(uri).get_proxy().SetConnections([exit1, exit2])
       
        print "\n------------------ Get connections"
         
        exitsList = Client.Handle(uri).get_proxy().GetConnections()

        for e in exitsList:
            print "name: "+e.name+", description: "+ e.description
            
     
        print "\n------------------ Modify The Venue"
        newName = "newName"
        newDescription = "newDescription"
        print "new venue has name: "+newName+" description: "+newDescription
        venue = Client.Handle(uri).get_proxy()
        venue.SetName(newName)
        venue.SetDescription(newDescription)
     
        print "\n------------------ All venues in server"
        venueList = self.client.GetVenues()
        for v in venueList:
            print "\n name: "+v.name+"\n "+v.description

        dnName = "dnName"
     
        print "\n------------------ Add Administrator "+"dn: "+dnName

        self.client.AddAdministrator(dnName)
        adminList = self.client.GetAdministrators()
     
        print "\n------------------ All administrators in server"
        for v in adminList:
            print "\n dnName: "+v
            
     
        print "\n------------------ Remove the administrator"
        self.client.RemoveAdministrator(dnName)
        adminList = self.client.GetAdministrators()

        print "\n------------------ All administrators in server"
        for v in adminList:
            print "\n dnName: "+v

        address = "225.224.224.224"
   
        print "\n------------------ Set base address: "+address
        self.client.SetBaseAddress(address)
        address = self.client.GetBaseAddress()
       
        print "\n------------------ Get base address: "+address

        mask = 20
     
        print "\n------------------ Set mask: "+str(mask)
        self.client.SetAddressMask(mask)
        theMask = self.client.GetAddressMask()
      
        print "\n------------------ Get mask: "+str(theMask)

        print "\n------------------ Set allocator =  MulticastAddressAllocator.RANDOM"
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
      
        print "\n------------------ SetStorageLocation: "+path
        self.client.SetStorageLocation(path)
        store = self.client.GetStorageLocation()
    
        print "\n------------------ GetStorageLocation: "+store

        videoAddress = '111.111.11.111'
        videoPort = 1000
        videoTtl = 1
       
        print  "\n------------------ Create static video stream"
        print '*** Static video stream:'
        print "host: ", videoAddress
        print "port: ", videoPort
        print "time to live: ", videoTtl

        venue = Client.Handle(uri).get_proxy()
        
        location = MulticastNetworkLocation(videoAddress, videoPort, videoTtl)
        capability = Capability( Capability.PRODUCER, Capability.VIDEO)
        videoStreamDescription = StreamDescription( "", "", location, capability)  
        videoStreamDescription.static = 1
        venue.AddStream(videoStreamDescription)

        audioAddress = '222.222.22.222'
        audioPort = 2000
        audioTtl = 2
        print  "\n------------------ Create static audio stream: "
        print '*** Static audio stream:'
        print "host: ", audioAddress
        print "port: ", audioPort
        print "time to live: ", audioTtl
        location = MulticastNetworkLocation(audioAddress, audioPort, audioTtl)
        capability = Capability( Capability.PRODUCER, Capability.AUDIO)
        audioStreamDescription = StreamDescription( "", "", location, capability)  
        audioStreamDescription.static = 1
        venue.AddStream(audioStreamDescription)

        print  "\n------------------ Get static streams"
        streamList = venue.GetStaticStreams()
        for stream in streamList:

            if(stream.capability.type == Capability.VIDEO):
                print "*** Static video stream:"
                print 'host: ',stream.location.host
                print 'port: ',stream.location.port
                print 'time to live: ',stream.location.ttl
                                    
            elif(stream.capability.type == Capability.AUDIO):
                print "\n*** Static audio stream:"
                print 'host: ',stream.location.host
                print 'port: ',stream.location.port
                print 'time to live: ',stream.location.ttl
               
        print  "\n------------------ Remove static streams"
        streamList = venue.GetStaticStreams()
        for stream in streamList:
            venue.RemoveStream(stream)

        print  "\n------------------ Get static streams"
        streamList = venue.GetStaticStreams()
        print "We have ", len(streamList), " static streams in venue"

        print "\n------------------ Set venue server encryption to 1"
        self.client.SetEncryptAllMedia(1)
        
        value = self.client.GetEncryptAllMedia()
        print "\n------------------ Get venue server encryption "+str(value)

        print "\n------------------ Set venue encryption with key = ' '"
        venue.SetEncryptMedia(1, ' ')

        print "\n------------------ Get venue encryption key = " +  venue.GetEncryptMedia()
            
        print "\n------------------ Remove the venue"
        self.client.RemoveVenue(uri)
        self.client.GetVenues()
        
        print "\n------------------ All venues in server"
        venueList = self.client.GetVenues()
        for v in venueList:
            print "\n name: "+v.name+"\n "+v.description
            
if __name__ == "__main__":       
    venueServerUrl = "https://localhost:8000/VenueServer"
    if len(sys.argv) > 1:
        venueServerUrl = sys.argv[1]
    VenueServerTest(venueServerUrl)
