#-----------------------------------------------------------------------------
# Name:        AGNodeService.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGNodeService.py,v 1.63 2004-04-29 14:21:10 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: AGNodeService.py,v 1.63 2004-04-29 14:21:10 turam Exp $"
__docformat__ = "restructuredtext en"

import os
import sys
import string
import ConfigParser
import shutil
import urlparse

from AccessGrid import Log
from AccessGrid.Toolkit import Service
from AccessGrid.hosting import Client
from AccessGrid.Descriptions import AGServiceDescription
from AccessGrid.Descriptions import AGServiceManagerDescription
from AccessGrid.AGServiceManager import AGServiceManagerI, AGServiceManagerIW
from AccessGrid.AGService import AGServiceIW
from AccessGrid.Types import ServiceConfiguration, AGResource
from AccessGrid.Utilities import LoadConfig, SaveConfig
from AccessGrid.AGParameter import ValueParameter
from AccessGrid.Descriptions import CreateAGServiceManagerDescription
from AccessGrid.Descriptions import CreateAGServiceDescription
from AccessGrid.Descriptions import CreateCapability
from AccessGrid.Descriptions import CreateResource
from AccessGrid.Descriptions import CreateClientProfile
from AccessGrid.Descriptions import CreateServiceConfiguration
from AccessGrid.Descriptions import CreateStreamDescription

from AccessGrid.AGServicePackageRepository import AGServicePackageRepository

from SOAPpy.Types import SOAPException

log = Log.GetLogger(Log.NodeService)
Log.SetDefaultLevel(Log.NodeService, Log.DEBUG)

class SetStreamException(Exception): pass

