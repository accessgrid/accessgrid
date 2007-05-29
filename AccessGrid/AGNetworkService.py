from AccessGrid.Descriptions import AGNetworkServiceDescription
from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.NetworkAddressAllocator import NetworkAddressAllocator
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.hosting import SecureServer, InsecureServer
from AccessGrid.Descriptions import Capability

from AccessGrid.interfaces.Venue_client import VenueIW
from AccessGrid.interfaces.VenueServer_client import VenueServerIW
from AccessGrid.interfaces.AGNetworkService_client import AGNetworkServiceIW
from AccessGrid.interfaces.AGNetworkService_interface import AGNetworkService as AGNetworkServiceI
from AccessGrid.GUID import GUID

from optparse import Option
import signal
import time

class AGNetworkService:
    '''
    Class to use when creating a network service.
    '''
    def __init__(self, name, description, version, mimeType, extension):
        '''
        Initiate the class.

        ** Arguments **

        * name * name of the service.
        * description * description of the service.
        * version * service version.
        '''
        self.name = name
        self.description = description
        self.version = version
        self.mimeType = mimeType
        self.extension = extension
        self.visible = 1
        self.id = GUID()
                
        # Defined in Start.
        self.venueProxies = {}
        self.url = None 
        self.log = None 
        self.app = None

        # Standard AG initialization for console apps.
        self.app = CmdlineApplication.instance()
        self.app.AddCmdLineOption(Option("-v", "--venueUrl",
                                         dest="venueUrl",
                                         help="Register with venue located at this url."))
        
        self.app.AddCmdLineOption(Option("-s", "--venueServerUrl",
                                         dest="venueServerUrl",
                                         help="Register with all venues at server located at this url."))
                                         
        self.capabilities = []

    def Start(self, service, soapI = None):
        '''
        Performs necessary AG initialization operations for authorization,
        logging, command line options, and so forth.  Starts a SOAP service
        and registers a signal handler to make it possible to stop the
        service from the command line.
        '''
        # Create the service interface.
        if not soapI:
            soapInterface = AGNetworkServiceI(service)
        else:
            soapInterface = soapI
                
        self.app.Initialize(self.name)
        self.log = self.app.GetLog()
                
        # Register signal handling for clean shutdown of service.
        signal.signal(signal.SIGINT, self.StopSignalLoop)
        signal.signal(signal.SIGTERM, self.StopSignalLoop)

        soapInterface.impl = service
        soapInterface.auth_method_name = None    
                
        # Start soap service.
        port = NetworkAddressAllocator().AllocatePort()
        self.server = InsecureServer((self.app.GetHostname(), port))
        self.url = self.server.RegisterObject(soapInterface, path='/AGNetworkService')
            
        # Start the execution
        self.server.RunInThread()
        
        self.log.debug("AGNetworkService.Start: Starting network service name: %s, description: %s, version: %s, url %s" %(self.name, self.description, self.version, self.url))

        # Register with venue/venueServer if urls are specified on the command line.
        # Otherwise, register manually. Later, read urls from config file.
        if self.app.options.venueUrl:
            self.RegisterWithVenues([self.app.options.venueUrl])
            
        if self.app.options.venueServerUrl:
            self.RegisterWithVenueServer(self.app.options.venueServerUrl)
                
    def Stop(self):
        '''
        Disconnects from venue and shuts down the SOAP server.
        '''
        if len(self.venueProxies) > 0:
            nsd = self.CreateDescription()
            for url in self.venueProxies.keys():
                try:
                    self.venueProxies[url].UnRegisterNetworkService(nsd)
                except:
                    self.log.exception("AGNetworkService.Stop: UnregisterNetworkService with venue %s failed for %s"
                                       %(url, nsd.name))

        # Stop soap service.
        try:
            self.flag = 0
            self.server.Stop()
        except:
            self.log.exception("AGNetworkService.Stop: Stop soap server failed")
                        
    def StartSignalLoop(self):
        '''
        Start loop that can get interrupted from signals and
        shut down service properly.
        '''

        self.flag = 1
        while self.flag:
            try:
                time.sleep(0.5)
            except:
                self.flag = 0
                self.log.debug("AGNetworkService.StartSignalLoop: Signal loop interrupted, exiting.")

    def StopSignalLoop(self, signum, frame):
        '''
        Signal callback that shuts down the service cleanly. 
        '''
        self.flag = 0
        self.Stop()
                
    def RegisterWithVenues(self, urls):
        '''
        Registers this network service with venues contained in the urls list.
        If no url list is specified, use venue url command line option.

        ** Arguments **

        * urls * list of venue urls. 
        '''
        if type(urls) != list:
            raise Exception, 'AGNetworkService.RegisterWithVenues: urls argument has to be a list of venue urls.'
        
        # Create a NetworkServiceDescription and register with the venue. 
        for url in urls:
            self.venueProxies[url] = VenueIW(url)
            nsd = self.CreateDescription()

            try:
                self.venueProxies[url].RegisterNetworkService(nsd)
                self.log.debug("AGNetworkService.Register: Register with venue %s" %(url))
            except:
                self.log.exception("AGNetworkService.Register: RegisterNetworkService with venue %s failed for %s"%(url, nsd))
    

    def RegisterWithVenueServer(self, url):
        '''
        Registers this network service with all venues on server located at url.
        If no url is specified, use venue url command line option.
        '''
        venueServer = VenueServerIW(url)
        
        # Get all venues from the server
        try:
            venues  = venueServer.GetVenues()
            urls = map(lambda x: x.uri, venues)
            self.RegisterWithVenues(urls)

        except:
            self.log.exception('AGNetworkService.RegisterWithVenueServer: Failed to register venues.')
                
    def UnRegisterFromVenues(self, urls):
        '''
        Disconnects from all venues contained in the urls list.
        '''
        
        # Create a NetworkServiceDescription and register with the venue. 
        for url in urls:
            nsd = AGNetworkServiceDescription(self.name, self.description, self.url,
                                              self.capabilities, self.version)
            try:
                if self.venueProxies.has_key(url):
                    self.venueProxies[url].UnRegisterNetworkService(nsd)
                    del self.venueProxies[url]
                    self.log.debug("AGNetworkService.UnRegister: UnRegister from venue %s" %(url))
                else:
                    self.log.debug("AGNetworkService.UnRegister: Can not unregister from venue %s, it is not listed."%(url))
            except:
                self.log.exception("AGNetworkService.UnRegister: UnRegisterNetworkService failed in venue %s for %s"%(self.url, nsd.ToString()))

    def UnRegisterFromVenueServer(self, url):
        '''
        Disconnects from all venues on server located at url.
        '''
        venueServer = VenueServerIW(url)
        
        # Get all venues from the server
        try:
            venues  = venueServer.GetVenues()
            urls = map(lambda x: x.uri, venues)
            self.UnRegisterFromVenues(urls)

        except:
            self.log.exception('AGNetworkService.UnRegisterFromVenueServer: Failed to unregister venues.')


    def CreateDescription(self):
        nsd = AGNetworkServiceDescription(self.name, self.description, self.url, self.capabilities,
                                          self.version)
        nsd.id = str(GUID())
        return nsd


        
