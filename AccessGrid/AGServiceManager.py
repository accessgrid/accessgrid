#-----------------------------------------------------------------------------
# Name:        AGServiceManager.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGServiceManager.py,v 1.43 2004-03-12 00:30:19 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: AGServiceManager.py,v 1.43 2004-03-12 00:30:19 turam Exp $"
__docformat__ = "restructuredtext en"

import sys
import os
import time

from AccessGrid import Log
from AccessGrid.hosting import Client
from AccessGrid.NetUtilities import GetHostname

from AccessGrid import Platform
from AccessGrid.Platform import ProcessManager
from AccessGrid.Types import AGServicePackage
from AccessGrid.DataStore import GSIHTTPDownloadFile
from AccessGrid import Utilities
from AccessGrid.Platform import GetConfigFilePath, GetSystemConfigDir, GetInstallDir
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator

log = Log.GetLogger(Log.ServiceManager)

class AGServiceManager:
    """
    AGServiceManager : exposes local resources and configures services
    to deliver them
    """

    def __init__( self, server ):
        self.server = server

        self.resources = []
        # note: services dict is keyed on pid
        self.services = dict()
        self.processManager = ProcessManager.ProcessManager()

        self.servicesDir = os.path.join(Platform.GetUserConfigDir(),"local_services")


        #
        # Create directory if not exist
        #
        if not os.path.exists(self.servicesDir):
            log.info("Creating user services directory %s", self.servicesDir)
            try:
                os.mkdir(self.servicesDir)
            except:
                log.exception("Couldn't create user services directory %s", self.servicesDir)

        self.__DiscoverResources()

    def Shutdown(self):
        log.info("Remove services")
        self.RemoveServices()
        log.info("Stop network interface")
        self.server.Stop()

    ####################
    ## RESOURCE methods
    ####################

    def GetResources( self ):
        """
        Return a list of resident resources
        """
        self.__DiscoverResources()
        return self.resources


    def DiscoverResources( self ):
        """Discover local resources (audio cards, etc.)
        """
        try:
            self.__DiscoverResources()
        except:
            raise Exception("AGServiceManager.DiscoverResources failed: " + str( sys.exc_value ))


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
            log.exception("Service Manager failed to retrieve service implementation for %s", serviceDescription.name)
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
            log.debug("Running Service; options: %s %s", executable, str(options))
            
            pid = self.processManager.start_process( executable, options )

            #
            # Wait for service to boot and become reachable,
            # timing out reasonably
            #
            serviceUrl = 'https://%s:%s/Service' % ( GetHostname(), port )
            elapsedTries = 0
            maxTries = 10
            while elapsedTries < maxTries:
                try:
                    Client.Handle(serviceUrl).IsValid()
                    log.info("Service %s successfully started", serviceDescription.name)
                    break
                except:
                    time.sleep(1)
                    elapsedTries += 1

            # Detect unreachable service
            if elapsedTries >= maxTries:
                log.error("Add %s failed; service is unreachable", serviceDescription.name)

        except:
            log.exception("Failed to add service")
            raise 

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



    def RemoveServices( self ):
        """Remove all services
        """
        for service in self.services.values():
            try:
                self.RemoveService( service )
            except Exception:
                log.exception("Exception in AGServiceManager.RemoveServices; continuing")



    def GetServices( self ):
        """Return list of services
        """
        return self.services.values()


    def StopServices( self ):
        """
        Stop all services on service manager
        """
        for service in self.services.values():
            Client.Handle( service.uri ).get_proxy().Stop()



    def GetInstallDir(self):
        """
        Returns the install directory path where services are expected to be found.
        """

        return GetInstallDir()
    
        
    ####################
    ## INTERNAL methods
    ####################

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






from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper

class AGServiceManagerI(SOAPInterface):
    """
    Interface Class for AGServiceManager
    """
    
    def __init__(self,impl):
        SOAPInterface.__init__(self,impl)
    
    def Shutdown(self):
        """
        Interface to shut down the service manager

        **Arguments:**
        **Raises:**
        **Returns:**
        """
        self.impl.Shutdown()

    def GetResources(self):
        """
        Interface to get a list of the resources known to the service manager

        **Arguments:**
        **Raises:**
        **Returns:**
            a list of the AGResources on the machine
        """
        return self.impl.GetResources()

    def DiscoverResources(self):
        """
        Interface to discover local resources

        **Arguments:**
        **Raises:**
        **Returns:**
        """
        self.impl.DiscoverResources()

    def AddService(self, servicePackageUri, resourceToAssign, serviceConfig):
        """
        Interface to add a service to the service manager

        **Arguments:**
            *servicePackageUri* URI from which service package can be retrieved
            *resourceToAssign* resource to assign to service
            *serviceConfig* configuration to apply to service after it's been added
        **Raises:**
        **Returns:**
        """
        return self.impl.AddService(servicePackageUri, resourceToAssign, serviceConfig)

    def RemoveService(self, serviceToRemove):
        """
        Interface to remove a service from the service manager

        **Arguments:**
            *serviceToRemove* A description of the service to remove
        **Raises:**
        **Returns:**
        """
        self.impl.RemoveService(serviceToRemove)

    def RemoveServices(self):
        """
        Interface to remove the services on a service manager

        **Arguments:**
        **Raises:**
        **Returns:**
        """
        self.impl.RemoveServices()

    def GetServices(self):
        """
        Interface to get a list of AGServiceDescriptions representing
        the services on the service manager

        **Arguments:**
        **Raises:**
        **Returns:**
            a list of AGServiceDescriptions
        """
        return self.impl.GetServices()

    def StopServices(self):
        """
        Interface to stop services on the service manager

        **Arguments:**
        **Raises:**
        **Returns:**
        """
        self.impl.StopServices()

    def GetInstallDir(self):
        """
        Interface to get the install dir

        **Arguments:**
        **Raises:**
        **Returns:**
            string representing the install dir of the AG software
        """
        return self.impl.GetInstallDir()





class AGServiceManagerIW(SOAPIWrapper):
    """
    Interface Wrapper Class for AGServiceManager
    """
    
    def __init__(self,url):
        SOAPIWrapper.__init__(self,url)
    
    def Shutdown(self):
        self.proxy.Shutdown()

    def GetResources(self):
        return self.proxy.GetResources()

    def DiscoverResources(self):
        self.proxy.DiscoverResources()

    def AddService(self, servicePackageUri, resourceToAssign, serviceConfig):
        return self.proxy.AddService(servicePackageUri, resourceToAssign, serviceConfig)

    def RemoveService(self, serviceToRemove):
        self.proxy.RemoveService(serviceToRemove)

    def RemoveServices(self):
        self.proxy.RemoveServices()

    def GetServices(self):
        return self.proxy.GetServices()

    def StopServices(self):
        self.proxy.StopServices()

    def GetInstallDir(self):
        return self.proxy.GetInstallDir()

