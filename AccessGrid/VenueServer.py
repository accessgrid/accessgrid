#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
#
# Author:      Everyone
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.79 2003-06-26 20:50:47 lefvert Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

# Standard stuff
import sys
import os
import os.path
import socket
import string
from threading import Thread, Lock, Condition
import traceback
import logging
import time
import ConfigParser

# AG Stuff
from AccessGrid.hosting.pyGlobus import Server
from AccessGrid.hosting import AccessControl
from AccessGrid.hosting.pyGlobus import ServiceBase
from AccessGrid.hosting.pyGlobus.Utilities import GetDefaultIdentityDN

from AccessGrid.Utilities import formatExceptionInfo, LoadConfig, SaveConfig
from AccessGrid.Utilities import GetHostname, PathFromURL
from AccessGrid.GUID import GUID
from AccessGrid.Venue import Venue, AdministratorNotFound
from AccessGrid.Venue import AdministratorAlreadyPresent
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid.DataStore import GSIHTTPTransferServer
from AccessGrid.EventServiceAsynch import EventService
from AccessGrid.scheduler import Scheduler
from AccessGrid.TextServiceAsynch import TextService

from AccessGrid.Descriptions import ConnectionDescription, StreamDescription
from AccessGrid.Descriptions import DataDescription, VenueDescription
from AccessGrid.Descriptions import CreateVenueDescription, ServiceDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.NetworkLocation import UnicastNetworkLocation
from AccessGrid.Types import Capability
from AccessGrid.Utilities import ServerLock

log = logging.getLogger("AG.VenueServer")

class VenueServerException(Exception):
    """
    A generic exception type to be raised by the Venue code.
    """
    pass

class NotAuthorized(Exception):
    """
    The exception raised when a caller is not authorized to make the call.
    """
    pass

class InvalidVenueURL(Exception):
    """
    The exception raised when a URL doesn't point to a venue.
    """
    pass

class UnbindVenueError(Exception):
    """
    The exception raised when the hosting environment can't detach a
    venue from the web services layer.
    """
    pass

class VenueNotFound(Exception):
    """
    The exception raised when a venue is not found on this venue server.
    """
    pass

class InvalidVenueDescription(Exception):
    """
    The exception raised when a venue description cannot be made from an
    anonymous struct.
    """
    pass

