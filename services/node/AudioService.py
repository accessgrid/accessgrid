#-----------------------------------------------------------------------------
# Name:        AudioService.py
# Purpose:
#
# Author:      Thomas D. Uram
#
# Created:     2003/06/02
# RCS-ID:      $Id: AudioService.py,v 1.20 2004-05-10 19:37:13 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys, os
import time
import string
try:    import _winreg
except: pass

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
        self.talk = OptionSetParameter( "talk", "On", ["On", "Off"] )
        self.inputGain = RangeParameter( "inputgain", 50, 0, 100 )
        self.outputGain = RangeParameter( "outputgain", 50, 0, 100 )

        self.configuration.append(self.talk)
        self.configuration.append(self.inputGain)
        self.configuration.append(self.outputGain)

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
                k = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                                    r"Software\Mbone Applications\common",
                                    0,
                                    _winreg.KEY_SET_VALUE)

                # Rat reads these (without '*')
                _winreg.SetValueEx(k, "rtpName", 0,
                                   _winreg.REG_SZ, self.profile.name)
                _winreg.SetValueEx(k, "rtpEmail", 0,
                                   _winreg.REG_SZ, self.profile.email)
                _winreg.SetValueEx(k, "rtpPhone", 0,
                                   _winreg.REG_SZ, self.profile.phoneNumber)
                _winreg.SetValueEx(k, "rtpLoc", 0,
                                   _winreg.REG_SZ, self.profile.location)
                _winreg.SetValueEx(k, "rtpNote", 0,
                                   _winreg.REG_SZ, str(self.profile.publicId) )
                _winreg.CloseKey(k)
            except:
                self.log.exception("Error writing RTP defaults to registry")
        


        
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
            ratKillExe = os.path.join('.', rk)

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
        self.__SetRTPDefaults( profile )
    SetIdentity.soap_export_as = "SetIdentity"
    



if __name__ == '__main__':

    from AccessGrid.AGService import AGServiceI, RunService

    # Look for executables in the current directory,
    # since the rat startup script needs to 
    if os.environ.has_key("PATH"):
        os.environ["PATH"] = os.pathsep.join([os.environ["PATH"],'.'])
    else:
        os.environ["PATH"] = '.'

    service = AudioService()
    serviceI = AGServiceI(service)
    RunService(service,serviceI,int(sys.argv[1]))
