#-----------------------------------------------------------------------------
# Name:        AGNodeService.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGNodeService.py,v 1.87 2005-01-06 22:24:50 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: AGNodeService.py,v 1.87 2005-01-06 22:24:50 turam Exp $"
__docformat__ = "restructuredtext en"

import os
import sys
import string
import ConfigParser
import shutil
import urlparse

from AccessGrid import Log
from AccessGrid import Version
from AccessGrid.Toolkit import Service
from AccessGrid.hosting import Client
from AccessGrid.Descriptions import AGServiceDescription
from AccessGrid.Descriptions import AGServiceManagerDescription
from AccessGrid.AGServiceManager import AGServiceManagerI, AGServiceManagerIW
from AccessGrid.AGService import AGServiceIW
from AccessGrid.Descriptions import ResourceDescription
from AccessGrid.Utilities import LoadConfig, SaveConfig
from AccessGrid.AGParameter import ValueParameter
from AccessGrid.Descriptions import CreateAGServiceManagerDescription
from AccessGrid.Descriptions import CreateAGServiceDescription
from AccessGrid.Descriptions import CreateCapability
from AccessGrid.Descriptions import CreateResourceDescription
from AccessGrid.Descriptions import CreateClientProfile
from AccessGrid.Descriptions import CreateStreamDescription
from AccessGrid.Descriptions import CreateParameter

from SOAPpy.Types import SOAPException

log = Log.GetLogger(Log.NodeService)

class SetStreamException(Exception): pass
class ServiceManagerAlreadyExists(Exception): pass
class ServiceManagerNotFound(Exception): pass


