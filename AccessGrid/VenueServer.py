#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.7 2003-01-14 19:39:25 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

# Standard stuff
import sys
import ConfigParser
import socket
import string
from threading import Thread
import shelve

# AG Stuff
from AccessGrid.hosting.pyGlobus import ServiceBase
from AccessGrid import Venue
import CoherenceService
import GUID
import NetworkLocation
import MulticastAddressAllocator
import DataStore
import scheduler
#from ReadWriteLock import ReadWriteLock
from AccessGrid.Descriptions import VenueDescription

class VenueServer(ServiceBase.ServiceBase):
    """
    
    """
    serverHost = ''
    serverURL = ''
    venueBaseURL = ''
    administrators = []
    
    configFile = ''
    config = {}
    configDefaults = {
        "VenueServer.houseKeeperFrequency" : 900,
        "VenueServer.persistenceData" : 'VenueData',
        "CoherenceService.coherencePortBase" : 9000,
        "DataStorage.store" : 'Data/',
        "DataStorage.port" : 8892
        }
    hostingEnvironment = None
    defaultVenue = None
    multicastAddressAllocator = None
    dataStorage = None
    houseKeeper = None
    venues = {}
    services = []
    
    def __init__(self, hostEnvironment = None, configFile=None):
        """ """
        # Figure out which configuration file to use for the
        # server configuration. If no configuration file was specified
        # look for a configuration file named VenueServer.cfg
        # VenueServer is the value of self.__class__
        classpath = string.split(str(self.__class__), '.')
        if configFile == None: 
            self.configFile = classpath[-1]+'.cfg'
        else:
            self.configFile = configFile
        
        # Instantiate a new config parser
        self.config = self.LoadConfig(self.configFile,
                          self.configDefaults)

        self.hostingEnvironment = hostEnvironment
        self.multicastAddressAllocator = MulticastAddressAllocator.MulticastAddressAllocator()
        self.dataStorage = None
        self.store = shelve.open(self.config['VenueServer.persistenceData'], 'c')
        #self.storeLock = ReadWriteLock()
        
        for vURL in self.store.keys():
            print "Loading Venue: %s" % vURL
            #self.storeLock.acquire_read()
            self.venues[vURL] = self.store[vURL]
            #self.storeLock.release_read()
            
        houseKeeper = scheduler.Scheduler()
