#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
# Created:     2002/12/12
# RCS-ID:      $Id: test_venueserver.py,v 1.1 2005-01-26 22:45:47 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: test_venueserver.py,v 1.1 2005-01-26 22:45:47 judson Exp $"

# Standard stuff
import sys
import os
import re
import os.path
import string
import threading
import time
import ConfigParser

from xml.dom.ext import PrettyPrint

from AccessGrid.Toolkit import Service
from AccessGrid import Log
from AccessGrid import Version
from AccessGrid.hosting import InsecureServer, SecureServer
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.Security.AuthorizationManager import AuthorizationManager
from AccessGrid.Security.AuthorizationManager import AuthorizationManagerI
from AccessGrid.Security.AuthorizationManager import AuthorizationIMixIn
from AccessGrid.Security.AuthorizationManager import AuthorizationIWMixIn
from AccessGrid.Security.AuthorizationManager import AuthorizationMixIn
from AccessGrid.Security import X509Subject, Role
from AccessGrid.Security.Action import ActionAlreadyPresent
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
from AccessGrid.Types import Capability

log = Log.GetLogger(Log.VenueServer)

# ZSI Stuff
from AccessGrid.cache.VenueServer_services import *
from AccessGrid.hosting.Tools import CreateObj
from AccessGrid.cache import Venue_interface

def GetHostingEnvironment():
    global __server
    return __server

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
    def __init__(self):
        """
        The constructor creates a new Venue Server object, initializes
        that object, then registers signal handlers so the venue can cleanly
        shutdown in the event of catastrophic signals.

        **Arguments:**
        """
        # Initialize our state
        self.multicastAddressAllocator = MulticastAddressAllocator()
        self.hostname = Service.instance().GetHostname()
        self.properties = dict()
        self.venues = dict()
        self.services = list()
        self.defaultVenue = None
        self.houseKeeperFrequency = 30

        # The houseKeeper is a task that is doing garbage collection and
        # other general housekeeping tasks for the Venue Server.
        self.houseKeeper = Scheduler()
#        self.houseKeeper.AddTask(self.Checkpoint,
#                                 int(self.houseKeeperFrequency), 0, 1)
#        self.houseKeeper.AddTask(self._CleanupClients, 15, 0, 1)

        # Start all the periodic tasks registered with the housekeeper thread
        self.houseKeeper.StartAllTasks()

    def authorize(self, auth_info, post, action):
        print "Authorizing call (%s, %s, %s)" % (auth_info, post, action)
        return 1
    
    def _CleanupClients(self):
        for venue in self.venues.values():
            venue._CleanupClientss()

    def Shutdown(self, secondsFromNow=0):
        """
        Shutdown shuts down the server.
        """
        log.info("Starting Shutdown!")

        self.houseKeeper.StopAllTasks()

        he = GetHostingEnvironment()
        he.Stop()
        
        log.info("Shutdown Complete.")

    def Checkpoint(self, secondsFromNow=0):
        """
        Checkpoint stores the current state of the running VenueServer to
        non-volatile storage. In the event of catastrophic failure, the
        non-volatile storage can be used to restart the VenueServer.

        The fequency at which Checkpointing is done will bound the amount of
        state that is lost (the longer the time between checkpoints, the more
        that can be lost).
        """

        log.info("Checkpointing completed at: %s", time.asctime())

        return 1

    def AddVenue(self, venueDesc, authPolicy = None):
        """
        The AddVenue method takes a venue description and creates a new
        Venue Object, then makes it available from this Venue Server.
        """
        # Create a new Venue object pass it the server
        # Usually the venueDesc will not have Role information 
        #   and defaults will be used.
        venue = Venue(venueDesc.name, venueDesc.description, "", venueDesc.id )

        venue.SetEncryptMedia(venueDesc.encryptMedia, venueDesc.encryptionKey)

        # Add Connections if there are any
        venue.SetConnections(venueDesc.connections)

        # Add Streams if there are any
#        venue.AddStreams(venueDesc.streams)

        # Add the venue to the list of venues
        oid = venue.GetId()
        self.venues[oid] = venue

        # Create an interface
        vi = Venue_interface.Venue(impl=venue, auth_method_name="authorize")

        # We have to register this venue as a new service.
        he = GetHostingEnvironment()
        path = "/Venues/%s" % oid
        he.RegisterObject(vi, path = path)

        # If this is the first venue, set it as the default venue
        if len(self.venues) == 1 and self.defaultVenue == '':
            self.SetDefaultVenue(oid)

        # return the URL to the new venue
        return he.GetURLBase() + path

    def ModifyVenue(self, oid, venueDesc):   
        """   
        ModifyVenue updates a Venue Description.   
        """
        venue = self.venues[oid]

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
            raise VenueNotFound, "Cannot find venue (id = %s)" % oid

        # Stop the web service interface
        try:
            self.hostEnvironment.UnregisterObject(venue)
        except Exception, e:
            log.exception(e)
            raise UnbindVenueError
        except:
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

    def SetProperty(self, pdict):
        """
        """
        for name,value in pdict.items():
            self.properties[name] = value

    def GetProperty(self, pdict):
        """
        """
        for name in pdict.keys():
            if self.properties.has_key(name):
                pdict[name] = self.properties[name]
            else:
                raise KeyError, "Couldn't find property (name=%s)" % name
    # Some simple output to advertise the location of the service

        return pdict
    
if __name__ == "__main__":
    global __server
    from ZSI.ServiceContainer import ServiceContainer
    from AccessGrid.cache import VenueServer_interface

    port = 7000
    url = "http://localhost:%d/VenueServer" % port
    address = ('localhost', port)

    __server = InsecureServer(address, debug = 1)
    
    vs = VenueServer()
    
    vsi = VenueServer_interface.VenueServer(impl=vs,
                                            auth_method_name="authorize")

    uri = __server.RegisterObject(vsi, path = "/VenueServer")

    print "Server: %s" % uri

    __server.Run()
