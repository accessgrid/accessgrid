#-----------------------------------------------------------------------------
# Name:        AGNodeService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGNodeService.py,v 1.13 2003-02-21 22:35:01 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import os
import sys
import pickle
import string

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.hosting.pyGlobus.ServiceBase import ServiceBase

from AccessGrid.Types import AGServiceImplementationRepository, AGServiceDescription, ServiceConfiguration, AGServiceManagerDescription
from AccessGrid.AuthorizationManager import AuthorizationManager
from AccessGrid.hosting.pyGlobus.AGGSISOAP import faultType
from AccessGrid.Platform import GetConfigFilePath

class AGNodeService( ServiceBase ):
    """
    AGNodeService is the central engine of an Access Grid node.
    It is the contact point for clients to access underlying Service Managers
    and AGServices, for control and configuration of the node.
    """

    def __init__( self ):
        self.name = None
        self.description = None
        self.httpBaseUri = None
        self.serviceManagers = []
        self.authManager = AuthorizationManager()
        self.__ReadAuthFile()
        self.defaultConfig = None
        self.configDir = "config"
        self.servicesDir = "services"

        configFile = GetConfigFilePath("AGNodeService.cfg")
        if configFile:
            print "loading config file = ", configFile
            self.__ReadConfigFile( configFile )

        if self.defaultConfig:
            print "loading default config = ", self.defaultConfig
            try:
                self.LoadConfiguration( self.defaultConfig ) 
            except:
                print "Failed to load default configuration"

        self.serviceImplRepository = AGServiceImplementationRepository( 0, self.servicesDir )


    ####################
    ## AUTHORIZATION methods
    ####################

    def AddAuthorizedUser( self, authorizedUser ):
        """Add user to list of authorized users"""
        try:
            self.authManager.AddAuthorizedUser( authorizedUser )
            self.__PushAuthorizedUserList()
        except:
            print "Exception in AGNodeService.AddAuthorizedUser ", sys.exc_type, sys.exc_value
            raise faultType("Failed to add user authorization: " + authorizedUser )
    AddAuthorizedUser.soap_export_as = "AddAuthorizedUser"


    def RemoveAuthorizedUser( self, authorizedUser ):
        """Remove user from list of authorized users"""
        try:
            self.authManager.RemoveAuthorizedUser( authorizedUser )
            self.__PushAuthorizedUserList()
        except:
            print "Exception in AGNodeService.RemoveAuthorizedUser ", sys.exc_type, sys.exc_value
            raise faultType("Failed to remove user authorization: " + authorizedUser )
    RemoveAuthorizedUser.soap_export_as = "RemoveAuthorizedUser"


    ####################
    ## SERVICE MANAGER methods
    ####################

    def AddServiceManager( self, serviceManager ):
        """Add a service manager"""
        try:
            Client.Handle( serviceManager.uri ).get_proxy().Ping()
        except:
            print "Exception in AddServiceManager ", sys.exc_type, sys.exc_value
            raise faultType("Service Manager is unreachable: " + serviceManager.uri )


        try:
            self.serviceManagers.append( serviceManager )
            Client.Handle( serviceManager.uri ).get_proxy().SetAuthorizedUsers( self.authManager.GetAuthorizedUsers() )
        except:
            print "Exception in AGNodeService.AddServiceManager ", sys.exc_type, sys.exc_value
            raise faultType("Failed to set Service Manager user authorization: " + serviceManager.uri )
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
            print "Exception in AGNodeService.RemoveServiceManager ", sys.exc_type, sys.exc_value
            raise faultType("AGNodeService.RemoveServiceManager failed: " + serviceManagerToRemove.uri )
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
        return self.serviceImplRepository.GetServiceImplementations()
    GetAvailableServices.soap_export_as = "GetAvailableServices"


    def GetServices( self ):
        """Get list of installed services """
        services = []
        try:
            for serviceManager in self.serviceManagers:
                print "-- ", serviceManager.uri
                serviceSubset = Client.Handle( serviceManager.uri ).get_proxy().GetServices().data
                print "got services from sm"
                for service in serviceSubset:
                    print "  got service ", service.uri
                    service = AGServiceDescription( service.name, service.description, service.uri,
                                                    service.capabilities, service.resource,
                                                    service.serviceManagerUri, service.executable )
                    services = services + [ service ]

        except:
            print "Exception in AGNodeService.GetServices ", sys.exc_type, sys.exc_value
            raise faultType("AGNodeService.GetServices failed: " + str( sys.exc_value ) )
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
            try:
                serviceCapabilities = []
                serviceCapabilities = map(lambda cap: cap.type, Client.Handle( service.uri ).get_proxy().GetCapabilities() )
                for streamDescription in streamDescriptions:
                    if streamDescription.capability.type in serviceCapabilities:
                        print "   ", service.uri, streamDescription.location.host
                        Client.Handle( service.uri ).get_proxy().ConfigureStream( streamDescription )
            except:
                print "Exception in AGNodeService.ConfigureStreams ", sys.exc_type, sys.exc_value
                raise faultType("AGNodeService.ConfigureStreams failed: " + str( sys.exc_value ) )
    ConfigureStreams.soap_export_as = "ConfigureStreams"


