import sys
import os
from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter


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

        # note: the datatype of the port parameter changes when a resource is set!
        self.configuration["Port"] = ValueParameter( "Port", None )
        self.configuration["Bandwidth"] = RangeParameter( "Bandwidth", 800, 0, 3072 )
        self.configuration["Frame Rate"] = RangeParameter( "Frame Rate", 25, 1, 30 )
        self.configuration["Stream Name"] = ValueParameter( "Stream Name", "Video" )


    def Start( self, connInfo ):
        __doc__ = """Start service"""
        try:

            #
            # Resolve assigned resource to a device understood by vic
            #
            vicDevice = self.resource.resource

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
            print "Location : ", self.streamDescription.location.host, self.streamDescription.location.port, self.streamDescription.location.ttl
            options = []
            options.append( "-u" )
            options.append( startupfile )
            options.append( "-C" )
            options.append( self.configuration["Stream Name"].value )
            """
            if self.streamDescription.encryptionKey != None:
               options.append( "-k" )
               options.append( self.streamDescription.encryptionKey )
            """
            options.append( '%s/%d/%d' % ( self.streamDescription.location.host, self.streamDescription.location.port, self.streamDescription.location.ttl ) )
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

    def SetResource( self, connInfo, resource ):
        """Set the resource used by this service"""
        print " * ** * inside VideoProducerService.SetResource"

        # Check authorization
        if not self.authManager.Authorize( connInfo.get_remote_name() ):  raise faultType("Authorization failed")

        self.resource = resource
        self.configuration["Port"] = OptionSetParameter( "Port", self.resource.portTypes[0], self.resource.portTypes )

    SetResource.soap_export_as = "SetResource"
    SetResource.pass_connection_info = 1


def AuthCallback(server, g_handle, remote_user, context):
    return 1

if __name__ == '__main__':
    from AccessGrid.hosting.pyGlobus import Client
    import thread

    agService = VideoProducerService()
    server = Server( 0, auth_callback=AuthCallback )
    service = server.create_service_object()
    agService._bind_to_service( service )

    print "Register with the service manager ! "
    thread.start_new_thread( Client.Handle( sys.argv[2] ).get_proxy().RegisterService,
                             ( sys.argv[1], agService.get_handle() ) )

    print "Starting server at", agService.get_handle()
    server.run()
