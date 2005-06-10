#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.189 2005-06-10 15:49:40 lefvert Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: VenueServer.py,v 1.189 2005-06-10 15:49:40 lefvert Exp $"


# Standard stuff
import sys
import os
import re
import os.path
import string
import threading
import time
import ConfigParser
import csv

from AccessGrid.Toolkit import Service
from AccessGrid import Log
from AccessGrid import Version
from AccessGrid import hosting
from AccessGrid.hosting import InsecureServer, SecureServer
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.interfaces.VenueServer_interface import VenueServer as VenueServerI
from AccessGrid.interfaces.Venue_interface import Venue as VenueI
from AccessGrid.Security.AuthorizationManager import AuthorizationManager
from AccessGrid.Security.AuthorizationManager import AuthorizationManagerI
from AccessGrid.Security.AuthorizationManager import AuthorizationIMixIn
from AccessGrid.Security.AuthorizationManager import AuthorizationIWMixIn
from AccessGrid.Security.AuthorizationManager import AuthorizationMixIn
from AccessGrid.Security import X509Subject, Role
from AccessGrid.Security .Action import ActionAlreadyPresent
from AccessGrid.Security.Subject import InvalidSubject

from AccessGrid.Platform.Config import SystemConfig, UserConfig

from AccessGrid.Utilities import LoadConfig, SaveConfig
from AccessGrid.hosting import PathFromURL, IdFromURL
from AccessGrid.GUID import GUID
from AccessGrid.Venue import Venue, VenueI
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid.DataStore import HTTPTransferServer
from AccessGrid.scheduler import Scheduler

from AccessGrid.Descriptions import ConnectionDescription, StreamDescription
from AccessGrid.Descriptions import DataDescription, VenueDescription
from AccessGrid.Descriptions import CreateVenueDescription, ServiceDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.NetworkLocation import UnicastNetworkLocation
from AccessGrid.Descriptions import Capability

