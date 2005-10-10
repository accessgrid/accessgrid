#-----------------------------------------------------------------------------
# Name:        AGService.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGService.py,v 1.48 2005-10-10 17:26:01 lefvert Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: AGService.py,v 1.48 2005-10-10 17:26:01 lefvert Exp $"
__docformat__ = "restructuredtext en"

import os
import sys
from optparse import Option

from AccessGrid import Log

from AccessGrid.GUID import GUID
from AccessGrid.AGParameter import *
from AccessGrid.Platform import IsWindows, IsLinux, IsOSX
from AccessGrid.Toolkit import Service
from AccessGrid.Platform.ProcessManager import ProcessManager
from AccessGrid.Descriptions import StreamDescription
from AccessGrid.Descriptions import CreateResourceDescription
from AccessGrid.Descriptions import CreateStreamDescription
from AccessGrid.Descriptions import CreateCapability
from AccessGrid.Descriptions import CreateClientProfile
from AccessGrid.Descriptions import CreateParameter
from AccessGrid.Descriptions import CreateAGServiceDescription
from AccessGrid.Descriptions import AGServiceDescription

class AGService:
    """
    AGService : Base class for developing services for the AG
    """
    def __init__( self ):
        if self.__class__ == AGService:
            raise Exception("Can't instantiate abstract class AGService")


        self.name = str(self.__class__).split('.')[-1]
        self.uri = 0
        self.serviceManagerUri = ''

        self.resource = 0
        self.executable = 0
        self.streamDescription = 0
        self.capabilities = []
        self.configuration = []
        self.started = 1
        self.enabled = 1
        self.running = 1
        self.packageFile = 0
        
        self.processManager = ProcessManager()
        
        self.log = Service.instance().GetLog()


    def Start( self ):
        """
        Start the service
        """
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
        elif IsLinux() or IsOSX():
           # linux : kill, instead of terminating
           self.started = 0
           self.processManager.KillAllProcesses()

    def GetCapabilities( self ):
        """
        Get capabilities
        """
        return self.capabilities


    def GetResource( self ):
        """
        Get resources
        """
        return self.resource


    def SetResource( self, resource ):
        """
        Set the resource used by this service
        """
        self.resource = resource
        
    def GetResources(self):
        return []

    def SetConfiguration( self, configuration ):
        """
        Set configuration of service
        """
        try:
            for parm in configuration:
                found = 0
                for i in range(len(self.configuration)):
                    if parm.name == self.configuration[i].name:
                       self.configuration[i].SetValue( parm.value )
                       found = 1
                
                if not found:
                    self.log.info("SetConfiguration: Unrecognized parameter ignored: %s", parm.name)
        except:
            self.log.exception("Exception in AGService.SetConfiguration")
            raise Exception("AGService.SetConfiguration failed : " + str(sys.exc_value) )


    def GetConfiguration( self ):
        """
        Return configuration of service
        """
        return self.configuration


    def SetStream( self, streamDescription ):
        """
        Set the StreamDescription
        """
        try:
            self.log.info("SetStream: %s %s %s" % (streamDescription.capability.type, 
                                       streamDescription.location.host,   
                                       streamDescription.location.port) )

            # Detect trivial re-configuration
            if self.streamDescription and \
                self.streamDescription.location.host == streamDescription.location.host       \
                and self.streamDescription.location.port == streamDescription.location.port \
                and self.streamDescription.encryptionKey == streamDescription.encryptionKey:
                # configuration with identical stream description;
                # bail out
                self.log.info("SetStream: ignoring trivial re-configuration")
                return 1


            m = map( lambda cap:cap.type, self.capabilities )
            if streamDescription.capability.type in m:
               self.streamDescription = streamDescription
        except:
            self.log.exception("Exception in SetStream ")
            raise Exception("AGService.SetStream failed : " + str(sys.exc_value) )

        return 0
    ConfigureStream = SetStream

    def IsStarted( self ):
        """
        Return the state of Service
        """
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
        return self.name
        
    def SetServiceManagerUrl(self,serviceManagerUri):
        self.serviceManagerUri = serviceManagerUri
        
    def GetServiceManagerUrl(self):
        return self.serviceManagerUri
        
    def GetDescription(self):
        return AGServiceDescription(self.name,
                                    self.uri,
                                    self.capabilities,
                                    self.resource,
                                    self.packageFile)

    def SetUri(self,uri):
        self.uri = uri
        
    def GetUri(self):
        return self.uri

    def SetPackageFile(self,packageFile, resource = None, config = None, identity = None):
        self.packageFile = packageFile
        self.SetResource(resource)
        self.SetConfiguration(config)
        self.SetIdentity(identity)
        
    def GetPackageFile(self):
        return self.packageFile

    def IsValid(self):
        return 1


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
    from AccessGrid.interfaces.AGServiceManager_client import AGServiceManagerIW
    
    serviceName = service.GetName()

    # Initialize the service
    svc = Service.instance()
    svc.AddCmdLineOption(Option("-p", "--port", type="int", dest="port",
                        default=9999, metavar="PORT",
                        help="Set the port the service should run on."))
    svc.AddCmdLineOption(Option("-s", "--serviceManagerUri", type="string", dest="serviceManagerUri",
                        default=None, metavar="SERVICE_MANAGER_URL",
                        help="URL of ServiceManager to register with"))
    svc.AddCmdLineOption(Option("-t", "--token", type="string", dest="token",
                        default=None, metavar="TOKEN",
                        help="Token to pass to service manager when registering"))


    svc.Initialize(serviceName)
    log = svc.GetLog()
    Log.SetDefaultLevel(serviceName, Log.DEBUG)   
    
    # Get options
    port = svc.GetOption("port")
    serviceManagerUri = svc.GetOption('serviceManagerUri')
    
    # Create the server
    hostname = Service.instance().GetHostname()
    server = None
    if svc.GetOption("secure"):
        server = SecureServer( (hostname, port) )
    else:
        server = InsecureServer( (hostname, port) )
    
    serviceInterface.impl = service
    serviceInterface.auth_method_name = None    


    # Register the service interface with the server
    servicePath = '/Services/%s.%s' % (serviceName, str(GUID()))
    server.RegisterObject(serviceInterface, path = servicePath)
    
    # Start the server
    server.RunInThread()
    url = server.FindURLForObject(service)
    log.info("Starting Service URI: %s", url)
    print "Starting Service URI: %s" % url
    
    # Set service data
    service.SetServiceManagerUrl(serviceManagerUri)
    service.SetUri(url)
    
    # Register with the calling service manager
    log.debug("Registering with service manager; url=%s", serviceManagerUri)
    token = svc.GetOption('token')
    AGServiceManagerIW(serviceManagerUri).RegisterService(token,url)
    
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



    
