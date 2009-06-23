#-----------------------------------------------------------------------------
# Name:        AGNodeService.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGNodeService.py,v 1.118 2007/12/06 22:43:20 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: AGNodeService.py,v 1.118 2007/12/06 22:43:20 turam Exp $"


import os
import sys
import string
import ConfigParser

from AccessGrid import Log
from AccessGrid import Version
from AccessGrid.Toolkit import Service
from AccessGrid.hosting import Client
from AccessGrid.NetworkLocation import ProviderProfile
from AccessGrid.Descriptions import AGServiceDescription
from AccessGrid.Descriptions import AGServiceManagerDescription
from AccessGrid.interfaces.AGServiceManager_client import AGServiceManagerIW
from AccessGrid.interfaces.AGService_client import AGServiceIW
from AccessGrid.Descriptions import ResourceDescription
from AccessGrid.Utilities import LoadConfig, SaveConfig
from AccessGrid.AGParameter import ValueParameter
from AccessGrid.Descriptions import NodeConfigDescription
from AccessGrid.AGServiceManager import AGServiceManager
from AccessGrid.Platform.Config import UserConfig, SystemConfig


from AccessGrid.interfaces.AGNodeService_interface import AGNodeService as AGNodeServiceI
from AccessGrid.interfaces.AGNodeService_client import AGNodeServiceIW

log = Log.GetLogger(Log.NodeService)

class SetStreamException(Exception): pass
class ServiceManagerAlreadyExists(Exception): pass
class ServiceManagerNotFound(Exception): pass
class ServiceManagerCannotBeRemovedBuiltIn(Exception): pass

def WriteNodeConfig(configName,config):
    """
    Writes the given node config to the given node config name

    A 'config' is a dictionary

        keys:   service manager urls
        values: [ [servicename, resource name, serviceconfig], ... ]

        serviceconfig should be a list of name,value pairs
    """
    userNodeConfigDir = UserConfig.instance().GetNodeConfigDir()
    fileName = os.path.join(userNodeConfigDir, configName)
    hostname = SystemConfig.instance().GetHostname()

    # Catch inability to write config file
    if((not os.path.exists(userNodeConfigDir)) or
       (not os.access(userNodeConfigDir,os.W_OK)) or
       (os.path.exists(fileName) and not os.access(fileName, os.W_OK) )):
        log.exception("Can't write config file %s" % (fileName))
        raise Exception("Can't write config file %s" % (fileName))



    numServiceManagers = 0
    numServices = 0
    node_servicemanagers = ''

    configParser = ConfigParser.ConfigParser()
    configParser.optionxform = str
    for key in config.keys(): 

        builtin = 0
        url = key          
        name = url
        
        servicemanager_services = ''

        #
        # Create Service Manager section
        #
        serviceManagerSection = 'servicemanager%d' % numServiceManagers
        configParser.add_section( serviceManagerSection )
        node_servicemanagers += serviceManagerSection + " "
        if url.find(hostname) >= 0:
            builtin = 1
        else:
            builtin = 0
        configParser.set( serviceManagerSection, 'builtin', builtin )
        if builtin:
            configParser.set( serviceManagerSection, "name", '' )
            configParser.set( serviceManagerSection, "url", '' )
        else:
            configParser.set( serviceManagerSection, "name", name )
            configParser.set( serviceManagerSection, "url", url )

        services = config[key]

        if not services:
            services = []

        for service in services:

            serviceName,resourceName,serviceConfig = service

            serviceSection = 'service%d' % numServices
            configParser.add_section( serviceSection )

            # 
            # Create Resource section
            #

            if resourceName:
                log.debug('Storing resource: %s', resourceName)
                resourceSection = 'resource%d' % numServices
                configParser.add_section( resourceSection )
                configParser.set( resourceSection, "name",
                                  resourceName )
                configParser.set( serviceSection, "resource",
                                  resourceSection )
            else:
                log.debug('No resource specified')

            # 
            # Create Service Config section
            #

            if serviceConfig:
                serviceConfigSection = 'serviceconfig%d' % numServices
                configParser.set( serviceSection, "serviceConfig", serviceConfigSection )
                configParser.add_section( serviceConfigSection )
                for k,v in serviceConfig:
                    configParser.set( serviceConfigSection, k, v )


            #
            # Create Service section
            #
            servicemanager_services += serviceSection + " "
            configParser.set( serviceSection, "packageName", serviceName )

            numServices += 1

        configParser.set( serviceManagerSection, "services", servicemanager_services )
        numServiceManagers += 1

    configParser.add_section('node')
    configParser.set('node', "servicemanagers", node_servicemanagers )

    #
    # Write config file
    #
    fp = open( fileName, "w" )
    fp.write("# AGTk %s node configuration\n" % (Version.GetVersion()))
    configParser.write(fp)
    fp.close()


