#-----------------------------------------------------------------------------
# Name:        AGService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGService.py,v 1.22 2003-08-20 19:27:02 eolson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import os
import sys
import logging
import logging.handlers
import Platform

try:     import win32process
except:  pass

from AccessGrid.hosting.pyGlobus.ServiceBase import ServiceBase

from AccessGrid.Types import *
from AccessGrid.AGParameter import *
from AccessGrid.Descriptions import StreamDescription
from AccessGrid.AuthorizationManager import AuthorizationManager
from AccessGrid.Platform import GetUserConfigDir

if sys.platform == 'win32':
    from AccessGrid.ProcessManagerWin32 import ProcessManagerWin32 as ProcessManager
else:
    from AccessGrid.ProcessManagerUnix import ProcessManagerUnix as ProcessManager

def GetLog():
    """
    Create a log with our standard format and return it
    """
    log = logging.getLogger("AG.AGService")
    log.setLevel(logging.DEBUG)
    logFile = os.path.join(GetUserConfigDir(), "AGService.log")
    hdlr = logging.handlers.RotatingFileHandler(logFile, "a", 10000000, 0)
    logFormat = "%(asctime)s %(levelname)-5s %(message)s (%(filename)s)"
    hdlr.setFormatter(logging.Formatter(logFormat))
    log.addHandler(hdlr)

    return log


class AGService( ServiceBase ):
    """
    AGService : Base class for developing services for the AG
    """
    def __init__( self, server ):
        if self.__class__ == AGService:
            raise Exception("Can't instantiate abstract class AGService")

        self.server = server
        
        self.resource = AGResource()
        self.executable = None

        self.capabilities = []
        self.authManager = AuthorizationManager()
        self.started = 1
        self.enabled = 1
        self.configuration = []
        self.streamDescription = StreamDescription()
        self.processManager = ProcessManager()

        self.log = GetLog()


    def Start( self ):
        """Start the service"""
        raise Exception("AGService.Start is abstract!")
    Start.soap_export_as = "Start"


    def _Start( self, options ):
        """
        Internal : Start the service; encapsulates Start functionality for subclasses
        """

        # if started, stop
        if self.started == 1:
           self.Stop()

        self.processManager.start_process( self.executable, options )
        self.started = 1


    def Stop( self ):
        """Stop the service"""
        try:
            self.started = 0
            self.processManager.terminate_all_processes()

        except Exception, e:
            self.log.exception("Exception in AGService.Stop")
            raise e
    Stop.soap_export_as = "Stop"

    def ForceStop(self):
        """
        Forcefully stop the service
        """
        if sys.platform == Platform.WIN:
           # windows : do nothing special to force stop; it's forced anyway
           AGService.Stop(self)
        elif sys.platform == Platform.LINUX:
           # linux : kill vic, instead of terminating
           self.started = 0
           self.processManager.kill_all_processes()

    def SetAuthorizedUsers( self, authorizedUsers ):
        """
        Set the authorizedUsers list; this is usually pushed from a ServiceManager,
        thus this wholesale Set of the authorized user list
        """

        try:
           self.authManager.SetAuthorizedUsers( authorizedUsers )
        except:
           self.log.exception("Exception in AGService.SetAuthorizedUsers")
           raise Exception("AGService.SetAuthorizedUsers failed : " + str(sys.exc_value) )
    SetAuthorizedUsers.soap_export_as = "SetAuthorizedUsers"


    def GetCapabilities( self ):
        """Get capabilities"""
        return self.capabilities
    GetCapabilities.soap_export_as = "GetCapabilities"


    def GetResource( self ):
        """Get resources"""
        return self.resource
    GetResource.soap_export_as = "GetResource"


    def SetResource( self, resource ):
        """Set the resource used by this service"""
        self.resource = resource
    SetResource.soap_export_as = "SetResource"


    def GetExecutable( self ):
        """Get resources"""
        return self.executable
    GetExecutable.soap_export_as = "GetExecutable"


    def SetExecutable( self, executable ):
        """Set the resource used by this service"""
        self.executable = executable
    SetExecutable.soap_export_as = "SetExecutable"


    def SetConfiguration( self, configuration ):
        """Set configuration of service"""
        try:
            self.resource = configuration.resource
            self.executable = configuration.executable

            for parm in configuration.parameters:
                for i in range(len(self.configuration)):
                    if parm.name == self.configuration[i].name:
                       self.configuration[i].SetValue( parm.value )
        except:
            self.log.exception("Exception in AGService.SetConfiguration")
            raise Exception("AGService.SetConfiguration failed : " + str(sys.exc_value) )
    SetConfiguration.soap_export_as = "SetConfiguration"


    def GetConfiguration( self ):
        """Return configuration of service"""
        try:
            serviceConfig = ServiceConfiguration( self.resource, self.executable, self.configuration )

        except:
            self.log.exception("Exception in GetConfiguration ")
            raise Exception("AGService.GetConfiguration failed : " + str(sys.exc_value) )

        return serviceConfig
    GetConfiguration.soap_export_as = "GetConfiguration"


    def ConfigureStream( self, streamDescription ):
        """Configure the Service according to the StreamDescription"""
        try:
            self.log.info("ConfigureStream: %s %s %s" % (streamDescription.capability.type, 
                                       streamDescription.location.host,   
                                       streamDescription.location.port) )

            # Detect trivial re-configuration
            if self.streamDescription.location.host == streamDescription.location.host       \
                and self.streamDescription.location.port == streamDescription.location.port:
                # configuration with identical stream description;
                # bail out
                self.log.info("ConfigureStream: ignoring trivial re-configuration")
                return 1


            m = map( lambda cap:cap.type, self.capabilities )
            if streamDescription.capability.type in m:
               self.streamDescription = streamDescription
        except:
            self.log.exception("Exception in ConfigureStream ")
            raise Exception("AGService.ConfigureStream failed : " + str(sys.exc_value) )

        return 0
    ConfigureStream.soap_export_as = "ConfigureStream"


    def IsStarted( self ):
        """Return the state of Service"""
        return self.started
    IsStarted.soap_export_as = "IsStarted"

    def SetEnabled(self, enabled):
        """
        Enable/disable the service
        """
        
        self.log.info("AGService.SetEnabled : enabled = " + str(enabled) )

        self.enabled = enabled

        # If it is being disabled, stop it
        if enabled == 0 and self.started:
            self.log.info("Stopping service")
            self.Stop()

    SetEnabled.soap_export_as = "SetEnabled"

    def GetEnabled(self):
        """
        Get the enabled state
        """
        return self.enabled
    GetEnabled.soap_export_as = "GetEnabled"


    def Shutdown(self):
       """
       Shut down the service
       """
       self.log.info("Shut service down")
       self.Stop()
       self.server.stop()
    Shutdown.soap_export_as = "Shutdown"


    def SetIdentity(self, profile):
        self.profile = profile
    SetIdentity.soap_export_as = "SetIdentity"