if __name__ == "__main__":
    # Test for AGNetworkService and venue soap interface.

    # Before running test; start a venue server on your local host.
    
    class FakeService(AGNetworkService):
        def __init__(self, name):
            AGNetworkService.__init__(self, name, 'Convert from 16kHz to 8kHz', '1.0')
            # Create in and out capabilities.
            self.capabilities = [Capability3( Capability3.CONSUMER,
                                               Capability3.VIDEO,
                                               "JPEG",
                                               90000, self.id),
                                 Capability3( Capability3.PRODUCER,
                                             Capability3.VIDEO,
                                             "JPEG",
                                             90000, self.id)]

            # Start the service.
            self.Start(self)

        def StopTransform(self, streamList):
            """
            Method for legacy support for AG 3.0.2. clients
            """
            return []

        def StopTransform3(self, streamList):
            
            return []
               
        def Transform(self, streamList):
            """
            Method for legacy support for AG 3.0.2. clients
            """
            return []

        def Transform3(self, streamList):
            return []


    # Create the network service.
    service = FakeService('FakeService')

    # Test venue soap interface.
    vProxy = VenueIW('https://localhost:8000/Venues/default')
    nsd = AGNetworkServiceDescription(service.name, service.description, service.url,
                                              service.capabilities, service.version)
            
    vProxy.RegisterNetworkService(nsd)
    services = vProxy.GetNetworkServices()
    if services[0].url != nsd.url:
        raise Exception, 'venue.RegisterNetworkService failed'

    vProxy.UnRegisterNetworkService(nsd)
    services = vProxy.GetNetworkServices()
    if len(services) != 0:
        raise Exception, 'venue.UnRegisterNetworkService failed'
    
    # Test network service interface.
    service.RegisterWithVenueServer('https://localhost:8000/VenueServer')
    service.UnRegisterFromVenueServer('https://localhost:8000/VenueServer')
    service.RegisterWithVenues(['https://localhost/Venues/default'])
              
    # Test network service soap interface.
    nsProxy = AGNetworkServiceIW(service.url)

    result = nsProxy.Transform3([])
    if not result == []:
        raise Exception, 'Transform failed'
    
    result = nsProxy.StopTransform3([])
    if not result == []:
        raise Exception, 'Stop transform failed'
    
    service.Stop()
    
    
    

