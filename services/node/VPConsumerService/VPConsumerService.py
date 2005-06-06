#-----------------------------------------------------------------------------
# Name:        VideoConsumerService.py
# Purpose:
#
# Author:      Thomas D. Uram
#
# Created:     2003/06/02
# RCS-ID:      $Id: VPConsumerService.py,v 1.2 2005-06-06 17:25:55 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys, os
try:    import _winreg
except: pass

from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter
from AccessGrid import Platform
from AccessGrid.Platform.Config import AGTkConfig, UserConfig
from AccessGrid.NetworkLocation import MulticastNetworkLocation

class VideoConsumerService( AGService ):

    def __init__( self ):
        AGService.__init__( self )

        self.capabilities = [ Capability( Capability.CONSUMER, Capability.VIDEO ) ]
        self.executable = os.path.join('.','vic')

        #
        # Set configuration parameters
        #
        pass


    def __SetRTPDefaults(self, profile):
        """
        Set values used by rat for identification
        """
        if profile == None:
            self.log.exception("Invalid profile (None)")
            raise Exception, "Can't set RTP Defaults without a valid profile."

        if sys.platform == 'linux2':
            try:
                rtpDefaultsFile=os.path.join(os.environ["HOME"], ".RTPdefaults")
                rtpDefaultsText="*rtpName: %s\n*rtpEmail: %s\n*rtpLoc: %s\n*rtpPhone: \
                                 %s\n*rtpNote: %s\n"
                rtpDefaultsFH=open( rtpDefaultsFile,"w")
                rtpDefaultsFH.write( rtpDefaultsText % ( profile.name,
                                       profile.email,
                                       profile.location,
                                       profile.phoneNumber,
                                       profile.publicId ) )
                rtpDefaultsFH.close()
            except:
                self.log.exception("Error writing RTP defaults file: %s", rtpDefaultsFile)

        elif sys.platform == 'win32':
            try:
                #
                # Set RTP defaults according to the profile
                #
                k = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER,
                                    r"Software\Mbone Applications\common")

                # Vic reads these values (with '*')
                _winreg.SetValueEx(k, "*rtpName", 0,
                                   _winreg.REG_SZ, profile.name)
                _winreg.SetValueEx(k, "*rtpEmail", 0,
                                   _winreg.REG_SZ, profile.email)
                _winreg.SetValueEx(k, "*rtpPhone", 0,
                                   _winreg.REG_SZ, profile.phoneNumber)
                _winreg.SetValueEx(k, "*rtpLoc", 0,
                                   _winreg.REG_SZ, profile.location)
                _winreg.SetValueEx(k, "*rtpNote", 0,
                                   _winreg.REG_SZ, str(profile.publicId) )
                _winreg.CloseKey(k)
            except:
                self.log.exception("Error writing RTP defaults to registry")
        
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

            # This is a consumer, so disable device selection in vic
            options.append('-XrecvOnly=1')
                    
            # Add address/port options (these must occur last; don't add options beyond here)
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
        self.__SetRTPDefaults(profile)
    SetIdentity.soap_export_as = "SetIdentity"



if __name__ == '__main__':

    from AccessGrid.interfaces.AGService_interface import AGService as AGServiceI
    from AccessGrid.AGService import RunService

    service = VideoConsumerService()
    serviceI = AGServiceI(service)
    RunService(service,serviceI)
