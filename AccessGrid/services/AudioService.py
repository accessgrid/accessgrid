#-----------------------------------------------------------------------------
# Name:        AudioService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/06/02
# RCS-ID:      $Id: AudioService.py,v 1.13 2003-04-09 20:30:05 olson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys, os
import time

from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter
from AccessGrid import Platform

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
         raise Exception("Failed to start service")
   Start.soap_export_as = "Start"


   def Stop( self ):
      """Stop the service"""
      self.started = 0
      try:

         #
         # See if we have rat-kill.
         #

         if sys.platform == Platform.WIN:
            rk = "rat-kill.exe"
         else:
            rk = "rat-kill"

         installDir = Platform.GetInstallDir()
         ratKillExe = os.path.join(installDir, rk)

         if os.access(ratKillExe, os.X_OK):
            self.processManager.start_process(ratKillExe, [])
            time.sleep(0.2)
         else:
            self.processManager.terminate_all_processes()

      except:
         print "Exception in AGService.Stop ", sys.exc_type, sys.exc_value
         raise Exception("AGService.Stop failed : ", str( sys.exc_value ) )
   Stop.soap_export_as = "Stop"


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
