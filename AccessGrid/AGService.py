import sys

try:     import win32process
except:  pass

from AccessGrid.Types import *
from AccessGrid.AGParameter import *
from AccessGrid.NetworkLocation import *
from AccessGrid.hosting.pyGlobus.ServiceBase import ServiceBase
from AccessGrid.Descriptions import StreamDescription

class AGService( ServiceBase ):
   """
   AGService : Base class for developing services for the AG
   """
   def __init__( self ):
      if self.__class__ == AGService:
         raise Exception("Can't instantiate abstract class AGService")
      
      self.resource = AGResource()
      self.executable = None

      self.location = MulticastNetworkLocation()
      self.inputStreamConfiguration = None
      self.outputStreamConfiguration = None
      self.capabilities = []
      self.authorizedUsers = []
      self.started = False
      self.childPid = None

      self.configuration = dict()

      self.streamDescription = StreamDescription()

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
      if self.started == True:
         self._Stop()

      options.insert(0,self.executable)
      print self
      print self.__class__, "starting with options = ", options
      self.childPid = os.spawnv( os.P_NOWAIT, self.executable, options )
      print "childPid = ", self.childPid
      self.started = True


   def Stop( self, connInfo ):
      """Stop the service"""
      self._Stop()
   Stop.soap_export_as = "Stop"
   Stop.pass_connection_info = 1

   def _Stop( self ):
      """Internal : Stop the service"""
      try:
         if self.childPid != None:
            if sys.platform == 'win32':
               win32process.TerminateProcess( self.childPid, 0 )
            else:
               os.kill( self.childPid, 9 )
               os.waitpid( self.childPid, 1 )
      except:
         print "Exception in AGService.Stop ", sys.exc_type, sys.exc_value

      self.started = False

   def SetAuthorizedUsers( self, connInfo, authorizedUsers ):
      """
      Set the authorizedUsers list; this is usually pushed from a ServiceManager,
      thus this wholesale Set of the authorized user list
      """
      self.authorizedUsers = authorizedUsers
      print "got authorized user list", authorizedUsers
   SetAuthorizedUsers.soap_export_as = "SetAuthorizedUsers"
   SetAuthorizedUsers.pass_connection_info = 1


   def GetCapabilities( self, connInfo ):
      """Get capabilities"""
      return self.capabilities
   GetCapabilities.soap_export_as = "GetCapabilities"
   GetCapabilities.pass_connection_info = 1


   def GetResource( self, connInfo ):
      """Get resources"""
      return self.resource
   GetResource.soap_export_as = "GetResource"
   GetResource.pass_connection_info = 1


   def SetResource( self, connInfo, resource ):
      """Set the resource used by this service"""
      print " * ** * inside SetResource"
      try:
         self.resource = resource
      except:
         print "Exception in AGService.SetResource ", sys.exc_type, sys.exc_value
   SetResource.soap_export_as = "SetResource"
   SetResource.pass_connection_info = 1


   def GetExecutable( self, connInfo ):
      """Get resources"""
      return self.executable
   GetExecutable.soap_export_as = "GetExecutable"
   GetExecutable.pass_connection_info = 1


   def SetExecutable( self, connInfo, executable ):
      """Set the resource used by this service"""
      self.executable = executable
   SetExecutable.soap_export_as = "SetExecutable"
   SetExecutable.pass_connection_info = 1


   def SetConfiguration( self, connInfo, configuration ):
      """Set configuration of service"""

      self.resource = configuration.resource
      self.executable = configuration.executable

      for parm in configuration.parameters:
         self.configuration[parm.name] = parm
         print "set config ", parm.name, parm.value, parm.__class__
   SetConfiguration.soap_export_as = "SetConfiguration"
   SetConfiguration.pass_connection_info = 1


   def GetConfiguration( self, connInfo ):
      """Return configuration of service"""
      try:
         serviceConfig = ServiceConfiguration( self.resource, self.executable, self.configuration.values() )
      except:
         print "Exception in GetConfiguration ", sys.exc_type, sys.exc_value
         return None

      return serviceConfig
   GetConfiguration.soap_export_as = "GetConfiguration"
   GetConfiguration.pass_connection_info = 1


   def ConfigureStream( self, connInfo, streamDescription ):
      """Configure the Service according to the StreamDescription"""
      print "in AudioService.ConfigureStream"
      try:
         m = map( lambda cap:cap.type, self.capabilities )
         print streamDescription.capability.type
         if streamDescription.capability.type in m:
            self.location = streamDescription.location
            self.streamDescription = streamDescription
      except:
         print "Exception in ConfigureStream ", sys.exc_type, sys.exc_value
   ConfigureStream.soap_export_as = "ConfigureStream"
   ConfigureStream.pass_connection_info = 1


   def IsStarted( self, connInfo ):
      """Return the state of Service"""
      return self.started
   IsStarted.soap_export_as = "IsStarted"
   IsStarted.pass_connection_info = 1


   def Ping( self ):
      return 1
   Ping.soap_export_as = "Ping"
   Ping.pass_connection_info = 0