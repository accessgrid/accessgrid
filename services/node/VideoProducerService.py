#-----------------------------------------------------------------------------
# Name:        VideoProducerService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/06/02
# RCS-ID:      $Id: VideoProducerService.py,v 1.10 2003-05-28 18:51:32 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys
import os

from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid import Platform
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter, TextParameter
from AccessGrid.NetworkLocation import MulticastNetworkLocation


vicstartup="""option add Vic.disable_autoplace true startupFile
option add Vic.muteNewSources true startupFile
option add Vic.maxbw 6000 startupFile
option add Vic.bandwidth %d startupFile
option add Vic.framerate %d startupFile
option add Vic.quality 75 startupFile
option add Vic.defaultFormat %s startupFile
option add Vic.inputType NTSC startupFile
set device \"%s\"
set defaultPort($device) %s
option add Vic.device $device startupFile
option add Vic.transmitOnStartup true startupFile
option add Vic.defaultTTL 127 startupFile
proc user_hook {} {
}
"""



class VideoProducerService( AGService ):

   encodings = [ "h261" ]

   def __init__( self, server ):
      AGService.__init__( self, server )

      self.capabilities = [ Capability( Capability.PRODUCER, Capability.VIDEO ) ]
      self.executable = "vic"

      #
      # Set configuration parameters
      #

      # note: the datatype of the port parameter changes when a resource is set!
      self.configuration["streamname"] = TextParameter( "streamname", "Video" )
      self.configuration["port"] = TextParameter( "port", "" ) 
      self.configuration["encoding"] = OptionSetParameter( "encoding", "h261", VideoProducerService.encodings )
      self.configuration["bandwidth"] = RangeParameter( "bandwidth", 800, 0, 3072 ) 
      self.configuration["framerate"] = RangeParameter( "framerate", 25, 1, 30 ) 


   def Start( self ):
      """Start service"""
      try:
         
         #
         # Resolve assigned resource to a device understood by vic
         #
         if self.resource == "None":
            vicDevice = "None"
         else:
            vicDevice = self.resource.resource

         #
         # Write vic startup file
         #
         startupfile = os.path.join(Platform.GetTempDir(),
            'VideoProducerService_%d.vic' % ( os.getpid() ) )
         
         f = open(startupfile,"w")
         f.write( vicstartup % (self.configuration["bandwidth"].value, 
                                    self.configuration["framerate"].value, 
                                    self.configuration["encoding"].value, 
                                    vicDevice,                 
                                    self.configuration["port"].value  ) )
         f.close()

         # Replace double backslashes in the startupfile name with single
         #  forward slashes (vic will crash otherwise)
         if sys.platform == Platform.WIN:
            startupfile = startupfile.replace("\\","/")

         # 
         # Start the service; in this case, store command line args in a list and let
         # the superclass _Start the service
         options = []
         options.append( "-u" )
         options.append( startupfile ) 
         options.append( "-C" )
         options.append( '"' + self.configuration["streamname"].value + '"'  )
         if self.streamDescription.encryptionFlag != 0:
            options.append( "-K" )
            options.append( self.streamDescription.encryptionKey )
         # Check whether the network location has a "type" attribute
         # Note: this condition is only to maintain compatibility between
         # older venue servers creating network locations without this attribute
         # and newer services relying on the attribute; it should be removed
         # when the incompatibility is gone
         if self.streamDescription.location.__dict__.has_key("type"):
             # use TTL from multicast locations only
             if self.streamDescription.location.type == MulticastNetworkLocation.TYPE:
                options.append( "-t" )
                options.append( '%d' % (self.streamDescription.location.ttl) )
         options.append( '%s/%d' % ( self.streamDescription.location.host, 
                                        self.streamDescription.location.port) )
         self.log.info("Starting VideoProducerService")
         self.log.info(" executable = %s" % self.executable)
         self.log.info(" options = %s" % options)
         self._Start( options )
         #os.remove(startupfile)
      except:
         self.log.exception("Exception in VideoProducerService.Start")
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

   def SetResource( self, resource ):
      """Set the resource used by this service"""

      self.log.info("VideoProducerService.SetResource : %s" % resource.resource )
      self.resource = resource
      if "portTypes" in self.resource.__dict__.keys():
          self.configuration["port"] = OptionSetParameter( "port", self.resource.portTypes[0], 
                                                           self.resource.portTypes )
   SetResource.soap_export_as = "SetResource"

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
   
   agService = VideoProducerService(server)

   service = server.create_service_object("Service")
   agService._bind_to_service( service )

   # Register the signal handler so we can shut down cleanly
   signal.signal(signal.SIGINT, SignalHandler)

   print "Starting server at", agService.get_handle()
   server.RunInThread()

   # Keep the main thread busy so we can catch signals
   while server.IsRunning():
      time.sleep(1)

