import sys
from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.hosting.pyGlobus.AGGSISOAP import faultType
from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter

class AudioService( AGService ):

   def __init__( self ):
      print self.__class__, ".init"
      AGService.__init__( self )

      self.capabilities = [ Capability( Capability.CONSUMER, Capability.AUDIO ), 
                            Capability( Capability.PRODUCER, Capability.AUDIO ) ]
      self.executable = "rat"

      #
      # Set configuration parameters
      #
      self.configuration["Microphone Gain"] = RangeParameter( "Microphone Gain", 30, 0, 100 )
      self.configuration["Speaker Volume"] = RangeParameter( "Speaker Volume", 50, 0, 100 ) 


   def Start( self, connInfo ):
      """Start service"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      try:

         # 
         # Start the service; in this case, store command line args in a list and let
         # the superclass _Start the service
         print "Start service"
         print "Location : ", self.streamDescription.location.host, self.streamDescription.location.port, self.streamDescription.location.ttl
         options = []
         #options.append( "-name" )
         #options.append( '"%s"' % ( self.streamDescription.name ) )
         options.append( "-t" )
         options.append( '%d' % (self.streamDescription.location.ttl ) )
         #if self.streamDescription.encryptionKey != None:
         #   options.append( "-k" )
         #   options.append( self.streamDescription.encryptionKey )
         options.append( '%s/%d' % ( self.streamDescription.location.host, self.streamDescription.location.port ) )
         self._Start( options )
         print "pid = ", self.childPid
      except:
         print "Exception ", sys.exc_type, sys.exc_value
         print "type ", sys.exc_type, type(sys.exc_type)
         print "value ", sys.exc_value, type(sys.exc_value), sys.exc_value.__class__
         raise faultType("OS Error (could be missing executable)")
   Start.soap_export_as = "Start"
   Start.pass_connection_info = 1


   def ConfigureStream( self, connInfo, streamDescription ):
      """Configure the Service according to the StreamDescription, and stop and start rat"""

      # Check authorization
      if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

      print "in AudioService.ConfigureStream"
      AGService.ConfigureStream( self, connInfo, streamDescription )

      # restart rat, since this is the only way to change the 
      # stream location (for now!)
      if self.started:
         self.Stop( connInfo )
         self.Start( connInfo )
   ConfigureStream.soap_export_as = "ConfigureStream"
   ConfigureStream.pass_connection_info = 1



def AuthCallback(server, g_handle, remote_user, context):
    return 1

if __name__ == '__main__':
   from AccessGrid.hosting.pyGlobus import Client
   import thread

   agService = AudioService()
   server = Server( 0, auth_callback=AuthCallback )
   service = server.create_service_object()
   agService._bind_to_service( service )

   print "Register with the service manager ! "
   thread.start_new_thread( Client.Handle( sys.argv[2] ).get_proxy().RegisterService, 
                            ( sys.argv[1], agService.get_handle() ) )

   print "Starting server at", agService.get_handle()
   server.run()
