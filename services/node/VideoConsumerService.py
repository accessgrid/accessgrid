#-----------------------------------------------------------------------------
# Name:        VideoConsumerService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/06/02
# RCS-ID:      $Id: VideoConsumerService.py,v 1.6 2003-05-28 18:51:32 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys

from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid import Platform


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
         # Check whether the network location has a "type" attribute
         # Note: this condition is only to maintain compatibility between
         # older venue servers creating network locations without this attribute
         # and newer services relying on the attribute; it should be removed
         # when the incompatibility is gone
         if self.streamDescription.location.__dict__.has_key("type"):
             if self.streamDescription.location.type == MulticastNetworkLocation.TYPE:
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
      """Configure the Service according to the StreamDescription"""

      ret = AGService.ConfigureStream( self, streamDescription )
      if ret and self.started:
         # service is already running with this config; ignore
         return

      # if started, stop
      if self.started:
         self.Stop()

      # if enabled, start
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
   
   agService = VideoConsumerService(server)

   service = server.create_service_object("Service")
   agService._bind_to_service( service )

   # Register the signal handler so we can shut down cleanly
   signal.signal(signal.SIGINT, SignalHandler)

   print "Starting server at", agService.get_handle()
   server.RunInThread()

   # Keep the main thread busy so we can catch signals
   while server.IsRunning():
      time.sleep(1)