from AccessGrid.AsyncoreEventService import EventService, VenueServerServiceDescription

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
    """

    configDefaults = {
        "VenueServer.dataPort" : 8006,
        "VenueServer.eventPort" : 8002,
        "VenueServer.textHost" : 'phosphorus.mcs.anl.gov',
        "VenueServer.textPort" : 5223,
        "VenueServer.encryptAllMedia" : 1,
        "VenueServer.houseKeeperFrequency" : 300,
        "VenueServer.persistenceFilename" : 'VenueServer.dat',
        "VenueServer.serverPrefix" : 'VenueServer',
        "VenueServer.venuePathPrefix" : 'Venues',
        "VenueServer.dataStorageLocation" : 'Data',
        "VenueServer.backupServer" : '',
        "VenueServer.addressAllocationMethod" : MulticastAddressAllocator.RANDOM,
        "VenueServer.baseAddress" : MulticastAddressAllocator.SDR_BASE_ADDRESS,
        "VenueServer.addressMask" : MulticastAddressAllocator.SDR_MASK_SIZE,
        "VenueServer.authorizationPolicy" : None,
        "VenueServer.performanceReportFile" : '',
        "VenueServer.performanceReportFrequency" : 0
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
        # Set attributes
        self.dataPort = -1
        self.encryptAllMedia = 1
        self.houseKeeperFrequency = 300
        self.persistenceFilename = "VenueServer.dat"
        self.serverPrefix = "VenueServer"
        self.venuePathPrefix = "Venues"
        self.dataStorageLocation = "Data"
        self.addressAllocationMethod = MulticastAddressAllocator.RANDOM
        self.baseAddress = MulticastAddressAllocator.SDR_BASE_ADDRESS
        self.addressMask = MulticastAddressAllocator.SDR_MASK_SIZE
        self.performanceReportFile = ''
        self.performanceReportFrequency = 0
        self.authorizationPolicy = None
        self.services = dict()
        
        # Basic variable initializations
        self.perfFile = None

        # Pointer to external world
        self.servicePtr = Service.instance()
        
        # Initialize the Usage log file.
        userConfig = UserConfig.instance()
        usage_fname = os.path.join(userConfig.GetLogDir(), "ServerUsage.csv")
        usage_hdlr = Log.FileHandler(usage_fname)
        usage_hdlr.setFormatter(Log.GetUsageFormatter())

        # This handler will only handle the Usage logger.
        Log.HandleLoggers(usage_hdlr, [Log.Usage])

        log.debug("VenueServer initializing authorization manager.")

	# report
	self.report = None

        # Initialize Auth stuff
        AuthorizationMixIn.__init__(self)
        self.AddRequiredRole(Role.Administrators)
        self.AddRequiredRole(Role.Everybody)

        # In the venueserver we default to admins
        self.authManager.SetDefaultRoles([Role.Administrators])

        # Initialize our state
        self.checkpointing = 0
        self.defaultVenue = None
        self.multicastAddressAllocator = MulticastAddressAllocator()
        self.hostname = Service.instance().GetHostname()
        self.venues = {}
        self.configFile = configFile
        self.simpleLock = ServerLock("VenueServer")
        
        # If we haven't been given a hosting environment, make one
        if hostEnvironment != None:
            self.hostingEnvironment = hostEnvironment
            self.internalHostingEnvironment = 0 # False
        else:
            defaultPort = 8000
            if self.servicePtr.GetOption("secure"):
                self.hostingEnvironment = SecureServer((self.hostname,
                                                        defaultPort) )
            else:
                self.hostingEnvironment = InsecureServer((self.hostname,
                                                          defaultPort) )
            self.internalHostingEnvironment = 1 # True

        # Figure out which configuration file to use for the
        # server configuration. If no configuration file was specified
        # look for a configuration file named VenueServer.cfg
        if self.configFile == None:
            classpath = string.split(str(self.__class__), '.')
            self.configFile = classpath[-1]+'.cfg'

        # Read in and process a configuration
        self._InitFromFile(LoadConfig(self.configFile, self.configDefaults))

        # Initialize the multicast address allocator
        self.multicastAddressAllocator.SetAllocationMethod(
           self.addressAllocationMethod)
        self.multicastAddressAllocator.SetBaseAddress(self.baseAddress)
        self.addressMask = int(self.addressMask)
        self.multicastAddressAllocator.SetAddressMask(self.addressMask)

        # Data Store Initialization -- This should hopefully move
        # to a different place when the data stores are started independently
        # of the venue server...

        # Check for and if necessary create the data store directory
        if not os.path.exists(self.dataStorageLocation):
            try:
                os.mkdir(self.dataStorageLocation)
            except OSError:
                log.exception("Could not create VenueServer Data Store.")
                self.dataStorageLocation = None

        # Starting Venue Server wide Services, these *could* also
        # be separated, we just have to figure out the mechanics and
        # make sure the usability doesn't plummet for administrators.
        self.dataTransferServer = HTTPTransferServer(('',
                                                      int(self.dataPort)) )
        self.dataTransferServer.run()

        
        # Add the event service
        self.eventService = EventService("Event Service",
                                         "asyncore based service for distributing events",
                                         str(GUID()), "AsyncoreEvent",
                                         (self.hostname, int(self.eventPort)))
        self.RegisterService(self.eventService.GetDescription())
        self.eventService.start()

        # Register the text service
        textServiceDescription = VenueServerServiceDescription(str(GUID()),
                                                               "Jabber Text Service",
                                                               "Text service based on jabber",
                                                               "JabberText",
                                                               (self.textHost, int(self.textPort)),
                                                               [])
        self.RegisterService(textServiceDescription)
        
        # End of server wide services initialization

        # Try to open the persistent store for Venues. If we fail, we
        # open a an empty store, ready to be loaded.
        try:
            self.LoadPersistentVenues(self.persistenceFilename)
        except VenueServerException, ve:
            log.exception(ve)
            self.venues = {}
            self.defaultVenue = None

        # Reinitialize the default venue
        log.debug("CFG: Default Venue: %s", self.defaultVenue)
        if self.defaultVenue and self.defaultVenue in self.venues.keys():
            log.debug("Setting default venue.")
        else:
            log.debug("Creating default venue")
            uri = self.AddVenue(VenueServer.defaultVenueDesc)
            oid = self.hostingEnvironment.FindObjectForURL(uri).impl.GetId()
            self.defaultVenue = oid

        # this wants an oid not a url
        self.SetDefaultVenue(self.defaultVenue)

        # End of Loading of Venues from persistence
        
        # The houseKeeper is a task that is doing garbage collection and
        # other general housekeeping tasks for the Venue Server.
        self.houseKeeper = Scheduler()
        self.houseKeeper.AddTask(self.Checkpoint,
                                 int(self.houseKeeperFrequency), 
                                 0,
                                 1)
        self.houseKeeper.AddTask(self.CleanupClients, 15, 0, 1)

        # Create report that tracks performance if the option is in the config
        # This should get cleaned out and made a command line option
        if self.performanceReportFile is not None and \
               int(self.performanceReportFrequency) > 0:
            try:
                keys = SystemConfig.instance().PerformanceSnapshot().keys()
                fields = dict()                
                for k in keys:
                    fields[k] = k
                    
                self.perfFile = csv.DictWriter(file(self.performanceReportFile,
                                                    'aU+'), fields,
                                               extrasaction='ignore')

                if not os.stat(self.performanceReportFile).st_size:
                    self.perfFile.writerow(fields)

                self.houseKeeper.AddTask(self.Report,
                                         int(self.performanceReportFrequency))
            except Exception:
                log.exception("Error starting reporting thread.")
                self.perfFile = None
        else:
            log.warn("Performance data configuration incorrect.")

        # Done with the performance report initialization

        # Start all the periodic tasks registered with the housekeeper thread
        self.houseKeeper.StartAllTasks()

        # Create the Web Service interface
        vsi = VenueServerI(impl=self, auth_method_name="authorize")

        if self.authorizationPolicy is None:
           log.info("Creating new authorization policy, non in config.")
           
           if hosting.GetHostingImpl() == "SOAPpy":
               self.authManager.AddActions(vsi._GetMethodActions())
           self.authManager.AddRoles(self.GetRequiredRoles())
           if hosting.GetHostingImpl() == "SOAPpy":
               # Default to giving administrators access to all actions.
               # This is implicitly adding the action too
               for action in vsi._GetMethodActions():
                  self.authManager.AddRoleToAction(action.GetName(),
                                               Role.Administrators.GetName())
            
           # Get authorization policy.
           pol = self.authManager.ExportPolicy()
           pol  = re.sub("\r\n", "<CRLF>", pol )
           pol  = re.sub("\r", "<CR>", pol )
           pol  = re.sub("\n", "<LF>", pol )
           self.config["VenueServer.authorizationPolicy"] = pol

           SaveConfig(self.configFile, self.config)
        else:
           log.debug("Using policy from config file.")

        # Get the silly default subject this really should be fixed
        try:
           subj = self.servicePtr.GetDefaultSubject()
           if subj is not None:
              log.debug("Default Subject: %s", subj.GetName())
              self.authManager.AddSubjectToRole(subj.GetName(),
                                                Role.Administrators.GetName())
        except InvalidSubject:
           log.exception("Invalid Default Subject!")

#        print "Venue Server Policy:"
#        print self.authManager.xml.toprettyxml()
        
        # Then we create the VenueServer service
        venueServerUri = self.hostingEnvironment.RegisterObject(vsi, path='/VenueServer')

        if hosting.GetHostingImpl() == "SOAPpy":
            # Then we create an authorization interface and serve it
            self.hostingEnvironment.RegisterObject(
                                  AuthorizationManagerI(self.authManager),
                                  path='/VenueServer/Authorization')

        

       
        
        
        # Some simple output to advertise the location of the service
        print("Server: %s \nData Port: %d" % ( venueServerUri,
                                               int(self.dataPort) ) )
        print "Default venue url:", self.GetDefaultVenue()

    def _InitFromFile(self, config):
        """
        """
        self.config = config
        for k in config.keys():
            (section, option) = string.split(k, '.')
          
            if option == "authorizationPolicy" and config[k] is not None:
               log.debug("Reading authorization policy.")
               pol = config[k]
               pol  = re.sub("<CRLF>", "\r\n", pol )
               pol  = re.sub("<CR>", "\r", pol )
               pol  = re.sub("<LF>", "\n", pol )
               try:
                  self.authManager.ImportPolicy(pol)
                  setattr(self, option, pol)
               except:
                  log.exception("Invalid authorization policy import")
                  setattr(self, option, config[k])
            elif option == "administrators" and len(config[k]) > 0:
               aName = Role.Administrators.GetName()

               if self.authManager.FindRole(aName) is None:
                  self.authManager.AddRole(Role.Administrators)

               for a in config[k].split(':'):
                  self.authManager.AddSubjectToRole(a, aName)
            else:
                setattr(self, option, config[k])

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

                # Deal with authorization
                try:
                    authPolicy =  cp.get(sec, 'authorizationPolicy')

                    # We can't persist crlf or cr or lf, so we replace them
                    # on each end (when storing and loading)
                    authPolicy  = re.sub("<CRLF>", "\r\n", authPolicy )
                    authPolicy  = re.sub("<CR>", "\r", authPolicy )
                    authPolicy  = re.sub("<LF>", "\n", authPolicy )
                except ConfigParser.NoOptionError, e:
                    log.warn(e)
                    authPolicy = None

                # do the real work
                vd = VenueDescription(name, desc, (venueEncryptMedia,
                                                   venueEncryptionKey),
                                      cl, sl, oid)
                uri = self.AddVenue(vd, authPolicy)
                vif = self.hostingEnvironment.FindObjectForURL(uri)
                v = vif.impl

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

    def MakeVenueURL(self, uniqueId):
        """
        Helper method to make a venue URI from a uniqueId.
        """
        url_base = self.hostingEnvironment.GetURLBase()
        uri = string.join([url_base, self.venuePathPrefix, uniqueId], '/')
        return uri

    def CleanupClients(self):
        for venue in self.venues.values():
            venue.CleanupClients()

    def Report(self):
        data = SystemConfig.instance().PerformanceSnapshot()
        if self.perfFile is not None:
            log.info("Saving Performance Data.")
            self.perfFile.writerow(data)

    def Shutdown(self, secondsFromNow = 0):
        """
        Shutdown shuts down the server.
        """
        #
        # Seconds from now is NOT working!
        #
        log.info("Starting Shutdown!")

        # Shut file
        if self.perfFile is not None:
            self.perfFile.close()
            
        # BEGIN Critical Section
        self.simpleLock.acquire()
             
        try:
            for v in self.venues.values():
                v.Shutdown()

            self.houseKeeper.StopAllTasks()
        except:
            log.exception("Exception shutting down venues")

        # END Critical Section
        self.simpleLock.release()
                 
        log.info("Shutdown -> Checkpointing...")
        self.Checkpoint(0)
        log.info("                            done")
        
        # BEGIN Critical Section
        self.simpleLock.acquire()
        
        # This blocks anymore checkpoints from happening
        log.info("Shutting down services...")

        # Send shutting down event to signal to services
        
        try:
            self.dataTransferServer.stop()
        except IOError, e:
            log.exception("Exception shutting down data service.", e)
        except:
            log.exception("Exception shutting down data service.")

        try:
            self.eventService.shutdown()
        except IOError, e:
            log.exception("Exception shutting down event client.", e)
        except:
            log.exception("Exception shutting down event client.")
        
        try:
            self.hostingEnvironment.Stop()
            del self.hostingEnvironment
        except:
            log.exception("Exception shutting down hosting environment")

        log.info("                              done.")

        log.info("Shutdown Complete.")
        
        # END Critical Section
        self.simpleLock.release()
             
    def Checkpoint(self, secondsFromNow = 0):
        """
        Checkpoint stores the current state of the running VenueServer to
        non-volatile storage. In the event of catastrophic failure, the
        non-volatile storage can be used to restart the VenueServer.

        The fequency at which Checkpointing is done will bound the amount of
        state that is lost (the longer the time between checkpoints, the more
        that can be lost).
        """

        #
        # Seconds from now is NOT working!
        #

        # Don't checkpoint if we are already
        if not self.checkpointing:
            self.checkpointing = 1
	    log.info("Checkpoint starting at: %s", time.asctime())
        else:
            return
        
        # Open the persistent store
        store = file(self.persistenceFilename, "w")
        store.write("# AGTk %s\n" % (Version.GetVersion()))

        try:
                       
            for venuePath in self.venues.keys():
                # Change out the uri for storage,
                # we don't bother to store the path since this is
                # a copy of the real list we're going to dump anyway

                try:            
		    self.simpleLock.acquire()
                    store.write(self.venues[venuePath].AsINIBlock())
		    self.simpleLock.release()
                except:
		    self.simpleLock.release()
                    log.exception("Exception Storing Venue!")
                    return 0

            # Close the persistent store
            store.close()
        except:
            store.close()
            log.exception("Exception Checkpointing!")
            return 0

        log.info("Checkpointing completed at: %s", time.asctime())

        # Get authorization policy.
        pol = self.authManager.ExportPolicy()
        pol  = re.sub("\r\n", "<CRLF>", pol )
        pol  = re.sub("\r", "<CR>", pol )
        pol  = re.sub("\n", "<LF>", pol )
        self.config["VenueServer.authorizationPolicy"] = pol
        
        # Finally we save the current config
        SaveConfig(self.configFile, self.config)

        self.checkpointing = 0

        return 1

    def AddVenue(self, venueDesc, authPolicy = None):
        """
        The AddVenue method takes a venue description and creates a new
        Venue Object, then makes it available from this Venue Server.
        """
        # Create a new Venue object pass it the server
        # Usually the venueDesc will not have Role information 
        #   and defaults will be used.

        venue = Venue(self, venueDesc.name, venueDesc.description,
                      self.dataStorageLocation, venueDesc.id )

        # create an event channel for this venue.
        # channel id is the same as venue id.
        self.eventService.CreateChannel(venue.GetId())
        self.UpdateService(self.eventService.GetDescription())

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

        try:
            
            # Add the venue to the list of venues
            oid = venue.GetId()
            self.venues[oid] = venue
            
            # Create an interface
            vi = VenueI(impl=venue, auth_method_name="authorize")
            
            if authPolicy is not None:
                venue.ImportAuthorizationPolicy(authPolicy)
            else:
                # This is a new venue, not from persistence,
                # so we have to create the policy
                log.info("Creating new auth policy for the venue.")
            
                # Get method actions
                if hosting.GetHostingImpl() == "SOAPpy":
                    venue.authManager.AddActions(vi._GetMethodActions())
                venue.authManager.AddRoles(venue.GetRequiredRoles())
                venue.authManager.AddRoles(venue.authManager.GetDefaultRoles())
                venue._AddDefaultRolesToActions()

                # Default to giving administrators access to all venue actions.
                for action in venue.authManager.GetActions():
                    venue.authManager.AddRoleToAction(action.GetName(),
                                                      Role.Administrators.GetName())
        
            # This could be done by the server, and probably should be
            subj = self.servicePtr.GetDefaultSubject()
        
            if subj is not None:
                venue.authManager.AddSubjectToRole(subj.GetName(),
                                                       Role.Administrators.GetName())
        
            #        print "Venue Policy:"
            #        print venue.authManager.xml.toprettyxml()
            
            # Set parent auth mgr to server so administrators cascades?
            venue.authManager.SetParent(self.authManager)
            
            # We have to register this venue as a new service.
            if(self.hostingEnvironment != None):
                self.hostingEnvironment.RegisterObject(vi,
                                                       path=PathFromURL(venue.uri))
                if hosting.GetHostingImpl() == "SOAPpy":
                    self.hostingEnvironment.RegisterObject(AuthorizationManagerI(venue.authManager),
                                                           path=PathFromURL(venue.uri)+"/Authorization")

        except:
            self.simpleLock.release()
            log.exception("AddVenue: Failed.")
            raise VenueServerException("AddVenue Failed!")

        # END Critical Section
        self.simpleLock.release()
        
        # If this is the first venue, set it as the default venue
        if len(self.venues) == 1 and self.defaultVenue == '':
            self.SetDefaultVenue(oid)

        venue.authManager.GetActions()
        
        # return the URL to the new venue
        return venue.uri

    def ModifyVenue(self, oid, venueDesc):   
        """   
        ModifyVenue updates a Venue Description.   
        """
        venue = self.venues[oid]

        # BEGIN Critical Section
        self.simpleLock.acquire()
            
        try:
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
        except:
            # END Critical Section
            self.simpleLock.release()
            log.exception("ModifyVenue: Failed.")
            raise VenueServerException("ModifyVenue Failed!")
            
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
        self.Checkpoint(0)

    def GetVenueDescriptions(self):
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
            log.exception("GetVenues: GetVenueDescriptions failed!")
            raise VenueServerException("GetVenueDescriptions Failed!")

    def GetVenues(self):
        cdl = []
               
        try:
            cdl = map(lambda venue: ConnectionDescription(venue.name,
                                                          venue.description,
                                                          venue.uri,
                                                          venue.uniqueId), self.venues.values())
            return cdl
        except:
            log.exception("GetVenues: Failed!")
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

        try:

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
            if vai != None:
                self.hostingEnvironment.RegisterObject(vai, path=defaultAuthPath)

        except:
            # END Critical Section
            self.simpleLock.release()
            log.exception("SetDefaultVenue: Failed.")
            raise VenueServerException("SetDefaultVenue Failed!")
        
            
        # END Critical Section
        self.simpleLock.release()

    def SetStorageLocation(self,  dataStorageLocation):
        """
        Set the path for data storage
        """
        # BEGIN Critical Section
        self.simpleLock.acquire()

        try:
            self.dataStorageLocation = dataStorageLocation
            self.config["VenueServer.dataStorageLocation"] = dataStorageLocation
            
            # Check for and if necessary create the data store directory
            if not os.path.exists(self.dataStorageLocation):
                try:
                    os.mkdir(self.dataStorageLocation)
                except OSError:
                    log.exception("Could not create VenueServer Data Store.")
                    self.dataStorageLocation = None

        except:
            # END Critical Section
            self.simpleLock.release()
            log.exception("SetStorageLocation: Failed.")
            raise VenueServerException("SetStorageLocation Failed!")
                     
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

        try:
            self.encryptAllMedia = int(value)
            self.config["VenueServer.encryptAllMedia"] = self.encryptAllMedia

        except:
            # END Critical Section
            self.simpleLock.release()
            log.exception("SetEncryptAllMedia: Failed.")
            raise VenueServerException("SetEncryptAllMedia Failed!")
                    
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
            
    def SetAddressAllocationMethod(self,  addressAllocationMethod):
        """
        Set the method used for multicast address allocation:
            either RANDOM or INTERVAL (defined in MulticastAddressAllocator)
        """
        # BEGIN Critical Section
        self.simpleLock.acquire()

        try:
            self.addressAllocationMethod = str(addressAllocationMethod)
            self.multicastAddressAllocator.SetAllocationMethod(
                self.addressAllocationMethod)
            self.config["VenueServer.addressAllocationMethod"] =  self.addressAllocationMethod

        except:
            # END Critical Section
            self.simpleLock.release()
            log.exception("SetAddressAllocationMethod: Failed.")
            raise VenueServerException("SetAddressAllocationMethod Failed!")

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

        try:
            self.baseAddress = str(address)
            self.multicastAddressAllocator.SetBaseAddress( address )
            self.config["VenueServer.baseAddress"] = address
        except:
            # END Critical Section
            self.simpleLock.release()
            log.exception("SetBaseAddress: Failed.")
            raise VenueServerException("SetAddressAllocationMethod Failed!")

        # END CRITICAL SECTION
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
        try:
            self.addressMask = int(mask)
            self.multicastAddressAllocator.SetAddressMask( self.addressMask )
            self.config["VenueServer.addressMask"] = self.addressMask
        except:
            # END Critical Section
            self.simpleLock.release()
            log.exception("SetAddressMask: Failed.")
            raise VenueServerException("SetAddressMask Failed!")
                        
        # END Critical Section
        self.simpleLock.release()

    def GetAddressMask(self):
        """
        Get address mask used when allocating multicast addresses in
        an interval
        """
        return self.multicastAddressAllocator.GetAddressMask( )

    def DumpDebugInfo(self):
        """
        Dump debug info.  The 'flag' argument is not used now,
        but could be used later to control the dump
        """
        for thrd in threading.enumerate():
            log.debug("Thread %s", thrd)

    def RegisterService(self, serviceDescription):
        """
        Registers a service with the venue.
        
        @Param serviceDescription: A service description.
        """
        log.debug("Register service %s", serviceDescription)
        
        self.services[serviceDescription.GetId()] = serviceDescription

        # Send service registered event

        return serviceDescription.GetId()

    def UpdateService(self, serviceDescription):
        self.services[serviceDescription.GetId()] = serviceDescription
    
    def UnregisterService(self, serviceDescription):
        """
        Removes a service from the venue
        
        @Param serviceDescription: A network service description.
        """
        privId = serviceDescription.GetId()
        if self.services.has_key(privId):
            i_sd = self.services[privId]
            if serviceDescription == i_sd:
                del self.services[privId]

                # Send service unregistered event
        else:
            return -1

    def Subscribe(self, privId, event):
       if self.eventSubscriptions.has_key(privId):
          if not event in self.eventSubscriptions[privId]:
             self.eventSubscriptions[privId].append(event)
          else:
             return -2
       else:
          return -1
             
    def Unsubscribe(self, privId, event):
       if self.eventSubscriptions.has_key(privId):
          if not event in self.eventSubscriptions[privId]:
             return -2
          else:
             self.eventSubscriptions[privId].remove(event)
       else:
          return -1
                            
    def GetServices(self):
        return self.services.values()