class AGNodeService:
    """
    AGNodeService is the central engine of an Access Grid node.
    It is the contact point for clients to access underlying Service Managers
    and AGServices, for control and configuration of the node.
    """

    defaultNodeConfigurationOption = \
                          "Node Configuration.defaultNodeConfiguration"
    NodeConfigFile = "AGNodeService.cfg"

    def __init__( self, app=None ):
        if app is not None:
            self.app = app
        else:
            self.app = Service.instance()
            
        self.serviceManagers = dict()
        self.config = None
        self.defaultConfig = None
        self.configDir = os.path.join(self.app.GetUserConfig().GetConfigDir(),
                                      "nodeConfig")
        self.servicesDir = self.app.GetToolkitConfig().GetNodeServicesDir()

        self.streamDescriptionList = dict()
        self.profile = None

        #
        # Ensure that the necessary user directories exist
        #
        if not os.path.exists(self.servicesDir):
            log.error("Services directory does not exist: %s",
                      self.servicesDir)

        if not os.path.exists(self.configDir): 
            try:
                log.info("Creating user node config directory %s",
                         self.configDir)
                os.mkdir(self.configDir)

                # Copy node configurations from system node config directory
                # to user node config directory
                log.info("Copying system node configs to user node config dir")
                self.agtkConfigDir = self.app.GetToolkitConfig().GetConfigDir()
                systemNodeConfigDir = os.path.join(self.agtkConfigDir,
                                                   "nodeConfig")
                configFiles = os.listdir(systemNodeConfigDir)
                for configFile in configFiles:
                    log.info("  node config: %s", configFile)
                    srcfile=os.path.join(systemNodeConfigDir,configFile)
                    destfile=os.path.join(self.configDir,configFile)
                    try:
                        shutil.copyfile(srcfile,destfile)
                    except:
                        log.exception("Couldn't copy file %s to %s", srcfile,
                                      destfile)
            except:
                log.exception("Couldn't create node service config dir: %s",
                              self.configDir)

        # Read the configuration file (directory options and such)
        self.__ReadConfigFile()

        # Start the service package repository
        # (now that the services directory is known)
        self.servicePackageRepository = AGServicePackageRepository(
            self.servicesDir, prefix="packages" )
        self.servicePackageRepository.Start()

    def LoadDefaultConfig(self):
        """
        Load default node configuration (service managers and services)
        """
        if self.defaultConfig:
            try:
                self.LoadConfiguration( self.defaultConfig ) 
            except:
                log.exception("Exception loading default configuration.")
                raise Exception("Failed to load default configuration <%s>",
                                self.defaultConfig)
        else:
            log.warn("There is no default configuration.")
            
    def Stop(self):
        self.servicePackageRepository.Stop()

    ####################
    ## SERVICE MANAGER methods
    ####################
    
    def AddServiceManager( self, serviceManager ):
        """
        Add a service manager
        """
        # Try to reach the service manager
        try:
            AGServiceManagerIW( serviceManager.uri ).IsValid()
        except:
            log.exception("AddServiceManager: Invalid service manager url (%s)"
                          % serviceManager.uri)
            raise Exception("Service Manager is unreachable: "
                            + serviceManager.uri)

        if self.serviceManagers.has_key( serviceManager.uri ):
            raise Exception("Service Manager already present:" + 
                            serviceManager.uri)

        # Add service manager to list
        self.serviceManagers[serviceManager.uri] = serviceManager

    def RemoveServiceManager( self, serviceManagerToRemove ):
        """
        Remove a service manager
        """
        try:
            if self.serviceManagers.has_key(serviceManagerToRemove.uri):
                del self.serviceManagers[serviceManagerToRemove.uri]
        except:
            log.exception("Exception in AGNodeService.RemoveServiceManager.")
            raise Exception("AGNodeService.RemoveServiceManager failed: " + 
                            serviceManagerToRemove.uri )

    def GetServiceManagers( self ):
        """
        Get list of service managers 
        """
        return self.serviceManagers.values()

    ####################
    ## SERVICE methods
    ####################
    def AddService( self, servicePackageUri, serviceManagerUri, 
                    resourceToAssign, serviceConfig ):
        """
        Add a service package to the service manager.  
        """
        
        log.debug("AddService %s", servicePackageUri.name)
        
        serviceDescription = None
        
        # Add the service to the service manager
        try:
            serviceDescription = AGServiceManagerIW(
                serviceManagerUri ).AddService( servicePackageUri,
                                                resourceToAssign,
                                                serviceConfig )
        except SOAPException, e:
            log.exception("Error adding service")
            raise Exception("Error adding service: " + e.string )
        except Exception, e:
            log.exception("Error adding service")
            raise Exception("Error adding service" )
        
        # Set the identity for the service
        if self.profile:
            AGServiceManagerIW( serviceDescription.uri ).SetIdentity(
                self.profile )

        # Configure the service with the appropriate stream description
        try:
            self.__SendStreamsToService( serviceDescription.uri )
        except SetStreamException:
            log.exception("Unable to update service %s",
                          serviceDescription.name)
            raise Exception("Unable to update service %s",
                            serviceDescription.name)

        return serviceDescription

    def GetAvailableServices( self ):
        """Get list of available services """
        return self.servicePackageRepository.GetServiceDescriptions()

    def GetServices( self ):
        """Get list of installed services """
        services = []
        try:
            for serviceManager in self.serviceManagers.values():
                serviceSubset = AGServiceManagerIW(
                    serviceManager.uri ).GetServices()
                for service in serviceSubset:
                    service = AGServiceDescription( service.name,
                                                    service.description,
                                                    service.uri,
                                                    service.capabilities,
                                                    service.resource,
                                                    service.executable,
                                                    service.serviceManagerUri,
                                                    service.servicePackageUri )
                    services.append( service )
        except:
            log.exception("Exception in AGNodeService.GetServices.")
            raise Exception("AGNodeService.GetServices failed: %s" \
                            % str( sys.exc_value ) )
        return services

    def SetServiceEnabled(self, serviceUri, enabled):
        """
        Enable the service, and send it a stream configuration if we have one
        """
        try:
            AGServiceIW( serviceUri ).SetEnabled(enabled)

            if enabled:
                self.__SendStreamsToService( serviceUri )
        except:
            log.exception(serviceUri)
            raise 

    def SetServiceEnabledByMediaType(self, mediaType, enableFlag):
        """
        Enable/disable services that handle the given media type
        """
        serviceList = self.GetServices()
        for service in serviceList:
            serviceMediaTypes = map( lambda cap: cap.type,
                                     service.capabilities )
            if mediaType in serviceMediaTypes:
                self.SetServiceEnabled( service.uri, enableFlag) 

    def StopServices(self):
        """
        Stop all services
        """
        exceptionText = ""

        for serviceManager in self.serviceManagers.values():
            try:
                AGServiceManagerIW(serviceManager.uri).StopServices()
            except:
                log.exception("Exception stopping services")
                exceptionText += sys.exc_info()[1]
        
        if len(exceptionText):
            raise Exception(exceptionText)

    ####################
    ## CONFIGURATION methods
    ####################

    def SetStreams( self, streamDescriptionList ):
        """
        Set streams according to stream descriptions.
        The stream descriptions are applied to the installed services
        according to matching capabilities
        """

        exceptionText = ""

        # Save the stream descriptions
        self.streamDescriptionList = dict()
        for streamDescription in streamDescriptionList:
            self.streamDescriptionList[streamDescription.capability.type] = \
                                                  streamDescription

        # Send the streams to the services
        services = self.GetServices()
        for service in services:
            try:
                self.__SendStreamsToService( service.uri )
            except SetStreamException:
                raise

        if len(exceptionText):
            raise SetStreamException(exceptionText)
                    
    
    def AddStream( self, streamDescription ):
        self.streamDescriptionList[streamDescription.capability.type] = \
                                                  streamDescription

        # Send the streams to the services
        services = self.GetServices()
        for service in services:
            self.__SendStreamsToService( service.uri )


    def RemoveStream( self, streamDescription ):

        # Remove the stream from the list
        if self.streamDescriptionList.has_key(
            streamDescription.capability.type ):
            del self.streamDescriptionList[streamDescription.capability.type]

        # Stop services using that stream's media type
        # (er, not yet)



    def LoadConfiguration( self, configName ):
        """
        Load named node configuration
        """

        exceptionText = ""

        class IncomingService:
            def __init__(self):
                self.packageName = None
                self.resource = None
                self.executable = None
                self.parameters = None

        # Read config file
        configFile = os.path.join(self.configDir, configName)

        if not os.path.exists(configFile):
            raise Exception("Configuration file does not exist (%s)", configFile)
        else:
            log.info("Trying to load default configuration from: %s", configFile)

        try:
            config = ConfigParser.ConfigParser()
            config.read( configFile )

            #
            # Parse config file into usable structures
            #
            serviceManagerList = []
            serviceManagerSections = string.split( config.get("node", "servicemanagers") )
            for serviceManagerSection in serviceManagerSections:
                #
                # Create Service Manager
                #
                serviceManager = AGServiceManagerDescription( config.get( serviceManagerSection, "name" ), 
                                                              config.get( serviceManagerSection, "url" ) )

                #
                # Extract Service List
                #
                serviceList = [] 
                serviceSections = string.split( config.get( serviceManagerSection, "services" ) )
                for serviceSection in serviceSections:
                    #
                    # Read the resource
                    #
                    resourceSection = config.get( serviceSection, "resource" )
                    if resourceSection == "None":
                        resource = "None"
                    else:
                        resource = AGResource( config.get( resourceSection, "type" ),
                                               config.get( resourceSection, "resource" ) )

                    #
                    # Read the service config
                    #
                    serviceConfigSection = config.get( serviceSection, "serviceConfig" )
                    parameters = []
                    for parameter in config.options( serviceConfigSection ):
                        parameters.append( ValueParameter( parameter, 
                                                           config.get( serviceConfigSection,
                                                                       parameter ) ) )

                    #
                    # Add Service to List
                    #
                    incomingService = IncomingService()
                    incomingService.packageName = config.get( serviceSection, "packageName" )
                    incomingService.executable = config.get( serviceSection, "executable" )
                    incomingService.resource = resource
                    incomingService.parameters = parameters
                    serviceList.append( incomingService )
                    
                #
                # Add Service Manager to List
                #
                serviceManagerList.append( ( serviceManager, serviceList ) )
        except:
            log.exception("Error reading node configuration file")
            raise Exception("Error reading node configuration file")

        #
        # Add service managers and services
        #
        self.serviceManagers = dict()
        for serviceManager, serviceList in serviceManagerList:

            #
            # Skip unreachable service managers
            #
            try:
                AGServiceManagerIW( serviceManager.uri ).IsValid()
            except:
                log.info("AddServiceManager: Invalid service manager url (%s)"
                         % serviceManager.uri)
                exceptionText += "Couldn't reach service manager: %s" % serviceManager.name
                continue

            # Add service manager to list
            self.serviceManagers[serviceManager.uri] = serviceManager

            #
            # Remove all services from service manager
            #
            try:
                AGServiceManagerIW( serviceManager.uri ).RemoveServices()
            except:
                log.exception("Exception removing services from Service Manager")
                exceptionText += "Couldn't remove services from Service Manager: %s" %(serviceManager.name)

            #
            # Add Service to Service Manager
            #
            for service in serviceList:
                try:
                    serviceConfig = ServiceConfiguration( service.resource,
                                                          service.executable,
                                                          service.parameters)
                    AGServiceManagerIW( serviceManager.uri ).AddService( 
                        self.servicePackageRepository.GetServiceDescription( service.packageName ), 
                        service.resource,
                        serviceConfig )
                except:
                    log.exception("Exception adding service %s" % (service.packageName))
                    exceptionText += "Couldn't add service %s" % (service.packageName)

        if len(exceptionText):
            raise Exception(exceptionText)



    def StoreConfiguration( self, configName ):
      """
      Store node configuration with specified name
      """
      try:
                
        fileName = os.path.join(self.configDir, configName)

        # Catch inability to write config file
        if((not os.path.exists(self.configDir)) or
           (not os.access(self.configDir,os.W_OK)) or
           (os.path.exists(fileName) and not os.access(fileName, os.W_OK) )):
            log.exception("Can't write config file %s" % (fileName))
            raise Exception("Can't write config file %s" % (fileName))

        numServiceManagers = 0
        numServices = 0

        config = ConfigParser.ConfigParser()

        nodeSection = "node"
        config.add_section(nodeSection)

        node_servicemanagers = ""

        for serviceManager in self.serviceManagers.values():

            servicemanager_services = ""

            #
            # Create Service Manager section
            #
            serviceManagerSection = 'servicemanager%d' % numServiceManagers
            config.add_section( serviceManagerSection )
            node_servicemanagers += serviceManagerSection + " "
            config.set( serviceManagerSection, "name", serviceManager.name )
            config.set( serviceManagerSection, "url", serviceManager.uri )

            services = AGServiceManagerIW( serviceManager.uri ).GetServices()
            for service in services:
                # 
                # Create Resource section
                #
                if not service.resource or service.resource == "None":
                    resourceSection = "None"
                else:
                    resourceSection = 'resource%d' % numServices
                    config.add_section( resourceSection )
                    config.set( resourceSection, "type", service.resource.type )
                    config.set( resourceSection, "resource", service.resource.resource )

                # 
                # Create Service Config section
                #
                serviceConfigSection = 'serviceconfig%d' % numServices
                config.add_section( serviceConfigSection )
                serviceConfig = AGServiceIW( service.uri ).GetConfiguration()
                for parameter in serviceConfig.parameters:
                    config.set( serviceConfigSection, parameter.name, parameter.value )


                #
                # Create Service section
                #
                serviceSection = 'service%d' % numServices
                config.add_section( serviceSection )
                servicemanager_services += serviceSection + " "
                config.set( serviceSection, "packageName", os.path.basename( service.servicePackageUri ) )
                config.set( serviceSection, "executable", serviceConfig.executable )
                config.set( serviceSection, "resource", resourceSection )
                config.set( serviceSection, "serviceconfig", serviceConfigSection )

                numServices += 1

            config.set( serviceManagerSection, "services", servicemanager_services )
            numServiceManagers += 1

        config.set(nodeSection, "servicemanagers", node_servicemanagers )

        #
        # Write config file
        #
        fp = open( fileName, "w" )
        config.write(fp)
        fp.close()

      except:
        log.exception("Exception in AGNodeService.StoreConfiguration.")
        raise Exception("Error while saving configuration")
    


    def SetDefaultConfiguration( self, configName ):
        """
        Set the name of the default configuration
        """
        configs = self.GetConfigurations()

        # Trap error cases
        if configName not in configs:
            raise ValueError("Attempt to set default config to non-existent configuration")
        
        self.defaultConfig = configName

        # Write out the node service config file with the new default config name
        self.__WriteConfigFile()


    def GetConfigurations( self ):
        """Get list of available configurations"""
        files = os.listdir( self.configDir )
        return files


    ####################
    ## OTHER methods
    ####################

    def GetCapabilities( self ):
        """Get list of capabilities"""
        capabilities = []
        try:
            services = self.GetServices()
            for service in services:
                capabilitySubset = AGServiceIW( service.uri ).GetCapabilities()
                capabilities = capabilities + capabilitySubset

        except:
            log.exception("Exception in AGNodeService.GetCapabilities.")
            raise Exception("AGNodeService.GetCapabilities failed: " + str( sys.exc_value ) )
        return capabilities

    def SetIdentity(self, profile):
        """
        Push this identity out to the services, so they can identify
        the user running the node (e.g., rat)
        """

        self.profile = profile

        services = self.GetServices()
        for service in services:
            try:
                AGServiceIW( service.uri ).SetIdentity(profile)
            except:
                log.exception("Exception setting identity; continuing")

    ####################
    ## INTERNAL methods
    ####################


    def __ReadConfigFile( self ):
        """
        Read the node service configuration file

        Note:  it is read from the user config dir if it exists, 
               then from the system config dir
        """
        try:
            configFile = self.app.FindConfigFile(AGNodeService.NodeConfigFile)
        except:
            log.exception("Error finding config file: %s",
                          AGNodeService.NodeConfigFile)
            raise

        log.debug("DEFAULT NODE SERVICE CONFIG: %s", configFile)
        
        if configFile and os.path.exists(configFile):

            log.info("Reading node service config file: %s" % configFile)

            try:
                self.config = LoadConfig( configFile )
            except:
                log.exception("Error loading file.")
                raise

            # Process default config option
            if AGNodeService.defaultNodeConfigurationOption in self.config.keys():
                self.defaultConfig = self.config[AGNodeService.defaultNodeConfigurationOption]


    def __WriteConfigFile( self ):
        """
        Write the node service configuration file

        It is always written to the user's config directory
        """
        configFile = os.path.join(self.app.GetUserConfig().GetConfigDir(),
                                  AGNodeService.NodeConfigFile)

        log.info("Writing node service config file: %s" % configFile)

        # Update the config to local values
        self.config[AGNodeService.defaultNodeConfigurationOption] = self.defaultConfig

        # Save the config file
        SaveConfig( configFile, self.config )
        

    def __SendStreamsToService( self, serviceUri ):
        """
        Send stream description(s) to service
        """
        failedSends = ""

        serviceCapabilities = map(lambda cap: cap.type, 
            AGServiceIW( serviceUri ).GetCapabilities() )
        for streamDescription in self.streamDescriptionList.values():
            try:
                if streamDescription.capability.type in serviceCapabilities:
                    log.info("Sending stream (type=%s) to service: %s", 
                                streamDescription.capability.type,
                                serviceUri )
                    AGServiceIW( serviceUri ).ConfigureStream( streamDescription )
            except:
                log.exception("Exception in AGNodeService.ConfigureStreams.")
                failedSends += "Error updating %s %s\n" % \
                    ( streamDescription.capability.type, streamDescription.capability.role )

        if len(failedSends):
            raise SetStreamException(failedSends)



