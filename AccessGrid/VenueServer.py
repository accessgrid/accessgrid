#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
#
# Author:      Everyone
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.43 2003-02-27 20:08:17 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

# Standard stuff
import sys
import os
import os.path
import socket
import string
from threading import Thread
import shelve
import signal
import traceback
import logging
import urlparse

# AG Stuff
from AccessGrid.hosting import AccessControl
from AccessGrid.hosting.pyGlobus import ServiceBase
from AccessGrid.hosting.pyGlobus.Utilities import GetDefaultIdentityDN

from AccessGrid.Utilities import formatExceptionInfo, LoadConfig, SaveConfig
from AccessGrid.Utilities import GetHostname
from AccessGrid.GUID import GUID
from AccessGrid.Descriptions import VenueDescription
from AccessGrid.Venue import Venue
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid.DataStore import GSIHTTPTransferServer
from AccessGrid.EventService import EventService
from AccessGrid.scheduler import Scheduler
from AccessGrid.TextService import TextService

log = logging.getLogger("AG.VenueServer")

class VenueServerException(Exception):
    """
    A generic exception type to be raised by the Venue code.
    """
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

    defaultVenueDescription = VenueDescription("Venue Server Lobby",
            """This is the lobby of the Venue Server, it has been created because there are no venues yet. Please configure your Venue Server! For more information see http://www.accessgrid.org/ and http://www.mcs.anl.gov/fl/research/accessgrid.""", "", None)

    def __init__(self, hostEnvironment = None, configFile=None):
        """
        The constructor creates a new Venue Server object, initializes
        that object, then registers signal handlers so the venue can cleanly
        shutdown in the event of catastrophic signals.
        """
        # Initialize our state
        # We need to get the first administrator from somewhere
        self.administrators = [GetDefaultIdentityDN()]
        self.defaultVenue = ''
        self.hostingEnvironment = hostEnvironment
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

        # Start Venue Server wide services
        log.info("HN: %s EP: %d TP: %d DP: %d" % ( self.hostname,
                                                    int(self.eventPort),
                                                    int(self.textPort),
                                                    int(self.dataPort) ) )

        self.dataTransferServer = GSIHTTPTransferServer(('', int(self.dataPort)))
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
        if len(self.defaultVenue) != 0 and self.defaultVenue in self.venues:
            self.SetDefaultVenue(self.defaultVenue)
        else:
            self.AddVenue(self.defaultVenueDescription)

        # The houseKeeper is a task that is doing garbage collection and
        # other general housekeeping tasks for the Venue Server.
        # The first task we register with the houseKeeper is a periodic
        # checkpoint, this tries to ensure that the persistent store is
        # kept up to date.
        self.houseKeeper = Scheduler()
        self.houseKeeper.AddTask(self.Checkpoint,
                                 int(self.houseKeeperFrequency), 0)
        self.houseKeeper.StartAllTasks()

    def LoadPersistentVenues(self, filename):
        """
        This method just encapsulates persistent venue loading.
        """
        try:
            # Open the persistent store
            store = shelve.open(filename)

            # Load Venues
            for vURL in store.keys():
                log.debug("Loading Venue: %s", vURL)

                # Rebuild the venue
                self.venues[vURL] = store[vURL]

                # Start the venue
                self.venues[vURL].Start(self.multicastAddressAllocator,
                                        self.dataTransferServer, self.eventService,
                                        self.textService)
                
                # Build the Venue URI
                venuePath = urlparse.urlparse(vURL)[2]

                # Somehow we have to register this venue as a new service
                # on the server.  This gets tricky, since we're not assuming
                # the VenueServer knows about the SOAP server.
                if(self.hostingEnvironment != None):
                    venueService = self.hostingEnvironment.create_service_object(pathId = venuePath)
                    self.venues[vURL]._bind_to_service(venueService)
                    
            # When we're done close the persistent store
            store.close()
        except:
            log.exception("Failed to load persistent venues")
            raise VenueServerException("Failed to load persistent venues.")

    def _authorize(self):
        """
        """
        sm = AccessControl.GetSecurityManager()
        if sm == None:
            return 1
        elif sm.GetSubject().GetName() in self.administrators:
            return 1
        else:
            return 0
    
    def InitFromFile(self, config):
        """
        """
        self.config = config
        for k in config.keys():
            (section, option) = string.split(k, '.')
            setattr(self, option, config[k])

    def MakeVenueURI(self, uniqueId):
        """
        Helper method to make a venue URI from a uniqueId.
        """
        uri = string.join([self.hostingEnvironment.get_url_base(),
                           self.venuePathPrefix, uniqueId], '/')
        return uri

    def AddVenue(self, venueDescription):
        """
        The AddVenue method takes a venue description and creates a new
        Venue Object, complete with a event service, then makes it
        available from this Venue Server.
        """

        if not self._authorize():
            log.exception("Unauthorized attempt to Add Venue.")
            raise VenueServerException("You are not authorized to perform this action.")
        try:
            # instantiate a local venueDecription from the input,
            # since it probably came from a SOAP client and we don't
            # want to store it
            venueDescription = VenueDescription( venueDescription.name,
                                                 venueDescription.description,
                                                 venueDescription.icon,
                                         venueDescription.extendedDescription )

            venueId = str(GUID())
            venueDescription.uri = self.MakeVenueURI(venueId)

            #
            # Create the directory to hold the venue's data.
            #

            if self.dataStorageLocation is None or not os.path.exists(self.dataStorageLocation):
                log.debug("Creating venue: Data storage location %s not valid",
                          self.dataStorageLocation)
                venueStoragePath = None
            else:
                venueStoragePath = os.path.join(self.dataStorageLocation,
                                                venueId)
                try:
                    os.mkdir(venueStoragePath)
                except OSError, e:
                    log.exception("Could not create venueStoragePath: ", e)
                    venueStoragePath = None


            # Create a new Venue object pass it the server's Multicast Address
            # Allocator, and the server's Data Storage object

            venue = Venue(venueId, venueDescription,
                          GetDefaultIdentityDN(), venueStoragePath)

            venue.Start(self.multicastAddressAllocator,
                        self.dataTransferServer, self.eventService,
                        self.textService)

