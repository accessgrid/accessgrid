#-----------------------------------------------------------------------------
# Name:        VideoConsumerService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/06/02
# RCS-ID:      $Id: VideoConsumerService.py,v 1.2 2003-04-29 19:02:15 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys

from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter


class VideoConsumerService( AGService ):

   def __init__( self, server ):
      AGService.__init__( self, server )

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
         if self.streamDescription.encryptionFlag != 0:
            options.append( "-K" )
            options.append( self.streamDescription.encryptionKey )
         options.append( "-t" )
         options.append( '%d' % ( self.streamDescription.location.ttl ) )
         options.append( '%s/%d' % ( self.streamDescription.location.host, 
                                     self.streamDescription.location.port ) )
         self.log.info("Starting VideoConsumerService")
         self.log.info(" executable = %s" % self.executable)
         self.log.info(" options = %s" % options)
         self._Start( options )
      except:
         self.log.exception("Exception in VideoConsumerService.Start")
         raise Exception("Failed to start service")
   Start.soap_export_as = "Start"

   def Stop( self ):
       """Stop the service"""

       # vic doesn't die easily (on linux at least), so force it to stop
       AGService.ForceStop(self)         

   Stop.soap_export_as = "Stop"


   def ConfigureStream( self, streamDescription ):
      """Configure the Service according to the StreamDescription, and stop and start app"""

      ret = AGService.ConfigureStream( self, streamDescription )
      if ret:
        return

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

   server = Server( int(sys.argv[1]), auth_callback=AuthCallback )
   
   agService = VideoConsumerService(server)

   service = server.create_service_object("Service")
   agService._bind_to_service( service )

   print "Starting server at", agService.get_handle()
   server.run()
