#-----------------------------------------------------------------------------
# Name:        AGServiceManager.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGServiceManager.py,v 1.17 2003-03-14 17:12:32 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import sys
import urllib
import os
import socket
import time
import logging

try:     import win32process
except:  pass
if sys.platform == 'win32':
    from AccessGrid.ProcessManagerWin32 import ProcessManagerWin32 as ProcessManager
else:
    from AccessGrid.ProcessManagerUnix import ProcessManagerUnix as ProcessManager

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.hosting.pyGlobus.ServiceBase import ServiceBase
from AccessGrid.hosting.pyGlobus.AGGSISOAP import faultType

from AccessGrid.Descriptions import AGServiceDescription
from AccessGrid.Types import AGServicePackage
from AccessGrid.AuthorizationManager import AuthorizationManager
from AccessGrid.DataStore import GSIHTTPDownloadFile
from AccessGrid import Utilities
from AccessGrid.Platform import GetConfigFilePath, GetSystemConfigDir
from AccessGrid import GUID

log = logging.getLogger("AG.ServiceManager")

class AGServiceManager( ServiceBase ):
    """
    AGServiceManager : exposes local resources and configures services
    to deliver them
    """

    def __init__( self ):
        self.name = None
        self.description = None
        self.resources = []
        # note: services dict is keyed on pid
        self.services = dict()
        self.authManager = AuthorizationManager()
        self.executable = None
        self.processManager = ProcessManager()

        self.servicesDir = "local_services"

        # note: unregisteredServices dict is keyed on token
        self.unregisteredServices = dict()

        #
        # Read the configuration file (directory options and such)
        #
        configFile = GetConfigFilePath("AGServiceManager.cfg")
        if configFile:
            self.__ReadConfigFile( configFile )

        self.__DiscoverResources()

    ####################
    ## AUTHORIZATION methods
    ####################

    def SetAuthorizedUsers( self, authorizedUsers ):
        """
        Set the authorizedUsers list; this is usually pushed from a NodeService,
        thus this wholesale Set of the authorized user list.  Also, push this
        list to known services
        """

        try:
            self.authManager.SetAuthorizedUsers( authorizedUsers )
            self.__PushAuthorizedUserList()
        except:
            log.exception("AGServiceManager.SetAuthorizedUsers.")
            raise faultType("AGServiceManager.SetAuthorizedUsers failed: " + str( sys.exc_value ))
        
    SetAuthorizedUsers.soap_export_as = "SetAuthorizedUsers"


    ####################
    ## RESOURCE methods
    ####################

    def GetResources( self ):
        """
        Return a list of resident resources
        """
        self.__DiscoverResources()
        return self.resources
    GetResources.soap_export_as = "GetResources"


    def DiscoverResources( self ):
        """Discover local resources (audio cards, etc.)
        """
        try:
            self.__DiscoverResources()
        except:
            raise faultType("AGServiceManager.DiscoverResources failed: " + str( sys.exc_value ))
    DiscoverResources.soap_export_as = "DiscoverResources"


    ####################
    ## SERVICE methods
    ####################

    def AddService( self, servicePackageUri, resourceToAssign, serviceConfig ):
        """
        Add a service package to the service manager.  
        """

        #
        # Determine resource to assign to service
        #
        resource = None
        if resourceToAssign != None and resourceToAssign != "None":
            foundResource = 0
            for resource in self.resources:
                if resourceToAssign.resource == resource.resource:
                    if resource.inUse == 1:
                        log.debug("** Resource is already in use! : %s ",
                                  resource.resource)
                    # should error out here later; for now,
                    # services aren't using the resources anyway
                    foundResource = 1
                    break

            if foundResource == 0:
                log.debug("** Resource does not exist! : %s ",
                          resourceToAssign.resource)
