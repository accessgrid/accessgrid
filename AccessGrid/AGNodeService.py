#-----------------------------------------------------------------------------
# Name:        AGNodeService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGNodeService.py,v 1.25 2003-04-28 20:12:26 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import os
import sys
import pickle
import string
import thread
import string
import ConfigParser
import logging

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.hosting.pyGlobus.ServiceBase import ServiceBase
from AccessGrid.hosting.pyGlobus.Utilities import GetHostname

from AccessGrid.Descriptions import AGServiceDescription, AGServiceManagerDescription
from AccessGrid.Types import ServiceConfiguration, AGResource
from AccessGrid.AuthorizationManager import AuthorizationManager
from AccessGrid.Platform import GetConfigFilePath

from AccessGrid.AGParameter import ValueParameter

log = logging.getLogger("AG.NodeService")

class AGNodeService( ServiceBase ):
    """
    AGNodeService is the central engine of an Access Grid node.
    It is the contact point for clients to access underlying Service Managers
    and AGServices, for control and configuration of the node.
    """

    defaultNodeConfigurationOption = "Node Configuration.defaultNodeConfiguration"
    configDirOption = "Node Configuration.configDirectory"
    servicesDirOption = "Node Configuration.servicesDirectory"


    def __init__( self ):
        self.name = None
        self.description = None
        self.httpBaseUri = None
        self.serviceManagers = []
        self.authManager = AuthorizationManager()
        self.__ReadAuthFile()
        self.config = None
        self.defaultConfig = None
        self.configDir = "config"
        self.servicesDir = "services"

        #
        # Read the configuration file (directory options and such)
        #
        self.__ReadConfigFile()

        #
        # Start the service package repository
        # (now that the services directory is known)
        #
        self.servicePackageRepository = AGServicePackageRepository( 0, self.servicesDir )

        #
        # Load default node configuration (service managers and services)
        #
        if self.defaultConfig:
            log.debug("Loading default node config: %s", self.defaultConfig)
            try:
                self.LoadConfiguration( self.defaultConfig ) 
            except:
                log.exception("Exception loading default configuration.")

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
    AddAuthorizedUser.soap_export_as = "AddAuthorizedUser"


    def RemoveAuthorizedUser( self, authorizedUser ):
        """Remove user from list of authorized users"""
        try:
            self.authManager.RemoveAuthorizedUser( authorizedUser )
            self.__PushAuthorizedUserList()
        except:
            log.exception("Exception in AGNodeService.RemoveAuthorizedUser.")
            raise Exception("Failed to remove user authorization: " + authorizedUser )
    RemoveAuthorizedUser.soap_export_as = "RemoveAuthorizedUser"


    ####################
    ## SERVICE MANAGER methods
    ####################

    def AddServiceManager( self, serviceManager ):
        """Add a service manager"""

        # Try to reach the service manager
        if not Client.Handle( serviceManager.uri ).IsValid():
            log.exception("Exception in AddServiceManager.")
            raise Exception("Service Manager is unreachable: "
                            + serviceManager.uri )

        #
        # Add service manager to list
        #
        try:
            self.serviceManagers.append( serviceManager )
            Client.Handle( serviceManager.uri ).get_proxy().SetAuthorizedUsers( 
                           self.authManager.GetAuthorizedUsers() )
        except:
            log.exception("Exception in AGNodeService.AddServiceManager.")
            raise Exception("Failed to set Service Manager user authorization: " + 
                            serviceManager.uri )
        
    AddServiceManager.soap_export_as = "AddServiceManager"

    def RemoveServiceManager( self, serviceManagerToRemove ):
        """Remove a service manager"""
        try:
            for i in range( len(self.serviceManagers) ):
                serviceManager = self.serviceManagers[i]
                if serviceManager.uri == serviceManagerToRemove.uri:
                    del self.serviceManagers[i]

                    break
        except:
            log.exception("Exception in AGNodeService.RemoveServiceManager.")
            raise Exception("AGNodeService.RemoveServiceManager failed: " + 
                            serviceManagerToRemove.uri )
    RemoveServiceManager.soap_export_as = "RemoveServiceManager"


    def GetServiceManagers( self ):
        """Get list of service managers """
        return self.serviceManagers
    GetServiceManagers.soap_export_as = "GetServiceManagers"


    ####################
    ## SERVICE methods
    ####################

    def GetAvailableServices( self ):
        """Get list of available services """
        return self.servicePackageRepository.GetServiceDescriptions()
    GetAvailableServices.soap_export_as = "GetAvailableServices"


    def GetServices( self ):
        """Get list of installed services """
        services = []
        try:
            for serviceManager in self.serviceManagers:
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
    GetServices.soap_export_as = "GetServices"


    ####################
    ## CONFIGURATION methods
    ####################

    def ConfigureStreams( self, streamDescriptions ):
        """
        Configure streams according to stream descriptions.
        The stream descriptions are applied to the installed services
        according to matching capabilities
        """
        services = self.GetServices()
        for service in services:
            serviceCapabilities = []
            serviceCapabilities = map(lambda cap: cap.type, Client.Handle( service.uri ).get_proxy().GetCapabilities() )
            for streamDescription in streamDescriptions:
                try:
                    if streamDescription.capability.type in serviceCapabilities:
                        Client.Handle( service.uri ).get_proxy().ConfigureStream( streamDescription )
                except:
                    log.exception("Exception in AGNodeService.ConfigureStreams.")
                    
    ConfigureStreams.soap_export_as = "ConfigureStreams"


    def LoadConfiguration( self, configName ):
        """
        Load named node configuration
        """

        class IncomingService:
            def __init__(self):
                self.packageName = None
                self.resource = None
                self.executable = None
                self.parameters = None

        #
        # Read config file
        #
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


        #
        # Add service managers and services
        #
        self.serviceManagers = []
        for serviceManager, serviceList in serviceManagerList:

            #
            # Skip unreachable service managers
            #
            if not Client.Handle( serviceManager.uri ).IsValid():
                log.info("Couldn't reach service manager: %s", serviceManager.uri)
                continue

            # Add service manager to list
            self.serviceManagers.append( serviceManager )

            #
            # Remove all services from service manager
            #
            Client.Handle( serviceManager.uri ).get_proxy().RemoveServices()

            #
            # Add Service to Service Manager
            #
            for service in serviceList:
                serviceConfig = ServiceConfiguration( service.resource, service.executable, service.parameters)
                Client.Handle( serviceManager.uri ).get_proxy().AddService( self.servicePackageRepository.GetPackageUrl( service.packageName ), 
                                                                            service.resource,
                                                                            serviceConfig )
    LoadConfiguration.soap_export_as = "LoadConfiguration"


    def StoreConfiguration( self, configName ):
      """
      Store node configuration with specified name
      """
      try:
        numServiceManagers = 0
        numServices = 0

        config = ConfigParser.ConfigParser()

        nodeSection = "node"
        config.add_section(nodeSection)

        node_servicemanagers = ""

        for serviceManager in self.serviceManagers:

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
        file = self.configDir + os.sep + configName
        fp = open( file, "w" )
        config.write(fp)
        fp.close()

      except:
        log.exception("Exception in AGNodeService.StoreConfiguration.")

    StoreConfiguration.soap_export_as = "StoreConfiguration"


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

    SetDefaultConfiguration.soap_export_as = "SetDefaultConfiguration"

    def GetConfigurations( self ):
        """Get list of available configurations"""
        files = os.listdir( self.configDir )
        return files
    GetConfigurations.soap_export_as = "GetConfigurations"


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
    GetCapabilities.soap_export_as = "GetCapabilities"


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
            for serviceManager in self.serviceManagers:
                Client.Handle( serviceManager.uri ).get_proxy().SetAuthorizedUsers( self.authManager.GetAuthorizedUsers() )
        except:
            log.exception("Exception in AGNodeService.RemoveAuthorizedUser.")

    def __ReadConfigFile( self ):
        """
        Read the node service configuration file
        """

        from AccessGrid.Utilities import LoadConfig

        configFile = GetConfigFilePath("AGNodeService.cfg")
        if configFile and os.path.exists(configFile):

            log.info("Reading node service config file: %s" % configFile)

            self.config = LoadConfig( configFile )

            # Process default config option
            if AGNodeService.defaultNodeConfigurationOption in self.config.keys():
                self.defaultConfig = self.config[AGNodeService.defaultNodeConfigurationOption]

            # Process config dir option
            if AGNodeService.configDirOption in self.config.keys():
                self.configDir = self.config[AGNodeService.configDirOption]
                # If relative path in config file, use SystemConfigDir as the base
                if not os.path.isabs(self.configDir):
                    self.configDir = GetConfigFilePath(self.configDir)

            # Process services dir option
            if AGNodeService.servicesDirOption in self.config.keys():
                self.servicesDir = self.config[AGNodeService.servicesDirOption]
                # If relative path in config file, use SystemConfigDir as the base
                if not os.path.isabs(self.servicesDir):
                    self.servicesDir = GetConfigFilePath(self.servicesDir)


    def __WriteConfigFile( self ):
        """
        Write the node service configuration file
        """
        from AccessGrid.Utilities import SaveConfig

        configFile = GetConfigFilePath("AGNodeService.cfg")
        if configFile and os.path.exists(configFile):

            log.info("Writing node service config file: %s" % configFile)

            # Update the config to local values
            self.config[AGNodeService.configDirOption] = self.configDir
            self.config[AGNodeService.servicesDirOption] = self.servicesDir
            self.config[AGNodeService.defaultNodeConfigurationOption] = self.defaultConfig

            # Save the config file
            SaveConfig( configFile, self.config )
        


from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid.DataStore import GSIHTTPTransferServer
from AccessGrid.Types import AGServicePackage, InvalidServicePackage

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
        self.s = GSIHTTPTransferServer(('', self.httpd_port)) 
        self.s.RegisterPrefix(prefix, self)
        thread.start_new_thread( self.s.run, () )
        self.running = 1

    def Stop(self):
        if self.running:
            self.running = 0
            self.s.stop()

    def GetDownloadFilename(self, id_token, url_path):
        """
        Implementation of Handler interface for DataStore
        """
        log.info("Download filename : %s",
                      self.servicesDir + os.sep + url_path)
        return self.servicesDir + os.sep + url_path 

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
                    except InvalidServicePackage, InvalidServiceDescription:
                        invalidServicePackages = invalidServicePackages + 1
                    serviceDesc.servicePackageUri = self.baseUrl + file
                    self.serviceDescriptions.append( serviceDesc )

        if invalidServicePackages:
            raise InvalidServicePackage('%d invalid service package(s) found' % invalidServicePackages )