class AGNodeService:
    """
    AGNodeService is the central engine of an Access Grid node.
    It is the contact point for clients to access underlying Service Managers
    and AGServices, for control and configuration of the node.
    """

    ServiceType = '_nodeservice._tcp'

    def __init__( self, app=None ):
        if app:
            self.app = app
        else:
            self.app = Service.instance()
            
        self.serviceManagers = dict()
        self.sysNodeConfigDir = self.app.GetToolkitConfig().GetNodeConfigDir()
        self.userNodeConfigDir = self.app.GetUserConfig().GetNodeConfigDir()
        self.servicesDir = self.app.GetToolkitConfig().GetNodeServicesDir()

        self.streamDescriptionList = dict()
        self.profile = None
        
        self.uri = 0

    ####################
    ## SERVICE MANAGER methods
    ####################
   
    def AddServiceManager( self, serviceManagerUrl ):
        """
        Add a service manager
        """
        log.info("NodeService.AddServiceManager")
        log.debug("  serviceManagerUrl = %s", serviceManagerUrl)
        
        # Check whether the service manager has already been added
        if self.serviceManagers.has_key( serviceManagerUrl ):
            raise ServiceManagerAlreadyExists(serviceManagerUrl)
                            
        # Try to reach the service manager
        try:
            serviceManagerDescription = AGServiceManagerIW( serviceManagerUrl ).GetDescription()
            AGServiceManagerIW( serviceManagerUrl ).SetNodeServiceUrl(self.uri)
        except Exception, e:
            if e.args[0].endswith('could not be resolved'):
                parts = urlparse.urlparse(serviceManager.uri)
                host,port = parts[1].split(':')
                raise Exception('Host name %s could not be resolved'%
                                host)
            elif e.args[0].endswith('(Connection refused)'):
                parts = urlparse.urlparse(serviceManager.uri)
                host,port = parts[1].split(':')
                raise Exception('Connection refused on port %s' %
                                port)
            else:
                log.exception("Failed to add service manager %s", serviceManager.uri)
                raise
        except:
            log.exception("AddServiceManager: Invalid service manager url (%s)"
                          % serviceManagerUrl)
            raise Exception("Service Manager is unreachable at "
                            + serviceManagerUrl)

        # Add service manager to list
        self.serviceManagers[serviceManagerUrl] = serviceManagerDescription
        
        return serviceManagerDescription

    def RemoveServiceManager( self, serviceManagerUrl ):
        """
        Remove a service manager
        """
        log.info("NodeService.RemoveServiceManager")
        log.debug("  url = %s", serviceManagerUrl)
        
        try:
            if self.serviceManagers.has_key(serviceManagerUrl):
                del self.serviceManagers[serviceManagerUrl]
            else:
                raise ServiceManagerNotFound(serviceManagerUrl)
        except:
            log.exception("Exception in AGNodeService.RemoveServiceManager.")
            raise Exception("AGNodeService.RemoveServiceManager failed: " + 
                            serviceManagerUrl )

    def GetServiceManagers( self ):
        """
        Get list of service managers 
        """
        log.info("NodeService.GetServiceManagers")
        return self.serviceManagers.values()

    ####################
    ## SERVICE methods
    ####################

    def GetServices( self ):
        """Get list of installed services """
        log.info("NodeService.GetServices")
        services = []
        try:
            for serviceManager in self.serviceManagers.values():
                serviceSubset = AGServiceManagerIW(
                    serviceManager.uri ).GetServices()
                services += serviceSubset
        except:
            log.exception("Exception in AGNodeService.GetServices.")
            raise Exception("AGNodeService.GetServices failed: %s" \
                            % str( sys.exc_value ) )
        return services

    def SetServiceEnabled(self, serviceUri, enabled):
        """
        Enable the service, and send it a stream configuration if we have one
        """
        log.info("NodeService.SetServiceEnabled")
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
        log.info("NodeService.SetServiceEnabledByMediaType")
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
        log.info("NodeService.StopServices")
        exceptionText = ""

        for serviceManager in self.serviceManagers.values():
            try:
                AGServiceManagerIW(serviceManager.uri).StopServices()
            except:
                log.exception("Exception stopping services")
                exceptionText += str(sys.exc_info()[1])
        
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

        log.info("NodeService.SetStreams")
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
        log.info("NodeService.AddStream")
        self.streamDescriptionList[streamDescription.capability.type] = \
                                                  streamDescription

        # Send the streams to the services
        services = self.GetServices()
        for service in services:
            self.__SendStreamsToService( service.uri )


    def RemoveStream( self, streamDescription ):

        log.info("NodeService.RemoveStream")
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

        log.info("NodeService.LoadConfiguration")
        exceptionText = ""

        class IncomingService:
            def __init__(self):
                self.packageName = None
                self.resource = None
                self.parameters = None

        # Read config file
        configFile = os.path.join(self.userNodeConfigDir, configName)

        if not os.path.exists(configFile):
            raise Exception("Configuration file does not exist (%s)" % configFile)
        else:
            log.info("Trying to load node configuration from: %s", configFile)

        try:
            config = ConfigParser.ConfigParser()
            config.optionxform = str
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
                    if config.has_option(serviceSection,'resource'):
                        resourceSection = config.get( serviceSection, "resource" )
                        resource = ResourceDescription( config.get( resourceSection, "resource" ) )
                    else:
                        resource = 0

                    #
                    # Read the service config
                    #
                    parameters = []
                    if config.has_option(serviceSection,'serviceConfig'):
                        serviceConfigSection = config.get( serviceSection, "serviceConfig" )
                        for parameter in config.options( serviceConfigSection ):
                            parameters.append( ValueParameter( parameter, 
                                                               config.get( serviceConfigSection,
                                                                           parameter ) ) )

                    #
                    # Add Service to List
                    #
                    incomingService = IncomingService()
                    incomingService.packageName = config.get( serviceSection, "packageName" )
                    incomingService.resource = resource
                    incomingService.parameters = parameters
                    serviceList.append( incomingService )
                    
                #
                # Add Service Manager to List
                #
                serviceManagerList.append( ( serviceManager, serviceList ) )
        except:
            log.exception("Error reading node configuration file %s" % configFile)
            raise Exception("Error reading node configuration file")

        #
        # Add service managers and services
        #
        self.serviceManagers = dict()
        for serviceManager, serviceList in serviceManagerList:
        
            serviceManagerProxy = AGServiceManagerIW(serviceManager.uri)

            #
            # Skip unreachable service managers
            #
            try:
                serviceManagerProxy.IsValid()
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
                serviceManagerProxy.RemoveServices()
            except:
                log.exception("Exception removing services from Service Manager")
                exceptionText += "Couldn't remove services from Service Manager: %s" %(serviceManager.name)
                
            servicePackages = serviceManagerProxy.GetServicePackageDescriptions()
                
            #
            # Add Service to Service Manager
            #
            for service in serviceList:
                try:
                
                    # Actually add the service to the servicemgr
                    serviceDesc = AGServiceManagerIW( serviceManager.uri ).AddServiceByName(service.packageName)
                    
                    serviceProxy = AGServiceIW(serviceDesc.uri)
                    
                    # Set the resource
                    if service.resource:
                        serviceProxy.SetResource(service.resource)
                    
                    # Set the configuration
                    if service.parameters:
                        serviceProxy.SetConfiguration(service.parameters)
                    
                    # Set the identity to be used by the service
                    if self.profile:
                        serviceProxy.SetIdentity(self.profile )
                    else:
                        log.info("Not setting identity for service %s; no profile",
                                 serviceDesc.name)
                        
                        
                except:
                    log.exception("Exception adding service %s" % (service.packageName))
                    exceptionText += "Couldn't add service %s" % (service.packageName)

        if len(exceptionText):
            raise Exception(exceptionText)

    def NeedMigrateNodeConfig(self,configName):
        log.info("NodeService.StoreConfiguration")
        configFile = os.path.join(self.userNodeConfigDir, configName)

        ret = 0
        
        f = file(configFile,'r')
        firstLine = f.readline()
        f.close()
        if firstLine.startswith('# AGTk 2.3'):
            log.debug("Node config %s already migrated; not migrating", configName)
            return 0

        cp = ConfigParser.ConfigParser()
        cp.read(configFile)
        for section in cp.sections():
            if section.startswith('servicemanager'):
                url = cp.get(section,'url')
                name = cp.get(section,'name')
                
                if url.find('12000') >= 0:
                    ret = 1
                    break
                if name.find('12000') >= 0:
                    ret = 1
                    break
        return ret
                
    def MigrateNodeConfig(self,configName):
        log.info("NodeService.StoreConfiguration")

        configFile = os.path.join(self.userNodeConfigDir, configName)

        # do migration
        wasMigrated = 0
        
        cp = ConfigParser.ConfigParser()
        cp.read(configFile)
        for section in cp.sections():
            if section.startswith('servicemanager'):
                url = cp.get(section,'url')
                name = cp.get(section,'name')
                
                if url.find('12000') >= 0:
                    url = url.replace('12000','11000')
                    cp.set(section,'url',url)
                    wasMigrated = 1
                if name.find('12000') >= 0:
                    name = name.replace('12000','11000')
                    cp.set(section,'name',name)
                    wasMigrated = 1

        if wasMigrated:
            log.info("Migrating node config %s", configName)
            
            orgConfigFile = configFile + ".org"
            log.info("Original node config moved to %s", orgConfigFile)
            os.rename(configFile,orgConfigFile)
            
            # write file
            f = file(configFile,'w')
            f.write("# AGTk %s node configuration\n" % (Version.GetVersion()))
            cp.write(f)
            f.close()
        else:
            log.info("Migration unnecessary")
            
                    

    def StoreConfiguration( self, configName ):
        """
        Store node configuration with specified name
        """
        log.info("NodeService.StoreConfiguration")
        try:

            fileName = os.path.join(self.userNodeConfigDir, configName)

            # Catch inability to write config file
            if((not os.path.exists(self.userNodeConfigDir)) or
               (not os.access(self.userNodeConfigDir,os.W_OK)) or
               (os.path.exists(fileName) and not os.access(fileName, os.W_OK) )):
                log.exception("Can't write config file %s" % (fileName))
                raise Exception("Can't write config file %s" % (fileName))

            numServiceManagers = 0
            numServices = 0

            config = ConfigParser.ConfigParser()
            config.optionxform = str

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
                
                    serviceSection = 'service%d' % numServices
                    config.add_section( serviceSection )

                    # 
                    # Create Resource section
                    #
                    if service.resource:
                        resourceSection = 'resource%d' % numServices
                        config.add_section( resourceSection )
                        config.set( resourceSection, "type", service.resource.type )
                        config.set( resourceSection, "resource", service.resource.resource )
                        config.set( serviceSection, "resource", resourceSection )

                    # 
                    # Create Service Config section
                    #
                    serviceConfig = AGServiceIW( service.uri ).GetConfiguration()
                    if serviceConfig:
                        serviceConfigSection = 'serviceconfig%d' % numServices
                        config.set( serviceSection, "serviceConfig", serviceConfigSection )
                        config.add_section( serviceConfigSection )
                        for parameter in serviceConfig:
                            config.set( serviceConfigSection, parameter.name, parameter.value )


                    #
                    # Create Service section
                    #
                    servicemanager_services += serviceSection + " "
                    config.set( serviceSection, "packageName", os.path.basename( service.packageFile ) )

                    numServices += 1

                config.set( serviceManagerSection, "services", servicemanager_services )
                numServiceManagers += 1

            config.set(nodeSection, "servicemanagers", node_servicemanagers )

            #
            # Write config file
            #
            fp = open( fileName, "w" )
            fp.write("# AGTk %s node configuration\n" % (Version.GetVersion()))
            config.write(fp)
            fp.close()

        except:
            log.exception("Exception in AGNodeService.StoreConfiguration.")
            raise Exception("Error while saving configuration")
    
    def GetConfigurations( self ):
        """Get list of available configurations"""
        log.info("NodeService.GetConfigurations")
        files = os.listdir( self.userNodeConfigDir )
        return files


    ####################
    ## OTHER methods
    ####################

    def GetCapabilities( self ):
        """Get list of capabilities"""
        log.info("NodeService.GetCapabilities")
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

    def Stop(self):
        pass
        
    def SetUri(self,uri):
        self.uri = uri
        
    def GetUri(self):
        return self.uri
    

    ####################
    ## INTERNAL methods
    ####################


    def __SendStreamsToService( self, serviceUri ):
        """
        Send stream description(s) to service
        """
        
        log.info("NodeService.__SendStreamsToService")
        failedSends = ""
        
        serviceCapabilities = map(lambda cap: cap.type, 
            AGServiceIW( serviceUri ).GetCapabilities() )
        for streamDescription in self.streamDescriptionList.values():
            try:
                if streamDescription.capability.type in serviceCapabilities:
                    log.info("Sending stream (type=%s) to service: %s", 
                                streamDescription.capability.type,
                                serviceUri )
                    AGServiceIW( serviceUri ).SetStream( streamDescription )
            except:
                log.exception("Exception in AGNodeService.__SendStreamsToService.")
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

    def AddServiceManager( self, serviceManagerUrl ):
        """
        Interface to add service manager

        **Arguments:**
            *serviceManager* A description of the service manager
            
        **Raises:**
        **Returns:**
        """
        
        return self.impl.AddServiceManager(serviceManagerUrl)

    def RemoveServiceManager( self, serviceManagerUrl ):
        """
        Interface to remove service manager

        **Arguments:**
            *serviceManagerToRemove* A description of the service manager to remove
            
        **Raises:**
        **Returns:**
        """
        self.impl.RemoveServiceManager(serviceManagerUrl)

    def GetServiceManagers(self):
        """
        Interface to get list of service managers

        **Arguments:**
        **Raises:**

        **Returns:**
            a list of AGServiceManagerDescriptions
        """

        return self.impl.GetServiceManagers()

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

    def NeedMigrateNodeConfig(self,configFile):
        return self.impl.NeedMigrateNodeConfig(configFile)
                
    def MigrateNodeConfig(self,configFile):
        self.impl.MigrateNodeConfig(configFile)

    def StoreConfiguration( self, configName ):
        """
        Interface to store a node configuration

        **Arguments:**
            *configName* Name of config file to load
            
        **Raises:**
        **Returns:**
        """

        self.impl.StoreConfiguration(configName)

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



