#-----------------------------------------------------------------------------
# Name:        VenueServerTest.py
# Purpose:     
#
# Author:      Susanne Lefvert
#
# Created:     2003/08/02
# RCS-ID:      $Id: VenueServerTest.py,v 1.13 2003-05-23 21:00:36 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.Descriptions import ConnectionDescription, StreamDescription
from AccessGrid.Descriptions import VenueDescription
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.Types import Capability
from AccessGrid.NetworkLocation import MulticastNetworkLocation
import sys


def VenueCompare( venue1, venue2 ):
    """
    Compare equality of two venues 
    """
    
    venuesEqual = 0

    if not venue1.name == venue2.name:
        return (0, "names not equal")
    
    if not venue1.description == venue2.description:
        return (0, "descriptions not equal")

    if not len(venue1.administrators) == len(venue2.administrators):
        return (0, "administrator lists not same length")

    for admin in venue1.administrators:
        if not admin in venue2.administrators:
            return (0, "admin list mismatch")

    if not venue1.encryptMedia == venue2.encryptMedia:
        return (0, "encrypt media mismatch")

    if not venue1.encryptionKey == venue2.encryptionKey:
        return (0, "encryption key mismatch")

    if not len(venue1.connections) == len(venue2.connections):
        return (0, "connection lists not same length")

    for conn in venue1.connections.values():
        if not conn in venue2.connections.values():
            return (0, "admin list mismatch")

    if not len(venue1.streams) == len(venue2.streams):
        return (0, "connection lists not same length")

    for stream in venue1.streams.values():
        if not stream in venue2.streams.values():
            return (0, "admin list mismatch")

    return 1


def PrintError( errorString ):
    print "* * FAILURE: ", errorString