from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper

class AGNodeServiceI(SOAPInterface):
    """
    Interface Class for the AGNodeService
    """

    def __init__(self,impl):

        SOAPInterface.__init__(self, impl)

    def _authorize(self, *args, **kw):
        # Authorize everybody.
        return 1

    def AddServiceManager( self, svcMgrDescStruct ):
        """
        Interface to add service manager

        **Arguments:**
            *serviceManager* A description of the service manager
            
        **Raises:**
        **Returns:**
        """
        
        serviceManagerDesc = CreateAGServiceManagerDescription(svcMgrDescStruct)
        
        self.impl.AddServiceManager(serviceManagerDesc)

    def RemoveServiceManager( self, svcMgrDescStruct ):
        """
        Interface to remove service manager

        **Arguments:**
            *serviceManagerToRemove* A description of the service manager to remove
            
        **Raises:**
        **Returns:**
        """
        serviceManagerDesc = CreateAGServiceManagerDescription(svcMgrDescStruct)
        
        self.impl.RemoveServiceManager(serviceManagerDesc)

    def GetServiceManagers(self):
        """
        Interface to get list of service managers

        **Arguments:**
        **Raises:**

        **Returns:**
            a list of AGServiceManagerDescriptions
        """

        return self.impl.GetServiceManagers()

    def AddService( self, serviceDescStruct, serviceManagerUri, 
                    resourceStruct, serviceConfigStruct ):
        """
        Interface to add a service

        **Arguments:**
            *servicePackageUri* The URI from where the service package can be retrieved
            *serviceManagerUri* The URI of the service manager to which the service should be added
            *resourceToAssign* The resource to assign to the service
            *serviceConfig* The service configuration to apply after adding the service
            
        **Raises:**
        **Returns:**
        """
        
        if serviceDescStruct:
            serviceDescription = CreateAGServiceDescription(serviceDescStruct)
        else:
            serviceDescription = None

        if resourceStruct:
            resource = CreateResource(resourceStruct)
        else:
            resource = None
        if serviceConfigStruct:
            serviceConfig = CreateServiceConfiguration(serviceConfigStruct)
        else:
            serviceConfig = None
            
        return self.impl.AddService(serviceDescription, serviceManagerUri, 
                    resource, serviceConfig )

    def GetAvailableServices(self):
        """
        Interface to get a list of available services

        **Arguments:**
        **Raises:**

        **Returns:**
            a list of AGServiceDescriptions
        """

        return self.impl.GetAvailableServices()

    def GetServices(self):
        """
        Interface to get a list of services

        **Arguments:**
        **Raises:**

        **Returns:**
            a list of AGServiceDescriptions
        """

        return self.impl.GetServices()

    def SetServiceEnabled(self, serviceUri, enabled):
        """
        Interface to enable/disable a service

        **Arguments:**
            *serviceUri* The URI of the service to enable/disable
            *enabled* Flag whether to enable/disable
            
        **Raises:**
        **Returns:**
        """

        self.impl.SetServiceEnabled(serviceUri, enabled)

    def SetServiceEnabledByMediaType(self, mediaType, enableFlag):
        """
        Interface to enable/disable services by media type

        **Arguments:**
            *mediaType* Media type of services to enable/disable
            *enableFlag* Flag whether to enable/disable
            
        **Raises:**
        **Returns:**
        """

        self.impl.SetServiceEnabledByMediaType(mediaType, enableFlag)

    def StopServices(self):
        """
        Interface to stop services

        **Arguments:**
        **Raises:**
        **Returns:**
        """

        self.impl.StopServices()

    def SetStreams( self, streamDescriptionStructList ):
        """
        Interface to set streams used by node

        **Arguments:**
            *streamDescriptionList* List of StreamDescriptions
            
        **Raises:**
        **Returns:**
        """
        streamDescriptionList = map( lambda streamDescStruct:
                                     CreateStreamDescription(streamDescStruct),
                                     streamDescriptionStructList)
                                     
        self.impl.SetStreams(streamDescriptionList)

    def AddStream( self, streamDescriptionStruct ):
        """
        Interface to add a stream

        **Arguments:**
            *streamDescription* The StreamDescription to add

        **Raises:**
        **Returns:**
        """
        streamDescription = CreateStreamDescription(streamDescriptionStruct)

        self.impl.AddStream(streamDescription)

    def RemoveStream( self, streamDescriptionStruct ):
        """
        Interface to remove a stream

        **Arguments:**
            *streamDescription* The StreamDescription to remove
            
        **Raises:**
        **Returns:**
        """

        streamDescription = CreateStreamDescription(streamDescriptionStruct)

        self.impl.RemoveStream(streamDescription)

    def LoadConfiguration( self, configName ):
        """
        Interface to load a node configuration

        **Arguments:**
            *configName* Name under which to store the current configuration
            
        **Raises:**
        **Returns:**
        """

        self.impl.LoadConfiguration(configName)

    def StoreConfiguration( self, configName ):
        """
        Interface to store a node configuration

        **Arguments:**
            *configName* Name of config file to load
            
        **Raises:**
        **Returns:**
        """

        self.impl.StoreConfiguration(configName)

    def SetDefaultConfiguration( self, configName ):
        """
        Interface to set the default node configuration

        **Arguments:**
            *configName* Name of config file to use as default for the node
            
        **Raises:**
        **Returns:**
        """

        self.impl.SetDefaultConfiguration(configName)

    def GetConfigurations(self):
        """
        Interface to get a list of node configurations

        **Arguments:**
        **Raises:**

        **Returns:**
            Interface to get list of service 
            a list of node configuration names
        """

        return self.impl.GetConfigurations()

    def GetCapabilities(self):
        """
        Interface to get a list of the node's capabilities
        (aggregated from its services)

        **Arguments:**
        **Raises:**

        **Returns:**
            a list of the capabilities of the node
               (or, its services)
        """

        return self.impl.GetCapabilities()

    def SetIdentity(self, profileStruct):
        """
        Interface to set the identity of the node executor

        **Arguments:**
            *profile* ClientProfile of the person commanding the node
            
        **Raises:**
        **Returns:**
        """
        
        profile = CreateClientProfile(profileStruct)

        self.impl.SetIdentity(profile)




