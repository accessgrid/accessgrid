#-----------------------------------------------------------------------------
# Name:        AGServiceManager.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGServiceManager.py,v 1.70 2004-05-14 22:27:59 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: AGServiceManager.py,v 1.70 2004-05-14 22:27:59 turam Exp $"
__docformat__ = "restructuredtext en"

import sys
import os
import time

from AccessGrid import Log
from AccessGrid import Utilities
from AccessGrid.Toolkit import Service
from AccessGrid.Platform.ProcessManager import ProcessManager
from AccessGrid.Platform.Config import AGTkConfig, UserConfig, SystemConfig
from AccessGrid.Types import AGServicePackage
from AccessGrid.DataStore import GSIHTTPDownloadFile, HTTPDownloadFile
from AccessGrid.NetworkAddressAllocator import NetworkAddressAllocator
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.Descriptions import CreateAGServiceDescription, CreateResource
from AccessGrid.Descriptions import CreateParameter
from AccessGrid.AGService import AGServiceIW
from AccessGrid.AGServicePackageRepository import AGServicePackageRepository

log = Log.GetLogger(Log.ServiceManager)

class ResourceNotFoundError(Exception):
    pass

class AGServiceManager:
    """
    AGServiceManager :

    exposes local resources and configures services to deliver them
    """

    def __init__( self, server, app=None ):
        self.server = server
        if app is not None:
            self.app = app
        else:
            self.app = Service.instance()

        self.resources = []
        
        # note: services dict is keyed on pid
        self.services = dict()
        self.processManager = ProcessManager()
        userConfig = self.app.GetUserConfig().instance()
        self.servicesDir = os.path.join(userConfig.GetBaseDir(),
                                        "local_services")

        # Create directory if not exist
        if not os.path.exists(self.servicesDir):
            log.info("Creating user services directory %s", self.servicesDir)
            try:
                os.mkdir(self.servicesDir)
            except:
                log.exception("Couldn't create user services directory %s", 
                              self.servicesDir)
        else:   
            log.info("Using services dir: %s", self.servicesDir)
                
        self.packageRepo = AGServicePackageRepository(self.servicesDir)

        self.__DiscoverResources()
        
        self.url = None

    def Shutdown(self):
        log.info("AGServiceManager.Shutdown")
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
        log.info("AGServiceManager.GetResources")
        self.__DiscoverResources()
        return self.resources


    ####################
    ## SERVICE methods
    ####################

    def AddService( self, serviceDescription, resourceToAssign, serviceConfig ):
        """
        Add a service package to the service manager.  
        """
        log.info("AGServiceManager.AddService")
        log.info("AddService: %s v %f u %s", serviceDescription.name, 
                  serviceDescription.version,
                  serviceDescription.servicePackageUri)
        
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
                    resource = res
                    break

            if foundResource == 0:
                log.debug("** Resource does not exist! : %s ",
                          resourceToAssign.resource)
                #raise ResourceNotFoundError(resourceToAssign.resource)


        #
        # Retrieve the service package
        #
        try:
            servicePackageToInstall = None
            
            #
            # Check for local copy of service package
            #
            log.info("Searching for local service package")
            servicePkgList = self.packageRepo.GetServicePackages()
            for servicePkg in servicePkgList:
                serviceDesc = servicePkg.GetServiceDescription()
                if serviceDesc.name == serviceDescription.name:
                    servicePackageToInstall = servicePkg
                    log.info("Found local service %s, v%d", 
                              serviceDesc.name,
                              serviceDesc.version)
                    break     

        except:
            log.exception("Error searching for local service package")
            raise Exception("Error searching for local service package")

        # Get the path to which to extract this service
        servicePath = self.__GetServicePath(serviceDescription)

        try:
            # Retrieve the service package if there is no local copy, 
            # or if we're adding a newer copy
            if(not servicePackageToInstall or 
               servicePackageToInstall.GetServiceDescription().version < serviceDescription.version):
                log.info("Service package not found") 
                log.info("Retrieving service package %s", 
                          serviceDescription.servicePackageUri)
                #
                # Retrieve service implementation
                #
                servicePackageToInstall = self.__RetrieveServicePackage( serviceDescription.servicePackageUri )
                
                
                try:
                    #
                    # Extract the service package
                    #

                    log.info("Extracting service package to %s", servicePath)

                    # Create dir for package
                    if not os.path.exists(servicePath):
                        log.info("Creating service path %s", servicePath)
                        os.makedirs(servicePath)

                    # Extract the package
                    servicePackageToInstall.ExtractPackage(servicePath)

                    # Get the (new) service description and set the resource
                    serviceDescription = servicePackageToInstall.GetServiceDescription()
                    serviceDescription.resource = resource

                except:
                    log.exception("Service Manager failed to extract service implementation")
                    raise Exception("Service Manager failed to extract service implementation")


        except:
            log.exception("Service Manager failed to retrieve service implementation for %s", 
                          serviceDescription.servicePackageUri)
            raise Exception("Service Manager couldn't retrieve service package")



        #
        # Start the service process
        #
        try:
            options = []
    
            #
            # Execute the service implementation
            #
            exeFile = os.path.join(servicePath, serviceDescription.executable )
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
            log.info("Running Service; options: %s %s", executable, str(options))
            
            # 
            # Change to the services directory to start the process     
            # Note: services rely on this being true    
            #   
            os.chdir(servicePath)   

            # Execute the service process 
            pid = self.processManager.StartProcess( executable, options )

            # Wait for service to boot and become reachable,
            # timing out reasonably
            hostname = self.app.GetHostname()
            serviceUrl = 'https://%s:%s/Service' % ( hostname, port )

            log.debug("Waiting for service to start: %s %s", serviceDescription.name, 
                      serviceUrl)

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
                log.error("Add %s failed; service is unreachable", 
                          serviceDescription.name)
                raise Exception("Service failed to become reachable")

        except:
            log.exception("Error starting service")
            raise Exception("Error starting service")

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
                log.info("Setting service configuration")
                AGServiceIW( serviceDescription.uri ).SetConfiguration( serviceConfig )
            else:
                log.debug("Not setting service configuration; none given")


            # Assign resource to the service
            #
            if serviceDescription.resource and serviceDescription.resource != "None":
                log.info("Assigning resource to service: %s", serviceDescription.resource.resource)
                AGServiceIW( serviceDescription.uri ).SetResource( serviceDescription.resource )
            else:
                log.debug("Not assigning resource; none given")
                
            # Query the service for its capabilities
            # (the service implementation knows its capabilities better than
            # the description file, which is where the current capabilities
            # storage was retrieved from)
            # 
            serviceDescription.capabilities = \
                AGServiceIW( serviceDescription.uri ).GetCapabilities()
            
        except:
            log.exception("Error configuring service")
            raise Exception("Error configuring service")

        return serviceDescription


    
    def RemoveService( self, serviceToRemove ):
        """Remove a service
        """
        log.info("AGServiceManager.RemoveService")

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
                    try:
                        AGServiceIW( service.uri ).Shutdown()
                    except:
                        log.exception("Error shutting down service %s", service.name)

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
            log.exception("Exception removing service %s", serviceToRemove.name)
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
        log.info("AGServiceManager.RemoveServices")
        for service in self.services.values():
            try:
                self.RemoveService( service )
            except Exception:
                log.exception("Exception in AGServiceManager.RemoveServices; continuing")



    def GetServices( self ):
        """Return list of services
        """
        log.info("AGServiceManager.GetServices")
        return self.services.values()


    def StopServices( self ):
        """
        Stop all services on service manager
        """
        log.info("AGServiceManager.StopServices")
        for service in self.services.values():
            AGServiceIW( service.uri ).Stop()



    def GetInstallDir(self):
        """
        Returns the install directory path where services are expected to be found.
        """
        log.info("AGServiceManager.GetInstallDir")

        return GetInstallDir()
    
        
    ####################
    ## INTERNAL methods
    ####################

    def __RetrieveServicePackage( self, servicePackageUri ):
        """Internal : Retrieve a service implementation"""
        log.info("__RetrieveServicePackage: %s", servicePackageUri)

        #
        # Retrieve the service package
        #
        filename = os.path.basename( servicePackageUri )
        servicePackageFile = os.path.join(self.servicesDir, filename)
        isNewServicePackage = not os.path.exists(servicePackageFile)
        if self.app.GetOption("insecure"):
            HTTPDownloadFile(None, servicePackageUri, servicePackageFile,
                             None, None)
        else:
            GSIHTTPDownloadFile(servicePackageUri, servicePackageFile,
                                None, None)

        package = AGServicePackage( servicePackageFile )
        package.serviceDesc.servicePackageUri = servicePackageUri
        
        return package

    def __DiscoverResources( self ):
        """
        This method retrieves the list of resources from the machine
        """
        log.info("__DiscoverResources")
        self.resources = SystemConfig.instance().GetResources()

                
    def __GetServicePath(self,serviceDescription):
        """
        Return the path in which services files will be unpacked for
        the given service
        """
        serviceDirName = serviceDescription.name.replace(' ', '_')
        servicePath = os.path.join(self.servicesDir,serviceDirName)
        return servicePath
        

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

        serviceConfig = []
        for parmStruct in serviceConfigStruct:
            serviceConfig.append(CreateParameter(parmStruct))
            
        # Perform no conversion on the resource (for now)
        resource = resourceStruct
            
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