class VenueServer(ServiceBase.ServiceBase):
    """
    The Virtual Venue Server object is responsible for creating,
    destroying, and configuring Virtual Venue objects.

    **Extends:**

        *AccessGrid.hosting.pyGlobus.ServiceBase.*
    
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

        **Arguments:**
        - *hostingEnvironment* a reference to the hosting environment.
        - *configFile* the filename of a configuration file for this venue server.
        
        """
        # Initialize our state
        self.persistenceFilename = 'VenueServer.dat'
        self.houseKeeperFrequency = 30
        self.venuePathPrefix = 'Venues'
        self.administrators = ''
        self.administratorList = []
        self.defaultVenue = ''
        self.multicastAddressAllocator = MulticastAddressAllocator()
        self.hostname = GetHostname()
        self.venues = {}
        self.services = []
        self.configFile = configFile
        self.dataStorageLocation = None
        self.dataPort = 0
        self.eventPort = 0
        self.textPort = 0

        if hostEnvironment != None:
            self.hostingEnvironment = hostEnvironment
            self.internalHostingEnvironment = 0 # False
        else:
            defaultPort = 8000
            self.hostingEnvironment = Server.Server(defaultPort)
            self.internalHostingEnvironment = 1 # True

        self.simpleLock = ServerLock("main")
        
        # Figure out which configuration file to use for the
        # server configuration. If no configuration file was specified
        # look for a configuration file named VenueServer.cfg
        if self.configFile == None:
            classpath = string.split(str(self.__class__), '.')
            self.configFile = classpath[-1]+'.cfg'

        # Read in and process a configuration
        self.InitFromFile(LoadConfig(self.configFile, self.configDefaults))

        # Check for and if necessary create the data store directory
        if not os.path.exists(self.dataStorageLocation):
            try:
                os.mkdir(self.dataStorageLocation)
            except OSError:
                log.exception("Could not create VenueServer Data Store.")
                self.dataStorageLocation = None

        # If there are no administrators set then we set it to the
        # owner of the current running process
        if len(self.administrators) == 0:
            dnAdmin = GetDefaultIdentityDN()
            if dnAdmin:
                self.administratorList.append(dnAdmin)
        else:
            self.administratorList = string.split(self.administrators, ":")
            
        # Start Venue Server wide services
        self.dataTransferServer = GSIHTTPTransferServer(('',
                                                         int(self.dataPort)),
                                                        numThreads = 4,
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
            self.defaultVenueDesc.administrators.append(GetDefaultIdentityDN())
            self.AddVenue(self.defaultVenueDesc)

        # The houseKeeper is a task that is doing garbage collection and
        # other general housekeeping tasks for the Venue Server.
        self.houseKeeper = Scheduler()
        self.houseKeeper.AddTask(self.Checkpoint,
                                 int(self.houseKeeperFrequency), 0)

        self.houseKeeper.AddTask(self.CleanupVenueClients, 10)
        
        self.houseKeeper.StartAllTasks()

        # Then we create the VenueServer service
        self.service = self.hostingEnvironment.BindService(self, 'VenueServer')

        # Some simple output to advertise the location of the service
        print("Server URL: %s \nEvent Port: %d Text Port: %d Data Port: %d" %
              ( self.service.GetHandle(), int(self.eventPort),
                int(self.textPort), int(self.dataPort) ) )

    def LoadPersistentVenues(self, filename):
        """
        This method loads venues from a persistent store.

        **Arguments:**

            *filename* The filename for the persistent store. It is
            currently a INI formatted file.
        """
        cp = ConfigParser.ConfigParser()
        cp.read(filename)

        log.debug("Reading persisted Venues from: %s", filename)
        
        # Load the global defaults first
        for sec in cp.sections():
            if cp.has_option(sec, 'type'):
                log.debug("Loading Venue: %s", sec)
                try:
                    administrators = string.split(cp.get(sec,
                                                         'administrators'),
                                                  ':')
                except ConfigParser.NoOptionError:
                    log.warn("No adminstrators for venue %s", sec)
                    administrators = []
                v = Venue(self, cp.get(sec, 'name'),
                          cp.get(sec, 'description'), administrators,
                          self.dataStorageLocation, id=sec)
                v.encryptMedia = cp.getint(sec, 'encryptMedia')
                v.cleanupTime = cp.getint(sec, 'cleanupTime')

                self.venues[self.IdFromURL(v.uri)] = v
                self.hostingEnvironment.BindService(v, PathFromURL(v.uri))

                # Deal with connections if there are any
                try:
                    connections = cp.get(sec, 'connections')
                except ConfigParser.NoOptionError:
                    connections = ""
                    
                if len(connections) != 0:
                    for c in string.split(connections, ':'):
                        uri = self.MakeVenueURL(self.IdFromURL(cp.get(c,
                                                                      'uri')))
                        cd = ConnectionDescription(cp.get(c, 'name'),
                                                   cp.get(c, 'description'),
                                                   uri)
                        v.AddConnection(cd)

                else:
                    log.debug("No connections to load for venue %s", sec)
                        
                # Deal with streams if there are any
                try:
                    streams = cp.get(sec, 'streams')
                except ConfigParser.NoOptionError:
                    streams = ""

                if len(streams) != 0:
                    for s in string.split(streams, ':'):
                        name = cp.get(s, 'name')
                        encryptionFlag = cp.getint(s, 'encryptionFlag')
                        if encryptionFlag:
                            encryptionKey = cp.get(s, 'encryptionKey')
                        else:
                            encryptionKey = None
                        locationAttrs = string.split(cp.get(s, 'location'),
                                                         " ")
                        capability = string.split(cp.get(s, 'capability'), ' ')

                        locationType = locationAttrs[0]
                        if locationType == MulticastNetworkLocation.TYPE:
                            (addr,port,ttl) = locationAttrs[1:]
                            loc = MulticastNetworkLocation(addr, int(port),
                                                           int(ttl))
                        else:
                            (addr,port) = locationAttrs[1:]
                            loc = UnicastNetworkLocation(addr, int(port))

                        cap = Capability(capability[0], capability[1])

                        sd = StreamDescription(name, loc, cap, 
                                               encryptionFlag, encryptionKey,
                                               1)
                        v.AddStream(sd)
                else:
                    log.debug("No streams to load for venue %s", sec)

                # Deal with data if there is any
                try:
                    dataList = cp.get(sec, 'data')
                except ConfigParser.NoOptionError:
                    dataList = ""

                persistentData = []

                if len(dataList) != 0:
                    for d in string.split(dataList, ':'):
                        dd = DataDescription(cp.get(d, 'name'))
                        dd.SetId(d)
                        try:
                            dd.SetDescription(cp.get(d, 'description'))
                        except ConfigParser.NoOptionError:
                            log.info("LoadPersistentVenues: Data has no description")
                        dd.SetStatus(cp.get(d, 'status'))
                        dd.SetSize(cp.getint(d, 'size'))
                        dd.SetChecksum(cp.get(d, 'checksum'))
                        dd.SetOwner(cp.get(d, 'owner'))

                        persistentData.append(dd)
                        
                v.dataStore.LoadPersistentData(persistentData)
                        # Ick
                #        v.data[dd.name] = dd
                #        v.UpdateData(dd)
                #else:
                #    log.debug("No data to load for Venue %s", sec)


                # Deal with apps if there are any
                try:
                    appList = cp.get(sec, 'applications')
                except ConfigParser.NoOptionError:
                    appList = ""

                if len(appList) != 0:
                    for id in string.split(appList, ':'):
                        name = cp.get(id, 'name')
                        description = cp.get(id, 'description')
                        mimeType = cp.get(id, 'mimeType')

                        appDesc = v.CreateApplication(name, description,
                                                      mimeType, id)
                        appImpl = v.applications[appDesc.id]

                        for o in cp.options(id):
                            if o != 'name' and o != 'description' and o != 'id' and o != 'uri' and o != mimeType:
                                value = cp.get(id, o)
                                appImpl.app_data[o] = value
                else:
                    log.debug("No data to load for Venue %s", sec)

                # Deal with services if there are any
                try:
                    serviceList = cp.get(sec, 'services')
                except ConfigParser.NoOptionError:
                    serviceList = ""

                if len(serviceList) != 0:
                    for id in string.split(serviceList, ':'):
                        name = cp.get(id, 'name')
                        description = cp.get(id, 'description')
                        mimeType = cp.get(id, 'mimeType')
                        uri = cp.get(id, 'uri')

                        sd = ServiceDescription(name, description, uri,
                                                mimeType)
                        v.services[name] = sd
                else:
                    log.debug("No services to load for Venue %s", sec)

    def _Authorize(self):
        """
        This is a placeholder authorization method. It will be
        replaced with the Role Based Authorization. Currently
        authorization is merely a check to see if the caller is an
        administrator.

        **Returns:**
            *1* on success
            *0* on failure
        """
        sm = AccessControl.GetSecurityManager()
        if sm == None:
            return 1
        elif sm.GetSubject().GetName() in self.administratorList:
            return 1
        else:
            log.exception("Authorization failed for %s",
                          sm.GetSubject().GetName())
            return 0

    def InitFromFile(self, config):
        """
        """
        self.config = config
        for k in config.keys():
            (section, option) = string.split(k, '.')
            setattr(self, option, config[k])

    def IdFromURL(self, URL):
        """
        """
        path = PathFromURL(URL)
        return path.split('/')[-1]
    
    def MakeVenueURL(self, uniqueId):
        """
        Helper method to make a venue URI from a uniqueId.
        """
        uri = string.join([self.hostingEnvironment.get_url_base(),
                           self.venuePathPrefix, uniqueId], '/')
        return uri


    def CleanupVenueClients(self):
        for venue in self.venues.values():
            venue.CleanupClients()

    def Checkpoint(self):
        """
        Checkpoint stores the current state of the running VenueServer to
        non-volatile storage. In the event of catastrophic failure, the
        non-volatile storage can be used to restart the VenueServer.

        The fequency at which Checkpointing is done will bound the amount of
        state that is lost (the longer the time between checkpoints, the more
        that can be lost).
        """
        # Before we backup we copy the previous backup to a safe place
        if os.path.isfile(self.persistenceFilename):
            nfn = self.persistenceFilename + '.bak'
            if os.path.isfile(nfn):
                try:
                    os.remove(nfn)
                except OSError:
                    log.exception("Couldn't remove backup file.")
                    return 0
            try:
                os.rename(self.persistenceFilename, nfn)
            except OSError:
                log.exception("Couldn't rename backup file.")
                return 0
            
        # Open the persistent store
        store = file(self.persistenceFilename, "w")

        try:            
            for venuePath in self.venues.keys():
                # Change out the uri for storage, we store the path
                venueURI = self.venues[venuePath].uri
                self.venues[venuePath].uri = venuePath

                try:            
                    # Store the venue.
                    store.write(self.venues[venuePath].AsINIBlock())
                except:
                    log.exception("Exception Storing Venue!")
                    return 0
                
                # Change the URI back
                self.venues[venuePath].uri = venueURI

            # Close the persistent store
            store.close()

        except:
            log.exception("Exception Checkpointing!")
            return 0

        log.info("Checkpointing completed at %s.", time.asctime())

        # Finally we save the current config
        SaveConfig(self.configFile, self.config)

        return 1

    def wsAddVenue(self, venueDescStruct):
        """
        Inteface call for Adding a venue.

        **Arguments:**

             *Venue Description Struct* A description of the new
             venue, currently an anonymous struct.

        **Raises:**
            *NotAuthorized* When an unauthorized call is made to add a venue.

            *VenueServerException* When the venue description struct
            isn't successfully converted to a real venue description
            object and the venue isn't added.

        **Returns:**
            *Venue URI* Upon success a uri to the new venue is returned.
        """

        
        if not self._Authorize():
            log.exception("Unauthorized attempt to Add Venue.")
            raise NotAuthorized

        venueDesc = CreateVenueDescription(venueDescStruct)

        if venueDesc == None:
            raise InvalidVenueDescription
            
        venueDesc.administrators.append(GetDefaultIdentityDN())

        try:
            self.simpleLock.acquire()
        
            venueUri = self.AddVenue(venueDesc)
        
            self.simpleLock.release()
        
            return venueUri
        except:
            self.simpleLock.release()
            log.exception("wsAddVenue: exception")
            raise

    wsAddVenue.soap_export_as = "AddVenue"
    
    def wsModifyVenue(self, URL, venueDescStruct):
        """
        Interface for modifying an existing Venue.

        **Arguments:**
            *URL* The URL to the venue.

            *Venue Description Struct* An anonymous struct that is the
            new venue description.

        **Raises:**
        
            *NotAuthorized* When an unauthorized modify call is made.

            *InvalideVenueURL* When the URL isn't a valid venue.

            *InvalidVenueDescription* If the Venue Description has a
            different URL than the URL argument passed in.

        """
        if not self._Authorize():   
            raise NotAuthorized

        if URL == None:
            raise InvalidVenueURL

        id = self.IdFromURL(URL)   
        vd = CreateVenueDescription(venueDescStruct)
        
        if vd.uri != URL:
            raise InvalidVenueDescription

        try:
            self.simpleLock.acquire()
            
            self.ModifyVenue(id, vd)

            self.simpleLock.release()
        except:
            self.simpleLock.release()
            log.exception("wsModifyVenue: exception")
            raise
        
    wsModifyVenue.soap_export_as = "ModifyVenue"

    def wsRemoveVenue(self, URL):
        """
        Interface for removing a Venue.

        **Arguments:**
            *URL* The url to the venue to be removed.

        **Raises:**

            *NotAuthorized* If a remove venue call is not authorized.

        """
        log.debug("wsRemoveVenue: url = %s", URL)
        
        if not self._Authorize():
            raise NotAuthorized

        id = self.IdFromURL(URL)

        try:
            self.simpleLock.acquire()
        
            self.RemoveVenue(id)
            
            self.simpleLock.release()
        except:
            self.simpleLock.release()
            log.exception("wsRemoveVenue: exception")
            raise
        
    wsRemoveVenue.soap_export_as = "RemoveVenue"

    def wsAddAdministrator(self, string):
        """
        Interface to add an administrator to the Venue Server.

        **Arguments:**

            *string* The DN of the new administrator.

        **Raises:**

            *NotAuthorized* This exception is raised if the call is
            coming from a non-administrator.

        **Returns:**

            *string* The DN of the administrator added.
        """
        if not self._Authorize():
            raise NotAuthorized

        try:
            self.simpleLock.acquire()
        
            returnString = self.AddAdministrator(string)

            self.simpleLock.release()
            
            return returnString
        except:
            self.simpleLock.release()
            log.exception("wsAddAdministrator: exception")
            raise
        
    wsAddAdministrator.soap_export_as = "AddAdministrator"

    def wsRemoveAdministrator(self, string):
        """
        **Arguments:**

            *string* The Distinguished Name (DN) of the administrator
            being removed.

        **Raises:**

            *NotAuthorized* This is raised when the caller is not an
            administrator.

        **Returns:**

            *string* The Distinguished Name (DN) of the administrator removed.
        """
        if not self._Authorize():
            raise NotAuthorized

        try:
            self.simpleLock.acquire()
        
            returnString = self.RemoveAdministrator(string)

            self.simpleLock.release()

            return returnString
        except:
            self.simpleLock.release()
            log.exception("wsRemoveAdministrator: exception")
            raise
    
    wsRemoveAdministrator.soap_export_as = "RemoveAdministrator"


    def wsGetVenues(self):
        """
        This is the interface to get a list of Venues from the Venue Server.

        **Returns:**

            *venue description list* A list of venues descriptions.
        """

        try:
            self.simpleLock.acquire()
        
            vdl = self.GetVenues()
            
            self.simpleLock.release()
            
            # This is because our SOAP implemenation doesn't like passing
            # dictionaries that have URLs for the keys.
            # This *should* go away.
            for v in vdl:
                v.connections = v.connections.values()
                
            return vdl
        except:
            self.simpleLock.release()
            log.exception("wsGetVenues: exception")
            raise
        
    wsGetVenues.soap_export_as = "GetVenues"

    def wsGetDefaultVenue(self):
        """
        Interface for getting the URL to the default venue.
        """
        try:
            self.simpleLock.acquire()
        
            returnURL = self.GetDefaultVenue()

            self.simpleLock.release()
        
            return returnURL
        except:
            self.simpleLock.release()
            log.exception("wsGetDefaultVenues: exception")
            raise
        
    wsGetDefaultVenue.soap_export_as = "GetDefaultVenue"

    def wsSetDefaultVenue(self, URL):
        """
        Interface to set default venue.

        **Arguments:**
            *URL* The URL to the default venue.
            
        **Raises:**
        
            *NotAuthorized* This exception is raised if the caller is
            not an administrator.

        **Returns:**

            *URL* the url of the default venue upon success.
        """
        if not self._Authorize():
            raise NotAuthorized

        try:
            self.simpleLock.acquire()

            self.SetDefaultVenue(URL)

            self.simpleLock.release()

            return URL
        except:
            self.simpleLock.release()
            log.exception("wsSetDefaultVenue: exception")
            raise
        
    wsSetDefaultVenue.soap_export_as = "SetDefaultVenue"

    def wsSetStorageLocation(self, location):
        """
        Interface for setting the location of the data store.
        
        **Arguments:**

            *location* This is a path for the data store.
            
        **Raises:**

            *NotAuthorized* Raised when the caller is not an administrator.
            
        **Returns:**

            *location* The new location on success.
        """
        if not self._Authorize():
            raise NotAuthorized

        try:
            self.simpleLock.acquire()
            
            self.SetStorageLocation(location)
            
            self.simpleLock.release()
        except:
            self.simpleLock.release()
            log.exception("wsSetStorageLocation: exception")
            raise

    wsSetStorageLocation.soap_export_as = "SetStorageLocation"

    def wsGetStorageLocation(self):
        """
        Inteface for getting the current data store path.
        
        **Arguments:**

        **Raises:**

        **Returns:**

            *location* The path to the data store location.
        """

        try:
            self.simpleLock.acquire()
        
            returnString = self.GetStorageLocation()
            
            self.simpleLock.release()
        
            return returnString
        except:
            self.simpleLock.release()
            log.exception("wsGetStorageLocation: exception")
            raise
            
    wsGetStorageLocation.soap_export_as = "GetStorageLocation"

    def wsSetAddressAllocationMethod(self, method):
        """
        Interface for setting the address allocation method for
        multicast addresses (for now).

        **Arguments:**

            *method* An argument specifying either RANDOM or INTERVAL
            allocation. RANDOM is a random address from the standard
            random range. INTERVAL means a random address from a
            specified range.

        **Raises:**

        **Returns:**
        """
        if not self._Authorize():
            raise NotAuthorized

        try:
            self.simpleLock.acquire()
            
            self.SetAddressAllocationMethod(method)
            
            self.simpleLock.release()
        except:
            self.simpleLock.release()
            log.exception("wsSetAddressAllocationMethod: exception")
            raise
        
    wsSetAddressAllocationMethod.soap_export_as = "SetAddressAllocationMethod"

    def wsGetAddressAllocationMethod(self):
        """
        Interface for getting the Address Allocation Method.

        **Arguments:**

        **Raises:**

        **Returns:**

            *method* The address allocation method configured, either
            RANDOM or INTERVAL.
        """
        try:
            self.simpleLock.acquire()
        
            returnValue = self.GetAddressAllocationMethod()
            
            self.simpleLock.release()
            
            return returnValue
        except:
            self.simpleLock.release()
            log.exception("wsGetAddressAllocationMethod: exception")
            raise
    
    wsGetAddressAllocationMethod.soap_export_as = "GetAddressAllocationMethod"

    def wsSetEncryptAllMedia(self, value):
        """
        Interface for setting the flag to encrypt all media or turn it off.

        **Arguments:**

            *value* The flag, 1 turns encryption on, 0 turns encryption off.

        **Raises:**

            *NotAuthorized* This is raised when the method is called
            by a non-administrator.

        **Returns:**

            *flag* the return value from SetEncryptAllMedia.
        """
        if not self._Authorize():
            raise NotAuthorized

        try:
            self.simpleLock.acquire()
            
            returnValue = self.SetEncryptAllMedia(value)
            
            self.simpleLock.release()
            
            return returnValue
        except:
            self.simpleLock.release()
            log.exception("wsSetEncryptAllMedia: exception")
            raise

    wsSetEncryptAllMedia.soap_export_as = "SetEncryptAllMedia"

    def wsGetEncryptAllMedia(self):
        """
        Interface to retrieve the value of the media encryption flag.

        **Arguments:**

        **Raises:**

        **Returns:**
        
        """
        try:
            self.simpleLock.acquire()

            returnValue = self.GetEncryptAllMedia()
            
            self.simpleLock.release()
            
            return returnValue
        except:
            self.simpleLock.release()
            log.exception("wsGetEncryptAllMedia: exception")
            raise
        
    wsGetEncryptAllMedia.soap_export_as = "GetEncryptAllMedia"

    def wsSetBaseAddress(self, address):
        """
        Interface for setting the base address for the allocation pool.

        **Arguments:**
        
            *address* The base address of the address pool to allocate from.
            
        **Raises:**

            *NotAuthorized*  When called by a non-administrator.

        **Returns:**
        
        """
        if not self._Authorize():
            raise NotAuthorized

        try:
            self.simpleLock.acquire()
            
            self.SetBaseAddress(address)
            
            self.simpleLock.release()
        except:
            self.simpleLock.release()
            log.exception("wsSetBaseAddress: exception")
            raise

    wsSetBaseAddress.soap_export_as = "SetBaseAddress"

    def wsGetBaseAddress(self):
        """
        Interface to retrieve the base address for the address allocation pool.

        **Arguments:**

        **Raises:**

        **Returns:**

            *base address* the base address of the address allocation pool.
        """
        try:
            self.simpleLock.acquire()
            
            returnValue = self.GetBaseAddress()
            
            self.simpleLock.release()
            
            return returnValue
        except:
            self.simpleLock.release()
            log.exception("wsGetBaseAddress: exception")
            raise
    
    wsGetBaseAddress.soap_export_as = "GetBaseAddress"

    def wsSetAddressMask(self, mask):
        """
        Interface to set the network mask of the address allocation pool.

        **Arguments:**

            *mask*  The network mask for the address allocation pool.
            
        **Raises:**

            *NotAuthorized* This is raised when the method is called
            by a non-administrator.

        **Returns:**
        """
        if not self._Authorize():
            raise NotAuthorized

        try:
            self.simpleLock.acquire()
            
            self.SetAddressMask(mask)

            self.simpleLock.release()

            return mask
        except:
            self.simpleLock.release()
            log.exception("wsSetAddressMask: exception")
            raise

    wsSetAddressMask.soap_export_as = "SetAddressMask"

    def wsGetAddressMask(self):
        """
        Interface to retrieve the address mask of the address allocation pool.

        **Arguments:**

        **Raises:**

        **Returns:**

            *mask* the network mask of the address allocation pool.
        """

        try:
            self.simpleLock.acquire()
            
            returnValue = self.GetAddressMask()
            
            self.simpleLock.release()
            
            return returnValue
        except:
            self.simpleLock.release()
            log.exception("wsGetAddressMask: exception")
            raise

    wsGetAddressMask.soap_export_as = "GetAddressMask"

    def wsShutdown(self, secondsFromNow):
        """
        Interface to shutdown the Venue Server.

        **Arguments:**

            *secondsFromNow* How long from the time the call is
            received until the server starts to shutdown.

        **Raises:**

        **Returns:**
        """
        if not self._Authorize():
            raise NotAuthorized

        log.debug("Calling wsShutdown with seconds %d" % secondsFromNow)

        self.Shutdown()
        
    wsShutdown.soap_export_as = "Shutdown"

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
            
        # Add the venue to the list of venues
        self.venues[self.IdFromURL(venue.uri)] = venue
        
        # We have to register this venue as a new service.
        venuePath = PathFromURL(venue.uri)
        if(self.hostingEnvironment != None):
            self.hostingEnvironment.BindService(venue, venuePath)
            
        # If this is the first venue, set it as the default venue
        if(len(self.venues) == 1):
            self.SetDefaultVenue(venue.uri)
                
        # return the URL to the new venue
        return venue.uri

    def ModifyVenue(self, id, venueDesc):   
        """   
        ModifyVenue updates a Venue Description.   
        """
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
        
    def RemoveVenue(self, id):
        """
        RemoveVenue removes a venue from the VenueServer.

        **Arguments:**
            *ID* The id of the venue to be removed.

        **Raises:**

            *UnbindVenueError* - This exception is raised when the
            hosting Environment fails to unbind the venue from the
            venue server.

            *VenueNotFound* - This exception is raised when the
            the venue is not found in the list of venues for this server.

        """

        log.debug("RemoveVenue: id = %s", id)
        
        # Get the venue object
        try:
            venue = self.venues[id]
        except KeyError:
            log.exception("RemoveVenue: Venue not found.")
            raise VenueNotFound

        # Stop the web service interface
        try:
            self.hostingEnvironment.UnbindService(venue)
        except:
            log.exception("RemoveVenue: Couldn't unbind venue.")
            raise UnbindVenueError
        
        # Shutdown the venue
        self.venues[id].Shutdown()
        
        # Clean it out of the venueserver
        del self.venues[id]

        # Checkpoint so we don't save it again
        self.Checkpoint()
        
    def AddAdministrator(self, string):
        """
        AddAdministrator adds an administrator to the list of administrators
        for this VenueServer.

        **Arguments:**

            *string* The Distinguished Name of the new administrator.

        **Raises:**

            *AdministratorAlreadyPresent* This exception is raised if
            the user is already an administrator.

        **Returns:**

            *string* The DN of the administrator added.

        """
        if string in self.administratorList:
            log.exception("AddAdministrator: Adminstrator already present.")
            raise AdministratorAlreadyPresent
        
        self.administratorList.append(string)

        self.config["VenueServer.administrators"] = ":".join(self.administratorList)
        return string

    def RemoveAdministrator(self, string):
        """
        RemoveAdministrator removes an administrator from the list of
        administrators for this VenueServer.

        **Arguments:**

            *string* The Distinguished Name (DN) of the administrator
            being removed.

        **Raises:**

            *AdministratorNotFound* This is raised when the
            administrator specified is not found in the Venue Servers
            administrators list.
        
        """
        if string in self.administratorList:
            self.administratorList.remove(string)
            self.config["VenueServer.administrators"] = ":".join(self.administratorList)
            return string
        else:
            log.exception("RemoveAdministrator: Administrator not found.")
            raise AdministratorNotFound
        
    def GetAdministrators(self):
        """
        GetAdministrators returns a list of adminisitrators for this
        VenueServer.
        """
        return self.administratorList

    GetAdministrators.soap_export_as = "GetAdministrators"

# This is not supported for 2.0
#     def RegisterServer(self, URL):
#         """
#         This method should register the server with the venues
#         registry at the URL passed in. This is by default a
#         registration page at Argonne for now.
#         """
#         if not self._Authorize():
#             raise NotAuthorized
#         registryService = SOAP.SOAPProxy(URL)
#         registryService.Register(data)

#     RegisterServer.soap_export_as = "RegisterServer"

    def GetVenues(self):
        """
        GetVenues returns a list of Venues Descriptions for the venues
        hosted by this VenueServer.

        **Arguments:**

        **Raises:**

            **VenueServerException** This is raised if there is a
            problem creating the list of Venue Descriptions.

        **Returns:**
            
            This returns a list of venue descriptions.

        """
        try:
            venueDescList = map(lambda venue: venue.AsVenueDescription(),
                                        self.venues.values() )

            return venueDescList
        except:
            log.exception("GetVenues: GetVenues failed!")
            raise VenueServerException("GetVenues Failed!")

    def GetDefaultVenue(self):
        """
        GetDefaultVenue returns the URL to the default Venue on the
        VenueServer.
        """
        return self.MakeVenueURL(self.defaultVenue)

    def SetDefaultVenue(self,  venueURL):
        """
        SetDefaultVenue sets which Venue is the default venue for the
        VenueServer.
        """
        defaultPath = "/Venues/default"
        id = self.IdFromURL(venueURL)
        self.defaultVenue = id
        self.config["VenueServer.defaultVenue"] = id
        self.hostingEnvironment.BindService(self.venues[id], defaultPath)
        
    def SetStorageLocation(self,  dataStorageLocation):
        """
        Set the path for data storage
        """
        self.dataStorageLocation = dataStorageLocation
        self.config["VenueServer.dataStorageLocation"] = dataStorageLocation

    def GetStorageLocation(self):
        """
        Get the path for data storage
        """
        return self.dataStorageLocation

    def SetAddressAllocationMethod(self,  addressAllocationMethod):
        """
        Set the method used for multicast address allocation:
            either RANDOM or INTERVAL (defined in MulticastAddressAllocator)
        """
        self.multicastAddressAllocator.SetAddressAllocationMethod(
            addressAllocationMethod )

    def GetAddressAllocationMethod(self):
        """
        Get the method used for multicast address allocation:
            either RANDOM or INTERVAL (defined in MulticastAddressAllocator)
        """
        return self.multicastAddressAllocator.GetAddressAllocationMethod()

    def SetEncryptAllMedia(self, value):
        """
        Turn on or off server wide default for venue media encryption.
        """
        self.encryptAllMedia = int(value)

        return self.encryptAllMedia

    def GetEncryptAllMedia(self):
        """
        Get the server wide default for venue media encryption.
        """
        return int(self.encryptAllMedia)

    def SetBaseAddress(self, address):
        """
        Set base address used when allocating multicast addresses in
        an interval
        """
        self.multicastAddressAllocator.SetBaseAddress( address )

    def GetBaseAddress(self):
        """
        Get base address used when allocating multicast addresses in
        an interval
        """
        return self.multicastAddressAllocator.GetBaseAddress( )

    def SetAddressMask(self,  mask):
        """
        Set address mask used when allocating multicast addresses in
        an interval
        """
        self.multicastAddressAllocator.SetAddressMask( mask )

    def GetAddressMask(self):
        """
        Get address mask used when allocating multicast addresses in
        an interval
        """
        return self.multicastAddressAllocator.GetAddressMask( )

    def Shutdown(self):
        """
        Shutdown shuts down the server.
        """
        if not self._Authorize():
            log.exception("Shutdown: Not authorized.")
            raise NotAuthorized

        log.info("Starting Shutdown!")

        for v in self.venues.values():
            v.Shutdown()
            
        self.houseKeeper.StopAllTasks()

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

        self.hostingEnvironment.Stop()
        del self.hostingEnvironment
        log.info("                              done.")

        log.info("Shutdown Complete.")
        
