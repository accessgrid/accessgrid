#-----------------------------------------------------------------------------
# Name:        AudioService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/06/02
# RCS-ID:      $Id: AudioService.py,v 1.8 2003-10-22 19:55:44 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys, os
import time
import string

from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter
from AccessGrid import Platform
from AccessGrid.NetworkLocation import MulticastNetworkLocation

class AudioService( AGService ):

   def __init__( self, server ):
      AGService.__init__( self, server )

      self.capabilities = [ Capability( Capability.CONSUMER, Capability.AUDIO ), 
                            Capability( Capability.PRODUCER, Capability.AUDIO ) ]
      self.executable = os.path.join(Platform.GetInstallDir(), "rat")

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
         if self.streamDescription.name and len(self.streamDescription.name.strip()) > 0:
            options.append( "-C" )
            if sys.platform == 'linux2':
                # Rat doesn't like spaces in linux command line arguments.
                stream_description_no_spaces = string.replace(self.streamDescription.name, " ", "_")
                options.append( stream_description_no_spaces )
            else:
                options.append(self.streamDescription.name)
         options.append( "-f" )
         options.append( "L16-16K-Mono" )
         # Check whether the network location has a "type" attribute
         # Note: this condition is only to maintain compatibility between
         # older venue servers creating network locations without this attribute
         # and newer services relying on the attribute; it should be removed
         # when the incompatibility is gone
         if self.streamDescription.location.__dict__.has_key("type"):
             if self.streamDescription.location.type == MulticastNetworkLocation.TYPE:
                options.append( "-t" )
                options.append( '%d' % (self.streamDescription.location.ttl ) )
         if self.streamDescription.encryptionFlag != 0:
            options.append( "-crypt" )
            options.append( self.streamDescription.encryptionKey )
         options.append( '%s/%d' % ( self.streamDescription.location.host, self.streamDescription.location.port ) )
         self.log.info("Starting AudioService")
         self.log.info(" executable = %s" % self.executable)
         self.log.info(" options = %s" % options)
         self._Start( options )
      except:
         self.log.exception("Exception in AudioService.Start")
         raise Exception("Failed to start service")
   Start.soap_export_as = "Start"


   def Stop( self ):
      """Stop the service"""
      self.started = 0
      try:
         self.log.info("Stop service")

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
         self.log.exception("Exception in AGService.Stop ")
         raise Exception("AGService.Stop failed : ", str( sys.exc_value ) )
      
   Stop.soap_export_as = "Stop"


   def ConfigureStream( self, streamDescription ):
      """Configure the Service according to the StreamDescription, and stop and start rat"""

      # Configure the stream
      ret = AGService.ConfigureStream( self, streamDescription )
      if ret and self.started:
         # service is already running with this config; ignore
         return

      # If started, stop
      if self.started:
         self.Stop()

      # If enabled, start
      if self.enabled:
         self.Start()
   ConfigureStream.soap_export_as = "ConfigureStream"

   def SetIdentity(self, profile):
      """
      Set the identity of the user driving the node
      """
      Platform.SetRtpDefaults( profile )
   SetIdentity.soap_export_as = "SetIdentity"



def AuthCallback(server, g_handle, remote_user, context):
    return 1

# Signal handler to shut down cleanly
def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the service.
    Then it stops the hostingEnvironment.
    """
    global agService
    agService.Shutdown()


if __name__ == '__main__':
   from AccessGrid.hosting.pyGlobus import Client
   import thread
   import signal
   import time

   server = Server( int(sys.argv[1]), auth_callback=AuthCallback )

   agService = AudioService(server)

   service = server.create_service_object("Service")
   agService._bind_to_service( service )

   # Register the signal handler so we can shut down cleanly
   signal.signal(signal.SIGINT, SignalHandler)

   print "Starting server at", agService.get_handle()
   server.RunInThread()

   # Keep the main thread busy so we can catch signals
   while server.IsRunning():
      time.sleep(1)