class AGNodeServiceIW(SOAPIWrapper):
    """
    Interface Wrapper Class for the AGNodeService
    """

    def __init__(self,url):

        SOAPIWrapper.__init__(self, url)

    def AddServiceManager( self, serviceManagerUrl ):
        serviceManagerDescStruct = self.proxy.AddServiceManager(serviceManagerUrl)
        serviceManagerDescription = CreateAGServiceManagerDescription(serviceManagerDescStruct)
        return serviceManagerDescription

    def RemoveServiceManager( self, serviceManagerUrl ):
        self.proxy.RemoveServiceManager(serviceManagerUrl)

    def GetServiceManagers(self):
        smList = list()
        for sm in self.proxy.GetServiceManagers():   
            smList.append(CreateAGServiceManagerDescription(sm))
        return smList
            
    def GetServices(self):
        svcList = list()
        for s in self.proxy.GetServices():
            svcList.append(CreateAGServiceDescription(s))
        return svcList

    def SetServiceEnabled(self, serviceUri, enabled):
        self.proxy.SetServiceEnabled(serviceUri, enabled)

    def SetServiceEnabledByMediaType(self, mediaType, enableFlag):
        self.proxy.SetServiceEnabledByMediaType(mediaType,enableFlag)

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

    def NeedMigrateNodeConfig(self,configFile):
        return self.proxy.NeedMigrateNodeConfig(configFile)
                
    def MigrateNodeConfig(self,configFile):
        self.proxy.MigrateNodeConfig(configFile)

    def StoreConfiguration( self, configName ):
        self.proxy.StoreConfiguration(configName)

    def GetConfigurations(self):
        return self.proxy.GetConfigurations()

    def GetCapabilities(self):
        capList = list()
        for s in self.proxy.GetCapabilities():
            capList.append(CreateCapability(s))
        return capList

