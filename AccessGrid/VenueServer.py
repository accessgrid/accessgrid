#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.3 2002-12-18 11:54:57 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

# Standard stuff
import ConfigParser
import socket
import string
from threading import Thread
import shelve

# AG Stuff
from AccessGrid.hosting.pyGlobus import ServiceBase
import CoherenceService
import NetworkLocation
import MulticastAddressAllocator
import DataStore
import Venue
import scheduler

class VenueServer(ServiceBase.ServiceBase):
    """
    
    """
    serverHost = ''
    serverURL = ''
    venueBaseURL = ''
    administrators = []
    
    configFile = ''
    config = {
        "VenueServer.houseKeeperFrequency" : 900,
        "VenueServer.persistenceData" : 'VenueData',
        "CoherenceService.coherencePortBase" : 9000,
        "DataStorage.store" : 'Data/',
        "DataStorage.port" : 8892
        }  
    serverInstance = None
    defaultVenue = None
    multicastAddressAllocator = None
    dataStorage = None
    houseKeeper = None
    venues = {}
    services = []
    
    def __init__(self, configFile=''):
        """ """
        # Figure out which configuration file to use for the
        # server configuration. If no configuration file was specified
        # look for a configuration file named VenueServer.cfg
        # VenueServer is the value of self.__class__
        classpath = string.split(str(self.__class__), '.')
        if configFile == '': 
            self.configFile = classpath[0]+'.cfg'
        else:
            self.configFile = configFile
        
        # Instantiate a new config parser
        self.LoadConfig(configFile, self.config)

        self.multicastAddressAllocator = MulticastAddressAllocator.MulticastAddressAllocator()
        self.dataStorage = None
        self.store = shelve.open(self.config['VenueServer.persistenceData'], 'c')
        for k in self.store.keys():
            venue = self.store[k]
            self.venues[venue.description.uri] = venue
        houseKeeper = Scheduler()
        houseKeeper.addTask(self.Checkpoint)
          
    def LoadConfig(self, file, config={}):
        """
        Returns a dictionary with keys of the form <section>.<option> and 
        the corresponding values.
        This is from the python cookbook credit: Dirk Holtwick.
        """
        config = config.copy()
        cp = ConfigParser.ConfigParser()
        cp.read(file)
        for sec in cp.sections():
            name = string.lower(sec)
            for opt in cp.options(sec):
                config[name + "." + string.lower(opt)] = string.strip(
                    cp.get(sec, opt))
        return config
    
    def AddVenue(self, connectionInfo, venueDescription):
        """ """
        
        print "Add Venue Called."
        
        # Get the next port for the coherenceService for the new venue
        self.coherencePortBase = self.coherencePortBase + 1
        
        # Build the new coherenceService
        coherenceService = CoherenceService.CoherenceService(NetworkLocation.UnicastNetworkLocation(self.serverHost, self.coherencePortBase))
                    
        # Create a new Venue object, pass it the coherenceService, 
        #   the server's Multicast Address Allocator, and the server's
        #   Data Storage object
        venue = Venue.Venue(self, venueID, venueDescription, coherenceService,
                      self.multicastAddressAllocator, self.dataStorage)
            
        # Somehow we have to register this venue as a new service on the 
        #  server.  This gets tricky, since we're not assuming the VenueServer
        #  knows about the SOAP server.
        print "Setting the new venue to handle calls"
        if(self.serverInstance != None):
            venueService = self.serverInstance.create_service(Venue)
        venueURI = venueService.get_handle()
        
        # If this is the first venue, set it as the default venue
        if(len(self.venues) == 0):
            self.SetDefaultVenue(venueURI)
                
        # Add the venue to the list of venues
        self.venues[venueURI] = venue
                            
        # return the URL to the new venue
        # return venue.GetDescription().GetGetURL()
        return venueURI
    
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
        This method should register the server with the venues registry at the
        URL passed in. This is by default a registration page at Argonne for 
        now.
        """
        # registryService = SOAP.SOAPProxy(URL)
        # registryService.Register(#data)
        
    RegisterServer.pass_connection_info = 1
    RegisterServer.soap_export_as = "RegisterServer"
    
    def GetVenues(self, connectionInfo):
        """ """
        return self.venues.keys()
    
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
        self.config.set('VenueServer', 'defaultVenue', venueURI)
        
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
        self.config.write(self.configFile)
        self.store.close()
        
    Shutdown.pass_connection_info = 1
    Shutdown.soap_export_as = "Shutdown"
    
    def Checkpoint(self):
        """ """
        for venueURI in self.venues.keys():
            self.store[venueURI] = self.venues[venueURI]
        self.store.close()
        self.store = shelve.open(self.config['VenueServer.persistenceData'])
        
if __name__ == "__main__":
    from AccessGrid.hosting.pyGlobus import Server, ServiceBase
    from AccessGrid.VenueServer import VenueServer
    import ConfigParser

    hostingEnvironment = Server.Server(8000)
    venueServerService = hostingEnvironment.create_service(VenueServer)

    print "Service running at: %s" % venueServerService.get_handle()

    hostingEnvironment.run()
