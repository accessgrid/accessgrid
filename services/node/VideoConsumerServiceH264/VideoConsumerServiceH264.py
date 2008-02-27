#-----------------------------------------------------------------------------
# Name:        VideoConsumerServiceH264.py
# Purpose:
# Created:     2003/06/02
# RCS-ID:      $Id: VideoConsumerServiceH264.py,v 1.17 2007/09/12 07:01:56 douglask Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys, os
try:    import _winreg
except: pass

import agversion
agversion.select(3)
from AccessGrid import Toolkit

from AccessGrid.Descriptions import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter
from AccessGrid.Platform import IsWindows, IsLinux, IsFreeBSD, IsOSX
from AccessGrid.Platform.Config import AGTkConfig, UserConfig, SystemConfig
from AccessGrid.NetworkLocation import MulticastNetworkLocation

class VideoConsumerServiceH264( AGService ):

    tileOptions = [ '1', '2', '3', '4', '5', '6', '7', '8', '9', '10' ]

    def __init__( self ):
        AGService.__init__( self )
        self.capabilities = [ Capability( Capability.CONSUMER,
                                          Capability.VIDEO,
                                          "H261",
                                          90000, self.id) ,
                                Capability( Capability.CONSUMER,
                                          Capability.VIDEO,
                                          "H264",
                                          90000, self.id),
                                Capability( Capability.CONSUMER,
                                          Capability.VIDEO,
                                          "MPEG4",
                                          90000, self.id),
                                Capability( Capability.CONSUMER,
                                          Capability.VIDEO,
                                          "H261AS",
                                          90000, self.id) 
                                          ]

        if IsWindows():
            vic = "vic.exe"
        else:
            vic = "vic"

        self.executable = os.path.join(os.getcwd(),vic)
        if not os.path.isfile(self.executable):
            self.executable = vic

        self.sysConf = SystemConfig.instance()

        self.profile = None

        self.startPriority = '7'
        self.startPriorityOption.value = self.startPriority

        # Set configuration parameters
        self.tiles = OptionSetParameter( "Thumbnail Columns", "2", VideoConsumerServiceH264.tileOptions )
        self.configuration.append( self.tiles )

        if IsWindows():
            try:
                import win32api

                # get number of processors
                systemInfo = win32api.GetSystemInfo()
                numprocs = systemInfo[5]
                self.allProcsMask = 2**numprocs-1

                self.procOptions = ['All']
                for i in range(numprocs):
                    self.procOptions.append(str(i+1))

                self.processorUsage = OptionSetParameter( "Processor usage", self.procOptions[0], self.procOptions )
                self.configuration.append( self.processorUsage )
            except:
                self.log.exception('Error initializing processor usage options')


    def __SetRTPDefaults(self, profile):
        """
        Set values used by rat for identification
        """
        if profile == None:
            self.log.exception("Invalid profile (None)")
            raise Exception, "Can't set RTP Defaults without a valid profile."

        if IsLinux() or IsOSX() or IsFreeBSD():
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
                # Set RTP defaults according to the profile
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
            
        
    def Start( self ):
        """Start service"""
        try:

            # Set processor affinity (windows only)
            if IsWindows():
                try:
                    if self.processorUsage.value == 'All':
                        self.log.info('Setting processor affinity to all processors')
                        SystemConfig.instance().SetProcessorAffinity(self.allProcsMask)
                    else:
                        val = 2**(int(self.processorUsage.value)-1)
                        self.log.info('Ssetting processor affinity : use processor %s', self.processorUsage.value)
                        SystemConfig.instance().SetProcessorAffinity(int(self.processorUsage.value))
                except:
                    self.log.exception("Exception setting processor affinity")

            # Enable firewall
            self.sysConf.AppFirewallConfig(self.executable, 1)

            # Start the service; in this case, store command line args
            # in a list and let the superclass _Start the service
            options = []
            if self.streamDescription.name and \
                   len(self.streamDescription.name.strip()) > 0:
                options.append( "-C" )
                options.append( self.streamDescription.name )
            if self.streamDescription.encryptionFlag != 0:
                options.append( "-K" )
                options.append( self.streamDescription.encryptionKey )
            # Check whether the network location has a "type"
            # attribute Note: this condition is only to maintain
            # compatibility between older venue servers creating
            # network locations without this attribute and newer
            # services relying on the attribute; it should be removed
            # when the incompatibility is gone
            if self.streamDescription.location.__dict__.has_key("type"):
                if self.streamDescription.location.type == MulticastNetworkLocation.TYPE:
                    options.append( "-t" )
                    options.append( '%d' % ( self.streamDescription.location.ttl ) )

            # Set name and email on command line, in case rtp defaults
            # haven't been written (to avoid vic prompting for
            # name/email)
            name=email="Participant"
            if self.profile:
                name = self.profile.name
                email = self.profile.email
            options.append('-XrtpName=%s' % (name,))
            options.append('-XrtpEmail=%s' % (email,))

            # Set some tk resources to customize vic
            # - this is a consumer, so disable device selection in vic
            options.append('-XrecvOnly=1')
            # - set drop time to something reasonable
            options.append('-XsiteDropTime=5')
            # - set vic window geometry
            options.append('-Xgeometry=500x500')
            # - set number of columns of thumbnails to display
            options.append('-Xtile=%s' % self.tiles.value)
                    
            # Add address/port options (these must occur last; don't
            # add options beyond here)
            options.append( '%s/%d' % (self.streamDescription.location.host,
                                       self.streamDescription.location.port))
            self.log.info("Starting VideoConsumerServiceH264")
            self.log.info(" executable = %s" % self.executable)
            self.log.info(" options = %s" % options)
            self._Start( options )
        except:
            self.log.exception("Exception in VideoConsumerServiceH264.Start")
            raise Exception("Failed to start service")

    def Stop( self ):
        """Stop the service"""

        # vic doesn't die easily (on linux at least), so force it to stop
        AGService.ForceStop(self)

        # Disable firewall
        self.sysConf.AppFirewallConfig(self.executable, 0)

    def SetStream( self, streamDescription ):
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

    def SetIdentity(self, profile):
        """
        Set the identity of the user driving the node
        """
        self.log.info("SetIdentity: %s %s", profile.name, profile.email)
        self.profile = profile
        self.__SetRTPDefaults(profile)

if __name__ == '__main__':

    from AccessGrid.interfaces.AGService_interface import AGService as AGServiceI
    from AccessGrid.AGService import RunService

    service = VideoConsumerServiceH264()
    serviceI = AGServiceI(service)
    RunService(service,serviceI)
