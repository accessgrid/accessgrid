#-----------------------------------------------------------------------------
# Name:        AGNodeService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGNodeService.py,v 1.45 2004-03-04 23:04:47 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: AGNodeService.py,v 1.45 2004-03-04 23:04:47 turam Exp $"
__docformat__ = "restructuredtext en"

import os
import sys
import string
import thread
import ConfigParser
import logging
import shutil

from AccessGrid.hosting import Client
from AccessGrid.NetUtilities import GetHostname

from AccessGrid import Platform
from AccessGrid.Descriptions import AGServiceDescription
from AccessGrid.Descriptions import AGServiceManagerDescription
from AccessGrid.Types import ServiceConfiguration, AGResource
from AccessGrid.AuthorizationManager import AuthorizationManager
from AccessGrid.Utilities import LoadConfig
from AccessGrid.AGParameter import ValueParameter

log = logging.getLogger("AG.NodeService")

class SetStreamException(Exception): pass

class AGNodeService:
    """
    AGNodeService is the central engine of an Access Grid node.
    It is the contact point for clients to access underlying Service Managers
    and AGServices, for control and configuration of the node.
    """

    defaultNodeConfigurationOption = "Node Configuration.defaultNodeConfiguration"
    NodeConfigFile = "AGNodeService.cfg"


    def __init__( self ):
        self.serviceManagers = dict()
        self.authManager = AuthorizationManager()
        self.__ReadAuthFile()
        self.config = None
        self.defaultConfig = None
        self.configDir = os.path.join(Platform.GetUserConfigDir(),"nodeConfig")
        self.servicesDir = os.path.join(Platform.GetSystemConfigDir(),"services")
        self.streamDescriptionList = dict()
        self.profile = None

        #
        # Ensure that the necessary user directories exist
        #
        if not os.path.exists(self.servicesDir):
            log.error("Services directory does not exist: %s", self.servicesDir)

        if not os.path.exists(self.configDir): 
            try:
                log.info("Creating user node config directory %s", self.configDir)
                os.mkdir(self.configDir)

                # Copy node configurations from system node config directory
                # to user node config directory
                log.info("Copying system node configs to user node config dir")
                systemNodeConfigDir = os.path.join(Platform.GetSystemConfigDir(),"nodeConfig")
                configFiles = os.listdir(systemNodeConfigDir)
                for configFile in configFiles:
                    log.info("  node config: %s", configFile)
                    srcfile=os.path.join(systemNodeConfigDir,configFile)
                    destfile=os.path.join(self.configDir,configFile)
                    try:
                        shutil.copyfile(srcfile,destfile)
                    except:
                        log.exception("Couldn't copy file %s to %s" % (srcfile,destfile))

            except:
                log.exception("Couldn't create node service config dir: %s", self.configDir)

        #
        # Read the configuration file (directory options and such)
        #
        self.__ReadConfigFile()

        #
        # Start the service package repository
        # (now that the services directory is known)
        #
        self.servicePackageRepository = AGServicePackageRepository( 0, self.servicesDir )

    def LoadDefaultConfig(self):
    
        """Load default node configuration (service managers and services)"""
        
        if self.defaultConfig:
            log.debug("Loading default node config: %s", self.defaultConfig)
            try:
                self.LoadConfiguration( self.defaultConfig ) 
            except:
                log.exception("Exception loading default configuration.")
                raise Exception("Failed to load default configuration %s" %self.defaultConfig)

    def Stop(self):
        self.servicePackageRepository.Stop()

    ####################
    ## AUTHORIZATION methods
    ####################

    def AddAuthorizedUser( self, authorizedUser ):
        """Add user to list of authorized users"""
        try:
            self.authManager.AddAuthorizedUser( authorizedUser )
            self.__PushAuthorizedUserList()
        except:
            log.exception("Exception in AGNodeService.AddAuthorizedUser.")
            raise Exception("Failed to add user authorization: " + authorizedUser )


    def RemoveAuthorizedUser( self, authorizedUser ):
        """Remove user from list of authorized users"""
        try:
            self.authManager.RemoveAuthorizedUser( authorizedUser )
            self.__PushAuthorizedUserList()
        except:
            log.exception("Exception in AGNodeService.RemoveAuthorizedUser.")
            raise Exception("Failed to remove user authorization: " + authorizedUser )


    ####################
    ## SERVICE MANAGER methods
    ####################

    def AddServiceManager( self, serviceManager ):
        """Add a service manager"""

        # Try to reach the service manager
        try:
            Client.Handle( serviceManager.uri ).IsValid()
        except:
            log.exception("AddServiceManager: Invalid service manager url (%s)"
                          % serviceManager.uri)
            raise Exception("Service Manager is unreachable: "
                            + serviceManager.uri)

        if self.serviceManagers.has_key( serviceManager.uri ):
            raise Exception("Service Manager already present:" + 
                            serviceManager.uri)

        #
        # Add service manager to list
        #
        self.serviceManagers[serviceManager.uri] = serviceManager

        try:
            Client.Handle( serviceManager.uri ).get_proxy().SetAuthorizedUsers( 
                           self.authManager.GetAuthorizedUsers() )
        except:
            log.exception("Failed to set Service Manager user authorization:" + 
                            serviceManager.uri )
            raise Exception("Failed to set Service Manager user authorization:" + 
                            serviceManager.uri )

    def RemoveServiceManager( self, serviceManagerToRemove ):
        """Remove a service manager"""
        try:
            if self.serviceManagers.has_key(serviceManagerToRemove.uri):
                del self.serviceManagers[serviceManagerToRemove.uri]
        except:
            log.exception("Exception in AGNodeService.RemoveServiceManager.")
            raise Exception("AGNodeService.RemoveServiceManager failed: " + 
                            serviceManagerToRemove.uri )


    def GetServiceManagers( self ):
        """Get list of service managers """
        return self.serviceManagers.values()


    ####################
    ## SERVICE methods
    ####################

    def AddService( self, servicePackageUri, serviceManagerUri, 
                    resourceToAssign, serviceConfig ):
        """
        Add a service package to the service manager.  
        """
        serviceDescription = None

        # Add the service to the service manager
        try:
            serviceDescription = Client.Handle( serviceManagerUri ).GetProxy().AddService( servicePackageUri,
                                                                  resourceToAssign,
                                                                  serviceConfig )
        except Exception, e:
            log.exception("Error adding service")
            raise Exception("Error adding service: " + e.faultstring )
        
        # Set the identity for the service
        if self.profile:
            Client.Handle( serviceDescription.uri ).GetProxy().SetIdentity( self.profile )

        # Configure the service with the appropriate stream description
        try:
            self.__SendStreamsToService( serviceDescription.uri )
        except SetStreamException:
            log.exception("Unable to update service " + serviceDescription.name)
            raise Exception("Unable to update service " + serviceDescription.name)

        return serviceDescription


    def GetAvailableServices( self ):
        """Get list of available services """
        return self.servicePackageRepository.GetServiceDescriptions()


    def GetServices( self ):
        """Get list of installed services """
        services = []
        try:
            for serviceManager in self.serviceManagers.values():
                serviceSubset = Client.Handle( serviceManager.uri ).get_proxy().GetServices().data
                for service in serviceSubset:
                    service = AGServiceDescription( service.name, service.description, service.uri,
                                                    service.capabilities, service.resource,
                                                    service.executable, service.serviceManagerUri,
                                                    service.servicePackageUri )
                    services.append( service )

        except:
            log.exception("Exception in AGNodeService.GetServices.")
            raise Exception("AGNodeService.GetServices failed: " + str( sys.exc_value ) )
        return services

    def SetServiceEnabled(self, serviceUri, enabled):
        """
        Enable the service, and send it a stream configuration if we have one
        """

        try:
            Client.Handle( serviceUri ).GetProxy().SetEnabled(enabled)

            if enabled:
                self.__SendStreamsToService( serviceUri )
        except faultType,e:
            log.exception(serviceUri)
            raise Exception(e.faultstring)



    def SetServiceEnabledByMediaType(self, mediaType, enableFlag):
        """
        Enable/disable services that handle the given media type
        """

        serviceList = self.GetServices()
        for service in serviceList:
            serviceMediaTypes = map( lambda cap: cap.type, service.capabilities )
            print "service : ", service.name, serviceMediaTypes
            if mediaType in serviceMediaTypes:
                print " -- set enable ", enableFlag
                self.SetServiceEnabled( service.uri, enableFlag) 


    def StopServices(self):
        """
        Stop all services
        """
        exceptionText = ""

        for serviceManager in self.serviceManagers.values():
            try:
                Client.Handle(serviceManager.uri).GetProxy().StopServices()
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
            self.streamDescriptionList[streamDescription.capability.type] = streamDescription

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
        self.streamDescriptionList[streamDescription.capability.type] = streamDescription

        # Send the streams to the services
        services = self.GetServices()
        for service in services:
            self.__SendStreamsToService( service.uri )


    def RemoveStream( self, streamDescription ):

        # Remove the stream from the list
        if self.streamDescriptionList.has_key( streamDescription.capability.type ):
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


        #
        # Read config file
        #
        configFile = self.configDir + os.sep + configName

        if not os.path.exists(configFile):
            raise Exception("Configuration file does not exist")

        try:
            config = ConfigParser.ConfigParser()
            config.read( self.configDir + os.sep + configName )

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
                        parameters.append( ValueParameter( parameter, config.get( serviceConfigSection, parameter ) ) )

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
                Client.Handle( serviceManager.uri ).IsValid()
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
                Client.Handle( serviceManager.uri ).get_proxy().RemoveServices()
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
                    Client.Handle( serviceManager.uri ).get_proxy().AddService( self.servicePackageRepository.GetPackageUrl( service.packageName ), 
                                                                                service.resource,
                                                                                serviceConfig )
                except:
                    log.exception("Exception adding service %s" % (service.name))
                    exceptionText += "Couldn't add service %s" % (service.name)

        if len(exceptionText):
            raise Exception(exceptionText)



    def StoreConfiguration( self, configName ):
      """
      Store node configuration with specified name
      """
      try:
                
        file = self.configDir + os.sep + configName

        # Catch inability to write config file
        if((not os.path.exists(self.configDir)) or
           (not os.access(self.configDir,os.W_OK)) or
           (os.path.exists(file) and not os.access(file, os.W_OK) )):
            log.exception("Can't write config file %s" % (file))
            raise Exception("Can't write config file %s" % (file))

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

            services = Client.Handle( serviceManager.uri ).get_proxy().GetServices()
            for service in services:
                # 
                # Create Resource section
                #
                if service.resource == "None":
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
                serviceConfig = Client.Handle( service.uri ).get_proxy().GetConfiguration()
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
        fp = open( file, "w" )
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
                capabilitySubset = Client.Handle( service.uri ).get_proxy().GetCapabilities().data
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
                Client.Handle( service.uri ).GetProxy().SetIdentity(profile)
            except:
                log.exception("Exception setting identity; continuing")

    ####################
    ## INTERNAL methods
    ####################

    def __ReadAuthFile( self ):
        """
        Read the node service authorization file.  A user whose DN appears in
        the file is authorized to control the node, including authorizing 
        other users
        """

        # if config file exists
        nodeAuthFile = "nodeauth.cfg"
        if os.path.exists( nodeAuthFile ):
            # read it
            f = open( nodeAuthFile )
            lines = f.readlines()
            f.close()

            # add users therein to authorization manager
            for line in lines:
                line = string.strip(line)
                self.authManager.AddAuthorizedUser( line )

            # push authorization to service managers
            self.__PushAuthorizedUserList()


    def __PushAuthorizedUserList( self ):
        """
        Push the list of authorized users to service managers
        """
        try:
            for serviceManager in self.serviceManagers.values():
                Client.Handle( serviceManager.uri ).get_proxy().SetAuthorizedUsers( self.authManager.GetAuthorizedUsers() )
        except:
            log.exception("Exception in AGNodeService.RemoveAuthorizedUser.")

    def __ReadConfigFile( self ):
        """
        Read the node service configuration file

        Note:  it is read from the user config dir if it exists, 
               then from the system config dir
        """

        configFile = Platform.GetConfigFilePath(AGNodeService.NodeConfigFile)
        if configFile and os.path.exists(configFile):

            log.info("Reading node service config file: %s" % configFile)
            self.config = LoadConfig( configFile )

            # Process default config option
            if AGNodeService.defaultNodeConfigurationOption in self.config.keys():
                self.defaultConfig = self.config[AGNodeService.defaultNodeConfigurationOption]


    def __WriteConfigFile( self ):
        """
        Write the node service configuration file

        It is always written to the user's config directory
        """
        from AccessGrid.Utilities import SaveConfig

        configDir = Platform.GetUserConfigDir()
        configFile = os.path.join(configDir, AGNodeService.NodeConfigFile)

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
            Client.Handle( serviceUri ).get_proxy().GetCapabilities() )
        for streamDescription in self.streamDescriptionList.values():
            try:
                if streamDescription.capability.type in serviceCapabilities:
                    log.info("Sending stream (type=%s) to service: %s", 
                                streamDescription.capability.type,
                                serviceUri )
                    Client.Handle( serviceUri ).get_proxy().ConfigureStream( streamDescription )
            except:
                log.exception("Exception in AGNodeService.ConfigureStreams.")
                failedSends += "Error updating %s %s\n" % \
                    ( streamDescription.capability.type, streamDescription.capability.role )

        if len(failedSends):
            raise SetStreamException(failedSends)


