#-----------------------------------------------------------------------------
# Name:        AGServiceManager.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGServiceManager.py,v 1.50 2004-04-12 22:41:15 eolson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: AGServiceManager.py,v 1.50 2004-04-12 22:41:15 eolson Exp $"
__docformat__ = "restructuredtext en"

import sys
import os
import time

from AccessGrid import Log
from AccessGrid.Platform.ProcessManager import ProcessManager
from AccessGrid.Platform.Config import AGTkConfig, UserConfig, SystemConfig
from AccessGrid import Utilities
from AccessGrid.Types import AGServicePackage
from AccessGrid.DataStore import GSIHTTPDownloadFile
from AccessGrid.NetworkAddressAllocator import NetworkAddressAllocator
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.Descriptions import CreateAGServiceDescription, CreateResource
from AccessGrid.Descriptions import CreateServiceConfiguration
from AccessGrid.AGService import AGServiceIW
from AccessGrid.AGServicePackageRepository import AGServicePackageRepository

log = Log.GetLogger(Log.ServiceManager)
hdlr = Log.StreamHandler()
Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())

class AGServiceManager:
    """
    AGServiceManager :

    exposes local resources and configures services to deliver them
    """

    def __init__( self, server ):
        self.server = server

        self.resources = []
        
        # note: services dict is keyed on pid
        self.services = dict()
        self.processManager = ProcessManager()
        self.resourcesFile = os.path.join(UserConfig.instance().GetConfigDir(),
                                          "videoresources")


        userConfig = UserConfig.instance()
        self.servicesDir = os.path.join(userConfig.GetConfigDir(),
                                        "local_services")

        # Create directory if not exist
        if not os.path.exists(self.servicesDir):
            log.info("Creating user services directory %s", self.servicesDir)
            try:
                os.mkdir(self.servicesDir)
            except:
                log.exception("Couldn't create user services directory %s", 
                              self.servicesDir)
                
        self.packageRepo = AGServicePackageRepository(self.servicesDir)

        self.__DiscoverResources()
        
        self.url = None

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


    ####################
    ## SERVICE methods
    ####################

    def AddService( self, serviceDescription, resourceToAssign, serviceConfig ):
        """
        Add a service package to the service manager.  
        """
        log.debug("AddService: %s v%f", serviceDescription.name, 
                  serviceDescription.version)
        
        # Get the service manager url (first time only)
        if not self.url:
            self.url = self.server.FindURLForObject(self)

        #
        # Determine resource to assign to service
        #
        resource = None
        if resourceToAssign != None and resourceToAssign != "None":
            foundResource = 0
            for res in self.resources:
                if resourceToAssign.resource == res.resource:
                    if res.inUse == 1:
                        log.debug("** Resource is already in use! : %s ",
                                  res.resource)
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
            # Check for local copy of service package
            #
            localSvcDesc = None
            svcDescList = self.packageRepo.GetServiceDescriptions()
            for svcDesc in svcDescList:
                if svcDesc.name == serviceDescription.name:
                    localSvcDesc = svcDesc
                    log.debug("Found local service %s, v%d", 
                              localSvcDesc.name,
                              localSvcDesc.version)
                    break                   

            # Retrieve the service package if there is no local copy, 
            # or if we're adding a newer copy
            if not localSvcDesc or localSvcDesc.version < serviceDescription.version:
                log.debug("Retrieving service package %s", 
                          serviceDescription.servicePackageUri)
                #
                # Retrieve service implementation
                #
                servicePackageFile = self.__RetrieveServicePackage( serviceDescription.servicePackageUri )
                serviceDescription = AGServicePackage( servicePackageFile ).GetServiceDescription()
            else:
                serviceDescription = localSvcDesc
            
            serviceDescription.resource = resource

        except:
            log.exception("Service Manager failed to retrieve service implementation for %s", 
                          serviceDescription.servicePackageUri)
            raise Exception("AGServiceManager.AddService failed: " + 
                            str( sys.exc_value ) )

        #
        # Execute service implementation
        #
        try:
            options = []
    
            #
            # Execute the service implementation
            #
            exeFile = os.path.join(self.servicesDir, serviceDescription.executable )
            if serviceDescription.executable.endswith(".py"):
                # python files are executed with python
                executable = sys.executable
                options.append( exeFile )
            else:
                # non-python files are executed directly
                executable = exeFile

            # Designate port for service
            port = NetworkAddressAllocator().AllocatePort()
            options.append( port )
            log.debug("Running Service; options: %s %s", executable, str(options))
            
            pid = self.processManager.StartProcess( executable, options )

            #
            # Wait for service to boot and become reachable,
            # timing out reasonably
            #
            hostname = SystemConfig.instance().GetHostname()
            serviceUrl = 'https://%s:%s/Service' % ( hostname, port )
            elapsedTries = 0
            maxTries = 10
            while elapsedTries < maxTries:
                try:
                    AGServiceIW(serviceUrl).IsValid()
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
            serviceDescription.serviceManagerUri = self.url
            serviceDescription.uri = serviceUrl
            self.services[pid] = serviceDescription

            # Configure the service
            #
            if serviceConfig and serviceConfig != "None":
                AGServiceIW( serviceDescription.uri ).SetConfiguration( serviceConfig )

            # Assign resource to the service
            #
            if serviceDescription.resource and serviceDescription.resource != "None":
                AGServiceIW( serviceDescription.uri ).SetResource( serviceDescription.resource )

            # Query the service for its capabilities
            # (the service implementation knows its capabilities better than
            # the description file, which is where the current capabilities
            # storage was retrieved from)
            # 
            serviceDescription.capabilities = \
                AGServiceIW( serviceDescription.uri ).GetCapabilities()
            
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
                    AGServiceIW( service.uri ).Shutdown()

                    #
                    # Kill service
                    #
                    self.processManager.TerminateProcess(pid)

                    #
                    # Free the resource
                    if service.resource and service.resource != "None":
                        foundResource = 0
                        for resource in self.resources:
                            if resource.resource == service.resource.resource:
                                resource.inUse = 0
                                foundResource = 1

                        if foundResource == 0:
                            log.debug("** The resource used by the service can not be found !! : %s", 
                                      service.resource.resource)

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
            AGServiceIW( service.uri ).Stop()



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
        servicePackageFile = os.path.join(self.servicesDir, filename)
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
        self.resources = Utilities.GetResourceList( self.resourcesFile )

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