class AGNodeService:
    """
    AGNodeService is the central engine of an Access Grid node.
    It is the contact point for clients to access underlying Service Managers
    and AGServices, for control and configuration of the node.
    @group WebServiceMethods: AddServiceManager, AddStream, GetCapabilities, GetConfigurations, GetServiceManagers, GetServices, IsValid, LoadConfiguration, MigrateNodeConfig, NeedMigrateNodeConfig, RemoveServiceManager, RemoveStream, SetServiceEnabled, SetStreams, StopServices, StoreConfiguration, GetVersion
    """

    ServiceType = '_nodeservice._tcp'

    def __init__( self, app=None, builtInServiceManager=None ):
        if app:
            self.app = app
        else:
            self.app = Service.instance()
            
        self.serviceManagers = dict()
        self.sysNodeConfigDir = self.app.GetToolkitConfig().GetNodeConfigDir()
        self.userNodeConfigDir = self.app.GetUserConfig().GetNodeConfigDir()
        self.servicesDir = self.app.GetToolkitConfig().GetNodeServicesDir()
        
        self.streamDescriptionList = []
        
        self.builtInServiceManager = builtInServiceManager
        if builtInServiceManager:
            builtInServiceManagerDesc = builtInServiceManager.GetDescription()
            self.serviceManagers[builtInServiceManager.uri] = builtInServiceManager
        
        self.uri = 0
        
        self.services = {}

    ####################
    ## SERVICE MANAGER methods
    ####################
   
    def AddServiceManagerObj( self, serviceManagerObj ):
        """
        Add a service manager
        """
        serviceManagerUrl = "no url, built in service manager"
        log.info("NodeService.AddServiceManager")
        log.debug("  serviceManagerUrl = %s", serviceManagerUrl)
        
        # Check whether the service manager has already been added
        #if self.serviceManagers.has_key( serviceManagerUrl ):
        #    raise ServiceManagerAlreadyExists(serviceManagerUrl)
                            
                            
        log.info("try to reach service amnager")
        # Try to reach the service manager
        try:
            log.info("get sm description")
            serviceManagerDescription = serviceManagerObj.GetDescription()
            log.info("set ns url")
            serviceManagerObj.SetNodeServiceUrl(self.uri)
            log.info("done setting ns url")
        except Exception:
                log.exception("Failed to add service manager %s", serviceManagerUrl)
                raise
        except:
            log.exception("AddServiceManager: Invalid service manager url (%s)"
                          % serviceManagerUrl)
            raise Exception("Service Manager is unreachable at "
                            + serviceManagerUrl)

        log.info("add sm to list")

        # Add service manager to list
        self.serviceManagers[serviceManagerUrl] = serviceManagerObj
        
        return serviceManagerDescription

    def AddServiceManager( self, serviceManagerUrl ):
        """
        Add a service manager
        """
        log.info("NodeService.AddServiceManager")
        log.debug("  serviceManagerUrl = %s", serviceManagerUrl)
        
        # Check whether the service manager has already been added
        if self.serviceManagers.has_key( serviceManagerUrl ):
            raise ServiceManagerAlreadyExists(serviceManagerUrl)
                            
                            
        log.info("try to reach service amnager")
        # Try to reach the service manager
        try:
            log.info("get sm description")
            serviceManagerDescription = AGServiceManagerIW( serviceManagerUrl ).GetDescription()
            log.info("set ns url")
            AGServiceManagerIW( serviceManagerUrl ).SetNodeServiceUrl(self.uri)
            log.info("done setting ns url")
        except Exception:
                log.exception("Failed to add service manager %s", serviceManagerUrl)
                raise
        except:
            log.exception("AddServiceManager: Invalid service manager url (%s)"
                          % serviceManagerUrl)
            raise Exception("Service Manager is unreachable at "
                            + serviceManagerUrl)

        log.info("add sm to list")

        # Add service manager to list
        self.serviceManagers[serviceManagerUrl] = serviceManagerDescription
        
        return serviceManagerDescription

    def RemoveServiceManager( self, serviceManagerUrl ):
        """
        Remove a service manager
        """
        log.info("NodeService.RemoveServiceManager")
        log.debug("  url = %s", serviceManagerUrl)

        if not self.serviceManagers.has_key(serviceManagerUrl):
            raise ServiceManagerNotFound(serviceManagerUrl)        
        
        if self.serviceManagers[serviceManagerUrl].builtin:
            raise ServiceManagerBuiltIn("Unable to remove builtin service manager")
        
        try:
            del self.serviceManagers[serviceManagerUrl]
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

        for serviceManager in self.serviceManagers.values():
            try:
                serviceSubset = serviceManager.GetObject().GetServices()
                services += serviceSubset
            except:
                log.exception("Exception in AGNodeService.GetServices.")

        self.services = {}
        for service in services:
            self.services[service.uri] = service

        return services


    def SetServiceEnabled(self, serviceUri, enabled):
        """
        Enable the service, and send it a stream configuration if we have one
        """
        log.info("NodeService.SetServiceEnabled")
        self.GetServices()
        try:
            if enabled:
                self.__SendStreamsToService( serviceUri )
            self.services[serviceUri].GetObject().SetEnabled(enabled)

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

    def StopServices(self,clearStreams=1):
        """
        Stop all services
        """
        log.info("NodeService.StopServices")
        exceptionText = ""

        for serviceManager in self.serviceManagers.values():
            try:
                serviceManager.GetObject().StopServices()
            except:
                log.exception("Exception stopping services")
                exceptionText += str(sys.exc_info()[1])
        
        if len(exceptionText):
            raise Exception(exceptionText)

        # Remove the streams
        if clearStreams:
            self.SetStreams([])

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
        self.streamDescriptionList = [] 
        for streamDescription in streamDescriptionList:
            self.streamDescriptionList.append(streamDescription)
        
        # Send the streams to the services
        services = self.GetServices()
        services.sort(lambda x,y: cmp(int(x.startPriority),int(y.startPriority)))
        for service in services:
            try:
                log.debug("Starting service %s (priority %s)", service.name , service.startPriority)
                self.__SendStreamsToService( service.uri )
            except Exception,e:
                exceptionText += str(e) + "\n"

        if len(exceptionText):
            raise SetStreamException(exceptionText)
    
    def AddStream( self, streamDescription ):
        log.info("NodeService.AddStream")
        self.streamDescriptionList.append(streamDescription)

        # Send the streams to the services
        services = self.GetServices()
        for service in services:
            self.__SendStreamsToService( service.uri )



    def RemoveStream( self, streamDescription ):

        log.info("NodeService.RemoveStream")
        # Remove the stream from the list

        for s in self.streamDescriptionList:
            if (s.location.host == streamDescription.location.host and
                s.location.port == streamDescription.location.port):
                del self.streamDescriptionList[streamDescription.capability.type]

        # Stop services using that stream's media type
        # (er, not yet)


    def LoadConfiguration( self, config ):
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
        if config.type == NodeConfigDescription.SYSTEM:
            configFile = os.path.join(self.sysNodeConfigDir, config.name)
        else:
            configFile = os.path.join(self.userNodeConfigDir, config.name)

        if not os.path.exists(configFile):
            raise Exception("Configuration file does not exist (%s)" % configFile)
        else:
            log.info("Trying to load node configuration from: %s", configFile)

        try:
            configParser = ConfigParser.ConfigParser()
            configParser.optionxform = str
            configParser.read( configFile )
            
            for s in configParser.sections():
                log.debug("section: %s", s)
                for o in configParser.options(s):
                    log.debug("  %s : %s", o, configParser.get(s,o))

            #
            # Parse config file into usable structures
            #
            serviceManagerList = []
            serviceManagerSections = string.split( configParser.get("node", "servicemanagers") )
          
            for serviceManagerSection in serviceManagerSections:
                #
                # Create Service Manager
                #
                serviceManager = AGServiceManagerDescription( configParser.get( serviceManagerSection, "name" ), 
                                                              configParser.get( serviceManagerSection, "url" ) )
                serviceManager.builtin = configParser.getint(serviceManagerSection,'builtin')

                #
                # Extract Service List
                #
                serviceList = [] 
                serviceSections = string.split( configParser.get( serviceManagerSection, "services" ) )
                for serviceSection in serviceSections:
                    #
                    # Read the resource
                    #
                    if configParser.has_option(serviceSection,'resource'):
                        resourceSection = configParser.get( serviceSection, "resource" )
                        if resourceSection == "None":
                            resource = None
                        else:
                            resource = ResourceDescription( configParser.get( resourceSection, "name" ) )
                    else:
                        resource = None

                    #
                    # Read the service config
                    #
                    parameters = []
                    if configParser.has_option(serviceSection,'serviceConfig'):
                        serviceConfigSection = configParser.get( serviceSection, "serviceConfig" )
                        for parameter in configParser.options( serviceConfigSection ):
                            # Special case - to be removed after some reasonable time
                            if not parameter == 'Position Window':
                                parameters.append( ValueParameter( parameter, 
                                                               configParser.get( serviceConfigSection,
                                                                           parameter ) ) )
                            else:
                                value = configParser.get( serviceConfigSection, parameter )
                                if value == 'On':
                                    log.debug("Correcting an old value for \'Position Window\' parameter")
                                    log.debug("Please Store this configuration again")
                                    parameters.append( ValueParameter( parameter, 'Justify Left'))
                                else:
                                    parameters.append( ValueParameter( parameter, value))

                    #
                    # Add Service to List
                    #
                    incomingService = IncomingService()
                    incomingService.packageName = configParser.get( serviceSection, "packageName" )
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
        # - reset sm list, preserving builtin service manager if exists
        for serviceManager, serviceList in serviceManagerList:
            if serviceManager.builtin:
                if not self.builtInServiceManager:
                    # skip the configuration for the built-in service manager since it does not exist;
                    # consider, in this case, creating it instead
                    log.warn("Configuration specifies built in service manager, which does not exist; skipping")
                    exceptionText += "Built-in service manager does not exist; skipped relevant configuration"
                    continue
                
                # use the built in service manager
                serviceManagerObj = self.builtInServiceManager
            else:
                # use the service manager object from the description (probably a ws proxy)
                serviceManagerObj = serviceManager.GetObject()

                # Add service manager to list
                log.debug("Using external service manager at %s", serviceManager.uri)
                self.serviceManagers[serviceManager.uri] = serviceManager

            #
            # Remove services from service manager
            #
            try:
                serviceManagerObj.RemoveServices()
            except:
                log.exception("Exception removing services from Service Manager")
                exceptionText += "Couldn't remove services from Service Manager: %s" %(serviceManager.name)

            #
            # Add Service to Service Manager
            #
            for service in serviceList:
                try:

                    prefs = self.app.GetPreferences()
                    
                    # Actually add the service to the servicemgr
                    # and set resources, parameters, and identity
                    serviceDesc = serviceManagerObj.AddServiceByName(service.packageName,
                                                                     service.resource,
                                                                     service.parameters,
                                                                     prefs.GetProfile())
                    
                except Exception,e:
                    log.exception("Exception adding service %s" % (service.packageName))
                    exceptionText += "Couldn't add service %s : %s\n" % (service.packageName, str(e))

        if len(exceptionText):
            raise Exception(exceptionText)


    def StoreConfiguration( self, config ):
        """
        Store node configuration with specified name
        """
        log.info("NodeService.StoreConfiguration")
        
        try:
            if config.type == NodeConfigDescription.SYSTEM:
                fileName = os.path.join(self.sysNodeConfigDir, config.name)
            else:
                fileName = os.path.join(self.userNodeConfigDir, config.name)

            # Catch inability to write config file
            if((not os.path.exists(self.userNodeConfigDir)) or
               (not os.access(self.userNodeConfigDir,os.W_OK)) or
               (os.path.exists(fileName) and not os.access(fileName, os.W_OK) )):
                log.exception("Can't write config file %s" % (fileName))
                raise Exception("Can't write config file %s" % (fileName))

            numServiceManagers = 0
            numServices = 0

            configParser = ConfigParser.ConfigParser()
            configParser.optionxform = str

            nodeSection = "node"
            configParser.add_section(nodeSection)

            node_servicemanagers = ""

            for key,serviceManager in self.serviceManagers.items():
                servicemanager_services = ""

                #
                # Create Service Manager section
                #
                serviceManagerSection = 'servicemanager%d' % numServiceManagers
                configParser.add_section( serviceManagerSection )
                node_servicemanagers += serviceManagerSection + " "
                configParser.set( serviceManagerSection, 'builtin', serviceManager.builtin )
                if serviceManager.builtin:
                    configParser.set( serviceManagerSection, "name", '' )
                    configParser.set( serviceManagerSection, "url", '' )
                else:
                    configParser.set( serviceManagerSection, "name", serviceManager.name )
                    configParser.set( serviceManagerSection, "url", key )
                
                services = serviceManager.GetObject().GetServices()

                if not services:
                    services = []

                for service in services:
                
                    serviceSection = 'service%d' % numServices
                    configParser.add_section( serviceSection )

                    # 
                    # Create Resource section
                    #
                    resource = service.GetObject().GetResource()
                    if resource and resource.name:
                        log.debug('Storing resource: %s', resource.name)
                        resourceSection = 'resource%d' % numServices
                        configParser.add_section( resourceSection )
                        configParser.set( resourceSection, "name",
                                          resource.name )
                        configParser.set( serviceSection, "resource",
                                          resourceSection )
                    else:
                        log.debug('No resource specified')

                    # 
                    # Create Service Config section
                    #

                    serviceConfig = service.GetObject().GetConfiguration()
                                                            
                    if serviceConfig:
                        serviceConfigSection = 'serviceconfig%d' % numServices
                        configParser.set( serviceSection, "serviceConfig", serviceConfigSection )
                        configParser.add_section( serviceConfigSection )
                        for parameter in serviceConfig:
                            configParser.set( serviceConfigSection, parameter.name, parameter.value )


                    #
                    # Create Service section
                    #
                    servicemanager_services += serviceSection + " "
                    packageName = os.path.basename(service.packageFile).split('\\')[-1]   
                    configParser.set( serviceSection, "packageName", packageName)

                    numServices += 1

                configParser.set( serviceManagerSection, "services", servicemanager_services )
                numServiceManagers += 1

            configParser.set(nodeSection, "servicemanagers", node_servicemanagers )

            #
            # Write config file
            #
            fp = open( fileName, "w" )
            fp.write("# AGTk %s node configuration\n" % (Version.GetVersion()))
            configParser.write(fp)
            fp.close()

        except:
            log.exception("Exception in AGNodeService.StoreConfiguration.")
            raise Exception("Error while saving configuration")
    
    def GetConfigurations( self ):
        """Get list of available configurations"""
        log.info("NodeService.GetConfigurations")
        
        configs = []
        
        # Get system node configs
        files = os.listdir( self.sysNodeConfigDir )
        for f in files:
            configs.append(NodeConfigDescription(f,NodeConfigDescription.SYSTEM))
            
        # Get user node configs
        files = os.listdir( self.userNodeConfigDir )
        for f in files:
            configs.append(NodeConfigDescription(f,NodeConfigDescription.USER))
            
        return configs


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
                #capabilitySubset = AGServiceIW( service.uri ).GetCapabilities()
                capabilitySubset = service.capabilities
                              
                for cap in capabilitySubset:
                    capabilities.append(cap)
                    
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
        if not self.streamDescriptionList:
            return
        failedSends = ""
        
        serviceCapabilities = self.services[serviceUri].GetObject().GetCapabilities()
        log.debug("service capabilities: %s", str(serviceCapabilities))
        for streamDescription in self.streamDescriptionList:
            log.debug("streamDescriptions: %s", str(streamDescription))
            try:
                #log.debug("capability type: %s", streamDescription.capability[0].type)
                
                # each service capability has to be present in the stream.
                match = 0
                for cap in serviceCapabilities:
                    for c in streamDescription.capability:
                        if c.matches(cap):
                            match = 1
                            break
                if match:
                    log.info("Sending stream (type=%s) to service: %s", 
                             streamDescription.capability,
                             serviceUri )
                    
                    self.services[serviceUri].GetObject().SetStream(streamDescription)
                    #return
                else:
                    log.debug("No stream match! Sending no new streams!")

            except:
                log.exception("Exception in AGNodeService.__SendStreamsToService.")
                failedSends += "Error updating %s\n" % \
                               ( streamDescription.capability)

        if len(failedSends):
            raise SetStreamException(failedSends)



    def IsValid(self):
        return 1

    def GetVersion(self):   
        return Version.GetVersion()
