#-----------------------------------------------------------------------------
# Name:        AudioService.py
# Purpose:
# Created:     2003/06/02
# RCS-ID:      $Id: AudioService.py,v 1.22 2007/09/12 07:00:14 douglask Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys, os
import time
import string
import wx
try:    import _winreg
except: pass

from AccessGrid.Descriptions import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter
from AccessGrid.AGParameter import RangeParameter

from AccessGrid import Platform
from AccessGrid.Platform.Config import AGTkConfig, UserConfig, SystemConfig
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.Platform.ProcessManager import ProcessManager

class AudioService( AGService ):

    def __init__( self ):
        AGService.__init__( self )
        self.thepath = os.getcwd()
        self.windowGeometry = None

        self.capabilities = [ Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                          "L16",16000,self.id),
                              Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                          "L16",8000,self.id),
                              Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                          "L8",16000, self.id),
                              Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                          "L8",8000, self.id),
                               Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                           "PCMU", 16000, self.id),
                              Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                          "PCMU",8000, self.id),
                              Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                          "GSM",16000, self.id),
                              Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                          "GSM",8000, self.id),
                              Capability( Capability.PRODUCER,
                                          Capability.AUDIO,
                                          "L16",16000, self.id)]
        
        if Platform.IsWindows():
            rat = "rat.exe"
            ratmedia = "ratmedia.exe"
            ratui = "rat-ui.exe"
            ratkill = "rat-kill.exe"
        else:
            rat = "rat"
            ratmedia = "ratmedia"
            ratui = "rat-ui"
            ratkill = "rat-kill"

        self.executable = os.path.join(os.getcwd(), rat)
        self.rat_media = os.path.join(os.getcwd(), ratmedia)
        self.rat_ui = os.path.join(os.getcwd(), ratui)
        self.rat_kill = os.path.join(os.getcwd(), ratkill)
        if not os.path.isfile(self.executable):
            self.executable = rat
            self.rat_media = ratmedia
            self.rat_ui = ratui
            self.rat_kill = ratkill
            # For some reason, a full path is need for ratkill
            for dir in os.getenv("PATH").split(":"):
                ratkill_fullpath = os.path.join(dir, ratkill)
                if os.access(ratkill_fullpath, os.X_OK):
                    self.rat_kill = ratkill_fullpath
                    break

        self.sysConf = SystemConfig.instance()

        # Set configuration parameters
        self.talk = OptionSetParameter( "Talk", "Off", ["On", "Off"] )
        self.inputGain = RangeParameter( "Input Gain", 50, 0, 100 )
        if Platform.isOSX():
            self.outputGain = RangeParameter( "Output Gain", 4, 0, 100 )
        else:
            self.outputGain = RangeParameter( "Output Gain", 50, 0, 100 )
        self.silenceSuppression = OptionSetParameter( "Silence Suppression", "Off", ["Off","Automatic","Manual"] )

        self.positionWindow = OptionSetParameter( 'Position Window', 'Off', ['Off', 'Justify Left', 'Justify Right'])

        self.configuration.append(self.talk)
        self.configuration.append(self.inputGain)
        self.configuration.append(self.outputGain)
        self.configuration.append(self.silenceSuppression)
        self.configuration.append(self.positionWindow)

        if Platform.isLinux() or Platform.isFreeBSD():
            # note: the forceOSSAC97 attribute will only exist for the above platforms
            self.forceOSSAC97 = OptionSetParameter( "Force AC97", "False", ["True", "False"] )
            self.configuration.append(self.forceOSSAC97)

        self.useSiteId = OptionSetParameter( "Use site id", "On", ["On", "Off"] )
        self.configuration.append(self.useSiteId)

        self.profile = None

    def __SetRTPDefaults(self, profile):
        """
        Set values used by rat for identification
        """
        if profile == None:
            self.log.exception("Invalid profile (None)")
            raise Exception, "Can't set RTP Defaults without a valid profile."

        if Platform.isLinux() or Platform.isFreeBSD() or Platform.isOSX():
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

        elif Platform.isWindows():
            try:
                # Set RTP defaults according to the profile
                k = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER,
                                    r"Software\Mbone Applications\common")

                # Rat reads these (without '*')
                _winreg.SetValueEx(k, "rtpName", 0,
                                   _winreg.REG_SZ, profile.name)
                _winreg.SetValueEx(k, "rtpEmail", 0,
                                   _winreg.REG_SZ, profile.email)
                _winreg.SetValueEx(k, "rtpPhone", 0,
                                   _winreg.REG_SZ, profile.phoneNumber)
                _winreg.SetValueEx(k, "rtpLoc", 0,
                                   _winreg.REG_SZ, profile.location)
                _winreg.SetValueEx(k, "rtpNote", 0,
                                   _winreg.REG_SZ, str(profile.publicId) )
                _winreg.CloseKey(k)
            except:
                self.log.exception("Error writing RTP defaults to registry")
        


        
    def WriteRatDefaults(self):
        if Platform.isWindows():
            # Write defaults into registry
            try:
                key = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER,
                                        "Software\\Mbone Applications\\rat")
                if self.talk.value == "On":
                    mute = 0
                else:
                    mute = 1
                    
                _winreg.SetValueEx(key, "audioInputMute", 0, _winreg.REG_DWORD,
                                   mute)
                _winreg.SetValueEx(key, "audioInputGain", 0, _winreg.REG_DWORD,
                                   self.inputGain.value )
                _winreg.SetValueEx(key, "audioOutputGain", 0,
                                   _winreg.REG_DWORD, self.outputGain.value )
                _winreg.SetValueEx(key, "audioSilence", 0,
                                   _winreg.REG_SZ, self.silenceSuppression.value )

                _winreg.CloseKey(key)
            except:
                self.log.exception("Couldn't put rat defaults in registry.")

        elif Platform.isLinux() or Platform.isOSX() or Platform.isFreeBSD():

            ratDefaultsFile = os.path.join(os.environ["HOME"],".RATdefaults")
            ratDefaults = dict()

            # Read file first, to preserve settings therein
            if os.access(ratDefaultsFile, os.R_OK):
                f = open(ratDefaultsFile,"r")
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line:
                        try:
                            k,v = line.split(':',1)
                            ratDefaults[k] = v
                        except:
                            self.log.exception('Error processing rat defaults line: %s', line)
                f.close()

            # Update settings
            if self.talk.value == "On":
                mute = 0
            else:
                mute = 1

            ratDefaults["*audioInputMute"] = str(mute)
            ratDefaults["*audioInputGain"] = str(self.inputGain.value )
            ratDefaults["*audioOutputGain"] = str(self.outputGain.value )
            ratDefaults["*audioSilence"] = str(self.silenceSuppression.value )

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
            # Initialize environment for rat
            try:
                self.__SetRTPDefaults(self.profile)
            except:
                self.log.exception("Error setting RTP defaults")
            self.WriteRatDefaults()

            if Platform.isLinux() or Platform.isFreeBSD():
                # note: the forceOSSAC97 attribute will only exist for the above platforms
                if self.forceOSSAC97.value == "True":
  	                self.log.info("Setting OSS_IS_AC97 = 1")
  	                os.environ['OSS_IS_AC97'] = "1"

            # Enable firewall
            self.sysConf.AppFirewallConfig(self.executable, 1)
            self.sysConf.AppFirewallConfig(self.rat_media, 1)
            self.sysConf.AppFirewallConfig(self.rat_ui, 1)
            self.sysConf.AppFirewallConfig(self.rat_kill, 1)
            
            # Start the service;
            # in this case, store command line args in a list and let
            # the superclass _Start the service
            options = []
            if self.streamDescription.name and \
                   len(self.streamDescription.name.strip()) > 0:
                options.append( "-C" )
                if Platform.isLinux() or Platform.isFreeBSD() or Platform.isOSX():
                    # Rat doesn't like spaces in linux command line arguments.
                    stream_description_no_spaces = string.replace(
                        self.streamDescription.name, " ", "_")
                    options.append( stream_description_no_spaces )
                else:
                    options.append(self.streamDescription.name)
            
            # pass public id as site id
            if self.useSiteId.value == 'On' and self.profile:
                # site id not supported in UCL rat yet, which is used on macs.
                options.append("-S")
                options.append(self.profile.publicId)
    
            if not self.positionWindow.value == 'Off':
                try:
                    if not self.windowGeometry:
                        h = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
                        self.windowGeometry = (h-375)
                    if self.positionWindow.value == 'Justify Left':
                        options.append( "-Xgeometry=300x300+400+%d" % self.windowGeometry )
                    else:
                        options.append( "-Xgeometry=300x300-400+%d" % self.windowGeometry )
                except:
                    self.log.exception('Error calculating window placement')
                
            options.append( "-f" )
            if Platform.isOSX():
                #options.append( "L16-8K-Mono" ) # prevent mac mash converter
                #                                # issues (at least on this G5).

                # 3.2 shipped with OpenAL-based RAT which performs well at 16K
                options.append( "L16-16K-Mono" ) 
            else:
                options.append( "L16-16K-Mono" )
            # Check whether the network location has a "type"
            # attribute Note: this condition is only to maintain
            # compatibility between older venue servers creating
            # network locations without this #attribute and newer
            # services relying on the attribute; it should be removed
            # when the incompatibility is gone
            if self.streamDescription.location.__dict__.has_key("type"):
                if self.streamDescription.location.type == MulticastNetworkLocation.TYPE:
                    options.append( "-t" )
                    options.append( '%d' % (self.streamDescription.location.ttl ) )
            if self.streamDescription.encryptionFlag != 0:
                options.append( "-crypt" )
                options.append( self.streamDescription.encryptionKey )
            options.append( '%s/%d' % (self.streamDescription.location.host,
                                       self.streamDescription.location.port))
            self.log.info("Starting AudioService")
            self.log.info(" executable = %s" % self.executable)

            self.log.info(" options = %s" % options)
            os.chdir(self.thepath)
            self._Start( options )

        except:
            self.log.exception("Exception in AudioService.Start")
            raise Exception("Failed to start service")


    def Stop( self ):
        """Stop the service"""
        self.started = 0
        try:
            self.log.info("Stop service")

            ratKillExe = self.rat_kill
            if os.access(ratKillExe, os.X_OK):
                self.log.info("Executing rat-kill")
                self.processManager.StartProcess(ratKillExe, [])
                time.sleep(0.2)
            else:
                self.log.info("rat-kill not found; rat may not die completely")

            self.processManager.TerminateAllProcesses()

            # Disable firewall
            self.sysConf.AppFirewallConfig(self.executable, 0)
            self.sysConf.AppFirewallConfig(self.rat_media, 0)
            self.sysConf.AppFirewallConfig(self.rat_ui, 0)
            self.sysConf.AppFirewallConfig(self.rat_kill, 0)

        except:
            self.log.exception("Exception in AGService.Stop ")
            raise Exception("AGService.Stop failed : ", str( sys.exc_value ) )

    def Shutdown(self):
        AGService.Shutdown(self)

    def SetStream( self, streamDescription ):
        """
        Configure the Service according to the StreamDescription, and
        stop and start rat
        """

        # Configure the stream
        ret = AGService.ConfigureStream( self, streamDescription )
        if ret and self.started:
            # service is already running with this config; ignore
            return

        # If started, stop
        if self.started:
            self.sysConf.AppFirewallConfig(self.rat_kill, 1)
            self.Stop()

        # If enabled, start
        if self.enabled:
            self.Start()

    def SetIdentity(self, profile):
        """
        Set the identity of the user driving the node
        """
        self.log.info("SetIdentity: %s %s", profile.name, profile.email)
        self.__SetRTPDefaults( profile )
        self.profile = profile

if __name__ == '__main__':

    from AccessGrid.interfaces.AGService_interface import AGService as AGServiceI
    from AccessGrid.AGService import RunService

    # Look for executables in the current directory,
    # since the rat startup script needs to 
    if os.environ.has_key("PATH"):
        os.environ["PATH"] = os.pathsep.join(['.',os.environ["PATH"]])
    else:
        os.environ["PATH"] = '.'

    service = AudioService()
    serviceI = AGServiceI(service)
    RunService(service,serviceI)