from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid.Types import AGServicePackage, InvalidServicePackage
from AccessGrid import DataStore

class AGServicePackageRepository:
    """
    AGServicePackageRepository encapsulates knowledge about local service
    packages and avails them to clients (service managers) via http(s)
    """

    def __init__( self, port, servicesDir):

        # if port is 0, find a free port
        if port == 0:
            port = MulticastAddressAllocator().AllocatePort()

        self.httpd_port = port
        self.servicesDir = servicesDir
     
        self.serviceDescriptions = []

        # 
        # Define base url
        #
        prefix = "packages"
        self.baseUrl = 'https://%s:%d/%s/' % ( GetHostname(), self.httpd_port, prefix )

        #
        # Start the transfer server
        #
        self.s = DataStore.GSIHTTPTransferServer(('', self.httpd_port)) 
        self.s.RegisterPrefix(prefix, self)
        thread.start_new_thread( self.s.run, () )
        self.running = 1

    def Stop(self):
        if self.running:
            self.running = 0
            self.s.stop()

    def GetDownloadFilename(self, id_token, url_path):
        """
        Return the path to the file specified by the given url path
        """
        file = os.path.join(self.servicesDir, url_path)

        # Catch request for non-existent file
        if not os.access(file,os.R_OK):
            log.info("Attempt to download non-existent file: %s" % (file) )
            raise DataStore.FileNotFound(file)

        log.info("Download filename : %s", file)
        return file

    def GetPackageUrl( self, file ):
        return self.baseUrl + file

    def GetServiceDescriptions( self ):
        """
        Get list of local service descriptions
        """
        self.__ReadServicePackages()
        return self.serviceDescriptions


    def __ReadServicePackages( self ):
        """
        Read service packages from local directory and build service descriptions
        """
        self.serviceDescriptions = []

        invalidServicePackages = 0

        if os.path.exists(self.servicesDir):
            files = os.listdir(self.servicesDir)
            for file in files:
                if file.endswith(".zip"):
                    try:
                        servicePackage = AGServicePackage( self.servicesDir + os.sep + file)
                        serviceDesc = servicePackage.GetServiceDescription()
                    except InvalidServicePackage:
                        invalidServicePackages = invalidServicePackages + 1
                    serviceDesc.servicePackageUri = self.baseUrl + file
                    self.serviceDescriptions.append( serviceDesc )

        else:
            log.exception("AGServicePackageRepository.__ReadServicePackages: The service directory does not exist %s"%self.servicesDir)

        if invalidServicePackages:
            log.exception("AGServicePackageRepository.__ReadServicePackages: %i invalid service package found" %invalidServicePackages)
            raise InvalidServicePackage('%d invalid service package(s) found' % invalidServicePackages )