class AGServiceManagerI(SOAPInterface):
    """
    Interface Class for AGServiceManager
    """
    
    def __init__(self,impl):
        SOAPInterface.__init__(self,impl)

    def _authorize(self, *args, **kw):
        # Authorize everybody.
        return 1
    
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

    def AddService(self, serviceDescStruct, resourceStruct, serviceConfigStruct):
        """
        Interface to add a service to the service manager

        **Arguments:**
            *serviceDescription* description of the service to add
            *resourceToAssign* resource to assign to service
            *serviceConfig* configuration to apply to service after it's been added
        **Raises:**
        **Returns:**
        """
        if serviceDescStruct and serviceDescStruct != "None":
            serviceDescription = CreateAGServiceDescription(serviceDescStruct)
        else:   
            serviceDescription = None

        if resourceStruct and resourceStruct != "None":
            resource = CreateResource(resourceStruct)
        else:
            resource = None
            
        if serviceConfigStruct and serviceConfigStruct != "None":
            serviceConfig = CreateServiceConfiguration(serviceConfigStruct)
        else:
            serviceConfig = None
        return self.impl.AddService(serviceDescription, resource, serviceConfig)

    def RemoveService(self, serviceDescStruct):
        """
        Interface to remove a service from the service manager

        **Arguments:**
            *serviceToRemove* A description of the service to remove
        **Raises:**
        **Returns:**
        """
        serviceDesc = CreateAGServiceDescription(serviceDescStruct)
        self.impl.RemoveService(serviceDesc)

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
        rscList = list()
        rscStructList = self.proxy.GetResources()
        for rscStruct in rscStructList:
            rscList.append( CreateResource(rscStruct))
        return rscList

    def DiscoverResources(self):
        self.proxy.DiscoverResources()

    def AddService(self, serviceDescription, resource, serviceConfig):
        serviceDescStruct = self.proxy.AddService(serviceDescription, resource, serviceConfig)
        serviceDesc = CreateAGServiceDescription(serviceDescStruct)
        return serviceDesc

    def RemoveService(self, serviceToRemove):
        self.proxy.RemoveService(serviceToRemove)

    def RemoveServices(self):
        self.proxy.RemoveServices()

    def GetServices(self):
        svcList = list()
        for s in self.proxy.GetServices():
            svcList.append(CreateAGServiceDescription(s))
        return svcList

    def StopServices(self):
        self.proxy.StopServices()

    def GetInstallDir(self):
        return self.proxy.GetInstallDir()

