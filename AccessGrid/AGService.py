#-----------------------------------------------------------------------------
# Name:        AGService.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGService.py,v 1.41 2004-10-11 18:19:23 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: AGService.py,v 1.41 2004-10-11 18:19:23 turam Exp $"
__docformat__ = "restructuredtext en"

import os
import sys
from optparse import Option

from AccessGrid import Log

from AccessGrid.Types import *
from AccessGrid.AGParameter import *
from AccessGrid.Platform import IsWindows, IsLinux
from AccessGrid.Toolkit import Service
from AccessGrid.Platform.ProcessManager import ProcessManager
from AccessGrid.Descriptions import StreamDescription
from AccessGrid.Descriptions import CreateResource
from AccessGrid.Descriptions import CreateStreamDescription
from AccessGrid.Descriptions import CreateCapability
from AccessGrid.Descriptions import CreateClientProfile
from AccessGrid.Descriptions import CreateParameter

class AGService:
    """
    AGService : Base class for developing services for the AG
    """
    def __init__( self ):
        if self.__class__ == AGService:
            raise Exception("Can't instantiate abstract class AGService")

        self.resource = AGResource()
        self.executable = None

        self.capabilities = []
        self.started = 1
        self.enabled = 1
        self.configuration = []
        self.streamDescription = StreamDescription()
        self.processManager = ProcessManager()
        
        self.log = Service.instance().GetLog()
        
        self.running = 1


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

        self.processManager.StartProcess( self.executable, options )
        self.started = 1


    def Stop( self ):
        """Stop the service"""
        try:
            self.started = 0
            self.processManager.TerminateAllProcesses()

        except Exception, e:
            self.log.exception("Exception in AGService.Stop")
            raise e

    def ForceStop(self):
        """
        Forcefully stop the service
        """
        if IsWindows():
           # windows : do nothing special to force stop; it's forced anyway
           AGService.Stop(self)
        elif IsLinux():
           # linux : kill vic, instead of terminating
           self.started = 0
           self.processManager.KillAllProcesses()

    def GetCapabilities( self ):
        """Get capabilities"""
        return self.capabilities


    def GetResource( self ):
        """Get resources"""
        return self.resource


    def SetResource( self, resource ):
        """Set the resource used by this service"""
        self.resource = resource


    def SetConfiguration( self, configuration ):
        """Set configuration of service"""
        try:
            for parm in configuration:
                found = 0
                for i in range(len(self.configuration)):
                    if parm.name == self.configuration[i].name:
                       self.configuration[i].SetValue( parm.value )
                       found = 1
                
                if not found:
                    log.info("SetConfiguration: Unrecognized parameter ignored: %s", parm.name)
        except:
            self.log.exception("Exception in AGService.SetConfiguration")
            raise Exception("AGService.SetConfiguration failed : " + str(sys.exc_value) )


    def GetConfiguration( self ):
        """Return configuration of service"""

        return self.configuration


    def ConfigureStream( self, streamDescription ):
        """Configure the Service according to the StreamDescription"""
        try:
            self.log.info("ConfigureStream: %s %s %s" % (streamDescription.capability.type, 
                                       streamDescription.location.host,   
                                       streamDescription.location.port) )

            # Detect trivial re-configuration
            if self.streamDescription.location.host == streamDescription.location.host       \
                and self.streamDescription.location.port == streamDescription.location.port \
                and self.streamDescription.encryptionKey == streamDescription.encryptionKey:
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
       self.running = 0
       
    def IsRunning(self):
        return self.running


    def SetIdentity(self, profile):
        self.profile = profile
        
    def GetName(self):
        className = str(self.__class__).split('.')[-1]
        return className


from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper

class AGServiceI(SOAPInterface):
    """
    Interface Class for AGService
    """
    
    def __init__(self,impl):
        SOAPInterface.__init__(self,impl)
    
    def _authorize(self, *args, **kw):
        # Authorize everybody.
        return 1

    def Start(self):
        self.impl.Start()

    def Stop(self):
        self.impl.Stop()
        
    def GetCapabilities( self ):
        return self.impl.GetCapabilities()

    def GetResource( self ):
        return self.impl.GetResource()

    def SetResource( self, resourceStruct ):
        resource = CreateResource(resourceStruct)
        self.impl.SetResource(resource )

    def SetConfiguration(self,serviceConfig ):
        self.impl.SetConfiguration(serviceConfig )

    def GetConfiguration( self ):
        return self.impl.GetConfiguration()

    def ConfigureStream( self, streamDescStruct ):
        streamDesc = CreateStreamDescription(streamDescStruct)
        self.impl.ConfigureStream(streamDesc )

    def IsStarted( self ):
        return self.impl.IsStarted()

    def SetEnabled(self, enabled):
        self.impl.SetEnabled(enabled)

    def GetEnabled(self):
        return self.impl.GetEnabled()

    def Shutdown(self):
        self.impl.Shutdown()

    def SetIdentity(self, profileStruct):
        profile = CreateClientProfile(profileStruct)
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
    
        capStructList = self.proxy.GetCapabilities()
        
        capList = map( lambda capStruct:
                       CreateCapability(capStruct),
                       capStructList)
        return capList


    def GetResource( self ):
        resourceStruct = self.proxy.GetResource()
        
        resource = CreateResource(resourceStruct)
        return resource

    def SetResource( self, resource ):
        self.proxy.SetResource(resource )

    def SetConfiguration(self,configuration ):
        self.proxy.SetConfiguration(configuration )

    def GetConfiguration( self ):
        config = []
        configStruct = self.proxy.GetConfiguration()
        for parmStruct in configStruct:
            config.append(CreateParameter(parmStruct))
        return config

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

    

#
# Utility routines to simplify service startup
# (these are full-service convenience routines that
# guarantee required behavior (signal handling, 
# service path); services that want to do something
# different need not use them)
#


# Signal handler to shut down cleanly
def SignalHandler(signum, frame, service):
    """
    SignalHandler catches signals and shuts down the service.
    Then it stops the hostingEnvironment.
    """
    service.Shutdown()

def RunService(service,serviceInterface):
    import signal, time
    from AccessGrid.hosting import SecureServer, InsecureServer
    from AccessGrid.AGServiceManager import AGServiceManagerIW
    
    serviceName = service.GetName()
    
    # Initialize the service
    svc = Service.instance()
    svc.AddCmdLineOption(Option("-p", "--port", type="int", dest="port",
                        default=9999, metavar="PORT",
                        help="Set the port the service should run on."))
    svc.AddCmdLineOption(Option("-s", "--serviceManagerUrl", type="string", dest="serviceManagerUrl",
                        default=None, metavar="SERVICE_MANAGER_URL",
                        help="URL of ServiceManager which started this service"))
    svc.AddCmdLineOption(Option("-t", "--token", type="string", dest="token",
                        default=None, metavar="TOKEN",
                        help="Token to pass to service manager when registering"))

    svc.Initialize(serviceName)
    log = svc.GetLog()
    Log.SetDefaultLevel(serviceName, Log.DEBUG)   
    
    port = svc.GetOption("port")
     
    # Create the server
    hostname = Service.instance().GetHostname()
    server = None
    if svc.GetOption('insecure'):
        server = InsecureServer( (hostname, port) )
    else:
        server = SecureServer( (hostname, port) )
    
    # Register the service interface with the server
    server.RegisterObject(serviceInterface, path = "/Service")
    
    # Start the server
    server.RunInThread()
    
    url = server.FindURLForObject(service)
    log.info("Starting Service URI: %s", url)
    print "Starting Service URI: %s" % url
    
    # Register with the calling service manager
    token = svc.GetOption('token')
    AGServiceManagerIW(svc.GetOption('serviceManagerUrl')).RegisterService(token,url)
    
    # Register the signal handler so we can shut down cleanly
    # lambda is used to pass the service instance to the 
    # signal handler
    signal.signal(signal.SIGINT, 
                  lambda signum,frame,service=service:
                  SignalHandler(signum,frame,service))
   
    # Loop main thread to catch signals
    while service.IsRunning():
       time.sleep(1)
       
    # Shutdown the server
    server.Stop()



    