from AccessGrid.hosting.SOAPInterface import SOAPInterface

class AGNodeServiceI(SOAPInterface):
    """
    Interface Class for the AGNodeService
    """

    def __init__(self,impl):

        SOAPInterface.__init__(self, impl)

    def AddAuthorizedUser(self, authorizedUser):
        """
        Interface to add authorized users
        """

        self.impl.AddAuthorizedUser(authorizedUser)

    def RemoveAuthorizedUser( self, authorizedUser ):
        """
        Interface to remove authorized user
        """

        self.impl.RemoveAuthorizedUser(authorizedUser)

    def AddServiceManager( self, serviceManager ):
        """
        Interface to add service manager

        **Arguments:**
            *serviceManager* A description of the service manager
        **Raises:**
        **Returns:**
        """

        self.impl.AddServiceManager(serviceManager)

    def RemoveServiceManager( self, serviceManagerToRemove ):
        """
        Interface to remove service manager

        **Arguments:**
            *serviceManagerToRemove* A description of the service manager to remove
        **Raises:**
        **Returns:**
        """

        self.impl.RemoveServiceManager(serviceManagerToRemove)

    def GetServiceManagers(self):
        """
        Interface to get list of service managers

        **Arguments:**
        **Raises:**
        **Returns:**
            a list of AGServiceManagerDescriptions
        """

        return self.impl.GetServiceManagers()

    def AddService( self, servicePackageUri, serviceManagerUri, 
                    resourceToAssign, serviceConfig ):
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

        return self.impl.AddService(servicePackageUri, serviceManagerUri, 
                    resourceToAssign, serviceConfig )

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

        self.impl.SetServiceEnabledByMediaType()

    def StopServices(self):
        """
        Interface to stop services

        **Arguments:**
        **Raises:**
        **Returns:**
        """

        self.impl.StopServices()

    def SetStreams( self, streamDescriptionList ):
        """
        Interface to set streams used by node

        **Arguments:**
            *streamDescriptionList* List of StreamDescriptions
        **Raises:**
        **Returns:**
        """

        self.impl.SetStreams(streamDescriptionList)

    def AddStream( self, streamDescription ):
        """
        Interface to add a stream

        **Arguments:**
            *streamDescription* The StreamDescription to add
        **Raises:**
        **Returns:**
        """

        self.impl.AddStream(streamDescription)

    def RemoveStream( self, streamDescription ):
        """
        Interface to remove a stream

        **Arguments:**
            *streamDescription* The StreamDescription to remove
        **Raises:**
        **Returns:**
        """

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

    def SetIdentity(self, profile):
        """
        Interface to set the identity of the node executor

        **Arguments:**
            *profile* ClientProfile of the person commanding the node
        **Raises:**
        **Returns:**
        """

        self.impl.SetIdentity()

