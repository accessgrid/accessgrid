#-----------------------------------------------------------------------------
# Name:        AudioService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/06/02
# RCS-ID:      $Id: AudioService.py,v 1.10 2003-03-21 22:11:37 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys
from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.hosting.pyGlobus.AGGSISOAP import faultType
from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter

class AudioService( AGService ):

   def __init__( self ):
      AGService.__init__( self )

      self.capabilities = [ Capability( Capability.CONSUMER, Capability.AUDIO ), 
                            Capability( Capability.PRODUCER, Capability.AUDIO ) ]
      self.executable = "rat"

      #
      # Set configuration parameters
      #
      #self.configuration["microphonegain"] = RangeParameter( "microphonegain", 30, 0, 100 )
      #self.configuration["speakervolume"] = RangeParameter( "speakervolume", 50, 0, 100 ) 


   def Start( self ):
      """Start service"""
      try:

         # 
         # Start the service; in this case, store command line args in a list and let
         # the superclass _Start the service
         options = []
         #options.append( "-name" )
         #options.append( self.streamDescription.name )
         options.append( "-t" )
         options.append( '%d' % (self.streamDescription.location.ttl ) )
         if self.streamDescription.encryptionKey != 0:
            options.append( "-crypt" )
            options.append( self.streamDescription.encryptionKey )
         options.append( '%s/%d' % ( self.streamDescription.location.host, self.streamDescription.location.port ) )
         self._Start( options )
      except:
         print "Exception in AudioService.Start", sys.exc_type, sys.exc_value
         raise faultType("Failed to start service")
   Start.soap_export_as = "Start"


   def ConfigureStream( self, streamDescription ):
      """Configure the Service according to the StreamDescription, and stop and start rat"""
      AGService.ConfigureStream( self, streamDescription )

      # restart rat, since this is the only way to change the 
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

   agService = AudioService()
   server = Server( int(sys.argv[1]), auth_callback=AuthCallback )
   service = server.create_service_object("Service")
   agService._bind_to_service( service )

   print "Starting server at", agService.get_handle()
   server.run()