#FIXME - # should error out here later

        try:
            #
            # Check for local copy of service implementation
            #
            # -- not yet implemented

            #
            # Retrieve service implementation
            #
            servicePackageFile = self.__RetrieveServicePackage( servicePackageUri )
            serviceDescription = AGServicePackage( servicePackageFile ).GetServiceDescription()
            serviceDescription.servicePackageUri = servicePackageUri
            serviceDescription.resource = resource

        except:
            print "Exception in AddService, retrieving service implementation\n-- ", sys.exc_type, sys.exc_value
            raise faultType("AGServiceManager.AddService failed: " + str( sys.exc_value ) )

        #
        # Add service
        #
        try:
            options = []


            if serviceDescription.executable.endswith(".py"):
                executable = sys.executable
                options.append( self.servicesDir + os.sep + serviceDescription.executable )
            else:
                executable = self.servicesDir + os.sep + serviceDescription.executable

            token = str(GUID.GUID())
            options.append( token )
            options.append( self.get_handle() )

            print "Running Service; options:", executable, options
            pid = self.processManager.start_process( executable, options )

        except:
            print "Exception in AddService, starting service ", sys.exc_type, sys.exc_value
            raise sys.exc_value

        try:

            #
            # Add the service to the list
            #
            serviceDescription.serviceManagerUri = self.get_handle()
            self.unregisteredServices[token] = ( pid, serviceDescription, serviceConfig )

        except:
            log.exception("Exception in AddService, retrieving service implementation.")
            raise sys.exc_value

    AddService.soap_export_as = "AddService"

    
    def RemoveService( self, serviceToRemove ):
        """Remove a service
        """
        exc = None
        pid = None

        try:

            #
            # Find service to stop using uri
            #
            for key in self.services.keys():
                service = self.services[key]
                if service.uri == serviceToRemove.uri:

                    pid = key
                    Client.Handle( service.uri ).get_proxy().Stop()

                    #
                    # Kill service
                    #
                    self.processManager.terminate_process(pid)

                    #
                    # Free the resource
                    if service.resource and service.resource != "None":
                        foundResource = 0
                        for resource in self.resources:
                            if resource.resource == service.resource.resource:
                                resource.inUse = 0
                                foundResource = 1

                        if foundResource == 0:
                            log.debug("** The resource used by the service can not be found !! : %s", service.resource.resource)

                    break

        except:
            log.exception("Exception in AGServiceManager.RemoveService.")
            exc = sys.exc_value

        #
        # Remove service from list
        #
        if pid:
            del self.services[pid]

        # raise exception now, if one occurred
        if exc:
            raise faultType("AGServiceManager.RemoveService failed : ", str( exc ) )

    RemoveService.soap_export_as = "RemoveService"


    def RemoveServices( self ):
        """Remove all services
        """

        try:
            for service in self.services.values():
                self.RemoveService( service )
        except:
            log.exception("Exception in AGServiceManager.RemoveServices.")
            raise faultType("AGServiceManager.RemoveServices failed : "
                            + str( sys.exc_value ) )
    RemoveServices.soap_export_as = "RemoveServices"


    def GetServices( self ):
        """Return list of services
        """
        return self.services.values()
    GetServices.soap_export_as = "GetServices"


    def StopServices( self ):
        """
        Stop all services on service manager
        """
        for service in self.services.values():
            Client.Handle( service.uri ).get_proxy().Stop()

    StopServices.soap_export_as = "StopServices"


    def RegisterService( self, token, uri ):
        """
        Register a service with the service manager.  Why?  When the
        service manager executes a service implementation, it assigns
        it a token.  When the service actually starts, it registers
        with the service manager by passing this token and its uri
        """

        try:

            # Use the token to identify the unregistered service
            #
            pid, service, serviceConfig = self.unregisteredServices[token]
            del self.unregisteredServices[token]

            # Set the uri and add service to list of services
            #
            service.uri = uri
            self.services[pid] = service

            # Push authorized user list
            Client.Handle( service.uri ).get_proxy().SetAuthorizedUsers( self.authManager.GetAuthorizedUsers() )

            # Assign resource to the service
            #
            if service.resource and service.resource != "None":
                Client.Handle( service.uri ).get_proxy().SetResource( service.resource )

            # Configure the service
            #
            if serviceConfig and serviceConfig != "None":
                Client.Handle( service.uri ).get_proxy().SetConfiguration( serviceConfig )
            
        except:
            log.exception("Exception in RegisterService.")
            raise faultType("AGServiceManager.RegisterService failed: " + str( sys.exc_value ))

    RegisterService.soap_export_as = "RegisterService"


    def Ping( self ):
        return 1
    Ping.soap_export_as = "Ping"


    ####################
    ## INTERNAL methods
    ####################

    def __PushAuthorizedUserList( self ):
        """Push the list of authorized users to service managers"""
        for service in self.services.values():
            Client.Handle( service.uri ).get_proxy().SetAuthorizedUsers( self.authManager.GetAuthorizedUsers() )


    def __RetrieveServicePackage( self, servicePackageUrl ):
        """Internal : Retrieve a service implementation"""
        log.info("Retrieving Service Package: %s", servicePackageUrl)

        #
        # Retrieve the service package
        #
        filename = os.path.basename( servicePackageUrl )
        servicePackageFile = self.servicesDir + os.sep + filename
        GSIHTTPDownloadFile(servicePackageUrl, servicePackageFile, None, None)

        #
        # Extract the executable from the service package
        #
        AGServicePackage( servicePackageFile ).ExtractExecutable( self.servicesDir )

        return servicePackageFile


    def __DiscoverResources( self ):
        """Discover local resources (video capture cards, etc.)
        """
        configDir = GetSystemConfigDir()
        filename = configDir + os.sep + "videoresources"
        self.resources = Utilities.GetResourceList( filename )


    def __ReadConfigFile( self, configFile ):
        """
        Read the node service configuration file
        """
        servicesDirOption = "Service Manager.servicesDirectory"

        from AccessGrid.Utilities import LoadConfig
        config = LoadConfig( configFile )
        if servicesDirOption in config.keys():
            self.servicesDir = config[servicesDirOption]