#            venue.SetEncryptMedia(self.encryptAllMedia)

            venuePath = urlparse.urlparse(venueDescription.uri)[2]
            venuePath = venuePath[1:]

            # Somehow we have to register this venue as a new service
            # on The server.  This gets tricky, since we're not assuming
            # the VenueServer knows about the SOAP server.
            if(self.hostingEnvironment != None):
                venueService = self.hostingEnvironment.create_service_object(pathId = venuePath)
                venue._bind_to_service(venueService)

            # Add the venue to the list of venues
            self.venues[venueDescription.uri] = venue

            # If this is the first venue, set it as the default venue
            if(len(self.venues) == 1):
                self.SetDefaultVenue(venueDescription.uri)

            # return the URL to the new venue
            return venueDescription.uri

        except:
            log.exception("Exception in AddVenue!")
            raise VenueServerException("Couldn't Add Venue.")

    AddVenue.soap_export_as = "AddVenue"

    def ModifyVenue(self, URL, venueDescription):
        """
        ModifyVenue updates a Venue Description.
        """
        if not self._authorize():
            raise VenueServerException("You are not authorized to perform this action.")

        # This should check
        # 1. That you are allowed to do this
        # 2. That you are setting the right venue description
        if(venueDescription.uri == URL):
            self.venues[URL].description = venueDescription

    ModifyVenue.soap_export_as = "ModifyVenue"

    def RemoveVenue(self, URL):
        """
        RemoveVenue removes a venue from the VenueServer.
        """
        if not self._authorize():
            raise VenueServerException("You are not authorized to perform this action.")

        venue = self.venues[URL]
        del self.venues[URL]

    RemoveVenue.soap_export_as = "RemoveVenue"

    def AddAdministrator(self, string):
        """
        AddAdminstrator adds an administrator to the list of administrators
        for this VenueServer.
        """
        if not self._authorize():
            raise VenueServerException("You are not authorized to perform this action.")

        self.administrators.append(string)

    AddAdministrator.soap_export_as = "AddAdministrator"

    def RemoveAdministrator(self, string):
        """
        RemoveAdministrator removes an administrator from the list of
        administrators for this VenueServer.
        """
        if not self._authorize():
            raise VenueServerException("You are not authorized to perform this action.")

        self.administrators.remove(string)

    RemoveAdministrator.soap_export_as = "RemoveAdministrator"

    def GetAdministrators(self):
        """
        GetAdministrators returns a list of adminsitrators for this
        VenueServer.
        """
        return self.administrators

    GetAdministrators.soap_export_as = "GetAdministrators"

    def AddService(self, serviceDescription):
        """
        AddService adds a service description to the list of service
        descriptions that are available to the Virtual Venues hosted by
        this VenueServer.
        """
        if not self._authorize():
            raise VenueServerException("You are not authorized to perform this action.")

        self.services[serviceDescription.uri] = serviceDescription

    AddService.soap_export_as = "AddService"

    def RemoveService(self, URL, serviceDescription):
        """
        RemoveService removes a service description from the list of
        service descriptions that this VenueServer knows about.
        """
        if not self._authorize():
            raise VenueServerException("You are not authorized to perform this action.")

        self.services.remove(serviceDescription)

    RemoveService.soap_export_as = "RemoveService"

    def ModifyService(self, URL, serviceDescription):
        """
        ModifyService updates a service description that is in the
        list of services for this VenueServer.
        """
        if not self._authorize():
            raise VenueServerException("You are not authorized to perform this action.")

        if URL == serviceDescription.uri:
            self.services[URL] = serviceDescription

    ModifyService.soap_export_as = "ModifyService"

    def RegisterServer(self, URL):
        """
        This method should register the server with the venues
        registry at the URL passed in. This is by default a
        registration page at Argonne for now.
        """
        if not self._authorize():
            raise VenueServerException("You are not authorized to perform this action.")
        # registryService = SOAP.SOAPProxy(URL)
        # registryService.Register(#data)

    RegisterServer.soap_export_as = "RegisterServer"

    def GetVenues(self):
        """
        GetVenues returns a list of Venues Descriptions for the venues hosted by
        this VenueServer.
        """
        try:
            venueDescriptionList = map( lambda venue: venue.GetDescription(),
                                        self.venues.values() )
            return venueDescriptionList
        except:
            log.exception("Exception in GetVenues!")
            raise VenueServerException("GetVenues Failed!")

    GetVenues.soap_export_as = "GetVenues"

    def GetDefaultVenue(self):
        """
        GetDefaultVenue returns the URL to the default Venue on the
        VenueServer.
        """
        return self.defaultVenue

    GetDefaultVenue.soap_export_as = "GetDefaultVenue"

    def SetDefaultVenue(self,  venueURL):
        """
        SetDefaultVenue sets which Venue is the default venue for the
        VenueServer.
        """
        if not self._authorize():
            raise VenueServerException("You are not authorized to perform this action.")
        self.defaultVenue = venueURL
        self.config["VenueServer.defaultVenue"] = venueURL
        defaultVenue = self.hostingEnvironment.create_service_object('Venues/default')
        self.venues[venueURL]._bind_to_service(defaultVenue)

    SetDefaultVenue.soap_export_as = "SetDefaultVenue"

    def SetStorageLocation(self,  dataStorageLocation):
        """
        Set the path for data storage
        """
        if not self._authorize():
            raise VenueServerException("You are not authorized to perform this action.")
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
            raise VenueServerException("You are not authorized to perform this action.")
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
            raise VenueServerException("You are not authorized to perform this action.")
        self.encryptAllMedia = value
        return self.encryptAllMedia

    SetEncryptAllMedia.soap_export_as = "SetEncryptAllMedia"

    def GetEncryptAllMedia(self):
        """
        Get the server wide default for venue media encryption.
        """
        return self.encryptAllMedia

    GetEncryptAllMedia.soap_export_as = "GetEncryptAllMedia"

    def SetBaseAddress(self, address):
        """
        Set base address used when allocating multicast addresses in
        an interval
        """
        if not self._authorize():
            raise VenueServerException("You are not authorized to perform this action.")
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
            raise VenueServerException("You are not authorized to perform this action.")
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
        if not self._authorize():
            raise VenueServerException("You are not authorized to perform this action.")
        self.Checkpoint()

        self.textService.Stop()
        self.eventService.Stop()
        # Shut down the dataStore
        # self.dataService.Stop()

        self.hostingEnvironment.stop()

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
        log.info("Checkpointing")

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

            store = shelve.open(self.persistenceFilename)

            for vURL in self.venues.keys():

                venue = self.venues[vURL]
                store[vURL] = venue

            store.close()
        except:
            log.exception("Exception Checkpointing!")
            raise VenueServerException("Checkpoint Failed!")

        log.info("Checkpoint Complete.")

        SaveConfig(self.configFile, self.config)