#FIXME - LoadConfig and StoreConfig work with some level of reliability,
#        but do need a complete reworking.
    def LoadConfiguration( self, configName ):
        """Load named node configuration"""

        print "In load configuration "
        hadServiceException = 0
        hadServiceManagerException = 0
        services = []
        serviceConfigs = []
        try:

            #
            # Remove all services from service managers
            #
            for serviceManager in self.serviceManagers:
                Client.Handle( serviceManager.uri ).get_proxy().RemoveServices()


            #
            # Remove service managers
            #
            self.serviceManagers = []

        except:
            print "Exception in AGNodeService.LoadConfiguration ", sys.exc_type, sys.exc_value
            raise faultType("AGNodeService.LoadConfiguration failed: " + str( sys.exc_value ) )

        #
        # Load configuration file
        #
        print "Loading configuration file"
        inp = open( self.configDir + os.sep + configName, "r")
        print "read"
        while inp:
            try:
                o = pickle.load(inp)
                if isinstance( o, AGServiceManagerDescription ):
                    self.serviceManagers.append( o )
                if isinstance( o, AGServiceDescription ):
                    services.append( o )
                    o = pickle.load(inp)
                    if isinstance( o, ServiceConfiguration ):
                        serviceConfigs.append( o )
                    else:
                        print "CONFIG FILE LOAD PROBLEM : service config doesn't follow service; instead ", o.__class__
            except EOFError:
                inp.close()
                inp = None
            except:
                print "Exception in LoadConfiguration ", sys.exc_type, sys.exc_value
                raise faultType("AGNodeService.LoadConfiguration failed: " + str( sys.exc_value ) )

        #
        # Test service manager presence
        #
        print "Test service manager presence"
        serviceManagerList = []
        for serviceManager in self.serviceManagers:
            try:
                Client.Handle( serviceManager.uri ).get_proxy().Ping(  )
                serviceManagerList.append( serviceManager )
            except:
                print "* * Couldn't contact host ; uri=", serviceManager.uri
                hadServiceManagerException = 1

        # Update service manager list to contain only reachable service managers
        self.serviceManagers = serviceManagerList


        #
        # Remove all services from service managers
        #
        for serviceManager in self.serviceManagers:
            Client.Handle( serviceManager.uri ).get_proxy().RemoveServices()

        #
        # Add services to service managers
        #
        print "Add services to hosts"
        serviceIndex = 0
        for s in services:


            try:
                # - Add the service

                ## need map from service description to service implementation description;
                ## otherwise, don't know how to add a service from a service description

                s.description = serviceIndex
                serviceIndex = serviceIndex + 1

                print "*** trying to add service ", s.name, " to servicemanager ", s.serviceManagerUri
                Client.Handle( s.serviceManagerUri ).get_proxy().AddServiceDescription( s )
            except:
                print "Exception adding service", sys.exc_type, sys.exc_value
                hadServiceException = 1


        import time
        time.sleep(1)

        for s in services:

            try:
                smservices = Client.Handle( s.serviceManagerUri ).get_proxy().GetServices()
            except:
                continue

            for sms in smservices:
                if sms.description == s.description:
                    print "found service to configure ; desc = ", s.description
                    try:
                        # - Configure the service
