#-----------------------------------------------------------------------------
# Name:        VideoService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/06/02
# RCS-ID:      $Id: VideoService.py,v 1.1 2003-12-17 16:09:40 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys, os

from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid import Platform
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter, TextParameter
from AccessGrid.NetworkLocation import MulticastNetworkLocation

vicstartup="""option add Vic.disable_autoplace %s startupFile
option add Vic.muteNewSources %s startupFile
option add Vic.maxbw 6000 startupFile
option add Vic.bandwidth %d startupFile
option add Vic.framerate %d startupFile
option add Vic.quality %d startupFile
option add Vic.defaultFormat %s startupFile
option add Vic.inputType %s startupFile
set device \"%s\"
set defaultPort($device) %s
option add Vic.device $device startupFile
option add Vic.transmitOnStartup %s startupFile
option add Vic.defaultTTL 127 startupFile
proc user_hook {} {
    update_note 0 \"%s\"
}
"""


def OnOff(onOffVal):
    if onOffVal == "On":
        return "true"
    elif onOffVal == "Off":
        return "false"
    raise Exception,"OnOff value neither On nor Off: %s" % onOffVal


class VideoService( AGService ):

   encodingOptions = [ "h261" ]
   standardOptions = [ "NTSC", "PAL" ]
   onOffOptions = [ "On", "Off" ]

   def __init__( self, server ):
      AGService.__init__( self, server )

      self.capabilities = [ Capability( Capability.PRODUCER, Capability.VIDEO ),
                            Capability( Capability.CONSUMER, Capability.VIDEO ) ]

      self.executable = os.path.join(Platform.GetInstallDir(), "vic")

      #
      # Set configuration parameters
      #

      # note: the datatype of the port parameter changes when a resource is set!
      self.streamname = TextParameter( "streamname", "Video" )
      self.port = TextParameter( "port", "" ) 
      self.encoding = OptionSetParameter( "encoding", "h261", VideoService.encodingOptions )
      self.standard = OptionSetParameter( "standard", "NTSC", VideoService.standardOptions )
      self.bandwidth = RangeParameter( "bandwidth", 800, 0, 3072 ) 
      self.framerate = RangeParameter( "framerate", 25, 1, 30 ) 
      self.quality = RangeParameter( "quality", 75, 1, 100 )
      self.transmitOnStart = OptionSetParameter( "transmitonstartup", "On", VideoService.onOffOptions )
      self.muteSources = OptionSetParameter( "mutesources", "Off", VideoService.onOffOptions )
      
      self.configuration.append( self.streamname )
      self.configuration.append( self.port )
      self.configuration.append( self.encoding )
      self.configuration.append( self.standard )
      self.configuration.append( self.bandwidth )
      self.configuration.append( self.framerate )
      self.configuration.append (self.quality )
      self.configuration.append (self.transmitOnStart )
      self.configuration.append (self.muteSources )

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
            vicDevice = vicDevice.replace("[","\[")
            vicDevice = vicDevice.replace("]","\]")

         #
         # Write vic startup file
         #
         startupfile = os.path.join(Platform.GetTempDir(),
            'VideoService_%d.vic' % ( os.getpid() ) )

         f = open(startupfile,"w")
         if self.port.value == '':
            portstr = "None"
         else:
            portstr = self.port.value
            
         if self.muteSources.value == "On":
            # streams are muted, so disable autoplace
            disableAutoplace = "true"
         else:
            # streams are not muted, so don't disable autoplace
            # (flags should not be negative!)
            disableAutoplace = "false"
         f.write( vicstartup % ( disableAutoplace,
                                 OnOff(self.muteSources.value),
                                 self.bandwidth.value,
                                 self.framerate.value, 
                                 self.quality.value,
                                 self.encoding.value,
                                 self.standard.value,
                                 vicDevice,                 
                                 portstr,
                                 OnOff(self.transmitOnStart.value),
                                 self.streamname.value ) )
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
         options.append( '"' + self.streamname.value + '"'  )
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
         self.log.info("Starting VideoService")
         self.log.info(" executable = %s" % self.executable)
         self.log.info(" options = %s" % options)
         self._Start( options )
         #os.remove(startupfile)
      except:
         self.log.exception("Exception in VideoService.Start")
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

      self.log.info("VideoService.SetResource : %s" % resource.resource )
      self.resource = resource
      if "portTypes" in self.resource.__dict__.keys():

          # Find the config element that refers to "port"
          try:
            index = self.configuration.index(self.port)
            found = 1
          except ValueError:
            found = 0

          # Create the port parameter as an option set parameter, now
          # that we have multiple possible values for "port"
          self.port = OptionSetParameter( "port", self.resource.portTypes[0], 
                                                           self.resource.portTypes )

          # Replace or append the "port" element
          if found:
            self.configuration[index] = self.port
          else:
            self.configuration.append(self.port)

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
   
   agService = VideoService(server)

   service = server.create_service_object("Service")
   agService._bind_to_service( service )

   # Register the signal handler so we can shut down cleanly
   signal.signal(signal.SIGINT, SignalHandler)

   print "Starting server at", agService.get_handle()
   server.RunInThread()

   # Keep the main thread busy so we can catch signals
   while server.IsRunning():
      time.sleep(1)

