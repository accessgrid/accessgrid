import sys
import os
from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.AGService import *
from AccessGrid.AGParameter import *


AG_VIDEO_PORT_TELEVISION = "Television"
AG_VIDEO_PORT_SVIDEO = "S-Video"
AG_VIDEO_PORT_COMPOSITE1 = "Composite1"
AG_VIDEO_PORT_COMPOSITE3 = "Composite3"
AG_VIDEO_PORTS = [ AG_VIDEO_PORT_TELEVISION, AG_VIDEO_PORT_SVIDEO, 
                   AG_VIDEO_PORT_COMPOSITE1, AG_VIDEO_PORT_COMPOSITE3 ]


vicstartup="""option add Vic.muteNewSources true startupFile
option add Vic.maxbw 6000 startupFile
option add Vic.bandwidth %d startupFile
option add Vic.framerate %d startupFile
option add Vic.quality 85 startupFile
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

   def __init__( self ):
      print self.__class__, ".init"
      AGService.__init__( self )

      self.capabilities = [ Capability( Capability.PRODUCER, Capability.VIDEO ) ]
      self.executable = "vic"

      #
      # Set configuration parameters
      #
      self.configuration["Port"] = OptionSetParameter( "Port", AG_VIDEO_PORT_SVIDEO, AG_VIDEO_PORTS ) 
      self.configuration["Bandwidth"] = RangeParameter( "Bandwidth", 800, 0, 3072 ) 
      self.configuration["Frame Rate"] = RangeParameter( "Frame Rate", 25, 1, 30 ) 
      self.configuration["Stream Name"] = ValueParameter( "Stream Name", "Video" )

      #
      # Discover vic video devices
      #
      self.__DiscoverVideoDevices()
      print "vic devices ", self.vicDevices


   def Start( self, connInfo ):
      __doc__ = """Start service"""
      try:
         
         #
         # Resolve assigned resource to a device understood by vic
         #
         vicDevice = None
         for device in self.vicDevices:   
            if device.find( self.resource.resource ) > -1:
               vicDevice = device
               break

         #
         # Write vic startup file
         #
         startupfile = 'VideoProducerService_%d.vic' % ( os.getpid() )
         f = open(startupfile,"w")
         f.write( vicstartup % (self.configuration["Bandwidth"].value, 
                                    self.configuration["Frame Rate"].value, 
#FIXME - encoding is hard-coded
                                    "h261", 
                                    vicDevice,
                                    self.configuration["Port"].value  ) )
         f.close()


         # 
         # Start the service; in this case, store command line args in a list and let
         # the superclass _Start the service
         print "Start service"
         print "Location : ", self.location.host, self.location.port, self.location.ttl
         options = []
         options.append( "-u" )
         options.append( startupfile ) 
         options.append( "-C" )
         options.append( self.configuration["Stream Name"].value )
         options.append( '%s/%d/%d' % ( self.location.host, self.location.port, self.location.ttl ) )
         self._Start( options )
         print "pid = ", self.childPid
      except:
         print "Exception in VideoProducerService.Start", sys.exc_type, sys.exc_value
   Start.soap_export_as = "Start"
   Start.pass_connection_info = 1


   def ConfigureStream( self, connInfo, streamDescription ):
      """Configure the Service according to the StreamDescription, and stop and start rat"""
      AGService.ConfigureStream( self, connInfo, streamDescription )

      # restart rat, since this is the only way to change the 
      # stream location (for now!)
      if self.started:
         self.Stop( connInfo )
         self.Start( connInfo )
   ConfigureStream.soap_export_as = "ConfigureStream"
   ConfigureStream.pass_connection_info = 1



   def __DiscoverVideoDevices( self ):
      """Discover video devices usable by vic, for matching with assigned resource"""

      deviceDiscoveryScript="""foreach d $inputDeviceList {
          set nick [$d nickname]
          if { $nick == "still"  || $nick == "x11" } {
         continue
          }
          set attr [$d attributes]
          if { $attr == "disabled" } {
         continue
          }

          set portnames [attribute_class $attr port]
          puts "device: $nick"
          puts "portnames: $portnames"
      }
      puts "doneWithPorts"

      adios
      """

      deviceDiscoveryScriptFile="enum.tcl"

      self.vicDevices = []

      f = open(deviceDiscoveryScriptFile,"w")
      f.write( deviceDiscoveryScript )
      f.close()

#FIXME - direct reference to vic
      f = os.popen('vic -u %s' % (deviceDiscoveryScriptFile) )
      outlines = f.readlines()
      f.close()

      os.remove( deviceDiscoveryScriptFile )

      for line in outlines:
         if line.beginswith("device:"):
            vicDevice = line[8:]
            self.vicDevices.append( vicDevice )

if __name__ == '__main__':

   agService = VideoProducerService()
   server = Server( 0 )
   service = server.create_service_object()
   agService._bind_to_service( service )

   print "Register with the service manager ! "
   thread.start_new_thread( Client.Handle( sys.argv[2] ).get_proxy().RegisterService, 
                            ( sys.argv[1], agService.get_handle() ) )

   print "Starting server at", agService.get_handle()
   server.run()
