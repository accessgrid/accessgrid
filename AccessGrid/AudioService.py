import sys
from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.AGService import *
from AccessGrid.AGParameter import *


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
      __doc__ = """Start service"""
      try:

         # 
         # Start the service; in this case, store command line args in a list and let
         # the superclass _Start the service
         print "Start service"
         print "Location : ", self.streamDescription.location.host, self.streamDescription.location.port, self.streamDescription.location.ttl
         options = []
         options.append( "-name" )
         options.append( '"%s"' % ( self.streamDescription.name ) )
         options.append( "-t" )
         options.append( '%d' % (self.streamDescription.location.ttl ) )
         options.append( '%s/%d' % ( self.streamDescription.location.host, self.streamDescription.location.port ) )
         self._Start( options )
         print "pid = ", self.childPid
      except:
         print "Exception ", sys.exc_type, sys.exc_value
         return AGServiceException("Couldn't start service!")
   Start.soap_export_as = "Start"
   Start.pass_connection_info = 1


   def ConfigureStream( self, connInfo, streamDescription ):
      """Configure the Service according to the StreamDescription, and stop and start rat"""
      print "in AudioService.ConfigureStream"
      AGService.ConfigureStream( self, connInfo, streamDescription )

      # restart rat, since this is the only way to change the 
      # stream location (for now!)
      if self.started:
         self.Stop( connInfo )
         self.Start( connInfo )
   ConfigureStream.soap_export_as = "ConfigureStream"
   ConfigureStream.pass_connection_info = 1


from AccessGrid.hosting.pyGlobus import Client
import thread
if __name__ == '__main__':

   agService = AudioService()
   server = Server( 0 )
   service = server.create_service_object()
   agService._bind_to_service( service )

   print "Register with the service manager ! "
   thread.start_new_thread( Client.Handle( sys.argv[2] ).get_proxy().RegisterService, 
                            ( sys.argv[1], agService.get_handle() ) )

   print "Starting server at", agService.get_handle()
   server.run()