#        houseKeeper.AddTask(self.Checkpoint, self.config['VenueServer.houseKeeperFrequency'], 0)
          
    def LoadConfig(self, file, config={}):
        """
        Returns a dictionary with keys of the form <section>.<option>
        and the corresponding values.
        This is from the python cookbook credit: Dirk Holtwick.
        """
        config = config.copy()
        self.cp = ConfigParser.ConfigParser()
        self.cp.read(file)
        for sec in self.cp.sections():
            name = string.lower(sec)
            for opt in self.cp.options(sec):
                config[name + "."
                       + string.lower(opt)] = string.strip(
                    self.cp.get(sec, opt))
        return config
    
    def AddVenue(self, connectionInfo, venueDescription):
        """ """        

        try:
            # instantiate a local venueDecription from the input, since it probably
            # came from a SOAP client and we don't want to store it
            venueDescription = VenueDescription( venueDescription.name, venueDescription.description, 
                                                 venueDescription.icon, venueDescription.extendedDescription )

            # Get the next port for the coherenceService for the new venue
            coherencePort = self.config['CoherenceService.coherencePortBase'] + len(self.venues.keys())

            # Build the new coherenceService
            coherenceService = CoherenceService.CoherenceService(NetworkLocation.UnicastNetworkLocation(socket.getfqdn(), coherencePort))
                            
            venueID = GUID.GUID()
            venuePath = "Venues/%s" % venueID
            venueURL = self.hostingEnvironment.get_url_base() + "/" + venuePath
            venueDescription.uri = venueURL

            # Create a new Venue object, pass it the coherenceService, 
            #   the server's Multicast Address Allocator, and the server's
            #   Data Storage object
            venue = Venue.Venue(self, venueID, venueDescription,
                        connectionInfo.get_remote_name(),
                        coherenceService,
                        self.multicastAddressAllocator,
                        self.dataStorage)
                
            # Somehow we have to register this venue as a new service
            # on the server.  This gets tricky, since we're not assuming
            # the VenueServer knows about the SOAP server.
            if(self.hostingEnvironment != None):
                venueService = self.hostingEnvironment.create_service_object(pathId = venuePath)
            venue._bind_to_service(venueService)
            
            print "Created Venue object"

            print "* * VENUE URI = ", venue.get_handle()

            # Update the venue description with the service uri
            venueDesc = venue.GetDescription( connectionInfo )
            venueDesc.uri = venue.get_handle()
            venue.SetDescription( connectionInfo, venueDesc )

            # If this is the first venue, set it as the default venue
            if(len(self.venues) == 0):
                self.SetDefaultVenue(connectionInfo, venueURL)
                            
            # Add the venue to the list of venues
            self.venues[venueURL] = venue
        
        except:
            print "Exception in AddVenue ", sys.exc_type, sys.exc_value
                            
        # return the URL to the new venue
        return venueURL
    
    AddVenue.pass_connection_info = 1
    AddVenue.soap_export_as = "AddVenue"
    
    def ModifyVenue(self, connectionInfo, URL, venueDescription):
        """ """
        # This should check
        # 1. That you are allowed to do this
        # 2. That you are setting the right venue description
        if(venueDescription.uri == URL):
            self.venues[URL] = venueDescription
                
    ModifyVenue.pass_connection_info = 1
    ModifyVenue.soap_export_as = "ModifyVenue"
    
    def RemoveVenue(self, connectionInfo, URL):
        """ """
        venue = self.venues[URL]
        # remove from server
        del self.venues[URL]
        
    RemoveVenue.pass_connection_info = 1
    RemoveVenue.soap_export_as = "RemoveVenue"
    
    def AddAdministrator(self, connectionInfo, string):
        """ """
        self.administrators.append(string)
        
    AddAdministrator.pass_connection_info = 1
    AddAdministrator.soap_export_as = "AddAdministrator"
    
    def RemoveAdminstrator(self, connectionInfo, string):
        """ """
        self.administrators.remove(string)
        
    RemoveAdminstrator.pass_connection_info = 1
    RemoveAdminstrator.soap_export_as = "RemoveAdminstrator"
    
    def GetAdminstrators(self, connectionInfo):
        """ """
        return self.administrators
    GetAdminstrators.pass_connection_info = 1
    GetAdminstrators.soap_export_as = "GetAdminstrators"
    
    def AddService(self, connectionInfo, serviceDescription):
        """ """
        self.services[serviceDescription.uri] = serviceDescription
        
    AddService.pass_connection_info = 1
    AddService.soap_export_as = "AddService"
    
    def RemoveService(self, connectionInfo, URL, serviceDescription):
        """ """
        self.services.remove(serviceDescription)
        
    RemoveService.pass_connection_info = 1
    RemoveService.soap_export_as = "RemoveService"
    
    def ModifyService(self, connectionInfo, URL, serviceDescription):
        """ """
        if URL == serviceDescription.uri:
            self.services[URL] = serviceDescription
        
    ModifyService.pass_connection_info = 1
    ModifyService.soap_export_as = "ModifyService"
    
    def RegisterServer(self, connectionInfo, URL):
        """ 
        This method should register the server with the venues
        registry at the URL passed in. This is by default a
        registration page at Argonne for now.
        """
        # registryService = SOAP.SOAPProxy(URL)
        # registryService.Register(#data)
        
    RegisterServer.pass_connection_info = 1
    RegisterServer.soap_export_as = "RegisterServer"
    
    def GetVenues(self, connectionInfo):
        """ """
        try:
            venueDescriptionList = map( lambda venue: venue.GetDescription( connectionInfo ), self.venues.values() )
            for venue in venueDescriptionList:
                print "  ---- venue ", venue.name, venue.description, venue.uri
        except:
            print "Exception in GetVenues ", sys.exc_type, sys.exc_value
        return venueDescriptionList
    
    GetVenues.pass_connection_info = 1
    GetVenues.soap_export_as = "GetVenues"
    
    def GetDefaultVenue(self, connectionInfo):
        """ """
        return self.defaultVenue
    
    GetDefaultVenue.pass_connection_info = 1
    GetDefaultVenue.soap_export_as = "GetDefaultVenue"
    
    def SetDefaultVenue(self, connectionInfo, venueURI):
        """ """
        self.defaultVenue = venueURI
        self.config["VenueServer.defaultVenue"] = venueURI
        self.cp.set("VenueServer", "defaultVenue", str(venueURI))
        
    SetDefaultVenue.pass_connection_info = 1
    SetDefaultVenue.soap_export_as = "SetDefaultVenue"
    
    def SetCoherencePortBase(self, connectionInfo, portBase):
        """ """
        self.portBase = coherencePortBase
        
    SetCoherencePortBase.pass_connection_info = 1
    SetCoherencePortBase.soap_export_as = "SetCoherencePortBase"
    
    def GetCoherencePortBase(self, connectionInfo):
        """ """
        return self.coherencePortBase
    
    GetCoherencePortBase.pass_connection_info = 1
    GetCoherencePortBase.soap_export_as = "GetCoherencePortBase"
    
    def Shutdown(self, connectionInfo, secondsFromNow):
        """ """
        self.cp.write(file(self.configFile, 'w'))
#        self.store.close()
#        exit(0)
        
    Shutdown.pass_connection_info = 1
    Shutdown.soap_export_as = "Shutdown"
    
    def Checkpoint(self):
        """ """
#         for vURL in self.venues.keys():
#             print "Shelving Venue: %s" % vURL
#             self.storeLock.acquire_write()
#             self.store[vURL] = self.venues[vURL]
#             self.storeLock.release_write()

        self.store.close()
        self.store = shelve.open(self.config['VenueServer.persistenceData'], 'c')
        print "Writing config %s" % self.configFile
        self.cp.write(file(self.configFile, 'w+'))
        print "Wrote config"
    
    Checkpoint.soap_export_as = "Checkpoint"

    def Ping( self ):
        return 1
    Ping.soap_export_as = "Ping"
    Ping.pass_connection_info = 0


        
if __name__ == "__main__":
    from AccessGrid.hosting.pyGlobus import Server, ServiceBase
    from AccessGrid.VenueServer import VenueServer
    
    # Explicitly binding the service to a path

    port = 0
    if len(sys.argv) > 1:
       port = int(sys.argv[1])
    hostingEnvironment = Server.Server(port)
    venueServer = VenueServer(hostingEnvironment)
    serviceObject = hostingEnvironment.create_service_object(pathId = 'VenueServer')
    venueServer._bind_to_service(serviceObject)
    
    # or
    # venueServerService = hostingEnvironment.create_service(VenueServer)

    print "Service running at: %s" % venueServer.get_handle()

    hostingEnvironment.run()
