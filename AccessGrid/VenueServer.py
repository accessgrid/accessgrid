#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
#
# Author:      Everyone
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.64 2003-04-09 20:31:04 olson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

# Standard stuff
import sys
import os
import os.path
import socket
import string
from threading import Thread, RLock
import traceback
import logging
import urlparse
import time
import ConfigParser
from AccessGrid.hosting.pyGlobus import Server

# AG Stuff
from AccessGrid.hosting import AccessControl
from AccessGrid.hosting.pyGlobus import ServiceBase
from AccessGrid.hosting.pyGlobus.Utilities import GetDefaultIdentityDN

from AccessGrid.Utilities import formatExceptionInfo, LoadConfig, SaveConfig
from AccessGrid.Utilities import GetHostname
from AccessGrid.GUID import GUID
from AccessGrid.Venue import Venue
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid.DataStore import GSIHTTPTransferServer
from AccessGrid.EventService import EventService
from AccessGrid.scheduler import Scheduler
from AccessGrid.TextService import TextService

from AccessGrid.Descriptions import ConnectionDescription, StreamDescription
from AccessGrid.Descriptions import DataDescription, VenueDescription
from AccessGrid.Descriptions import CreateVenueDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.Types import Capability

log = logging.getLogger("AG.VenueServer")

class VenueServerException(Exception):
    """
    A generic exception type to be raised by the Venue code.
    """
    pass

class NotAuthorized(Exception):
    pass

class InvalidVenueURL(Exception):
    pass

