#-----------------------------------------------------------------------------
# Name:        AGService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGService.py,v 1.8 2003-02-12 20:57:23 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import sys

try:     import win32process
except:  pass

from AccessGrid.hosting.pyGlobus.ServiceBase import ServiceBase

from AccessGrid.Types import *
from AccessGrid.AGParameter import *
from AccessGrid.Descriptions import StreamDescription
from AccessGrid.hosting.pyGlobus.AGGSISOAP import faultType
from AccessGrid.AuthorizationManager import AuthorizationManager


if sys.platform == 'win32':
    from AccessGrid.ProcessManagerWin32 import ProcessManagerWin32 as ProcessManager
else:
    from AccessGrid.ProcessManagerUnix import ProcessManagerUnix as ProcessManager


class AGService( ServiceBase ):
   """
   AGService : Base class for developing services for the AG
   """
   def __init__( self ):
      if self.__class__ == AGService:
         raise Exception("Can't instantiate abstract class AGService")
      
      self.resource = AGResource()
      self.executable = None

      self.inputStreamConfiguration = None
      self.outputStreamConfiguration = None
      self.capabilities = []
      self.authManager = AuthorizationManager()
      self.started = 1
      self.childPid = None
      self.configuration = dict()
      self.streamDescription = StreamDescription()
      self.processManager = ProcessManager()



   def Start( self, connInfo ):
      """Start the service"""
      raise Exception("AGService.Start is abstract!")
   Start.soap_export_as = "Start"
   Start.pass_connection_info = 1


   def _Start( self, options ):
      """
      Internal : Start the service; encapsulates Start functionality for subclasses
      """

      # if started, stop
      if self.started == 1:
         self._Stop()


      self.processManager.start_process( self.executable, options )

      """
      options.insert(0,self.executable)
      print self
      print self.__class__, "starting with options = ", options
      self.childPid = os.spawnv( os.P_NOWAIT, self.executable, options )
      print "childPid = ", self.childPid
      """
      self.started = 1


   def Stop( self, connInfo ):
      """Stop the service"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      try:
         self._Stop()
      except:
         print "Exception in AGService.Stop ", sys.exc_type, sys.exc_value
         raise faultType("AGService.Stop failed : ", str( sys.exc_value ) )
   Stop.soap_export_as = "Stop"
   Stop.pass_connection_info = 1


   def _Stop( self ):
      """Internal : Stop the service"""

      self.started = 0

      self.processManager.terminate_all_processes()

      """
      if self.childPid != None:
         if sys.platform == 'win32':
            win32process.TerminateProcess( self.childPid, 0 )
         else:
            os.kill( self.childPid, 9 )
            os.waitpid( self.childPid, 1 )
      """


   def SetAuthorizedUsers( self, connInfo, authorizedUsers ):
      """
      Set the authorizedUsers list; this is usually pushed from a ServiceManager,
      thus this wholesale Set of the authorized user list
      """

      try:
         self.authManager.SetAuthorizedUsers( authorizedUsers )
         print "got authorized user list", authorizedUsers
      except:
         print "Exception in AGService.SetAuthorizedUsers : ", sys.exc_type, sys.exc_value
         raise faultType("AGService.SetAuthorizedUsers failed : " + str(sys.exc_value) )
   SetAuthorizedUsers.soap_export_as = "SetAuthorizedUsers"
   SetAuthorizedUsers.pass_connection_info = 1


   def GetCapabilities( self, connInfo ):
      """Get capabilities"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      return self.capabilities
   GetCapabilities.soap_export_as = "GetCapabilities"
   GetCapabilities.pass_connection_info = 1


   def GetResource( self, connInfo ):
      """Get resources"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      return self.resource
   GetResource.soap_export_as = "GetResource"
   GetResource.pass_connection_info = 1


   def SetResource( self, connInfo, resource ):
      """Set the resource used by this service"""
      print " * ** * inside SetResource"

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      self.resource = resource
   SetResource.soap_export_as = "SetResource"
   SetResource.pass_connection_info = 1


   def GetExecutable( self, connInfo ):
      """Get resources"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      return self.executable
   GetExecutable.soap_export_as = "GetExecutable"
   GetExecutable.pass_connection_info = 1


   def SetExecutable( self, connInfo, executable ):
      """Set the resource used by this service"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      self.executable = executable
   SetExecutable.soap_export_as = "SetExecutable"
   SetExecutable.pass_connection_info = 1


   def SetConfiguration( self, connInfo, configuration ):
      """Set configuration of service"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      try:
         self.resource = configuration.resource
         self.executable = configuration.executable

         for parm in configuration.parameters:
            self.configuration[parm.name] = parm
            print "set config ", parm.name, parm.value, parm.__class__
      except:
         print "Exception in AGService.SetConfiguration : ", sys.exc_type, sys.exc_value
         raise faultType("AGService.SetConfiguration failed : " + str(sys.exc_value) )
   SetConfiguration.soap_export_as = "SetConfiguration"
   SetConfiguration.pass_connection_info = 1


   def GetConfiguration( self, connInfo ):
      """Return configuration of service"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      try:
         serviceConfig = ServiceConfiguration( self.resource, self.executable, self.configuration.values() )
      except:
         print "Exception in GetConfiguration ", sys.exc_type, sys.exc_value
         raise faultType("AGService.GetConfiguration failed : " + str(sys.exc_value) )

      return serviceConfig
   GetConfiguration.soap_export_as = "GetConfiguration"
   GetConfiguration.pass_connection_info = 1


   def ConfigureStream( self, connInfo, streamDescription ):
      """Configure the Service according to the StreamDescription"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      print "in AudioService.ConfigureStream"
      try:
         m = map( lambda cap:cap.type, self.capabilities )
         print streamDescription.capability.type
         if streamDescription.capability.type in m:
            self.streamDescription = streamDescription
      except:
         print "Exception in ConfigureStream ", sys.exc_type, sys.exc_value
         raise faultType("AGService.ConfigureStream failed : " + str(sys.exc_value) )

   ConfigureStream.soap_export_as = "ConfigureStream"
   ConfigureStream.pass_connection_info = 1


   def IsStarted( self, connInfo ):
      """Return the state of Service"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      return self.started
   IsStarted.soap_export_as = "IsStarted"
   IsStarted.pass_connection_info = 1


   def Ping( self ):
      return 1
   Ping.soap_export_as = "Ping"
   Ping.pass_connection_info = 0
