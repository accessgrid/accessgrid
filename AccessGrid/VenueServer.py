#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
#
# Author:      Everyone
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.141 2004-05-03 20:10:45 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: VenueServer.py,v 1.141 2004-05-03 20:10:45 eolson Exp $"
__docformat__ = "restructuredtext en"

# Standard stuff
import sys
import os
import re
import os.path
import string
from threading import Thread, Lock, Condition
import time
import ConfigParser

from AccessGrid.Toolkit import Service
from AccessGrid import Log
from AccessGrid.hosting import SecureServer, InsecureServer
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.Security.AuthorizationManager import AuthorizationManager
from AccessGrid.Security.AuthorizationManager import AuthorizationManagerI
from AccessGrid.Security.AuthorizationManager import AuthorizationIMixIn
from AccessGrid.Security.AuthorizationManager import AuthorizationIWMixIn
from AccessGrid.Security.AuthorizationManager import AuthorizationMixIn
from AccessGrid.Security import X509Subject, Role
from AccessGrid.Security .Action import ActionAlreadyPresent

from AccessGrid.Security.Utilities import CreateSubjectFromGSIContext

from AccessGrid.Platform.Config import SystemConfig, UserConfig

from AccessGrid.Utilities import LoadConfig, SaveConfig
from AccessGrid.hosting import PathFromURL, IdFromURL
from AccessGrid.GUID import GUID
from AccessGrid.Venue import Venue, VenueI
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid.DataStore import GSIHTTPTransferServer, HTTPTransferServer
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

log = Log.GetLogger(Log.VenueServer)

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