class VenueServer(ServiceBase.ServiceBase):
    """
    The Virtual Venue Server object is responsible for creating,
    destroying, and configuring Virtual Venue objects.

    The Virtual Venue Server object is:

    . adminstrators -- list of strings (each is a DN of a adminsitrative user)
    . defaultVenue -- VenueURL
    . hostingEnvironment -- AccessGrid.hosting.pyGlobus.Server
    . multicastAddressAllocator -- AccessGrid.MulticastAddressAllocator
    . hostname -- the hostname of the local machine
    . venues -- a list of Venues Objects that are being made available
    . dataStorageLocation -- string
    . eventPort -- the local port to run the EventService on.
    . textPort -- the local port to run the TextService on.
    . configFile -- string
    . dataTransferServer -- a DataStore Transfer Server for storing files.
    . eventService -- an Event Service so all venues can have event
    infrastructure.
    . textService -- a Text Service for all venues.
    . services -- a list of service descriptions, these are either network or
               application services that are available so any venue hosted
               by this venue server can add these to the services available
               from within that venue
    . houseKeeper -- Scheduler
    """

    configDefaults = {
            "VenueServer.eventPort" : 8002,
            "VenueServer.textPort" : 8004,
            "VenueServer.dataPort" : 8006,
            "VenueServer.encryptAllMedia" : 1,
            "VenueServer.houseKeeperFrequency" : 30,
            "VenueServer.persistenceFilename" : 'VenueServer.dat',
            "VenueServer.serverPrefix" : 'VenueServer',
            "VenueServer.venuePathPrefix" : 'Venues',
            "VenueServer.dataStorageLocation" : 'Data',
            "VenueServer.dataSize" : '10M'
            }

    defaultVenueDesc = VenueDescription("Venue Server Lobby", """ This is the lobby of the Venue Server, it has been created because there are no venues yet. Please configure your Venue Server! For more information see http://www.accessgrid.org/ and http://www.mcs.anl.gov/fl/research/accessgrid.""")

    def __init__(self, hostEnvironment = None, configFile=None):
        """
        The constructor creates a new Venue Server object, initializes
        that object, then registers signal handlers so the venue can cleanly
        shutdown in the event of catastrophic signals.
        """
        # Initialize our state
        self.administrators = ''
        self.administratorList = []
        self.defaultVenue = ''
        if None != hostEnvironment: 
            self.hostingEnvironment = hostEnvironment
            self.internalHostingEnvironment = 0 # False
        else:
            defaultPort = 8000
            self.hostingEnvironment = Server.Server(defaultPort)
            self.internalHostingEnvironment = 1 # True
        self.multicastAddressAllocator = MulticastAddressAllocator()
        self.hostname = GetHostname()
        self.venues = {}
        self.services = []
        self.configFile = configFile
        self.dataStorageLocation = None
        self.eventPort = 0
        self.textPort = 0
        
        # Figure out which configuration file to use for the
        # server configuration. If no configuration file was specified
        # look for a configuration file named VenueServer.cfg
        if self.configFile == None:
            classpath = string.split(str(self.__class__), '.')
            self.configFile = classpath[-1]+'.cfg'

        # Read in and process a configuration
        self.InitFromFile(LoadConfig(self.configFile, self.configDefaults))

        # If there are no administrators set then we set it to the
        # owner of the current running process
        if len(self.administrators) == 0:
            dnAdmin = GetDefaultIdentityDN()
            if dnAdmin:
                self.administratorList.append(dnAdmin)
        else:
            self.administratorList = string.split(self.administrators, ":")
            
        # Start Venue Server wide services
        log.info("HN: %s EP: %d TP: %d DP: %d" % ( self.hostname,
                                                    int(self.eventPort),
                                                    int(self.textPort),
                                                    int(self.dataPort) ) )

        self.dataTransferServer = GSIHTTPTransferServer(('',
                                                         int(self.dataPort)),
                                                        numThreads = 5,
                                                        sslCompat = 0)
        self.dataTransferServer.run()

        self.eventService = EventService((self.hostname, int(self.eventPort)))
        self.eventService.start()

        self.textService = TextService((self.hostname, int(self.textPort)))
        self.textService.start()

        # Try to open the persistent store for Venues. If we fail, we
        # open a temporary store, but it'll be empty.
        try:
            self.LoadPersistentVenues(self.persistenceFilename)
        except VenueServerException, ve:
            log.exception(ve)
            try:
                self.LoadPersistentVenues(self.persistenceFilename+'.bak')
            except VenueServerException, ve:
                log.exception(ve)
                self.venues = {}
                self.defaultVenues = ''

        #
        # Reinitialize the default venue
        #
        log.debug("CFG: Default Venue: %s", self.defaultVenue)
        
        if len(self.defaultVenue) != 0 and self.defaultVenue in self.venues.keys():
            log.debug("Setting default venue")
            self.SetDefaultVenue(self.MakeVenueURL(self.defaultVenue))
        else:
            log.debug("Creating default venue")
            self.AddVenue(self.defaultVenueDesc)

        # The houseKeeper is a task that is doing garbage collection and
        # other general housekeeping tasks for the Venue Server.
        self.houseKeeper = Scheduler()
        self.houseKeeper.AddTask(self.Checkpoint,
                                 int(self.houseKeeperFrequency), 0)
        self.houseKeeper.StartAllTasks()

    def LoadPersistentVenues(self, filename):
        """
        """
        cp = ConfigParser.ConfigParser()
        cp.read(filename)

        for sec in cp.sections():
            if cp.has_option(sec, "type"):
                name = cp.get(sec, 'name')
                description = cp.get(sec, 'description')
                administrators = string.split(cp.get(sec, 'administrators'),
                                              ':')
                v = Venue(self, name, description, administrators,
                          self.dataStorageLocation)
                v.encryptMedia = cp.getint(sec, 'encryptMedia')
                v.cleanupTime = cp.getint(sec, 'cleanupTime')
                v._ChangeUniqueId(sec)

                self.venues[self.IdFromURL(v.uri)] = v
                self.hostingEnvironment.BindService(v, self.PathFromURL(v.uri))
                
                cl = {}
                for c in string.split(cp.get(sec, 'connections'), ':'):
                    if len(c) != 0:
                        name = cp.get(c, 'name')
                        desc = cp.get(c, 'description')
                        uri = self.MakeVenueURL(self.IdFromURL(cp.get(c,
                                                                      'uri')))
                        cd = ConnectionDescription(name, desc, uri)
                        cl[cd.uri] = cd
                        
                v.SetConnections(cl)
                        
                for s in string.split(cp.get(sec, 'streams'), ':'):
                    if len(s) != 0:
                        name = cp.get(s, 'name')
                        desc = cp.get(s, 'description')
                        encryptionKey = cp.get(s, 'encryptionKey')
                        (addr, port, ttl) = string.split(cp.get(s, 'location'),
                                                         " ")
                        capability = cp.get(s, 'capability')
                        l = MulticastNetworkLocation(addr, int(port), int(ttl))
                        c = Capability(string.split(capability, ' '))
                        
                        uri = self.MakeVenueURL(self.IdFromURL(cp.get(s,
                                                                      'uri')))
                        sd = StreamDescription(name, desc, l, c)
                        v.AddStream(sd)

    def _authorize(self):
        """
        """
        sm = AccessControl.GetSecurityManager()
        if sm == None:
            return 1
        elif sm.GetSubject().GetName() in self.administratorList:
            return 1
        else:
            log.exception("Authorization failed for %s", sm.GetSubject().GetName())
            return 0

    def InitFromFile(self, config):
        """
        """
        self.config = config
        for k in config.keys():
            (section, option) = string.split(k, '.')
            setattr(self, option, config[k])

    def PathFromURL(self, URL):
        """
        """
        return urlparse.urlparse(URL)[2]

    def IdFromURL(self, URL):
        """
        """
        path = self.PathFromURL(URL)
        return path.split('/')[-1]
    
    def wsAddVenue(self, venueDescStruct):
        """
        Inteface call for Adding a venue.
        """
        
        if not self._authorize():
            log.exception("Unauthorized attempt to Add Venue.")
            raise NotAuthorized
        else:
            try:
                venueDesc = CreateVenueDescription(venueDescStruct)
                venueDesc.administrators.append(GetDefaultIdentityDN())
                venueUri = self.AddVenue(venueDesc)
                return venueUri
            except:
                log.exception("Exception in AddVenue!")
                raise VenueServerException("Couldn't Add Venue.")


    wsAddVenue.soap_export_as = "AddVenue"
    
    def wsModifyVenue(self, URL, venueDescStruct):
        if not self._authorize():   
            raise NotAuthorized

        if URL == None:
            raise InvalidVenueURL
        else:
            vd = CreateVenueDescription(venueDescStruct)
        
            self.ModifyVenue(URL, vd)
        
    wsModifyVenue.soap_export_as = "ModifyVenue"
    
    def MakeVenueURL(self, uniqueId):
        """
        Helper method to make a venue URI from a uniqueId.
        """
        uri = string.join([self.hostingEnvironment.get_url_base(),
                           self.venuePathPrefix, uniqueId], '/')
        return uri

    def AddVenue(self, venueDesc):
        """
        The AddVenue method takes a venue description and creates a new
        Venue Object, complete with a event service, then makes it
        available from this Venue Server.
        """
        # Create a new Venue object pass it the server
        venue = Venue(self, venueDesc.name, venueDesc.description,
                      venueDesc.administrators, self.dataStorageLocation)
        
        # Add Connections if there are any
        venue.SetConnections(venueDesc.connections)
        
        # Add Streams if there are any
        for sd in venueDesc.streams:
            venue.streamList.AddStream(sd)
            
        venuePath = self.PathFromURL(venue.uri)
            
        # Add the venue to the list of venues
        self.venues[self.IdFromURL(venue.uri)] = venue
        
        # We have to register this venue as a new service.
        if(self.hostingEnvironment != None):
            self.hostingEnvironment.BindService(venue, venuePath)
            
        # If this is the first venue, set it as the default venue
        if(len(self.venues) == 1):
            self.SetDefaultVenue(venue.uri)
                
        # return the URL to the new venue
        return venue.uri

    def ModifyVenue(self, URL, venueDesc):   
        """   
        ModifyVenue updates a Venue Description.   
        """
        id = self.IdFromURL(URL)   
        if(venueDesc.uri == URL):
            self.venues[id].name = venueDesc.name
            self.venues[id].description = venueDesc.description
            self.venues[id].uri = venueDesc.uri
            self.venues[id].administrators = venueDesc.administrators
            self.venues[id].encryptMedia = venueDesc.encryptMedia
            if self.venues[id].encryptMedia:
                self.venues[id].encryptionKey = venueDesc.encryptionKey

            self.venues[id].SetConnections(venueDesc.connections)
            
            for sd in venueDesc.streams:
                self.venues[id].AddStream(sd)
        
    def RemoveVenue(self, URL):
        """
        RemoveVenue removes a venue from the VenueServer.
        """
        if not self._authorize():
            raise NotAuthorized

        id = self.IdFromURL(URL)
        
        venue = self.venues[id]
        del self.venues[id]
        
    RemoveVenue.soap_export_as = "RemoveVenue"

    def AddAdministrator(self, string):
        """
        AddAdministrator adds an administrator to the list of administrators
        for this VenueServer.
        """
        if not self._authorize():
            raise NotAuthorized

        if string not in self.administratorList:
            if None == self.administratorList[0]:
                self.administratorList[0] = string
            else:
                self.administratorList.append(string)

            self.config["VenueServer.administrators"] = ":".join(self.administratorList)
            return string
        else:
            raise VenueServerException("Administrator already present.")
        
    AddAdministrator.soap_export_as = "AddAdministrator"

    def RemoveAdministrator(self, string):
        """
        RemoveAdministrator removes an administrator from the list of
        administrators for this VenueServer.
        """
        if not self._authorize():
            raise NotAuthorized

        if string in self.administratorList:
            self.administratorList.remove(string)
            self.config["VenueServer.administrators"] = ":".join(self.administratorList)
            return string
        else:
            raise VenueServerException("Administrator not found.")
        
    RemoveAdministrator.soap_export_as = "RemoveAdministrator"

    def GetAdministrators(self):
        """
        GetAdministrators returns a list of adminisitrators for this
        VenueServer.
        """
        return self.administratorList

    GetAdministrators.soap_export_as = "GetAdministrators"

    def RegisterServer(self, URL):
        """
        This method should register the server with the venues
        registry at the URL passed in. This is by default a
        registration page at Argonne for now.
        """
        if not self._authorize():
            raise NotAuthorized
        # registryService = SOAP.SOAPProxy(URL)
        # registryService.Register(#data)

    RegisterServer.soap_export_as = "RegisterServer"

    def GetVenues(self):
        """
        GetVenues returns a list of Venues Descriptions for the venues
        hosted by this VenueServer.
        """
        try:
            venueDescList = map(lambda venue: venue.AsVenueDescription(),
                                        self.venues.values() )

            for v in venueDescList:
                v.connections = v.connections.values()

            return venueDescList
        except:
            log.exception("Exception in GetVenues!")
            raise VenueServerException("GetVenues Failed!")

    GetVenues.soap_export_as = "GetVenues"

    def GetDefaultVenue(self):
        """
        GetDefaultVenue returns the URL to the default Venue on the
        VenueServer.
        """
        return self.MakeVenueURL(self.defaultVenue)

    GetDefaultVenue.soap_export_as = "GetDefaultVenue"

    def SetDefaultVenue(self,  venueURL):
        """
        SetDefaultVenue sets which Venue is the default venue for the
        VenueServer.
        """
        if not self._authorize():
            raise NotAuthorized

        defaultPath = "/Venues/default"

        path = self.PathFromURL(venueURL)
        id = self.IdFromURL(venueURL)
        
        defaultVenue = self.hostingEnvironment.CreateServiceObject(defaultPath)

        self.defaultVenue = id

        self.config["VenueServer.defaultVenue"] = id

        self.venues[id]._bind_to_service(defaultVenue)

    SetDefaultVenue.soap_export_as = "SetDefaultVenue"

    def SetStorageLocation(self,  dataStorageLocation):
        """
        Set the path for data storage
        """
        if not self._authorize():
            raise NotAuthorized
        
        self.dataStorageLocation = dataStorageLocation
        self.config["VenueServer.dataStorageLocation"] = dataStorageLocation

    SetStorageLocation.soap_export_as = "SetStorageLocation"


    def GetStorageLocation(self):
        """
        Get the path for data storage
        """
        return self.dataStorageLocation

    GetStorageLocation.soap_export_as = "GetStorageLocation"


    def SetAddressAllocationMethod(self,  addressAllocationMethod):
        """
        Set the method used for multicast address allocation:
            either RANDOM or INTERVAL (defined in MulticastAddressAllocator)
        """
        if not self._authorize():
            raise NotAuthorized
        
        self.multicastAddressAllocator.SetAddressAllocationMethod( addressAllocationMethod )

    SetAddressAllocationMethod.soap_export_as = "SetAddressAllocationMethod"

    def GetAddressAllocationMethod(self):
        """
        Get the method used for multicast address allocation:
            either RANDOM or INTERVAL (defined in MulticastAddressAllocator)
        """
        return self.multicastAddressAllocator.GetAddressAllocationMethod()

    GetAddressAllocationMethod.soap_export_as = "GetAddressAllocationMethod"

    def SetEncryptAllMedia(self, value):
        """
        Turn on or off server wide default for venue media encryption.
        """
        if not self._authorize():
            raise NotAuthorized
        
        self.encryptAllMedia = int(value)
        return self.encryptAllMedia

    SetEncryptAllMedia.soap_export_as = "SetEncryptAllMedia"

    def GetEncryptAllMedia(self):
        """
        Get the server wide default for venue media encryption.
        """
        return int(self.encryptAllMedia)

    GetEncryptAllMedia.soap_export_as = "GetEncryptAllMedia"

    def SetBaseAddress(self, address):
        """
        Set base address used when allocating multicast addresses in
        an interval
        """
        if not self._authorize():
            raise NotAuthorized
        
        self.multicastAddressAllocator.SetBaseAddress( address )

    SetBaseAddress.soap_export_as = "SetBaseAddress"

    def GetBaseAddress(self):
        """
        Get base address used when allocating multicast addresses in
        an interval
        """
        return self.multicastAddressAllocator.GetBaseAddress( )

    GetBaseAddress.soap_export_as = "GetBaseAddress"

    def SetAddressMask(self,  mask):
        """
        Set address mask used when allocating multicast addresses in
        an interval
        """
        if not self._authorize():
            raise NotAuthorized
        
        self.multicastAddressAllocator.SetAddressMask( mask )

    SetAddressMask.soap_export_as = "SetAddressMask"

    def GetAddressMask(self):
        """
        Get address mask used when allocating multicast addresses in
        an interval
        """
        return self.multicastAddressAllocator.GetAddressMask( )

    GetAddressMask.soap_export_as = "GetAddressMask"

    def Shutdown(self, secondsFromNow):
        """
        Shutdown shuts down the server.
        """
        log.info("Starting Shutdown!")

        for v in self.venues.values():
            v.Shutdown()
            
        self.houseKeeper.StopAllTasks()

        if not self._authorize():
            raise NotAuthorized

        log.info("Shutdown -> Checkpointing...")
        self.Checkpoint()
        log.info("                            done")
        
        # This blocks anymore checkpoints from happening
        log.info("Shutting down services...")
        log.info("                         text")
        self.textService.Stop()
        log.info("                         event")
        self.eventService.Stop()
        log.info("                         data")
        self.dataTransferServer.stop()
        if self.internalHostingEnvironment:
            log.info("                         internally created hostingEnvironment")
            self.hostingEnvironment.Stop()
            del self.hostingEnvironment
        log.info("                              done.")

        log.info("Shutdown Complete.")
        
    Shutdown.soap_export_as = "Shutdown"

    def Checkpoint(self):
        """
        Checkpoint stores the current state of the running VenueServer to
        non-volatile storage. In the event of catastrophic failure, the
        non-volatile storage can be used to restart the VenueServer.

        The fequency at which Checkpointing is done will bound the amount of
        state that is lost (the longer the time between checkpoints, the more
        that can be lost).
        """
        try:
            # Before we backup we copy the previous backup to a safe place
            if os.path.isfile(self.persistenceFilename):
                nfn = self.persistenceFilename + '.bak'
                if os.path.isfile(nfn):
                    try:
                        os.remove(nfn)
                    except OSError, e:
                        log.exception("Couldn't remove backup file.")
                try:
                    os.rename(self.persistenceFilename, nfn)
                except OSError, e:
                    log.exception("Couldn't rename backup file.")
                    raise e

            # Open the persistent store
            store = file(self.persistenceFilename, "w")
            
            for venuePath in self.venues.keys():
                # Change out the uri for storage, we store the path
                venueURI = self.venues[venuePath].uri
                self.venues[venuePath].uri = venuePath

                # Store the venue.
                store.write(self.venues[venuePath].AsINIBlock())
                
                # Change the URI back
                self.venues[venuePath].uri = venueURI

            # Close the persistent store
            store.close()

        except:
            log.exception("Exception Checkpointing!")
            raise VenueServerException("Checkpoint Failed!")

        log.info("Checkpointing completed at %s.", time.asctime())

        # Finally we save the current config
        SaveConfig(self.configFile, self.config)

