#-----------------------------------------------------------------------------
# Name:        AGService.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGService.py,v 1.68 2007-10-01 21:52:52 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: AGService.py,v 1.68 2007-10-01 21:52:52 turam Exp $"
__docformat__ = "restructuredtext en"

import os
import sys
from optparse import Option

from AccessGrid import Log

from AccessGrid.GUID import GUID
from AccessGrid.AGParameter import *
from AccessGrid.Platform import IsWindows, IsLinux, IsOSX, IsFreeBSD
from AccessGrid.Toolkit import Service,GetDefaultApplication
from AccessGrid.Platform.ProcessManager import ProcessManager
from AccessGrid.Descriptions import StreamDescription
from AccessGrid.Descriptions import AGServiceDescription

from AccessGrid.interfaces.AGService_client import AGServiceIW
from AccessGrid.interfaces.AGService_interface import AGService as AGServiceI

    

class AGService:
    """
    AGService : Base class for developing services for the AG
    @group WebServiceMethods: GetCapabilities,GetConfiguration,GetDescription,GetEnabled,GetPackageFile,GetResource,GetResources,GetServiceManagerUrl,IsStarted,IsValid,SetConfiguration,SetEnabled,SetIdentity,SetPackageFile,SetResource,SetServiceManagerUrl,SetStream,Shutdown,Start,Stop
    """
    START_PRIORITY_MIN = '1'
    START_PRIORITY_MAX = '10'
    START_PRIORITY_OPTIONS = [ '1', '2', '3', '4', '5', '6', '7', '8', '9', '10' ]
    def __init__( self ):
        if self.__class__ == AGService:
            raise Exception("Can't instantiate abstract class AGService")


        self.name = str(self.__class__).split('.')[-1]
        self.uri = 0
        self.serviceManagerUri = ''

        self.resource = None
        self.executable = ""
        self.streamDescription = None
        self.startPriority = "5"
        
        self.capabilities = []
        self.startPriorityOption = OptionSetParameter("Start Priority", self.startPriority, 
        						self.START_PRIORITY_OPTIONS)
        self.configuration = [ self.startPriorityOption ]
        self.started = 1
        self.enabled = 1
        self.running = 1
        self.packageFile = ""
        self.id = GUID()
        # Variable used by new service with AG3.1 interface to indicate when the server has first been configured
        # Afterwards relies on streamDescription comparision as with older AG3.0.x services.
        self.isConfigured = False  
        
        self.processManager = ProcessManager()
        
        app = GetDefaultApplication()
        if not app: 
            app = Service.instance()
        self.log = app.GetLog()
        
    def Start( self ):
        """
        Start the service
        """
        raise Exception("AGService.Start is abstract!")


    def _Start( self, options ):
        """
        Internal : Start the service; encapsulates Start functionality for subclasses
        """

        # prevent SOAP socket from being inherited by child processes
        # which we're about to spawn
        try:
            import posix
            import fcntl
            from ZSI.ServiceContainer import GetSOAPContext
            ctx = GetSOAPContext()
            if ctx:
                fd = ctx.connection.fileno()
                old = fcntl.fcntl(fd, fcntl.F_GETFD)
                fcntl.fcntl(fd, fcntl.F_SETFD, old | fcntl.FD_CLOEXEC)
        except (ImportError,KeyError):
            pass

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
        elif IsLinux() or IsOSX() or IsFreeBSD():
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
            self.log.info("SetStream: incoming stream %s %s %s" % (streamDescription.capability, 
                                                   streamDescription.location.host,   
                                                   streamDescription.location.port) )

            if self.streamDescription:
                self.log.info("SetStream: current stream %s %s %s" % (self.streamDescription.capability, 
                                                       self.streamDescription.location.host,   
                                                       self.streamDescription.location.port) )

                # Detect trivial re-configuration
                if self.streamDescription and \
                    self.streamDescription.location.host == streamDescription.location.host       \
                    and self.streamDescription.location.port == streamDescription.location.port \
                    and self.streamDescription.encryptionKey == streamDescription.encryptionKey:
                    # configuration with identical stream description;
                    # bail out
                    self.log.info("SetStream: ignoring trivial re-configuration")
                    return 1

            self.log.info("SetStream: new configuration, set everything new!")
            
            # each service capability has to be present in the stream.
            for cap in self.capabilities:
                match = 0
                for c in streamDescription.capability:
                    if c.matches(cap):
                        match = 1
                if not match:
                    return 0

            if isinstance(streamDescription, StreamDescription):
                self.log.debug("StreamDescription okay, assign it to service!")
                self.streamDescription = streamDescription
            else:
                if streamDescription == None:
                    self.log.debug("StreamDescription invalid  == None!")
                else:
                    self.log.debug("StreamDescription invalid format!")
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
        if not enabled and self.started:
            self.log.info("Stopping service")
            self.Stop()
        elif enabled and not self.started:
            self.log.info('Starting service')
            self.Start()


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
        for cp in self.capabilities:
            self.log.debug("GetDescription:Capability in Service %s", cp)
        r = AGServiceDescription(self.name,
                                 self.uri,
                                 self.capabilities,
                                 self.GetResource(),
                                 self.packageFile)
        r.startPriority = self.startPriority
                
        return r


    def SetUri(self,uri):
        self.uri = uri
        
    def GetUri(self):
        return self.uri

    def SetPackageFile(self,packageFile, resource = None, config = None, identity = None):
        self.packageFile = packageFile
        if resource: self.SetResource(resource)
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

def RunService(service,serviceInterface,unusedCompatabilityArg=None,app=None):
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
    svc.AddCmdLineOption(Option("--test", action='store_true', dest="test",
                        default=None, metavar="TEST",
                        help="Test service and then exit"))


    svc.Initialize(serviceName)
    log = svc.GetLog()
    Log.SetDefaultLevel(serviceName, Log.DEBUG)   

    # Get options
    port = svc.GetOption("port")
    serviceManagerUri = svc.GetOption('serviceManagerUri')
    test = svc.GetOption('test')
    if test:
        from AccessGrid.NetworkLocation import MulticastNetworkLocation
        stream = StreamDescription('test stream',
                                   MulticastNetworkLocation('224.2.2.2',20000,1))
        stream.capability = service.capabilities
        resources = service.GetResources()
        if len(resources) > 0:
            service.SetResource(resources[0])
        service.SetStream(stream)
        return
    
    # Create the server
    
    if not app:
        app = GetDefaultApplication()
    hostname = app.GetHostname()
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
    if serviceManagerUri:
        log.debug("Registering with service manager; url=%s", serviceManagerUri)
        token = svc.GetOption('token')
        AGServiceManagerIW(serviceManagerUri).RegisterService(token,url)
    else:
        log.info("Service Manager does not exist for service %s"%(url))

    

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



    
