#-----------------------------------------------------------------------------
# Name:        VideoConsumerService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/06/02
# RCS-ID:      $Id: VideoConsumerService.py,v 1.10 2003-03-21 22:11:37 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys
from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter


class VideoConsumerService( AGService ):

   def __init__( self ):
      AGService.__init__( self )

      self.capabilities = [ Capability( Capability.CONSUMER, Capability.VIDEO ) ]
      self.executable = "vic"

      #
      # Set configuration parameters
      #
      pass


   def Start( self ):
      __doc__ = """Start service"""
      try:

         # 
         # Start the service; in this case, store command line args in a list and let
         # the superclass _Start the service
         options = []
         if self.streamDescription.name and len(self.streamDescription.name.strip()) > 0:
            options.append( "-C" )
            options.append( self.streamDescription.name )
         if self.streamDescription.encryptionKey != 0:
            options.append( "-K" )
            options.append( self.streamDescription.encryptionKey )
         options.append( "-t" )
         options.append( '%d' % ( self.streamDescription.location.ttl ) )
         options.append( '%s/%d' % ( self.streamDescription.location.host, 
                                     self.streamDescription.location.port ) )
         print "starting with options:", options
         self._Start( options )
      except:
         print "Exception in VideoConsumerService.Start", sys.exc_type, sys.exc_value
         raise faultType("Failed to start service")
   Start.soap_export_as = "Start"


   def ConfigureStream( self, streamDescription ):
      """Configure the Service according to the StreamDescription, and stop and start app"""
      AGService.ConfigureStream( self, streamDescription )

      # restart app, since this is the only way to change the 
      # stream location (for now!)
      if self.started:
         self.Stop()
         self.Start()
   ConfigureStream.soap_export_as = "ConfigureStream"


def AuthCallback(server, g_handle, remote_user, context):
    return 1

if __name__ == '__main__':
   from AccessGrid.hosting.pyGlobus import Client
   import thread

   agService = VideoConsumerService()
   server = Server( int(sys.argv[1]), auth_callback=AuthCallback )
   service = server.create_service_object("Service")
   agService._bind_to_service( service )

   print "Starting server at", agService.get_handle()
   server.run()
