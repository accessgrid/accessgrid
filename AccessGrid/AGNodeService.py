import os
import sys
import pickle
import string

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.hosting.pyGlobus.ServiceBase import ServiceBase

from AccessGrid.Types import AGServiceImplementationRepository, AGServiceDescription, ServiceConfiguration, AGServiceManagerDescription
from AccessGrid.AuthorizationManager import AuthorizationManager
from AccessGrid.hosting.pyGlobus.AGGSISOAP import faultType



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
      self.serviceImplRepository = AGServiceImplementationRepository()
      self.configDir = "config/"
      self.authManager = AuthorizationManager()
      self.__ReadAuthFile()


   ####################
   ## AUTHORIZATION methods
   ####################

   def AddAuthorizedUser( self, connInfo, authorizedUser ):
      """Add user to list of authorized users"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      try:
         self.authManager.AddAuthorizedUser( authorizedUser )
         self.__PushAuthorizedUserList()
      except:
         print "Exception in AGNodeService.AddAuthorizedUser ", sys.exc_type, sys.exc_value
         raise faultType("Failed to add user authorization: " + authorizedUser )
   AddAuthorizedUser.soap_export_as = "AddAuthorizedUser"
   AddAuthorizedUser.pass_connection_info = 1


   def RemoveAuthorizedUser( self, connInfo, authorizedUser ):
      """Remove user from list of authorized users"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      try:
         self.authManager.RemoveAuthorizedUser( authorizedUser )
         self.__PushAuthorizedUserList()
      except:
         print "Exception in AGNodeService.RemoveAuthorizedUser ", sys.exc_type, sys.exc_value
         raise faultType("Failed to remove user authorization: " + authorizedUser )
   RemoveAuthorizedUser.soap_export_as = "RemoveAuthorizedUser"
   RemoveAuthorizedUser.pass_connection_info = 1


   ####################
   ## SERVICE MANAGER methods
   ####################

   def AddServiceManager( self, connInfo, serviceManager ):
      """Add a service manager"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

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
   AddServiceManager.pass_connection_info = 1


   def RemoveServiceManager( self, connInfo, serviceManagerToRemove ):
      """Remove a service manager"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

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
   RemoveServiceManager.pass_connection_info = 1


   def GetServiceManagers( self, connInfo ):
      """Get list of service managers """

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      return self.serviceManagers
   GetServiceManagers.soap_export_as = "GetServiceManagers"
   GetServiceManagers.pass_connection_info = 1


   ####################
   ## SERVICE methods
   ####################


   def GetAvailableServices( self, connInfo ):
      """Get list of available services """

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      return self.serviceImplRepository.GetServiceImplementations()
   GetAvailableServices.soap_export_as = "GetAvailableServices"
   GetAvailableServices.pass_connection_info = 1


   def GetServices( self, connInfo ):
      """Get list of installed services """

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")


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
   GetServices.pass_connection_info = 1


   ####################
   ## CONFIGURATION methods
   ####################
   
   def ConfigureStreams( self, connInfo, streamDescriptions ):
      """
      Configure streams according to stream descriptions.
      The stream descriptions are applied to the installed services
      according to matching capabilities
      """

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      services = self.GetServices( connInfo )
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
   ConfigureStreams.pass_connection_info = 1


#FIXME - LoadConfig and StoreConfig work with some level of reliability, 
#        but do need a complete reworking.  
   def LoadConfiguration( self, connInfo, configName ):
      """Load named node configuration"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

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
      inp = open( self.configDir+configName, "r")
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
      for serviceManager in self.serviceManagers:
         try:
            Client.Handle( serviceManager.uri ).get_proxy().Ping(  )
         except:
            print "* * Couldn't contact host ; uri=", serviceManager.uri
            hadServiceManagerException = 1
#FIXME - # need to handle unreachable service managers ####del self.hosts[ h.id ]

      #
      # Add services to hosts
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

         smservices = Client.Handle( s.serviceManagerUri ).get_proxy().GetServices()

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
   LoadConfiguration.pass_connection_info = 1
      

   def StoreConfiguration( self, connInfo, configName ):
      """Store current configuration using specified name"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      print "in StoreConfiguration"
      try:
         out = open( self.configDir+configName, "w")
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

         inp = open( self.configDir+configName, "r")
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
   StoreConfiguration.pass_connection_info = 1


   def GetConfigurations( self, connInfo ):
      """Get list of available configurations"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      files = os.listdir( self.configDir )
      return files
   GetConfigurations.soap_export_as = "GetConfigurations"
   GetConfigurations.pass_connection_info = 1


   ####################
   ## OTHER methods
   ####################

   def GetCapabilities( self, connInfo ):
      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      capabilities = []
      try:
         services = self.GetServices( connInfo )
         for service in services:
            print "-- ", service.uri
            capabilitySubset = Client.Handle( service.uri ).get_proxy().GetCapabilities().data
            capabilities = capabilities + capabilitySubset

      except:
         print "Exception in AGNodeService.GetCapabilities ", sys.exc_type, sys.exc_value
         raise faultType("AGNodeService.GetCapabilities failed: " + str( sys.exc_value ) )
      return capabilities
   GetCapabilities.soap_export_as = "GetCapabilities"
   GetCapabilities.pass_connection_info = 1

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