class VenueServer(AuthorizationMixIn):
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
            "VenueServer.administrators" : '',
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
            "VenueServer.addressMask" : MulticastAddressAllocator.SDR_MASK_SIZE,
            "VenueServer.authorizationPolicy" : ''
            }

    defaultVenueDesc = VenueDescription("Venue Server Lobby", """This is the lobby of the Venue Server, it has been created because there are no venues yet. Please configure your Venue Server! For more information see http://www.accessgrid.org/ and http://www.mcs.anl.gov/fl/research/accessgrid.""")

    def __init__(self, hostEnvironment = None, configFile=None):
        """
        The constructor creates a new Venue Server object, initializes
        that object, then registers signal handlers so the venue can cleanly
        shutdown in the event of catastrophic signals.

        **Arguments:**
        - *hostingEnvironment* a reference to the hosting environment.
        - *configFile* the filename of a configuration file for this venue server.

        """
        # Pointer to external world
        self.servicePtr = Service.instance()
        
        # Initialize the Usage log file.
        userConfig = UserConfig.instance()
        usage_fname = os.path.join(userConfig.GetLogDir(), "ServerUsage.csv")
        usage_hdlr = Log.FileHandler(usage_fname)
        usage_hdlr.setFormatter(Log.GetUsageFormatter())

        # This handler will only handle the Usage logger.
        Log.HandleLoggers(usage_hdlr, [Log.Usage])

        # Initialize Auth stuff
        AuthorizationMixIn.__init__(self)
        self.AddRequiredRole(Role.Role("Administrators"))
        rl = self.GetRequiredRoles()
        self.authManager.AddRoles(rl)

        # Get the silly default subject this really should be fixed
        certMgr = self.servicePtr.GetCertificateManager()
        admins = self.authManager.FindRole("Administrators")
        admins.AddSubject(self.servicePtr.GetDefaultSubject())
        admins.SetRequireDefault(1)

        # In the venueserver we default to admins
        self.authManager.SetDefaultRoles([admins])
        
        # Initialize our state
        self.checkpointing = 0
        self.persistenceFilename = 'VenueServer.dat'
        self.houseKeeperFrequency = 30
        self.venuePathPrefix = 'Venues'
        self.defaultVenue = ''
        self.multicastAddressAllocator = MulticastAddressAllocator()
        self.hostname = SystemConfig.instance().GetHostname()
        self.venues = {}
        self.services = []
        self.configFile = configFile
        self.dataStorageLocation = None
        self.dataPort = 0
        self.eventPort = 0
        self.textPort = 0
        self.simpleLock = ServerLock("VenueServer")
        
        # If we haven't been given a hosting environment, make one
        if hostEnvironment != None:
            self.hostingEnvironment = hostEnvironment
            self.internalHostingEnvironment = 0 # False
        else:
            defaultPort = 8000
            if self.servicePtr.GetOption("insecure"):
                self.hostingEnvironment = InsecureServer((self.hostname, defaultPort) )
            else:
                self.hostingEnvironment = SecureServer((self.hostname, defaultPort) )
            self.internalHostingEnvironment = 1 # True

        # Figure out which configuration file to use for the
        # server configuration. If no configuration file was specified
        # look for a configuration file named VenueServer.cfg
        if self.configFile == None:
            classpath = string.split(str(self.__class__), '.')
            self.configFile = classpath[-1]+'.cfg'

        adminRole = self.authManager.FindRole('Administrators')

        # Read in and process a configuration
        self.InitFromFile(LoadConfig(self.configFile, self.configDefaults))

        # Initialize the multicast address allocator
        self.multicastAddressAllocator.SetAllocationMethod(self.addressAllocationMethod)
        self.multicastAddressAllocator.SetBaseAddress(self.baseAddress)
        self.addressMask = int(self.addressMask)
        self.multicastAddressAllocator.SetAddressMask(self.addressMask)

        #
        # Data Store Initialization -- This should hopefully move
        # to a different place when the data stores are started independently
        # of the venue server...
        #

        # Check for and if necessary create the data store directory
        if not os.path.exists(self.dataStorageLocation):
            try:
                os.mkdir(self.dataStorageLocation)
            except OSError:
                log.exception("Could not create VenueServer Data Store.")
                self.dataStorageLocation = None

        # Start Venue Server wide services
        if self.servicePtr.GetOption("insecure"):
            self.dataTransferServer = HTTPTransferServer(('',
                                                         int(self.dataPort)) )
        else:
            self.dataTransferServer = GSIHTTPTransferServer(('',
                                                         int(self.dataPort)),
                                                        numThreads = 4,
                                                        sslCompat = 0)
        self.dataTransferServer.run()
        # End of Data Store Initialization


        # 
        # Starting Venue Server wide Services, these *could* also
        # be separated, we just have to figure out the mechanics and
        # make sure the usability doesn't plummet for administrators.
        #
        self.eventService = EventService((self.hostname, int(self.eventPort)))
        self.eventService.start()

        self.textService = TextService((self.hostname, int(self.textPort)))
        self.textService.start()

        # Try to open the persistent store for Venues. If we fail, we
        # open a an empty store, ready to be loaded.
        try:
            self.LoadPersistentVenues(self.persistenceFilename)
        except VenueServerException, ve:
            log.exception(ve)
            self.venues = {}
            self.defaultVenue = ''

        # Reinitialize the default venue
        log.debug("CFG: Default Venue: %s", self.defaultVenue)
        if self.defaultVenue != '' and self.defaultVenue in self.venues.keys():
            log.debug("Setting default venue.")
            self.SetDefaultVenue(self.defaultVenue)
        else:
            log.debug("Creating default venue")
            self.defaultVenue = ''
            uri = self.AddVenue(self.defaultVenueDesc)
            v = self.hostingEnvironment.FindObjectForURL(uri)
        # End of Loading of Venues from persistence
        
        # The houseKeeper is a task that is doing garbage collection and
        # other general housekeeping tasks for the Venue Server.
        self.houseKeeper = Scheduler()
        self.houseKeeper.AddTask(self.Checkpoint,
                                 int(self.houseKeeperFrequency), 0)

        self.houseKeeper.AddTask(self.CleanupVenueClients, 10)

        self.houseKeeper.StartAllTasks()

        # End of Services starting

        # Create the interface
        vsi = VenueServerI(self)
        
        # Get all the methodactions
        ma = vsi._GetMethodActions()
        try:
            self.authManager.AddActions(ma)
        except ActionAlreadyPresent:
            # Do not add action if it is already present.
            pass

        # Default to giving administrators access to all actions.
        adminRole = self.authManager.FindRole('Administrators')
        if adminRole == None:
            raise "AdminRoleNotFound"
        allActions = self.authManager.GetActions()
        for action in allActions:
            if not action.HasRole(adminRole):
                action.AddRole(adminRole)
            
        # Then we create the VenueServer service
        self.hostingEnvironment.RegisterObject(vsi, path='/VenueServer')

        # Then we create an authorization interface and serve it
        self.hostingEnvironment.RegisterObject(
                                  AuthorizationManagerI(self.authManager),
                                  path='/VenueServer/Authorization')

        
        
        # Some simple output to advertise the location of the service
        print("Server: %s \nEvent Port: %d Text Port: %d Data Port: %d" %
              ( self.hostingEnvironment.GetURLBase(), int(self.eventPort),
                int(self.textPort), int(self.dataPort) ) )

    def LoadPersistentVenues(self, filename):
        """This method loads venues from a persistent store.

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

                # We can't persist crlf or cr or lf, so we replace them
                # on each end (when storing and loading)
                desc = cp.get(sec, 'description')
                desc = re.sub("<CRLF>", "\r\n", desc)
                desc = re.sub("<CR>", "\r", desc)
                desc = re.sub("<LF>", "\n", desc)

                name = cp.get(sec, 'name')
                oid = sec
                venueEncryptMedia = cp.getint(sec, 'encryptMedia')
                if venueEncryptMedia:
                    venueEncryptionKey = cp.get(sec, 'encryptionKey')
                else:
                    venueEncryptionKey = None
                cleanupTime = cp.getint(sec, 'cleanupTime')

                # Deal with connections if there are any
                cl = list()
                try:
                    connections = cp.get(sec, 'connections')
                except ConfigParser.NoOptionError:
                    connections = ""

                for c in string.split(connections, ':'):
                    if c:
                        uri = self.MakeVenueURL(IdFromURL(cp.get(c, 'uri')))
                        cd = ConnectionDescription(cp.get(c, 'name'),
                                                   cp.get(c, 'description'),
                                                   uri)
                        cl.append(cd)


                # Deal with streams if there are any
                sl = list()
                try:
                    streams = cp.get(sec, 'streams')
                except ConfigParser.NoOptionError:
                    streams = ""

                for s in string.split(streams, ':'):
                    if s:
                        name = cp.get(s, 'name')
                        encryptionFlag = cp.getint(s, 'encryptionFlag')
                    
                        if encryptionFlag:
                            encryptionKey = cp.get(s, 'encryptionKey')
                        else:
                            encryptionKey = None

                        if encryptionFlag != venueEncryptMedia:
                            log.info("static stream\"" + name +
                        "\"encryption did not match its venue.  Setting it.")
                            encryptionFlag = venueEncryptMedia
                            if encryptionKey != venueEncryptionKey:
                                log.info("static stream\"" + name +
                     "\"encryption key did not match its venue.  Setting it.")
                                encryptionKey = venueEncryptionKey

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
                                               encryptionFlag,
                                               encryptionKey, 1)
                        sl.append(sd)

                # do the real work
                vd = VenueDescription(name, desc, (venueEncryptMedia, venueEncryptionKey),
                                      cl, sl, oid)
                uri = self.AddVenue(vd)
                vif = self.hostingEnvironment.FindObjectForURL(uri)
                v = vif.impl
                v.cleanupTime = cleanupTime
                
                # Deal with apps if there are any
                try:
                    appList = cp.get(sec, 'applications')
                except ConfigParser.NoOptionError:
                    appList = ""

                if len(appList) != 0:
                    for oid in string.split(appList, ':'):
                        name = cp.get(oid, 'name')
                        description = cp.get(oid, 'description')
                        mimeType = cp.get(oid, 'mimeType')

                        appDesc = v.CreateApplication(name, description,
                                                      mimeType, oid)
                        appImpl = v.applications[appDesc.id]

                        for o in cp.options(oid):
                            if o != 'name' and o != 'description' and \
                               o != 'id' and o != 'uri' and o != mimeType:
                                value = cp.get(oid, o)
                                appImpl.app_data[o] = value
                else:
                    log.debug("No applications to load for Venue %s", sec)

                # Deal with services if there are any
                try:
                    serviceList = cp.get(sec, 'services')
                except ConfigParser.NoOptionError:
                    serviceList = ""

                for oid in serviceList.split(':'):
                    if oid:
                        name = cp.get(oid, 'name')
                        description = cp.get(oid, 'description')
                        mimeType = cp.get(oid, 'mimeType')
                        uri = cp.get(oid, 'uri')
                    
                        v.AddService(ServiceDescription(name, description, uri,
                                                        mimeType))

                # Deal with authorization
                try:
                    authPolicy =  cp.get(sec, 'authorizationPolicy')

                    # We can't persist crlf or cr or lf, so we replace them
                    # on each end (when storing and loading)
                    authPolicy  = re.sub("<CRLF>", "\r\n", authPolicy )
                    authPolicy  = re.sub("<CR>", "\r", authPolicy )
                    authPolicy  = re.sub("<LF>", "\n", authPolicy )

                    v.ImportAuthorizationPolicy(authPolicy)
                except ConfigParser.NoOptionError, e:
                    log.warn(e)
                    authPolicy = ''

                

    def InitFromFile(self, config):
        """
        """
        self.config = config
        for k in config.keys():
            (section, option) = string.split(k, '.')
          
            if option == "authorizationPolicy":
                if len(config[k]) > 0:
                    self.authManager.ImportPolicy(config[k])
            
            elif option == "administrators":
                adminList = string.split(config[k],':')
                for a in adminList:
                    if a != "":
                        xs = X509Subject.CreateSubjectFromString(a)
                        admins = self.authManager.FindRole("Administrators")
                        if not admins.HasSubject(xs):
                            admins.AddSubject(xs)
                        admins.SetRequireDefault(1)
                                    
            else:
                setattr(self, option, config[k])

    def MakeVenueURL(self, uniqueId):
        """
        Helper method to make a venue URI from a uniqueId.
        """
        url_base = self.hostingEnvironment.GetURLBase()
        uri = string.join([url_base, self.venuePathPrefix, uniqueId], '/')
        return uri

    def CleanupVenueClients(self):
        for venue in self.venues.values():
            venue.CleanupClients()

    def Shutdown(self):
        """
        Shutdown shuts down the server.
        """
        log.info("Starting Shutdown!")

        # BEGIN Critical Section
        self.simpleLock.acquire()
        
        for v in self.venues.values():
            v.Shutdown()

        self.houseKeeper.StopAllTasks()

        # END Critical Section
        self.simpleLock.release()

        log.info("Shutdown -> Checkpointing...")
        self.Checkpoint()
        log.info("                            done")

        # BEGIN Critical Section
        self.simpleLock.acquire()
        
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

        # END Critical Section
        self.simpleLock.release()
        
    def Checkpoint(self):
        """
        Checkpoint stores the current state of the running VenueServer to
        non-volatile storage. In the event of catastrophic failure, the
        non-volatile storage can be used to restart the VenueServer.

        The fequency at which Checkpointing is done will bound the amount of
        state that is lost (the longer the time between checkpoints, the more
        that can be lost).
        """
        
        # Don't checkpoint if we are already
        if not self.checkpointing:
            self.checkpointing = 1
        else:
            self.checkpointing = 0
            return
        
        # Grab a copy of the venues to dump
        # This is a critical section so we lock around it
        self.simpleLock.acquire()
        venuesToDump = self.venues.copy()
        self.simpleLock.release()

        # Before we backup we copy the previous backup to a safe place
        # We only do this once, ie, if the file exists, we don't copy
        # over it.
        if os.path.isfile(self.persistenceFilename):
            nfn = self.persistenceFilename + '.bak'
            if not os.path.exists(nfn):
                try:
                    os.rename(self.persistenceFilename, nfn)
                except OSError:
                    log.exception("Couldn't rename backup file.")
                    return 0

        # Open the persistent store
        store = file(self.persistenceFilename, "w")

        try:
                       
            for venuePath in venuesToDump.keys():
                # Change out the uri for storage,
                # we don't bother to store the path since this is
                # a copy of the real list we're going to dump anyway
                venueUri = venuesToDump[venuePath].uri
                venuesToDump[venuePath].uri = venuePath

                try:            
                    # Store the venue.
                    store.write(venuesToDump[venuePath].AsINIBlock())
                except:
                    self.simpleLock.release()
                    log.exception("Exception Storing Venue!")
                    venuesToDump[venuePath].uri = venueUri
                    return 0

                venuesToDump[venuePath].uri = venueUri
                venuesToDump[venuePath].dataStore.StorePersistentData()

            # Close the persistent store
            store.close()
        except:
            store.close()
            log.exception("Exception Checkpointing!")
            return 0

        log.info("Checkpointing completed at %s.", time.asctime())

        # Get authorization policy.
        if self.authManager:
            self.config["VenueServer.authorizationPolicy"] = self.authManager.ExportPolicy()

        # Finally we save the current config
        SaveConfig(self.configFile, self.config)

        return 1

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
                      self.dataStorageLocation, venueDesc.id )

        # Make sure new venue knows about server's external role manager.
        venue.SetEncryptMedia(venueDesc.encryptMedia, venueDesc.encryptionKey)

        # Add Connections if there are any
        venue.SetConnections(venueDesc.connections)

        # Add Streams if there are any
        for sd in venueDesc.streams:
            sd.encryptionFlag = venue.encryptMedia
            sd.encryptionKey = venue.encryptionKey
            venue.streamList.AddStream(sd)

        # BEGIN Critical Section
        self.simpleLock.acquire()

        # Add the venue to the list of venues

        oid = venue.GetId()
        self.venues[oid] = venue

        # Create an interface
        vi = VenueI(venue)
        
        # Get method actions
        venue.authManager.AddActions(vi._GetMethodActions())
        venue.authManager.AddRoles(venue.GetRequiredRoles())
        venue._AddDefaultRolesToActions()

        # Default to giving administrators access to all venue actions.
        venueAdminRole = venue.authManager.FindRole("Administrators")
        venueActions = venue.authManager.GetActions()
        for action in venueActions:
            action.AddRole(venueAdminRole)
        
        # We have to register this venue as a new service.
        if(self.hostingEnvironment != None):
            self.hostingEnvironment.RegisterObject(vi,
                                                   path=PathFromURL(venue.uri))
            self.hostingEnvironment.RegisterObject(AuthorizationManagerI(venue.authManager),
                                                   path=PathFromURL(venue.uri)+"/Authorization")

        # END Critical Section
        self.simpleLock.release()
        
        # If this is the first venue, set it as the default venue
        if len(self.venues) == 1 and self.defaultVenue == '':
            self.SetDefaultVenue(oid)

        a = venue.authManager.GetActions()
        
        # return the URL to the new venue
        return venue.uri

    def ModifyVenue(self, oid, venueDesc):   
        """   
        ModifyVenue updates a Venue Description.   
        """
        venue = self.venues[oid]

        # BEGIN Critical Section
        self.simpleLock.acquire()

        venue.name = venueDesc.name
        venue.description = venueDesc.description
        venue.uri = venueDesc.uri
        venue.SetEncryptMedia(venueDesc.encryptMedia,
                              venueDesc.encryptionKey)

        venue.SetConnections(venueDesc.connections)

        current_streams = venue.GetStaticStreams()    
        for sd in current_streams:
            venue.RemoveStream(sd)

        for sd in venueDesc.streams:
            sd.encryptionFlag = venue.encryptMedia
            sd.encryptionKey = venue.encryptionKey
            venue.AddStream(sd)

        self.venues[oid] = venue
        
        # END Critical Section
        self.simpleLock.release()
        
    def RemoveVenue(self, oid):
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

        log.debug("RemoveVenue: id = %s", oid)

        # Get the venue object
        try:
            venue = self.venues[oid]
        except KeyError:
            log.exception("RemoveVenue: Venue not found.")
            raise VenueNotFound

        # Stop the web service interface
        try:
            self.simpleLock.acquire()
            self.hostingEnvironment.UnregisterObject(venue)
            self.simpleLock.release()
        except Exception, e:
            self.simpleLock.release()
            log.exception(e)
            raise UnbindVenueError
        except:
            self.simpleLock.release()
            log.exception("RemoveVenue: Couldn't unbind venue.")
            raise UnbindVenueError

        # Shutdown the venue
        venue.Shutdown()

        # Clean it out of the venueserver
        del self.venues[oid]

        # Checkpoint so we don't save it again
        self.Checkpoint()

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
            vdl =  map(lambda venue: venue.AsVenueDescription(),
                       self.venues.values())
            return vdl
        except:
            log.exception("GetVenues: GetVenues failed!")
            raise VenueServerException("GetVenues Failed!")

    def GetDefaultVenue(self):
        """
        GetDefaultVenue returns the URL to the default Venue on the
        VenueServer.
        """
        return self.MakeVenueURL(self.defaultVenue)

    def SetDefaultVenue(self, oid):
        """
        SetDefaultVenue sets which Venue is the default venue for the
        VenueServer.
        """
        log.info("Setting default venue; oid=%s",oid)
        defaultPath = "/Venues/default"
        defaultAuthPath = defaultPath+"/Authorization"
        self.defaultVenue = oid

        # BEGIN Critical Section
        self.simpleLock.acquire()

        # Unregister the previous default venue
        ovi = self.hostingEnvironment.FindObjectForPath(defaultPath)
        ovia = self.hostingEnvironment.FindObjectForPath(defaultAuthPath)
        if ovi != None:
            self.hostingEnvironment.UnregisterObject(ovi, path=defaultPath)
        # handle authorization too
        if ovia != None:
            self.hostingEnvironment.UnregisterObject(ovia, path=defaultAuthPath)
            
        # Setup the new default venue
        self.config["VenueServer.defaultVenue"] = oid
        u,vi = self.hostingEnvironment.FindObject(self.venues[oid])
        vaurl = self.MakeVenueURL(oid)+"/Authorization"
        vai = self.hostingEnvironment.FindObjectForURL(vaurl)
        self.hostingEnvironment.RegisterObject(vi, path=defaultPath)
        self.hostingEnvironment.RegisterObject(vai, path=defaultAuthPath)

        # END Critical Section
        self.simpleLock.release()

    def SetStorageLocation(self,  dataStorageLocation):
        """
        Set the path for data storage
        """
        # BEGIN Critical Section
        self.simpleLock.acquire()

        self.dataStorageLocation = dataStorageLocation
        self.config["VenueServer.dataStorageLocation"] = dataStorageLocation

        # END Critical Section
        self.simpleLock.release()

    def GetStorageLocation(self):
        """
        Get the path for data storage
        """
        return self.dataStorageLocation

    def SetEncryptAllMedia(self, value):
        """
        Turn on or off server wide default for venue media encryption.
        """
        # BEGIN Critical Section
        self.simpleLock.acquire()

        self.encryptAllMedia = int(value)
        self.config["VenueServer.encryptAllMedia"] = value

        # END Critical Section
        self.simpleLock.release()

        return self.encryptAllMedia

    def GetEncryptAllMedia(self):
        """
        Get the server wide default for venue media encryption.
        """
        return int(self.encryptAllMedia)

    def RegenerateEncryptionKeys(self):
        """
        This regenerates all the encryptions keys in all the venues.
        """
        for v in self.venues:
            v.RegenerateEncryptionKeys()
            
    def SetBackupServer(self, server):
        """
        Turn on or off server wide default for venue media encryption.
        """
        # BEGIN Critical Section
        self.simpleLock.acquire()

        self.backupServer = server
        self.config["backupServer"] = server

        # END Critical Section
        self.simpleLock.release()

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
        # BEGIN Critical Section
        self.simpleLock.acquire()

        self.addressAllocationMethod = addressAllocationMethod
        self.multicastAddressAllocator.SetAllocationMethod(
            addressAllocationMethod )
        self.config["VenueServer.addressAllocationMethod"] = addressAllocationMethod

        # END Critical Section
        self.simpleLock.release()

    def GetAddressAllocationMethod(self):
        """
        Get the method used for multicast address allocation:
            either RANDOM or INTERVAL (defined in MulticastAddressAllocator)
        """
        return self.multicastAddressAllocator.GetAllocationMethod()

    def SetBaseAddress(self, address):
        """
        Set base address used when allocating multicast addresses in
        an interval
        """
        # BEGIN Critical Section
        self.simpleLock.acquire()

        self.baseAddress = address
        self.multicastAddressAllocator.SetBaseAddress( address )
        self.config["VenueServer.baseAddress"] = address

        # END Critical Section
        self.simpleLock.release()

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
        # BEGIN Critical Section
        self.simpleLock.acquire()

        self.addressMask = mask
        self.multicastAddressAllocator.SetAddressMask( mask )
        self.config["VenueServer.addressMask"] = mask

        # END Critical Section
        self.simpleLock.release()

    def GetAddressMask(self):
        """
        Get address mask used when allocating multicast addresses in
        an interval
        """
        return self.multicastAddressAllocator.GetAddressMask( )

class VenueServerI(SOAPInterface, AuthorizationIMixIn):
    """
    This is the SOAP interface to the venue server.
    """
    def __init__(self, impl):
        SOAPInterface.__init__(self, impl)

    def _authorize(self, *args, **kw):
        """
        The authorization callback. We should be able to implement this
        just once and remove a bunch of the older code.
        """
        if self.impl.servicePtr.GetOption("insecure"):
            return 1

        subject, action = self._GetContext()
        
        log.info("Authorizing action: %s for subject %s", action.name,
                 subject.name)

        authManager = self.impl.authManager
        
        return authManager.IsAuthorized(subject, action)

    def Shutdown(self, secondsFromNow):
        """
        Interface to shutdown the Venue Server.

        **Arguments:**
            *secondsFromNow* How long from the time the call is
            received until the server starts to shutdown.
        **Raises:**
        **Returns:**
        """
        log.debug("Calling Shutdown with seconds %d" % secondsFromNow)

        self.impl.Shutdown()

        log.debug("Shutdown complete.")

    def Checkpoint(self):
        """
        Interface to checkpoint the Venue Server.

        **Arguments:**
        **Raises:**
        **Returns:**
        """
        log.debug("Calling checkpoint")

        self.impl.Checkpoint()

        log.debug("Checkpoint complete.")
        
    def AddVenue(self, venueDescStruct):
        """
        Inteface call for Adding a venue.

        **Arguments:**

            *Venue Description Struct* A description of the new
            venue, currently an anonymous struct.

        **Raises:**
            *VenueServerException* When the venue description struct
            isn't successfully converted to a real venue description
            object and the venue isn't added.

        **Returns:**
            *Venue URI* Upon success a uri to the new venue is returned.
        """
        # Deserialize
        venueDesc = CreateVenueDescription(venueDescStruct)

        # The id should be server assigned.
        venueDesc.id = None

        # do the call
        try:
            venueUri = self.impl.AddVenue(venueDesc)
            return venueUri
        except:
            log.exception("AddVenue: exception")
            raise

    def ModifyVenue(self, URL, venueDescStruct):
        """
        Interface for modifying an existing Venue.

        **Arguments:**
            *URL* The URL to the venue.

            *Venue Description Struct* An anonymous struct that is the
            new venue description.

        **Raises:**
            *InvalideVenueURL* When the URL isn't a valid venue.

            *InvalidVenueDescription* If the Venue Description has a
            different URL than the URL argument passed in.

        """
        # Check for argument
        if URL == None:
            raise InvalidVenueURL

        # pull info out of the url
        oid = IdFromURL(URL)

        # Create a venue description
        vd = CreateVenueDescription(venueDescStruct)
        
        # Make sure it's valid
        if vd.uri != URL:
            raise InvalidVenueDescription

        # Lock and do the call
        try:
            self.impl.ModifyVenue(oid, vd)
        except:
            log.exception("ModifyVenue: exception")
            raise

    def RemoveVenue(self, URL):
        """
        Interface for removing a Venue.

        **Arguments:**
            *URL* The url to the venue to be removed.
        """
        oid = IdFromURL(URL)

        try:
            self.impl.RemoveVenue(oid)
        except:
            log.exception("RemoveVenue: exception")
            raise

    def GetVenues(self):
        """
        This is the interface to get a list of Venues from the Venue Server.

        **Returns:**
            *venue description list* A list of venues descriptions.
        """
        try:
            vdl = self.impl.GetVenues()
            return vdl
        except:
            log.exception("GetVenues: exception")
            raise

    def GetDefaultVenue(self):
        """
        Interface for getting the URL to the default venue.
        """
        try:
            returnURL = self.impl.GetDefaultVenue()
            return returnURL
        except:
            log.exception("GetDefaultVenues: exception")
            raise

    def SetDefaultVenue(self, URL):
        """
        Interface to set default venue.

        **Arguments:**
            *URL* The URL to the default venue.

        **Raises:**

        **Returns:**
            *URL* the url of the default venue upon success.
        """
        try:
            oid = IdFromURL(URL)
            self.impl.SetDefaultVenue(oid)

            return URL
        except:
            log.exception("SetDefaultVenue: exception")
            raise

    def AddAdministrator(self, string):
        """
        LEGACY CALL: This is replace by GetAuthorizationManager.

        Interface to add an administrator to the Venue Server.
        
        **Arguments:**
        
        *string* The DN of the new administrator.
        
        **Raises:**
        
        **Returns:**
        
        *string* The DN of the administrator added.
        """
        try:
            xs = X509Subject.CreateSubjectFromString(string)
            admins = self.impl.authManager.FindRole("Administrators")
            admins.AddSubject(xs)
            return xs
        except:
            log.exception("AddAdministrator: exception")
            raise
        
    def RemoveAdministrator(self, string):
        """
        LEGACY CALL: This is replace by GetAuthorizationManager.

        **Arguments:**
        
        *string* The Distinguished Name (DN) of the administrator
        being removed.
        
        **Raises:**
        
        **Returns:**
        
        *string* The Distinguished Name (DN) of the administrator removed.
        """
        try:
            xs = X509Subject.CreateSubjectFromString(string)
            admins = self.impl.authManager.FindRole("Administrators")
            admins.RemoveSubject(xs)
        except:
            log.exception("RemoveAdministrator: exception")
            raise
        
    def GetAdministrators(self):
        """
        LEGACY CALL: This is replace by GetAuthorizationManager.

        GetAdministrators returns a list of adminisitrators for this
        VenueServer.
        """
        try:
            adminRole = self.impl.authManager.FindRole("Administrators")
            subjs = self.impl.authManager.GetSubjects(role=adminRole)
            return subjs
        except:
            log.exception("GetAdministrators: exception")
            raise

    def SetStorageLocation(self, location):
        """
        Interface for setting the location of the data store.

        **Arguments:**


            *location* This is a path for the data store.

        **Raises:**
        **Returns:**
            *location* The new location on success.
        """
        try:
            self.impl.SetStorageLocation(location)
        except:
            log.exception("SetStorageLocation: exception")
            raise

    def GetStorageLocation(self):
        """
        Inteface for getting the current data store path.

        **Arguments:**
        **Raises:**
        **Returns:**
            *location* The path to the data store location.
        """
        try:
            returnString = self.impl.GetStorageLocation()
            return returnString
        except:
            log.exception("GetStorageLocation: exception")
            raise

    def SetAddressAllocationMethod(self, method):
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
        try:
            self.impl.SetAddressAllocationMethod(method)
        except:
            log.exception("SetAddressAllocationMethod: exception")
            raise

    def GetAddressAllocationMethod(self):
        """
        Interface for getting the Address Allocation Method.

        **Arguments:**
        **Raises:**
        **Returns:**
            *method* The address allocation method configured, either
            RANDOM or INTERVAL.
        """
        try:
            returnValue = self.impl.GetAddressAllocationMethod()

            return returnValue
        except:
            log.exception("GetAddressAllocationMethod: exception")
            raise
    
    def SetEncryptAllMedia(self, value):
        """
        Interface for setting the flag to encrypt all media or turn it off.

        **Arguments:**
            *value* The flag, 1 turns encryption on, 0 turns encryption off.
        **Raises:**
        **Returns:**
            *flag* the return value from SetEncryptAllMedia.
        """
        try:
            returnValue = self.impl.SetEncryptAllMedia(value)

            return returnValue
        except:
            log.exception("SetEncryptAllMedia: exception")
            raise
    
    def GetEncryptAllMedia(self):
        """
        Interface to retrieve the value of the media encryption flag.

        **Arguments:**
        **Raises:**
        **Returns:**
        """
        try:
            returnValue = self.impl.GetEncryptAllMedia()

            return returnValue
        except:
            log.exception("GetEncryptAllMedia: exception")
            raise

    def RegenerateEcryptionKeys(self):
        """
        Interface method to regenerate all encryption keys for all
        venues on this server.
        """
        try:
            self.impl.RegenerateEncryptionKeys()
        except Exception, e:
            log.exception("Failed to regenerate all encryption keys.")
            raise
            
    def SetBackupServer(self, server):
        """
        Interface for setting a fallback venue server.

        **Arguments:**
            *server* The string hostname of the server.
        **Raises:**
        **Returns:**
            *server* the return value from SetBackupServer
        """
        try:
            returnValue = self.impl.SetBackupServer(server)

            return returnValue
        except:
            log.exception("SetBackupServer: exception")
            raise
    
    def GetBackupServer(self):
        """
        Interface to retrieve the value of the backup server name.

        **Arguments:**
        **Raises:**
        **Returns:**
            the string hostname of the back up server or "".
        """
        try:
            returnValue = self.impl.GetBackupServer()

            return returnValue
        except:
            log.exception("GetBackupServer: exception")
            raise

    def SetBaseAddress(self, address):
        """
        Interface for setting the base address for the allocation pool.

        **Arguments:**
            *address* The base address of the address pool to allocate from.
        **Raises:**
        **Returns:**
        """
        try:
            self.impl.SetBaseAddress(address)
        except:
            log.exception("SetBaseAddress: exception")
            raise

    def GetBaseAddress(self):
        """
        Interface to retrieve the base address for the address allocation pool.

        **Arguments:**
        **Raises:**
        **Returns:**
            *base address* the base address of the address allocation pool.
        """
        try:
            returnValue = self.impl.GetBaseAddress()

            return returnValue
        except:
            log.exception("GetBaseAddress: exception")
            raise

    def SetAddressMask(self, mask):
        """
        Interface to set the network mask of the address allocation pool.

        **Arguments:**
            *mask*  The network mask for the address allocation pool.
        **Raises:**
        **Returns:**
        """
        try:
            self.impl.SetAddressMask(mask)

            return mask
        except:
            log.exception("SetAddressMask: exception")
            raise

    def GetAddressMask(self):
        """
        Interface to retrieve the address mask of the address allocation pool.

        **Arguments:**
        **Raises:**
        **Returns:**
            *mask* the network mask of the address allocation pool.
        """

        try:
            returnValue = self.impl.GetAddressMask()

            return returnValue
        except:
            log.exception("GetAddressMask: exception")
            raise

class VenueServerIW(SOAPIWrapper, AuthorizationIWMixIn):
    """
    """
    def __init__(self, url=None):
        SOAPIWrapper.__init__(self, url)

    def Shutdown(self, secondsFromNow):
        return self.proxy.Shutdown(secondsFromNow)

    def Checkpoint(self):
        return self.proxy.Checkpoint()

    def AddVenue(self, venueDescription):
        return self.proxy.AddVenue(venueDescription)

    def ModifyVenue(self, url, venueDescription):
        if url == None:
            raise InvalidURL

        if venueDescription == None:
            raise InvalidVenueDescription

        return self.proxy.ModifyVenue(url, venueDescription)

    def RemoveVenue(self, url):
        return self.proxy.RemoveVenue(url)

    def GetVenues(self):
        vl = self.proxy.GetVenues()
        rl = list()
        for v in vl:
            vd = CreateVenueDescription(v)
            vd.SetURI(v.uri)
            rl.append(vd)
        return rl

    def GetDefaultVenue(self):
        return self.proxy.GetDefaultVenue()

    def SetDefaultVenue(self, url):
        return self.proxy.SetDefaultVenue(url)

    def SetStorageLocation(self, location):
        return self.proxy.SetStorageLocation(url)

    def GetStorageLocation(self):
        return self.proxy.GetStorageLocation()

    def SetAddressAllocationMethod(self, method):
        return self.proxy.SetAddressAllocationMethod(method)

    def GetAddressAllocationMethod(self):
        return self.proxy.GetAddressAllocationMethod()

    def SetEncryptAllMedia(self, value):
        return self.proxy.SetEncryptAllMedia(value)

    def GetEncryptAllMedia(self):
        return self.proxy.GetEncryptAllMedia()

    def RegenerateEncryptionKeys(self):
        return self.proxy.RegenerateEncryptionKeys()
    
    def SetBackupServer(self, serverURL):
        return self.proxy.SetBackupServer(serverURL)

    def GetBackupServer(self):
        return self.proxy.GetBackupServer()

    def SetBaseAddress(self, address):
        return self.proxy.SetBaseAddress(address)

    def GetBaseAddress(self):
        return self.proxy.GetBaseAddress()

    def SetAddressMask(self, mask):
        return self.proxy.SetAddressMask(mask)

    def GetAddressMask(self):
        return self.proxy.GetAddressMask()
    
    
