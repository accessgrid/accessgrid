#-----------------------------------------------------------------------------
# Name:        VideoProducerService.py
# Purpose:
# Created:     2003/06/02
# RCS-ID:      $Id: VideoProducerService.py,v 1.39 2004-10-11 18:37:57 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import re
import sys, os
try:    import _winreg
except: pass

from AccessGrid import Toolkit

from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter, TextParameter
from AccessGrid.Platform import IsWindows, IsLinux
from AccessGrid.Platform.Config import AGTkConfig, UserConfig, SystemConfig
from AccessGrid.NetworkLocation import MulticastNetworkLocation

vicstartup="""option add Vic.disable_autoplace true startupFile
option add Vic.muteNewSources true startupFile
option add Vic.maxbw 6000 startupFile
option add Vic.bandwidth %d startupFile
option add Vic.framerate %d startupFile
option add Vic.quality %d startupFile
option add Vic.defaultFormat %s startupFile
option add Vic.inputType %s startupFile
option add Vic.device \"%s\" startupFile
option add Vic.defaultTTL 127 startupFile
option add Vic.rtpName \"%s\" startupFile
option add Vic.rtpEmail \"%s\" startupFile
proc user_hook {} {
    global videoDevice inputPort transmitButton transmitButtonState

    update_note 0 \"%s\"

    after 200 {
        if { ![winfo exists .menu] } {
            build.menu
        }
 
        if { ![info exists env(VIC_DEVICE)] } {
            set deviceName \"%s\"

            foreach v $inputDeviceList {
                if { [string last $deviceName [$v nickname]] != -1 } {
                    set videoDevice $v
                    select_device $v
                    break
                }
            }
        }
        set inputPort %s
        grabber port %s

        if { [$transmitButton cget -state] != \"disabled\" } {
            set transmitButtonState 1
            transmit
        }
    }
}
"""

