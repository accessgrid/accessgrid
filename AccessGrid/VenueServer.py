#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
#
# Author:      Everyone
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.96 2003-09-17 13:59:17 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: VenueServer.py,v 1.96 2003-09-17 13:59:17 judson Exp $"
__docformat__ = "restructuredtext en"

# Standard stuff
import sys
import os
import re
import os.path
import socket
import string
from threading import Thread, Lock, Condition
import traceback
import logging
import time
import ConfigParser

from AccessGrid import Toolkit
from AccessGrid.hosting.pyGlobus import Server
from AccessGrid.hosting import AccessControl
from AccessGrid.hosting.pyGlobus import ServiceBase
from AccessGrid.DataStore import DataService

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid import NetService

from AccessGrid.Utilities import formatExceptionInfo, LoadConfig, SaveConfig
from AccessGrid.Utilities import GetHostname, PathFromURL
from AccessGrid.GUID import GUID
from AccessGrid.Venue import Venue, AdministratorNotFound, RegisterDefaultVenueRoles
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
from AccessGrid.hosting.AccessControl import RoleManager, Subject

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
            "VenueServer.dataServiceUrl" : '',
            "VenueServer.dataPort" : 8006,
            "VenueServer.encryptAllMedia" : 1,
            "VenueServer.houseKeeperFrequency" : 30,
            "VenueServer.persistenceFilename" : 'VenueServer.dat',
            "VenueServer.serverPrefix" : 'VenueServer',
            "VenueServer.venuePathPrefix" : 'Venues',
            "VenueServer.dataStorageLocation" : 'Data',
            "VenueServer.dataSize" : '10M',
            "VenueServer.backupServer" : '',
            "VenueServer.addressAllocationMethod" : MulticastAddressAllocator.RANDOM,
            "VenueServer.baseAddress" : MulticastAddressAllocator.SDR_BASE_ADDRESS,
            "VenueServer.addressMask" : MulticastAddressAllocator.SDR_MASK_SIZE
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
        self.defaultVenue = ''
        self.multicastAddressAllocator = MulticastAddressAllocator()
        self.hostname = GetHostname()
        self.venues = {}
        self.services = []
        self.configFile = configFile
        self.eventPort = 0
        self.textPort = 0
        self.internalDataService = None
               
        # Create a role manager so it can be used when loading persistent data. 
        self.roleManager = RoleManager()
        self.RegisterDefaultRoles() 

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

        # Initialize the multicast address allocator
        self.multicastAddressAllocator.SetAddressAllocationMethod(self.addressAllocationMethod)
        self.multicastAddressAllocator.SetBaseAddress(self.baseAddress)
        self.addressMask = int(self.addressMask)
        self.multicastAddressAllocator.SetAddressMask(self.addressMask)

        if self.dataServiceUrl != '':
            # Connect to a remote data service
            try:
                dataServiceProxy = Client.Handle(self.dataServiceUrl).GetProxy()
            except:
                log.info('Can not connect to remote data service at %s', self.dataServiceUrl)
                self.dataServiceUrl = None
                
        else:
            self.internalDataService = DataService(self.dataStorageLocation, self.dataPort, 8600)
            self.dataServiceUrl = self.internalDataService.GetHandle()

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
                self.defaultVenue = ''

        #
        # Reinitialize the default venue
        #
        log.debug("CFG: Default Venue: %s", self.defaultVenue)
        
        if len(self.defaultVenue) != 0 and self.defaultVenue in self.venues.keys():
            log.debug("Setting default venue")
           
            self.SetDefaultVenue(self.MakeVenueURL(self.defaultVenue))
        else:
            log.debug("Creating default venue")
            if not self.defaultVenueDesc.roleManager:
                self.defaultVenueDesc.roleManager = RoleManager()
                
            RegisterDefaultVenueRoles(self.defaultVenueDesc.roleManager)
            # Let the venue role manager know about the venueserver role manager.
            self.defaultVenueDesc.roleManager.RegisterExternalRoleManager("VenueServer", self.roleManager)
            # Set default Venue administrators to include all VenueServer administrators.
            self.defaultVenueDesc.roleManager.GetRole("Venue.Administrators").AddSubject("Role.VenueServer.Administrators")
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
        self.BindRoleManager()
        self.RegisterDefaultSubjects() # Register primary user as administrator

        # Some simple output to advertise the location of the service
        print("Server URL: %s \nEvent Port: %d Text Port: %d" %
              ( self.service.GetHandle(), int(self.eventPort),
                int(self.textPort) ) )

    def BindRoleManager(self):
        """ This method you to bind a role manager to our service object. """
        self._service_object.SetRoleManager(self.roleManager)

    def SetRoleManager(self, role_manager):
        """ Store manager in two places because we need to load roles from 
            persistent data into self.manager before manager is bound to service.
        """
        self.roleManager = role_manager 
        self._service_object.SetRoleManager(role_manager)

    def GetRoleManager(self):
        """ Return self.roleManager because it is valid sooner.   After binding
            it is the same as self._service_object.GetRoleManager() 
        """
        return self.roleManager # same as self._service_object.GetRoleManager() 

    def RegisterDefaultRoles(self):
        self.GetRoleManager().RegisterRole("VenueServer.Administrators")

    def RegisterDefaultSubjects(self):
        role = self.GetRoleManager().validRoles["VenueServer.Administrators"]
        certMgr = Toolkit.GetApplication().GetCertificateManager()

        defaultIdentity = certMgr.GetDefaultIdentity()
        if defaultIdentity is not None:
            role.AddSubject(defaultIdentity.GetSubject())

    def LoadPersistentVenues(self, filename):
        """        This method loads venues from a persistent store.

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

                # Deal with roles if there are any
                roleManager = None
                role_names = []
                try:
                    role_names = string.split(cp.get(sec, 'roles'), ':')
                except ConfigParser.NoOptionError:
                    log.warn("No roles for venue %s", sec)
                    role_names = []

                # Read the subjects for the role names we just read (if any).
                if len(role_names):
                    try:
                        roleManager = RoleManager()
                        for role_name in role_names:
                            roleManager.RegisterRole(role_name) # create role if needed.
                            role_subjects = string.split(cp.get(sec, role_name), ':')
                            # Add subjects/users to role.
                            r = roleManager.GetRole(role_name)
                            for subj in role_subjects:
                                r.AddSubject(subj)
                    except ConfigParser.NoOptionError:
                        log.warn("specific role %s details not in venue %s, registering default users", role_name, sec)
                        roleManager = None   # default roles and users will be used.

                # We can't persist crlf or cr or lf, so we replace them
                # on each end (when storing and loading)
                desc = cp.get(sec, 'description')
                desc = re.sub("<CRLF>", "\r\n", desc)
                desc = re.sub("<CR>", "\r", desc)
                desc = re.sub("<LF>", "\n", desc)
                
                v = Venue(self, cp.get(sec, 'name'), desc, roleManager, id=sec)
                # Make sure the venue Role Manager knows about the VenueServer role manager.
                v.GetRoleManager().RegisterExternalRoleManager("VenueServer", self.roleManager)
                v.encryptMedia = cp.getint(sec, 'encryptMedia')
                if v.encryptMedia:
                    v.encryptionKey = cp.get(sec, 'encryptionKey')
                else:
                    v.encryptionKey = None
                v.cleanupTime = cp.getint(sec, 'cleanupTime')

                self.venues[self.IdFromURL(v.uri)] = v
                self.hostingEnvironment.BindService(v, PathFromURL(v.uri))

                # Bind the venue's role manager to the service.
                v.BindRoleManager()

               
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

                        if encryptionFlag != v.encryptMedia:
                            log.info("static stream\"" + name + "\"encryption did not match its venue.  Setting it.")
                            encryptionFlag = v.encryptMedia
                            if encryptionKey != v.encryptionKey:
                                log.info("static stream\"" + name + "\"encryption key did not match its venue.  Setting it.")
                                encryptionKey = v.encryptionKey

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

                    
                # Register with data service
                privateId = v.AddNetService(NetService.DataStoreNetService.TYPE)
                (eventServiceLocation, channelId) = v.GetEventServiceLocation()

                try:
                    dataService = Client.Handle(self.dataServiceUrl).GetProxy()
                    dataStoreUrl = dataService.RegisterVenue(privateId, eventServiceLocation, v.uniqueId)
                    v.SetDataStore(dataStoreUrl)
                except:
                    log.exception("VenueServer Can not connect to data store %s"%self.dataServiceUrl)

                # Deal with data if there is any
                try:
                    dataList = cp.get(sec, 'data')
                except ConfigParser.NoOptionError:
                    dataList = ""

                # Handle data lists found in venue persistence
                # (data was persisted with venues in 2.0, so this is 
                # for backward compatibility)
                if len(dataList) != 0:
                    log.info("dataList found in venue persistence")

                    # Get the list of files in the venue
                    venueFiles = Client.Handle(dataStoreUrl).GetProxy().GetFiles()

                    # For each file referenced in venue persistence
                    for d in string.split(dataList, ':'):

                        # Does the file exist in the data store?
                        for f in venueFiles:
                            if  f[0] == cp.get(d, 'name') and f[1] == cp.getint(d, 'size'):

                                log.info(" - found match between venue persisted data and file in datastore")
                        
                                # Create the data description from the venue-persisted data
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

                                # Add the data description to the data store
                                log.info(" - setting description for file %s" % f[0] )
                                Client.Handle(dataStoreUrl).GetProxy().SetDescription(f[0],dd)

                                break

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

    def _IsInRole(self, role_name=""):
        """
            Role Based Authorization method.
            Role name is passed in.  This method returns
            whether the current user is a member of that role.

            **Returns:**
                *1* on success
                *0* on failure
        """

        sm = AccessControl.GetSecurityManager()
        if sm == None:
            return 1

        role_manager = self.GetRoleManager()

        return sm.ValidateCurrentSubjectInRole(role_name, role_manager)

    def InitFromFile(self, config):
        """
        """
        self.config = config
        for k in config.keys():
            (section, option) = string.split(k, '.')
            if option == "administrators":
                adminList = string.split(config[k],':')
                for a in adminList:
                    self.AddAdministrator(a)
            else:
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
        config = self.config.copy()
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

        
        if not self._IsInRole("VenueServer.Administrators"):
            log.exception("Unauthorized attempt to Add Venue.")
            raise NotAuthorized

        venueDesc = CreateVenueDescription(venueDescStruct)

        if venueDesc == None:
            raise InvalidVenueDescription
            
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
        if not self._IsInRole("VenueServer.Administrators"):   
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
        
        if not self._IsInRole("VenueServer.Administrators"):
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
        if not self._IsInRole("VenueServer.Administrators"):
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
        if not self._IsInRole("VenueServer.Administrators"):
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
        if not self._IsInRole("VenueServer.Administrators"):
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
        if not self._IsInRole("VenueServer.Administrators"):
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
        if not self._IsInRole("VenueServer.Administrators"):
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
        if not self._IsInRole("VenueServer.Administrators"):
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

    def wsSetBackupServer(self, server):
        """
        Interface for setting a fallback venue server.

        **Arguments:**

            *server* The string hostname of the server.

        **Raises:**

            *NotAuthorized* This is raised when the method is called
            by a non-administrator.

        **Returns:**

            *server* the return value from SetBackupServer
        """
        if not self._IsInRole("VenueServer.Administrators"):
            raise NotAuthorized

        try:
            self.simpleLock.acquire()
            
            returnValue = self.SetBackupServer(server)
            
            self.simpleLock.release()
            
            return returnValue
        except:
            self.simpleLock.release()
            log.exception("wsSetBackupServer: exception")
            raise

    wsSetBackupServer.soap_export_as = "SetBackupServer"

    def wsGetBackupServer(self):
        """
        Interface to retrieve the value of the backup server name.

        **Arguments:**

        **Raises:**

        **Returns:**
            the string hostname of the back up server or "".
        """
        try:
            self.simpleLock.acquire()

            returnValue = self.GetBackupServer()
            
            self.simpleLock.release()
            
            return returnValue
        except:
            self.simpleLock.release()
            log.exception("wsGetBackupServer: exception")
            raise
        
    wsGetBackupServer.soap_export_as = "GetBackupServer"

    def wsSetBaseAddress(self, address):
        """
        Interface for setting the base address for the allocation pool.

        **Arguments:**
        
            *address* The base address of the address pool to allocate from.
            
        **Raises:**

            *NotAuthorized*  When called by a non-administrator.

        **Returns:**
        
        """
        if not self._IsInRole("VenueServer.Administrators"):
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
        if not self._IsInRole("VenueServer.Administrators"):
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
        if not self._IsInRole("VenueServer.Administrators"):
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
        # Usually the venueDesc will not have Role information 
        #   and defaults will be used.
      
        venue = Venue(self, venueDesc.name, venueDesc.description,
                      venueDesc.roleManager)

        # Make sure new venue knows about server's external role manager.
        if "VenueServer" not in venue.GetRoleManager().GetExternalRoleManagerList():
            venue.GetRoleManager().RegisterExternalRoleManager("VenueServer", self.GetRoleManager())

        venue.SetEncryptMedia(venueDesc.encryptMedia, venueDesc.encryptionKey)
        
        # Add Connections if there are any
        venue.SetConnections(venueDesc.connections)
        
        # Add Streams if there are any
        for sd in venueDesc.streams:
            sd.encryptionFlag = venue.encryptMedia
            sd.encryptionKey = venue.encryptionKey
            venue.streamList.AddStream(sd)
            
        # Add the venue to the list of venues
        self.venues[self.IdFromURL(venue.uri)] = venue
        
        # We have to register this venue as a new service.
        venuePath = PathFromURL(venue.uri)
        if(self.hostingEnvironment != None):
            self.hostingEnvironment.BindService(venue, venuePath)
            # Initialize Role Manager and Roles for venue
            venue.BindRoleManager()
            venue.RegisterDefaultSubjects()
            
        # If this is the first venue, set it as the default venue
        if(len(self.venues) == 1):
            self.SetDefaultVenue(venue.uri)

            
        # Register with the venue
        privateId = venue.AddNetService(NetService.DataStoreNetService.TYPE)
        (eventServiceLocation, channelId) = venue.GetEventServiceLocation()

       
        try:
            dataService = Client.Handle(self.dataServiceUrl).GetProxy()
            dataStoreUrl = dataService.RegisterVenue(privateId, eventServiceLocation, venue.uniqueId)
            venue.SetDataStore(dataStoreUrl)
        except:
            log.exception("VenueServer Can not connect to data store %s"%self.dataServiceUrl)
                                
        # return the URL to the new venue
        return venue.uri

    def ModifyVenue(self, id, venueDesc):   
        """   
        ModifyVenue updates a Venue Description.   
        """
        self.venues[id].name = venueDesc.name
        self.venues[id].description = venueDesc.description
        self.venues[id].uri = venueDesc.uri

        # Usually venueDesc.roleManager will be None, and Roles are
        #   modified separately.
        if venueDesc.roleManager:
            self.venues[id].SetRoleManager(venueDesc.roleManager)
            # Make sure at least default roles exist.
            self.venues[id].RegisterDefaultRoles() 
            # Allow venue to access our (VenueServer) role manager
            if "VenueServer" not in self.venues[id].GetRoleManager().GetExternalRoleManagerList():
                self.roleManager.RegisterExternalRoleManager("VenueServer", self.roleManager)

        self.venues[id].SetEncryptMedia(venueDesc.encryptMedia, venueDesc.encryptionKey)
            
        self.venues[id].SetConnections(venueDesc.connections)
        
        # Modify streams by removing old and adding new
        current_streams = self.venues[id].GetStaticStreams()    
        for sd in current_streams:
            self.venues[id].RemoveStream(sd)
        for sd in venueDesc.streams:
            sd.encryptionFlag = self.venues[id].encryptMedia
            sd.encryptionKey = self.venues[id].encryptionKey
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
        role = self.GetRoleManager().GetRole("VenueServer.Administrators")
        if role.HasSubject(string):
            log.exception("AddAdministrator: Administrator already present.")
            raise AdministratorAlreadyPresent
        
        role.AddSubject(string)

        self.config["VenueServer.administrators"] = ":".join(role.GetSubjectListAsStrings())
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
        role = self.GetRoleManager().GetRole("VenueServer.Administrators")
        if role.HasSubject(string):
            role.RemoveSubject(string)
            self.config["VenueServer.administrators"] = ":".join(role.GetSubjectListAsStrings())
            return string
        else:
            log.exception("RemoveAdministrator: Administrator not found.")
            raise AdministratorNotFound
        
    def GetAdministrators(self):
        """
        GetAdministrators returns a list of adminisitrators for this
        VenueServer.
        """
        role = self.GetRoleManager().GetRole("VenueServer.Administrators")
        return role.GetSubjectListAsStrings()

    GetAdministrators.soap_export_as = "GetAdministrators"


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
        rm = self.venues[id].GetRoleManager()
        self.hostingEnvironment.BindService(self.venues[id], defaultPath)
        # This venue already has a role manager.  Assign it to this
        #   service as well so the same role manager will be used
        #   when connecting to "/Venues/default" or the venue's long name.
        self.venues[id].SetRoleManager(rm)
        if "VenueServer" not in self.venues[id].GetRoleManager().GetExternalRoleManagerList():
            log.exception("\"VenueServer\" not in external role manager list.")
        
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

    def SetEncryptAllMedia(self, value):
        """
        Turn on or off server wide default for venue media encryption.
        """
        self.encryptAllMedia = int(value)
        self.config["VenueServer.encryptAllMedia"] = value

        return self.encryptAllMedia

    def GetEncryptAllMedia(self):
        """
        Get the server wide default for venue media encryption.
        """
        return int(self.encryptAllMedia)

    def SetBackupServer(self, server):
        """
        Turn on or off server wide default for venue media encryption.
        """
        self.backupServer = server
        self.config["backupServer"] = server

        return self.backupServer

    def GetBackupServer(self):
        """
        Get the server wide default for venue media encryption.
        """
        return self.backupServer

    def SetAddressAllocationMethod(self,  addressAllocationMethod):
        """
        Set the method used for multicast address allocation:
            either RANDOM or INTERVAL (defined in MulticastAddressAllocator)
        """
        self.addressAllocationMethod = addressAllocationMethod
        self.multicastAddressAllocator.SetAddressAllocationMethod(
            addressAllocationMethod )
        self.config["VenueServer.addressAllocationMethod"] = addressAllocationMethod

    def GetAddressAllocationMethod(self):
        """
        Get the method used for multicast address allocation:
            either RANDOM or INTERVAL (defined in MulticastAddressAllocator)
        """
        return self.multicastAddressAllocator.GetAddressAllocationMethod()

    def SetBaseAddress(self, address):
        """
        Set base address used when allocating multicast addresses in
        an interval
        """
        self.baseAddress = address
        self.multicastAddressAllocator.SetBaseAddress( address )
        self.config["VenueServer.baseAddress"] = address

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
        self.addressMask = mask
        self.multicastAddressAllocator.SetAddressMask( mask )
        self.config["VenueServer.addressMask"] = mask

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
            
        if not self._IsInRole("VenueServer.Administrators"):
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
        if self.internalDataService:
            log.info("                         data service")
            self.internalDataService.Shutdown()

        self.hostingEnvironment.Stop()
        del self.hostingEnvironment
        log.info("                              done.")

        log.info("Shutdown Complete.")
        
