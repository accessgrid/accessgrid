#-----------------------------------------------------------------------------
# Name:        AudioService.py
# Purpose:
#
# Author:      Thomas D. Uram
#
# Created:     2003/06/02
# RCS-ID:      $Id: AudioService.py,v 1.15 2004-04-26 15:39:49 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys, os
import time
import string

from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter
from AccessGrid import Platform
from AccessGrid.Platform.Config import AGTkConfig, UserConfig
from AccessGrid.NetworkLocation import MulticastNetworkLocation

class AudioService( AGService ):

    def __init__( self ):
        AGService.__init__( self )

        self.capabilities = [ Capability( Capability.CONSUMER, Capability.AUDIO ),
                              Capability( Capability.PRODUCER, Capability.AUDIO ) ]
        self.executable = os.path.join('.','rat')

        #
        # Set configuration parameters
        #
        self.talk = OptionSetParameter( "Talk", "On", ["On", "Off"] )
        self.inputGain = RangeParameter( "Input gain", 50, 0, 100 )
        self.outputGain = RangeParameter( "Output gain", 50, 0, 100 )

        self.configuration.append(self.talk)
        self.configuration.append(self.inputGain)
        self.configuration.append(self.outputGain)

    def WriteRatDefaults(self):
        if Platform.isWindows():
            import _winreg

            # Write defaults into registry
            key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Software\\Mbone Applications\\rat", 0,
                                  _winreg.KEY_SET_VALUE)
            if self.talk.value == "On":    mute = 0
            else:                          mute = 1
            _winreg.SetValueEx(key, "audioInputMute", 0, _winreg.REG_DWORD,
                mute)
            _winreg.SetValueEx(key, "audioInputGain", 0, _winreg.REG_DWORD,
                self.inputGain.value )
            _winreg.SetValueEx(key, "audioOutputGain", 0, _winreg.REG_DWORD,
                self.outputGain.value )

            _winreg.CloseKey(key)

        elif Platform.isLinux() or Platform.isOSX():

            ratDefaultsFile = os.path.join(os.environ["HOME"],".RATdefaults")
            ratDefaults = dict()

            # Read file first, to preserve settings therein
            if os.access(ratDefaultsFile, os.R_OK):
                f = open(ratDefaultsFile,"r")
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line:
                        k,v = line.split(':',1)
                        ratDefaults[k] = v
                f.close()

            # Update settings
            if self.talk.value == "On":    mute = 0
            else:                          mute = 1
            ratDefaults["*audioInputMute"] = str(mute)
            ratDefaults["*audioInputGain"] = str(self.inputGain.value )
            ratDefaults["*audioOutputGain"] = str(self.outputGain.value )

            # Write file with these settings
            f = open(ratDefaultsFile, "w")
            for k,v in ratDefaults.items():
                f.write("%s: %s\n" % (k,v) )
            f.close()



        else:
            raise Exception("Unknown platform: %s" % sys.platform)


    def Start( self ):
        """Start service"""
        try:

            self.WriteRatDefaults()

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

            installDir = AGTkConfig.instance().GetInstallDir()
            ratKillExe = os.path.join(installDir, rk)

            if os.access(ratKillExe, os.X_OK):
                self.log.info("Executing rat-kill")
                self.processManager.StartProcess(ratKillExe, [])
                time.sleep(0.2)
            else:
                self.log.info("rat-kill not found; rat may not die completely")

            self.processManager.TerminateAllProcesses()

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
        UserConfig.instance().SetRtpDefaults( profile )
    SetIdentity.soap_export_as = "SetIdentity"




if __name__ == '__main__':

    from AccessGrid.AGService import AGServiceI, RunService

    service = AudioService()
    serviceI = AGServiceI(service)
    RunService(service,serviceI,int(sys.argv[1]))
