#-----------------------------------------------------------------------------
# Name:        AGService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGService.py,v 1.27 2004-03-12 00:31:20 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: AGService.py,v 1.27 2004-03-12 00:31:20 turam Exp $"
__docformat__ = "restructuredtext en"

import os
import sys
import Platform

from AccessGrid import Log
from AccessGrid.Log import handlers

from AccessGrid.Types import *
from AccessGrid.AGParameter import *
from AccessGrid.Descriptions import StreamDescription
from AccessGrid.AuthorizationManager import AuthorizationManager
from AccessGrid.Platform import GetUserConfigDir, isWindows, isLinux
from AccessGrid.ProcessManager import ProcessManager

def GetLog():
    """
    Create a log with our standard format and return it
    """
    log = Log.GetLogger(Log.AGService)
    Log.SetDefaultLevel(Log.AGService, Log.DEBUG)
    logFile = os.path.join(GetUserConfigDir(), "AGService.log")
    hdlr = Log.handlers.RotatingFileHandler(logFile, "a", 10000000, 0)
    hdlr.setFormatter(Log.GetFormatter())
    Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())

    return log


class AGService:
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

    def ForceStop(self):
        """
        Forcefully stop the service
        """
        if isWindows():
           # windows : do nothing special to force stop; it's forced anyway
           AGService.Stop(self)
        elif isLinux():
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


    def GetCapabilities( self ):
        """Get capabilities"""
        return self.capabilities


    def GetResource( self ):
        """Get resources"""
        return self.resource


    def SetResource( self, resource ):
        """Set the resource used by this service"""
        self.resource = resource


    def GetExecutable( self ):
        """Get resources"""
        return self.executable


    def SetExecutable( self, executable ):
        """Set the resource used by this service"""
        self.executable = executable


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


    def GetConfiguration( self ):
        """Return configuration of service"""
        try:
            serviceConfig = ServiceConfiguration( self.resource, self.executable, self.configuration )

        except:
            self.log.exception("Exception in GetConfiguration ")
            raise Exception("AGService.GetConfiguration failed : " + str(sys.exc_value) )

        return serviceConfig


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


    def IsStarted( self ):
        """Return the state of Service"""
        return self.started

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


    def GetEnabled(self):
        """
        Get the enabled state
        """
        return self.enabled


    def Shutdown(self):
       """
       Shut down the service
       """
       self.log.info("Shut service down")
       self.Stop()
       self.server.stop()


    def SetIdentity(self, profile):
        self.profile = profile





from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper

class AGServiceI(SOAPInterface):
    """
    Interface Class for AGService
    """
    
    def __init__(self,impl):
        SOAPInterface.__init__(self,impl)
    
    def Start(self):
        self.impl.Start()

    def Stop(self):
        self.impl.Stop()
        
    def SetAuthorizedUsers( self, authorizedUsers ):
        self.impl.SetAuthorizedUsers(authorizedUsers )

    def GetCapabilities( self ):
        return self.impl.GetCapabilities()

    def GetResource( self ):
        return self.impl.GetResource()

    def SetResource( self, resource ):
        self.impl.SetResource(resource )

    def GetExecutable( self ):
        return self.impl.GetExecutable()

    def SetExecutable( self, executable ):
        self.impl.SetExecutable( self, executable )

    def SetConfiguration(configuration ):
        self.impl.SetConfiguration(configuration )

    def GetConfiguration( self ):
        return self.impl.GetConfiguration()

    def ConfigureStream( self, streamDescription ):
        self.impl.ConfigureStream(streamDescription )

    def IsStarted( self ):
        return self.impl.IsStarted()

    def SetEnabled(self, enabled):
        self.impl.SetEnabled(enabled)

    def GetEnabled(self):
        return self.impl.GetEnabled()

    def Shutdown(self):
        self.impl.Shutdown()

    def SetIdentity(self, profile):
        self.impl.SetIdentity(profile)

    
    
    
class AGServiceIW(SOAPIWrapper):
    """
    Interface Wrapper Class for AGService
    """
    
    def __init__(self,url):
        SOAPIWrapper.__init__(self,url)
    
    def Start(self):
        self.proxy.Start()

    def Stop(self):
        self.proxy.Stop()
        
    def GetCapabilities( self ):
        return self.proxy.GetCapabilities()

    def GetResource( self ):
        return self.proxy.GetResource()

    def SetResource( self, resource ):
        self.proxy.SetResource(resource )

    def GetExecutable( self ):
        return self.proxy.GetExecutable()

    def SetExecutable( self, executable ):
        self.proxy.SetExecutable( self, executable )

    def SetConfiguration(configuration ):
        self.proxy.SetConfiguration(configuration )

    def GetConfiguration( self ):
        return self.proxy.GetConfiguration()

    def ConfigureStream( self, streamDescription ):
        self.proxy.ConfigureStream(streamDescription )

    def IsStarted( self ):
        return self.proxy.IsStarted()

    def SetEnabled(self, enabled):
        self.proxy.SetEnabled(enabled)

    def GetEnabled(self):
        return self.proxy.GetEnabled()

    def Shutdown(self):
        self.proxy.Shutdown()

    def SetIdentity(self, profile):
        self.proxy.SetIdentity(profile)

    
    
    
    
