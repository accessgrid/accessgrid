#-----------------------------------------------------------------------------
# Name:        AGServiceManager.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGServiceManager.py,v 1.31 2003-08-28 18:45:54 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import sys
import os
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
from AccessGrid.hosting.pyGlobus.Utilities import GetHostname

from AccessGrid.Types import AGServicePackage
from AccessGrid.AuthorizationManager import AuthorizationManager
from AccessGrid.DataStore import GSIHTTPDownloadFile
from AccessGrid import Utilities
from AccessGrid.Platform import GetConfigFilePath, GetSystemConfigDir, GetInstallDir
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator

log = logging.getLogger("AG.ServiceManager")

class AGServiceManager( ServiceBase ):
    """
    AGServiceManager : exposes local resources and configures services
    to deliver them
    """

    def __init__( self, server ):
        self.server = server

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

    def Shutdown(self):
        log.info("Remove services")
        self.RemoveServices()
        log.info("Stop network interface")
        self.server.stop()
    Shutdown.soap_export_as = "Shutdown"

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
            raise Exception("AGServiceManager.SetAuthorizedUsers failed: " + str( sys.exc_value ))
        
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
            raise Exception("AGServiceManager.DiscoverResources failed: " + str( sys.exc_value ))
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
            raise Exception("AGServiceManager.AddService failed: " + str( sys.exc_value ) )

        #
        # Execute service implementation
        #
        try:
            options = []
    
            #
            # Execute the service implementation
            #
            if serviceDescription.executable.endswith(".py"):
                executable = sys.executable
                options.append( self.servicesDir + os.sep + serviceDescription.executable )
            else:
                executable = self.servicesDir + os.sep + serviceDescription.executable

            # Designate port for service
            port = MulticastAddressAllocator().AllocatePort()
            options.append( port )
            print "Running Service; options:", executable, options
            pid = self.processManager.start_process( executable, options )

            #
            # Wait for service to boot and become reachable,
            # timing out reasonably
            #
            serviceUrl = 'https://%s:%s/Service' % ( GetHostname(), port )
            elapsedTries = 0
            maxTries = 10
            while elapsedTries < maxTries:
                print "Trying client handle "
                try:
                    Client.Handle(serviceUrl).IsValid()
                    print "* * Service handle is valid ! "
                    break
                except:
                    print "Wait another sec for service to boot"
                    print " - elapsedTries = ", elapsedTries
                    time.sleep(1)
                    elapsedTries += 1

            # Detect unreachable service
            if elapsedTries >= maxTries:
                raise Exception("Add service failed; service is unreachable")

        except:
            print "Exception in AddService, executing service ", sys.exc_type, sys.exc_value
            raise sys.exc_value

        #
        # Add and configure the service
        #
        try:

            #
            # Set the uri and add service to list of services
            #
            serviceDescription.serviceManagerUri = self.get_handle()
            serviceDescription.uri = serviceUrl
            self.services[pid] = serviceDescription

            # Push authorized user list
            Client.Handle( serviceDescription.uri ).get_proxy().SetAuthorizedUsers( self.authManager.GetAuthorizedUsers() )

            # Assign resource to the service
            #
            if serviceDescription.resource and serviceDescription.resource != "None":
                Client.Handle( serviceDescription.uri ).get_proxy().SetResource( serviceDescription.resource )

            # Configure the service
            #
            if serviceConfig and serviceConfig != "None":
                Client.Handle( serviceDescription.uri ).get_proxy().SetConfiguration( serviceConfig )

            # Query the service for its capabilities
            # (the service implementation knows its capabilities better than
            # the description file, which is where the current capabilities
            # storage was retrieved from)
            # 
            serviceDescription.capabilities = \
                Client.Handle( serviceDescription.uri ).GetProxy().GetCapabilities()
            
        except:
            log.exception("Exception in AddService, adding service to service list.")
            raise sys.exc_value

        return serviceDescription

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
                    Client.Handle( service.uri ).get_proxy().Shutdown()

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
            raise Exception("AGServiceManager.RemoveService failed : ", str( exc ) )

    RemoveService.soap_export_as = "RemoveService"


    def RemoveServices( self ):
        """Remove all services
        """
        for service in self.services.values():
            try:
                self.RemoveService( service )
            except Exception:
                log.exception("Exception in AGServiceManager.RemoveServices; continuing")

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


    def GetInstallDir(self):
        """
        Returns the install directory path where services are expected to be found.
        """
        print '------------ get install dir ', GetInstallDir()

        return GetInstallDir()
    
    GetInstallDir.soap_export_as = "GetInstallDir"
        
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
        isNewServicePackage = not os.path.exists(servicePackageFile)
        GSIHTTPDownloadFile(servicePackageUrl, servicePackageFile, None, None)

        #
        # Extract the executable from the service package
        #
        package = AGServicePackage( servicePackageFile )
        package.ExtractExecutable( self.servicesDir )

        if isNewServicePackage:
            #
            # Open permissions on the service package and executable 
            #
            os.chmod( servicePackageFile, 0777 )
            os.chmod( os.path.join(self.servicesDir, package.exeFile), 0777 )

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
            # If relative path in config file, use SystemConfigDir as the base
            if not os.path.isabs(self.servicesDir):
                self.servicesDir = GetConfigFilePath(self.servicesDir)
