#-----------------------------------------------------------------------------
# Name:        MacVideoProducerService.py
# Purpose:
# Created:     2004/11
# RCS-ID:      $Id: MacVideoProducerService.py,v 1.1 2004-11-18 20:25:36 eolson Exp $
# Copyright:   (c) 2004
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import re
import sys, os
try:    import _winreg
except: pass

import pyGlobus.ioc

from AccessGrid import Toolkit

from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter, TextParameter
from AccessGrid.Platform import IsWindows, IsLinux
from AccessGrid.Platform.Config import AGTkConfig, UserConfig, SystemConfig
from AccessGrid.NetworkLocation import MulticastNetworkLocation


class MacVideoProducerService( AGService ):

    encodings = [ "h261" ]
    onOffOptions = [ "On", "Off" ]

    def __init__( self ):
        AGService.__init__( self )

        self.capabilities = [ Capability( Capability.PRODUCER,
                                          Capability.VIDEO ) ]
        self.executable = os.path.join(os.getcwd(),'qtStream.app/Contents/MacOS/qtStream')

        self.sysConf = SystemConfig.instance()

        # Set configuration parameters

        # note: the datatype of the port parameter changes when a resource is set!
        self.streamname = TextParameter( "streamname", "Video" )
        self.port = TextParameter( "port", "" )
        self.encoding = OptionSetParameter( "encoding", "h261", MacVideoProducerService.encodings )
        self.bandwidth = RangeParameter( "bandwidth", 1200, 0, 3072 )
        self.framerate = RangeParameter( "framerate", 15, 1, 30 )
        self.quality = RangeParameter( "quality", 90, 1, 100 )
        self.transmitOnStart = OptionSetParameter( "transmitonstartup", "On", MacVideoProducerService.onOffOptions )
        self.configuration.append( self.streamname )
        self.configuration.append( self.port )
        self.configuration.append( self.encoding )
        self.configuration.append( self.bandwidth )
        self.configuration.append( self.framerate )
        self.configuration.append (self.quality )
        self.configuration.append (self.transmitOnStart )
        
        self.profile = None


                

    def Start( self ):
        """Start service"""
        try:

            #
            # Start the service; in this case, store command line args in a list and let
            # the superclass _Start the service
            options = []
            if (self.transmitOnStart.value == "On"):
                options.append( '-t')
            options.append( '-E ' + str(self.encoding.value) )
            options.append( '-B ' + str(self.bandwidth.value) )
            options.append( '-F ' + str(self.framerate.value) )
            options.append( '-Q ' + str(self.quality.value) )
            options.append( '%s' % (self.streamDescription.location.host) )
            options.append( '%d' % (self.streamDescription.location.port) )
            if self.streamDescription.location.__dict__.has_key("type"):
                # use TTL from multicast locations only
                if self.streamDescription.location.type == MulticastNetworkLocation.TYPE:
                    options.append( '%d' % (self.streamDescription.location.ttl) )

            self.log.info("Starting VideoProducerService")
            self.log.info(" executable = %s" % self.executable)
            self.log.info(" options = %s" % options)
            self._Start( options )
            #os.remove(startupfile)
        except:
            self.log.exception("Exception in VideoProducerService.Start")
            raise Exception("Failed to start service")

    def Stop( self ):
        """Stop the service"""

        # vic doesn't die easily (on linux at least), so force it to stop
        AGService.ForceStop(self)

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

    def SetResource( self, resource ):
        """Set the resource used by this service"""

        self.log.info("VideoProducerService.SetResource : %s" % resource.resource )
        self.resource = resource

    def SetIdentity(self, profile):
        """
        Set the identity of the user driving the node
        """
        self.log.info("SetIdentity: %s %s", profile.name, profile.email)
        self.profile = profile

if __name__ == '__main__':

    from AccessGrid.AGService import AGServiceI, RunService

    service = MacVideoProducerService()
    serviceI = AGServiceI(service)
    RunService(service,serviceI)