class AGNodeServiceIW(SOAPIWrapper):
    """
    Interface Wrapper Class for the AGNodeService
    """

    def __init__(self,url):

        SOAPIWrapper.__init__(self, url)

    def AddServiceManager( self, serviceManager ):
        self.proxy.AddServiceManager(serviceManager)

    def RemoveServiceManager( self, serviceManagerToRemove ):
        self.proxy.RemoveServiceManager(serviceManagerToRemove)

    def GetServiceManagers(self):
        smList = list()
        for sm in self.proxy.GetServiceManagers():   
            smList.append(CreateAGServiceManagerDescription(sm))
        return smList
            
    def AddService( self, servicePackageUri, serviceManagerUri, 
                    resourceToAssign, serviceConfig ):
        serviceDescStruct = self.proxy.AddService(servicePackageUri, serviceManagerUri, 
                    resourceToAssign, serviceConfig )
        serviceDescription = CreateAGServiceDescription(serviceDescStruct)
        return serviceDescription

    def GetAvailableServices(self):
        svcList = list()

        services = self.proxy.GetAvailableServices()

        for s in services:
            svcList.append(CreateAGServiceDescription(s))
        
        return svcList

    def GetServices(self):
        svcList = list()
        for s in self.proxy.GetServices():
            svcList.append(CreateAGServiceDescription(s))
        return svcList

    def SetServiceEnabled(self, serviceUri, enabled):
        self.proxy.SetServiceEnabled(serviceUri, enabled)

    def SetServiceEnabledByMediaType(self, mediaType, enableFlag):
        self.proxy.SetServiceEnabledByMediaType()

    def StopServices(self):
        self.proxy.StopServices()

    def SetStreams( self, streamDescriptionList ):
        self.proxy.SetStreams(streamDescriptionList)

    def AddStream( self, streamDescription ):
        self.proxy.AddStream(streamDescription)

    def RemoveStream( self, streamDescription ):
        self.proxy.RemoveStream(streamDescription)

    def LoadConfiguration( self, configName ):
        self.proxy.LoadConfiguration(configName)

    def StoreConfiguration( self, configName ):
        self.proxy.StoreConfiguration(configName)

    def SetDefaultConfiguration( self, configName ):
        self.proxy.SetDefaultConfiguration(configName)

    def GetConfigurations(self):
        return self.proxy.GetConfigurations()

    def GetCapabilities(self):
        capList = list()
        for s in self.proxy.GetCapabilities():
            capList.append(CreateCapability(s))
        return capList

    def SetIdentity(self, profile):
        self.proxy.SetIdentity(profile)

