import sys 
import urllib
import os
import socket
import time

try:     import win32process
except:  pass


from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.hosting.pyGlobus.ServiceBase import ServiceBase
from AccessGrid.Types import AGServiceImplementation, AGServiceDescription
from AccessGrid.hosting.pyGlobus.AGGSISOAP import faultType

import Utilities


class AGServiceManager( ServiceBase ):
   """ 
   AGServiceManager : exposes local resources and configures services to deliver them
   """

   def __init__( self ):
      self.name = None
      self.description = None
      self.resources = []
      # note: services dict is keyed on pid
      self.services = dict()
      self.authorizedUsers = []
      self.executable = None
      self.__host = socket.gethostname()

      self.nextToken = 9500

      self.DiscoverResources(1)

      self.unregisteredServices = dict()

   def SetAuthorizedUsers( self, connInfo, authorizedUsers ):
      """
      Set the authorizedUsers list; this is usually pushed from a NodeService,
      thus this wholesale Set of the authorized user list.  Also, push this
      list to known services
      """

      try:
         self.authorizedUsers = authorizedUsers
         print "got authorized user list", authorizedUsers

         self.__PushAuthorizedUserList()
      except:
         print "AGServiceManager.SetAuthorizedUsers : ", sys.exc_type, sys.exc_value
   SetAuthorizedUsers.soap_export_as = "SetAuthorizedUsers"
   SetAuthorizedUsers.pass_connection_info = 1
   

   def __PushAuthorizedUserList( self ):
      """Push the list of authorized users to service managers"""
      for service in self.services:
         Client.Handle( service.uri ).get_proxy().SetAuthorizedUsers( self.authorizedUsers )


   def GetResources( self, connInfo ):
      """
      Return a list of resident resources
      """
      return self.resources
   GetResources.soap_export_as = "GetResources"
   GetResources.pass_connection_info = 1

   def DiscoverResources( self, connInfo ):
      """Discover local resources (audio cards, etc.)
      """

      self.resources = Utilities.GetResourceList()
   DiscoverResources.soap_export_as = "DiscoverResources"
   DiscoverResources.pass_connection_info = 1


   def AddService( self, connInfo, serviceImplementation, resourceToAssign ):
      """
      Add a service to the service manager.  The service is an executable
      or python script, which will be started by the ServiceManager
      """

      if connInfo.get_remote_name() not in self.authorizedUsers:
         print "User not authorized!"
         print "user ", connInfo.get_remote_name()
         print "auth users ", self.authorizedUsers
         raise faultType, "User not authorized"

      try:
         #
         # Determine resource to assign to service
         #
         print "** resourceToAssign = ", resourceToAssign, type(resourceToAssign)
         if resourceToAssign != None and resourceToAssign != "None":
            foundResource = False
            for resource in self.resources:
               if resource.resource == resourceToAssign.resource:
                  if resource.inUse == True:
                     print "** Resource is already in use ! ", resource.resource
                     # should error out here later; for now, services aren't using the resources anyway
                  foundResource = True
                  break

            if foundResource == False:
               print "** Resource does not exist! ", resourceToAssign.resource
               # should error out here later; for now, services aren't using the resources anyway

      except:
         print "Exception in AddService, checking resource\n-- ", sys.exc_type, sys.exc_value
      try:
         #
         # Check for local copy of service implementation
         #
         # -- not yet implemented

         #
         # Retrieve service implementation
         #
         serviceImplFile = self.__RetrieveServiceImplementation( serviceImplementation )
         svcImpl = AGServiceImplementation()
         serviceDescription = svcImpl.GetServiceDescription( serviceImplFile )
         serviceDescription.resource = resourceToAssign
         print "service description = ", serviceDescription.name, serviceDescription.description, serviceDescription.executable
         self.__AddServiceDescription( connInfo, serviceDescription )

      except:
         print "Exception in AddService, retrieving service implementation\n-- ", sys.exc_type, sys.exc_value
   AddService.soap_export_as = "AddService"
   AddService.pass_connection_info = 1


   def AddServiceDescription( self, connInfo, serviceDescription ):
      """
      Add a service to the service manager.  The service is an executable
      or python script, which will be started by the ServiceManager
      """
      serviceDescription = AGServiceDescription( serviceDescription.name, 
                                                 serviceDescription.description, 
                                                 serviceDescription.uri, 
                                                 serviceDescription.capabilities, 
                                                 serviceDescription.resource, 
                                                 serviceDescription.serviceManagerUri, 
                                                 serviceDescription.executable )


      self.__AddServiceDescription( connInfo, serviceDescription )
   AddServiceDescription.soap_export_as = "AddServiceDescription"
   AddServiceDescription.pass_connection_info = 1


   def __AddServiceDescription( self, connInfo, serviceDescription ):
      try:
         #
         # Execute the service implementation
         #
         options = []


         if serviceDescription.executable.endswith(".py"):
            executable = Utilities.Which( "python" )
            options.append(executable)
            options.append( serviceDescription.executable )
         else:
            executable = serviceDescription.executable
            options.append( serviceDescription.executable )


         token = '%d' %(self.nextToken)

         options.append( '%d' % self.nextToken )
         options.append( self.get_handle() )
         self.nextToken = self.nextToken + 1

         print "starting with options ", options
         pid = os.spawnv( os.P_NOWAIT, executable, options )


      except:
         print "Exception in AddService, starting service ", sys.exc_type, sys.exc_value
      try:

         #
         # Add the service to the list
         #
         serviceDescription.serviceManagerUri = self.get_handle()
         self.unregisteredServices[token] = ( pid, serviceDescription )
         print "service added ", serviceDescription.name, serviceDescription.uri, serviceDescription.serviceManagerUri, self.get_handle()
      
      except:
         print "Exception in AddService, other ", sys.exc_type, sys.exc_value


   def RemoveService( self, connInfo, serviceToRemove ):
      """Remove a service
      """

      pid = None

      try:

         #
         # Find service to stop using uri
         #
         for key in self.services.keys():
            service = self.services[key]
            if service.uri == serviceToRemove.uri:

               pid = key
               Client.Handle( service.uri ).get_proxy().Stop()

               #
               # Kill service pid (note: key is pid)
               #
               if sys.platform == 'win32':
                  win32process.TerminateProcess( pid, 0 )
               else:
                  os.kill( pid, 9 )

               # 
               # Wait on it
               #
               try:
                  os.waitpid( pid, 1 )
               except:
                  pass
      
               #
               # Free the resource
               #
               foundResource = False
               for resource in self.resources:
                  if resource.resource == service.resource.resource:
                     resource.inUse = False
                     foundResource = True

               if foundResource == False:
                  print "** Resource used by service not found !! ", service.resource.resource

               break

      except:
         print "Exception in AGSM.RemoveService ", sys.exc_type, sys.exc_value
      
      # 
      # Remove service from list
      #
      if pid:
         print "Removing service from list"
         del self.services[pid]

   RemoveService.soap_export_as = "RemoveService"
   RemoveService.pass_connection_info = 1

   def RemoveServices( self, connInfo ):
      """Remove all services
      """
      for service in self.services.values():
         self.RemoveService( connInfo, service )
   RemoveServices.soap_export_as = "RemoveServices"
   RemoveServices.pass_connection_info = 1

   def GetServices( self, connInfo ):
      """Return list of services
      """
      return self.services.values()
   GetServices.soap_export_as = "GetServices"
   GetServices.pass_connection_info = 1


   def __RetrieveServiceImplementation( self, serviceImplementation ):
      """Internal : Retrieve a service implementation"""
      filecontent = urllib.urlopen( serviceImplementation ).read()
      filename = os.path.basename( serviceImplementation )
      print "Retrieved ",filename

      f = open( "local_services/"+filename, 'wb')
      f.write(filecontent)
      f.close()

      return "local_services/"+filename


   def RegisterService( self, connInfo, token, uri ):
      try:

         # Use the token to identify the unregistered service
         #
         pid, service = self.unregisteredServices[token]
         del self.unregisteredServices[token]

         # Set the uri and add service to list of services
         #
         service.uri = uri
         self.services[pid] = service

         # Assign resource to the service
         #
         print "NOW SETTING RESOURCE "
         Client.Handle( service.uri ).get_proxy().SetResource( service.resource )

      except:
         print "--- Exception in RegisterService ", sys.exc_type, sys.exc_value
   RegisterService.soap_export_as = "RegisterService"
   RegisterService.pass_connection_info = 1


   def Ping( self ):
      return 1
   Ping.soap_export_as = "Ping"
   Ping.pass_connection_info = 0


if __name__ == '__main__':

   serviceManager = AGServiceManager()

   server = Server( int(sys.argv[1]) )
   service = server.create_service_object()

   serviceManager._bind_to_service( service )
   print "Starting service; URI: ", serviceManager.get_handle()
   server.run()
