#-----------------------------------------------------------------------------
# Name:        AudioService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/06/02
# RCS-ID:      $Id: AudioService.py,v 1.17 2003-04-23 19:29:50 olson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys, os
import time

import logging
log = logging.getLogger("AG.AudioService")

from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter
from AccessGrid import Platform

class AudioService( AGService ):

   def __init__( self, server ):
      AGService.__init__( self, server )

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
         if self.streamDescription.encryptionFlag != 0:
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
      self.server.stop()
      print "Stopping audio service"
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

         self.processManager.terminate_all_processes()

      except:
         print "Exception in AGService.Stop ", sys.exc_type, sys.exc_value
         raise Exception("AGService.Stop failed : ", str( sys.exc_value ) )

      print "audio service Stop returning"
      
   Stop.soap_export_as = "Stop"


   def ConfigureStream( self, streamDescription ):
      """Configure the Service according to the StreamDescription, and stop and start rat"""
      ret = AGService.ConfigureStream( self, streamDescription )
      if ret:
         return

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

   top = logging.getLogger("AG")
   top.setLevel(logging.DEBUG)
   top.addHandler(logging.StreamHandler())

   server = Server( int(sys.argv[1]), auth_callback=AuthCallback )

   agService = AudioService(server)

   service = server.create_service_object("Service")
   agService._bind_to_service( service )

   print "Starting server at", agService.get_handle()
   server.run()