class VenueServerTest:
    def __init__(self, url):
        print "\n------------------ CONNECTING TO SERVER"
        
        serverHandle = Client.Handle(url)
        try:
            serverHandle.IsValid()
        except:
            print "Invalid server handle; exiting"
            sys.exit(1)

        self.venueServerProxy = serverHandle.get_proxy()
        print "------------------ CONNECT OK"
        

        #
        # Add a venue
        #

        print "\n------------------ INSERT VENUE"

        # Make a venue description
        venue = VenueDescription( "test venue",
                                  "test venue description")


        # Set Exits
        venue.connections["urlExit1"] =  ConnectionDescription("exit1", "test exit1", "") 
        venue.connections["urlExit2"] =  ConnectionDescription("exit2", "test exit2", "")

        # Set Static Video
        venue.streams = []
        svml = MulticastNetworkLocation("224.2.2.2", 24000, 127)
        staticVideoCap = Capability(Capability.PRODUCER, Capability.VIDEO)
        venue.streams.append(StreamDescription("Static Video",
                                               svml, staticVideoCap,
                                               0, None, 1))
        # Set Static Audio
        saml = MulticastNetworkLocation("224.2.2.2", 24002, 127)
        staticAudioCap = Capability(Capability.PRODUCER, Capability.AUDIO)
        venue.streams.append(StreamDescription("Static Audio",
                                               saml, staticAudioCap,
                                               0, None, 1))

        # Set Encryption
        venue.encryptMedia = 1
        venue.encryptionKey = "1234567890"

        # Add the venue to the server
        uri = self.venueServerProxy.AddVenue(venue)
        self.venueProxy = Client.Handle( uri ).GetProxy()


        #
        # Check that the venue has been added
        #
        
        print "\n------------------ All venues in server"
        addedVenue = None
        venueList = self.venueServerProxy.GetVenues()
        for v in venueList:
            print "\n name: "+v['name']+"\n "+v['description']
            if v.uri == uri:
                addedVenue = v

        print "\n------------------ Validate added venue"
        if addedVenue:
            ret = VenueCompare( addedVenue, venue )
            if ret[0]:
                print "venue corrupted on add: ", ret[1]

        #
        # Modify the venue
        #
        
        print "\n------------------ Modify The Venue"
        venue.name = "newName"
        venue.description = "newDescription"
        venue.streams = ()
        venue.encryptMedia = 0
        venue.encryptionKey = ""
        self.venueServerProxy.ModifyVenue( uri, venue )
        venueList = self.venueServerProxy.GetVenues()
        for v in venueList:
            if v.uri == uri:
                modifiedVenue = v
        ret = VenueCompare( venue, modifiedVenue )
        if ret[0]:
            print "venue corrupted on modify: ", ret[1]

        #
        # Other venue server tests
        # 

        dnName = "dnName"
        print "\n------------------ Add Administrator "+"dn: "+dnName
        self.venueServerProxy.AddAdministrator(dnName)
        adminList = self.venueServerProxy.GetAdministrators()
        if dnName not in adminList:
            PrintError( "AddAdministrator: added admin not in list")
     
        print "\n------------------ Remove the administrator"
        self.venueServerProxy.RemoveAdministrator(dnName)
        adminList = self.venueServerProxy.GetAdministrators()
        if dnName in adminList:
            PrintError( "RemoveAdministrator: removed admin still in list")

        setAddress = "225.224.224.224"
        print "\n------------------ Set base address: "+setAddress
        self.venueServerProxy.SetBaseAddress(setAddress)
        getAddress = self.venueServerProxy.GetBaseAddress()
        print "\n------------------ Get base address: "+getAddress
        if not setAddress == getAddress:
            PrintError( "SetBaseAddress/GetBaseAddress asymmetry")
       
        setMask = 20
        print "\n------------------ Set mask: "+str(setMask)
        self.venueServerProxy.SetAddressMask(setMask)
        getMask = self.venueServerProxy.GetAddressMask()
        print "\n------------------ Get mask: "+str(getMask)
        if not getMask == setMask:
            PrintError( "SetAddressMask/GetAddressMask asymmetry")
      

        setMethod = MulticastAddressAllocator.INTERVAL
        print "\n------------------ Set allocator = ", setMethod
        self.venueServerProxy.SetAddressAllocationMethod(setMethod)
        getMethod = self.venueServerProxy.GetAddressAllocationMethod()
        print "\n------------------ Get allocator = ", getMethod
        if not setMethod == getMethod:
            PrintError( "SetAddressAllocatorMethod/GetAddressAllocatorMethod asymmetry")


        setPath = "/homes/"
        print "\n------------------ SetStorageLocation: "+setPath
        self.venueServerProxy.SetStorageLocation(setPath)
        getPath = self.venueServerProxy.GetStorageLocation()
        print "\n------------------ GetStorageLocation: "+getPath
        if not setPath == getPath:
            PrintError( "SetStorageLocation/GetStorageLocation asymmetry")




        # 
        # Venue tests
        # 

        exit1 = ConnectionDescription("Exit1", "Exit1 description", "uri exit 1")
        exit2 = ConnectionDescription("Exit2", "Exit2 description", "uri exit 2")
        setConnectionList = [exit1, exit2]
        print "\n------------------ Set connections", str(len(setConnectionList))
        self.venueProxy.SetConnections(setConnectionList)
        getConnectionList = self.venueProxy.GetConnections()
        print "\n------------------ Get connections", str(len(getConnectionList))
        if not len( getConnectionList ) == len( setConnectionList ):
            PrintError( "SetConnections/GetConnections asymmetry")

     
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
        videoStreamDescription = StreamDescription( "", location, capability)  
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
        audioStreamDescription = StreamDescription( "", location, capability)  
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
                if not stream.location.host == videoStreamDescription.location.host:
                    PrintError( "video stream host mismatch" )
                if not stream.location.port == videoStreamDescription.location.port:
                    PrintError( "video stream port mismatch" )
                if not stream.location.ttl == videoStreamDescription.location.ttl:
                    PrintError( "video stream ttl mismatch" )
                                    
            elif(stream.capability.type == Capability.AUDIO):
                print "\n*** Static audio stream:"
                print 'host: ',stream.location.host
                print 'port: ',stream.location.port
                print 'time to live: ',stream.location.ttl
                if not stream.location.host == audioStreamDescription.location.host:
                    PrintError( "video stream host mismatch" )
                if not stream.location.port == audioStreamDescription.location.port:
                    PrintError( "video stream port mismatch" )
                if not stream.location.ttl == audioStreamDescription.location.ttl:
                    PrintError( "video stream ttl mismatch" )
               
        print  "\n------------------ Remove static streams"
        streamList = venue.GetStaticStreams()
        for stream in streamList:
            venue.RemoveStream(stream)
        print  "\n------------------ Get static streams"
        streamList = venue.GetStaticStreams()
        if len(streamList) > 0:
            PrintError( "Streams remain after removal" )

        encryptMedia = 1
        print "\n------------------ Set venue server encryption to 1"
        self.venueServerProxy.SetEncryptAllMedia(encryptMedia)
        value = self.venueServerProxy.GetEncryptAllMedia()
        print "\n------------------ Get venue server encryption "+str(value)
        if not value == encryptMedia:
            PrintError( "SetEncryptAllMedia/GetEncryptAllMedia asymmetry" )

        setEncryptionKey = "123456"
        print "\n------------------ Set venue encryption with key = ", setEncryptionKey
        self.venueProxy.SetEncryptMedia(1, setEncryptionKey)
        getEncryptionKey = self.venueProxy.GetEncryptMedia()
        print "\n------------------ Get venue encryption key = " + getEncryptionKey
        if not setEncryptionKey == getEncryptionKey:
            PrintError( "SetEncryptMedia/GetEncryptMedia asymmetry" )
            

        print "\n------------------ Remove the venue"
        self.venueServerProxy.RemoveVenue(uri)
        self.venueServerProxy.GetVenues()
        print "\n------------------ All venues in server"
        removedVenue = None
        venueList = self.venueServerProxy.GetVenues()
        for v in venueList:
            print "\n name: "+v.name+"\n "+v.description
            if v.uri == uri:
                removedVenue = v

        if removedVenue:
            PrintError( "RemoveVenue failed to remove venue" )
            
if __name__ == "__main__":       
    venueServerUrl = "https://localhost:8000/VenueServer"
    if len(sys.argv) > 1:
        venueServerUrl = sys.argv[1]
    VenueServerTest(venueServerUrl)