## FIXME - all of this config store/load code is bad, but fetching this index by searching the list
##          should go even if the bad code stays for a while
                        index = services.index( s )
                        print "*** trying to configure service ", s.name, " using config ", serviceConfigs[index]
                        Client.Handle( sms.uri ).get_proxy().SetConfiguration( serviceConfigs[index] )
                    except:
                        print "Exception setting config", sys.exc_type, sys.exc_value
                        hadServiceException = 1

        if hadServiceManagerException and hadServiceException:
            raise faultType("AGNodeService.LoadConfiguration failed: service manager and service faults")
        elif hadServiceManagerException:
            raise faultType("AGNodeService.LoadConfiguration failed: service manager fault")
        elif hadServiceException:
            raise faultType("AGNodeService.LoadConfiguration failed: service fault")
    LoadConfiguration.soap_export_as = "LoadConfiguration"


    def StoreConfiguration( self, configName ):
        """Store current configuration using specified name"""

        print "in StoreConfiguration"
        try:
            out = open( self.configDir + os.sep + configName, "w")
            print "in StoreConfiguration"
            print "in StoreConfiguration"
            for serviceManager in self.serviceManagers:
                serviceManager = AGServiceManagerDescription( serviceManager.name, serviceManager.description, serviceManager.uri )
                print "serviceManager ", serviceManager.uri, serviceManager.__class__
                pickle.dump( serviceManager, out )
                svcs = Client.Handle( serviceManager.uri ).get_proxy().GetServices().data
                print svcs.__class__
                for svc in svcs:
                    svc = AGServiceDescription( svc.name, svc.description, svc.uri, svc.capabilities,
                                                svc.resource, svc.serviceManagerUri, svc.executable )
                    print "service ", svc.name, svc.uri, svc.serviceManagerUri, svc.executable
                    pickle.dump( svc, out )
                    configuration = 5
                    print "get proxy"
                    c = Client.Handle( svc.uri ).get_proxy()
                    print "ping"
                    c.Ping()
                    print "get config"
                    cfg = c.GetConfiguration()
                    cfg = ServiceConfiguration( cfg.resource, cfg.executable, cfg.parameters )
                    print c.__class__
                    print cfg.__class__
                    pickle.dump( cfg, out )
            out.close()

            inp = open( self.configDir + os.sep + configName, "r")
            while inp:
                try:
                    o = pickle.load(inp)
                    print "got object ", o, o.__class__
                except EOFError:
                    inp.close()
                    inp = None

        except:
            out.close()
            print "Exception in StoreConfiguration ", sys.exc_type, sys.exc_value
            raise faultType("AGNodeService.StoreConfiguration failed: " + str( sys.exc_value ))
    StoreConfiguration.soap_export_as = "StoreConfiguration"


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
                print "-- ", service.uri
                capabilitySubset = Client.Handle( service.uri ).get_proxy().GetCapabilities().data
                capabilities = capabilities + capabilitySubset

        except:
            print "Exception in AGNodeService.GetCapabilities ", sys.exc_type, sys.exc_value
            raise faultType("AGNodeService.GetCapabilities failed: " + str( sys.exc_value ) )
        return capabilities
    GetCapabilities.soap_export_as = "GetCapabilities"


    def Ping( self ):
        """
        Allows clients to determine whether node service is alive
        """
        return 1
    Ping.soap_export_as = "Ping"


    ####################
    ## INTERNAL methods
    ####################

    def __ReadAuthFile( self ):
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
                print "added user ", line

            # push authorization to service managers
            self.__PushAuthorizedUserList()


    def __PushAuthorizedUserList( self ):
        """Push the list of authorized users to service managers"""
        try:
            for serviceManager in self.serviceManagers:
                Client.Handle( serviceManager.uri ).get_proxy().SetAuthorizedUsers( self.authManager.GetAuthorizedUsers() )
        except:
            print "Exception in AGNodeService.RemoveAuthorizedUser ", sys.exc_type, sys.exc_value

    def __ReadConfigFile( self, configFile ):

        defaultNodeConfigurationOption = "Node Configuration.defaultNodeConfiguration"
        configDirOption = "Node Configuration.configDirectory"
        servicesDirOption = "Node Configuration.servicesDirectory"

        from AccessGrid.Utilities import LoadConfig
        config = LoadConfig( configFile )
        if defaultNodeConfigurationOption in config.keys():
            self.defaultConfig = config[defaultNodeConfigurationOption]
        if configDirOption in config.keys():
            self.configDir = config[configDirOption]
        if servicesDirOption in config.keys():
            self.servicesDir = config[servicesDirOption]

