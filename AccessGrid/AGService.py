#-----------------------------------------------------------------------------
# Name:        AGService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGService.py,v 1.12 2003-04-09 15:40:14 olson Exp $
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



   def Start( self ):
      """Start the service"""
      raise Exception("AGService.Start is abstract!")
   Start.soap_export_as = "Start"


   def _Start( self, options ):
      """
      Internal : Start the service; encapsulates Start functionality for subclasses
      """

      # if started, stop
      if self.started == 1:
         self.Stop()

      self.processManager.start_process( self.executable, options )
      self.started = 1


   def Stop( self ):
       """Stop the service"""
       try:
           self.started = 0
           self.processManager.terminate_all_processes()
       except Exception, e:
           log.exception("Exception in AGService.Stop")
           print "Exception in AGService.Stop ", sys.exc_type, sys.exc_value
           raise e
           # raise faultType("AGService.Stop failed : ", str( sys.exc_value ) )
           
   Stop.soap_export_as = "Stop"


   def SetAuthorizedUsers( self, authorizedUsers ):
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


   def GetCapabilities( self ):
      """Get capabilities"""
      return self.capabilities
   GetCapabilities.soap_export_as = "GetCapabilities"


   def GetResource( self ):
      """Get resources"""
      return self.resource
   GetResource.soap_export_as = "GetResource"


   def SetResource( self, resource ):
      """Set the resource used by this service"""
      self.resource = resource
   SetResource.soap_export_as = "SetResource"


   def GetExecutable( self ):
      """Get resources"""
      return self.executable
   GetExecutable.soap_export_as = "GetExecutable"


   def SetExecutable( self, executable ):
      """Set the resource used by this service"""
      self.executable = executable
   SetExecutable.soap_export_as = "SetExecutable"


   def SetConfiguration( self, configuration ):
      """Set configuration of service"""
      try:
         self.resource = configuration.resource
         self.executable = configuration.executable

         for parm in configuration.parameters:
            if parm.name in self.configuration.keys():
                self.configuration[parm.name].SetValue( parm.value )
      except:
         print "Exception in AGService.SetConfiguration : ", sys.exc_type, sys.exc_value
         raise faultType("AGService.SetConfiguration failed : " + str(sys.exc_value) )
   SetConfiguration.soap_export_as = "SetConfiguration"


   def GetConfiguration( self ):
      """Return configuration of service"""
      try:
         serviceConfig = ServiceConfiguration( self.resource, self.executable, self.configuration.values() )
      except:
         print "Exception in GetConfiguration ", sys.exc_type, sys.exc_value
         raise faultType("AGService.GetConfiguration failed : " + str(sys.exc_value) )

      return serviceConfig
   GetConfiguration.soap_export_as = "GetConfiguration"


   def ConfigureStream( self, streamDescription ):
      """Configure the Service according to the StreamDescription"""
      try:
         m = map( lambda cap:cap.type, self.capabilities )
         print streamDescription.capability.type
         if streamDescription.capability.type in m:
            self.streamDescription = streamDescription
      except:
         print "Exception in ConfigureStream ", sys.exc_type, sys.exc_value
         raise faultType("AGService.ConfigureStream failed : " + str(sys.exc_value) )
   ConfigureStream.soap_export_as = "ConfigureStream"


   def IsStarted( self ):
      """Return the state of Service"""
      return self.started
   IsStarted.soap_export_as = "IsStarted"