class VideoProducerService( AGService ):

    encodings = [ "h261" ]
    standards = [ "NTSC", "PAL" ]

    def __init__( self ):
        AGService.__init__( self )

        self.capabilities = [ Capability( Capability.PRODUCER,
                                          Capability.VIDEO ) ]
        if IsWindows():
            vic = "vic.exe"
        else:
            vic = "vic"

        self.executable = os.path.join(os.getcwd(),vic)

        self.sysConf = SystemConfig.instance()

        # Set configuration parameters

        # note: the datatype of the port parameter changes when a resource is set!
        self.streamname = TextParameter( "streamname", "Video" )
        self.port = TextParameter( "port", "" )
        self.encoding = OptionSetParameter( "encoding", "h261", VideoProducerService.encodings )
        self.standard = OptionSetParameter( "standard", "NTSC", VideoProducerService.standards )
        self.bandwidth = RangeParameter( "bandwidth", 800, 0, 3072 )
        self.framerate = RangeParameter( "framerate", 24, 1, 30 )
        self.quality = RangeParameter( "quality", 75, 1, 100 )
        self.configuration.append( self.streamname )
        self.configuration.append( self.port )
        self.configuration.append( self.encoding )
        self.configuration.append( self.standard )
        self.configuration.append( self.bandwidth )
        self.configuration.append( self.framerate )
        self.configuration.append (self.quality )
        
        self.profile = None


    def __SetRTPDefaults(self, profile):
        """
        Set values used by rat for identification
        """
        if profile == None:
            self.log.exception("Invalid profile (None)")
            raise Exception, "Can't set RTP Defaults without a valid profile."

        if IsLinux():
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

        elif IsWindows():
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
        else:
            self.log.error("No support for platform: %s", sys.platform)
        
    def MapWinDevice(self,deviceStr):
        """
        Abuse registry to get correct mapping from vfw names
        to video sources
        """
        h261width = 352
        h261height = 288
        
        self.log.info("Mapping windows device: %s", deviceStr)
        if deviceStr.find('Videum') >= 0:
            self.log.info("- videum")
            devnum = -1
            videum_re = re.compile(".*(\d)_Videum.*")
            m = videum_re.search(deviceStr)
            if m:
                self.log.info("Found match : %d", int(m.group(1)))
                devnum = int(m.group(1))
            else:
                self.log.info("No match")
                if deviceStr.startswith('Videum Video Capture'):
                    self.log.info("is videum video capture")
                    devnum = 0
                else:
                    self.log.info("is not videum video capture")

            self.log.info("Videum device: %d", devnum)
            if devnum >= 0:
                # Set the registry
                keyStr = r"Software\Winnov\Videum\vic.exe%d" % (devnum,)
                key = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER,
                                        keyStr)
                _winreg.SetValueEx(key,'Source',0,_winreg.REG_DWORD,int(devnum))
                _winreg.SetValueEx(key,'Height',0,_winreg.REG_DWORD,int(h261height))
                _winreg.SetValueEx(key,'Width',0,_winreg.REG_DWORD,int(h261width))
                _winreg.CloseKey(key)
                

    def Start( self ):
        """Start service"""
        try:
            # Enable firewall
            self.sysConf.AppFirewallConfig(self.executable, 1)

            # Resolve assigned resource to a device understood by vic
            print "self.resource = ", type(self.resource), self.resource
            print "res = ", self.resource.resource
            if self.resource == "None":
                vicDevice = "None"
            else:
                vicDevice = self.resource.resource
                vicDevice = vicDevice.replace("[","\[")
                vicDevice = vicDevice.replace("]","\]")

            if IsWindows():
                try:
                    self.MapWinDevice(self.resource.resource)
                except:
                    self.log.exception("Exception mapping device")


            #
            # Write vic startup file
            #
            startupfile = os.path.join(UserConfig.instance().GetTempDir(),
               'VideoProducerService_%d.vic' % ( os.getpid() ) )

            f = open(startupfile,"w")
            if self.port.value == '':
                portstr = "None"
            else:
                portstr = self.port.value
            
            name=email="Participant"
            if self.profile:
                name = self.profile.name
                email = self.profile.email
            else:
                # Error case
                name = email = Toolkit.GetDefaultSubject().GetCN()
                self.log.error("Starting service without profile set")
                
            f.write( vicstartup % (self.bandwidth.value,
                                    self.framerate.value,
                                    self.quality.value,
                                    self.encoding.value,
                                    self.standard.value,
                                    vicDevice,
                                    "%s(%s)" % (name,self.streamname.value),
                                    email,
                                    email,
                                    vicDevice,
                                    portstr,
                                    portstr ) )
            f.close()

            # Replace double backslashes in the startupfile name with single
            #  forward slashes (vic will crash otherwise)
            if IsWindows():
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
                                           
            # Set the device for vic to use
            os.environ["VIC_DEVICE"] = vicDevice
                                           
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

        # Disable firewall
        self.sysConf.AppFirewallConfig(self.executable, 0)

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
        if "portTypes" in self.resource.__dict__.keys():

            # Find the config element that refers to "port"
            try:
                index = self.configuration.index(self.port)
                found = 1
            except ValueError:
                found = 0

            # Create the port parameter as an option set parameter, now
            # that we have multiple possible values for "port"
            if ( isinstance(self.port, TextParameter) or isinstance(self.port, ValueParameter) ) and self.port.value != "" and self.port.value in self.resource.portTypes:
                self.port = OptionSetParameter( "port", self.port.value,
                                                             self.resource.portTypes )
            else:
                self.port = OptionSetParameter( "port", self.resource.portTypes[0],
                                                             self.resource.portTypes )

            # Replace or append the "port" element
            if found:
                self.configuration[index] = self.port
            else:
                self.configuration.append(self.port)

    def SetIdentity(self, profile):
        """
        Set the identity of the user driving the node
        """
        self.log.info("SetIdentity: %s %s", profile.name, profile.email)
        self.profile = profile
        self.__SetRTPDefaults(profile)

if __name__ == '__main__':

    from AccessGrid.AGService import AGServiceI, RunService

    service = VideoProducerService()
    serviceI = AGServiceI(service)
    RunService(service,serviceI)
