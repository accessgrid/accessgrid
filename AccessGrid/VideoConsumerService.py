import sys
from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.AGService import *
from AccessGrid.AGParameter import *


class VideoConsumerService( AGService ):

   def __init__( self ):
      print self.__class__, ".init"
      AGService.__init__( self )

      self.capabilities = [ Capability( Capability.CONSUMER, Capability.VIDEO ) ]
      self.executable = "vic"

      #
      # Set configuration parameters
      #
      pass


   def Start( self, connInfo ):
      __doc__ = """Start service"""
      try:

         # 
         # Start the service; in this case, store command line args in a list and let
         # the superclass _Start the service
         print "Start service"
         print "Location : ", self.location.host, self.location.port, self.location.ttl
         options = []
         options.append( '%s/%d/%d' % ( self.location.host, self.location.port, self.location.ttl ) )
         self._Start( options )
         print "pid = ", self.childPid
      except:
         print "Exception ", sys.exc_type, sys.exc_value
   Start.soap_export_as = "Start"
   Start.pass_connection_info = 1


   def ConfigureStream( self, connInfo, streamDescription ):
      """Configure the Service according to the StreamDescription, and stop and start app"""
      print "in AudioService.ConfigureStream"
      AGService.ConfigureStream( self, connInfo, streamDescription )

      # restart app, since this is the only way to change the 
      # stream location (for now!)
      if self.started:
         self.Stop( connInfo )
         self.Start( connInfo )
   ConfigureStream.soap_export_as = "ConfigureStream"
   ConfigureStream.pass_connection_info = 1


if __name__ == '__main__':

   agService = VideoConsumerService()
   server = Server( 0 )
   service = server.create_service_object()
   agService._bind_to_service( service )

   thread.start_new_thread( Client.Handle( sys.argv[2] ).get_proxy().RegisterService, 
                            ( sys.argv[1], agService.get_handle() ) )

   print "Starting server at", agService.get_handle()
   server.run()
