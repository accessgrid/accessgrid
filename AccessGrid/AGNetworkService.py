from AccessGrid.ServiceCapability import ServiceCapability
from AccessGrid.Descriptions import AGNetworkServiceDescription
from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.NetworkAddressAllocator import NetworkAddressAllocator
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.hosting import SecureServer
from AccessGrid.Venue import VenueIW
from AccessGrid.AGNetworkServiceIW import AGNetworkServiceIW
from AccessGrid.VenueServer import VenueServerIW
from AccessGrid.Descriptions import CreateStreamDescription

from optparse import Option
import signal
import time

class AGNetworkService:
    '''
    Class to use when creating a network service.
    '''
    def __init__(self, name, description, version):
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
                                         
        self.inCapabilities = []
        self.outCapabilities = []
                    
    def Start(self, service):
        '''
        Performs necessary AG initialization operations for authorization,
        logging, command line options, and so forth.  Starts a SOAP service
        and registers a signal handler to make it possible to stop the
        service from the command line.
        '''
        # Create the service interface.
        soapInterface = AGNetworkServiceI(service)
        
        self.app.Initialize(self.name)
        self.log = self.app.GetLog()
                
        # Register signal handling for clean shutdown of service.
        signal.signal(signal.SIGINT, self.StopSignalLoop)
        signal.signal(signal.SIGTERM, self.StopSignalLoop)
        
        # Start soap service.
        port = NetworkAddressAllocator().AllocatePort()
        self.server = SecureServer((self.app.GetHostname(), port))
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
            nsd = AGNetworkServiceDescription(self.name, self.description, self.url, self.venueProxies.keys(),
                                              self.inCapabilities, self.outCapabilities, self.version)
            for url in self.venueProxies.keys():
                try:
                    self.venueProxies[url].UnRegisterNetworkService(nsd)
                except:
                    self.log.exception("AGNetworkService.Stop: UnregisterNetworkService with venue %s failed for %s"
                                       %(url, nsd.ToString()))

        # Stop soap service.
        try:
            self.server.Stop()
        except:
            self.log.exception("AGNetworkService.Stop: Stop soap server failed %s")
                        
    def StartSignalLoop(self):
        '''
        Start loop that can get interrupted from signals and
        shut down service properly.
        '''

        flag = 1
        while flag:
            try:
                time.sleep(0.5)
            except IOError:
                flag = 0
                self.log.debug("AGNetworkService.StartSignalLoop: Signal loop interrupted, exiting.")

    def StopSignalLoop(self, signum, frame):
        '''
        Signal callback that shuts down the service cleanly. 
        '''
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
            nsd = AGNetworkServiceDescription(self.name, self.description, self.url, self.venueProxies.keys(),
                                              self.inCapabilities, self.outCapabilities, self.version)
            
            try:
                self.venueProxies[url].RegisterNetworkService(nsd)
                self.log.debug("AGNetworkService.Register: Register with venue %s" %(url))
            except:
                self.log.exception("AGNetworkService.Register: RegisterNetworkService with venue %s failed for %s"%(url, nsd.ToString()))
    

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
            nsd = AGNetworkServiceDescription(self.name, self.description, self.url, self.venueProxies.keys(),
                                              self.inCapabilities, self.outCapabilities, self.version)
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

class AGNetworkServiceI(SOAPInterface):
    def __init__(self, impl):
        SOAPInterface.__init__(self, impl)
        
    def _authorize(self, *args, **kw):
        return 1
    
    def Transform(self, streamList):
        streams = []
        for stream in streamList:
            streams.append(CreateStreamDescription(stream))
            
        return self.impl.Transform(streams)

    def StopTransform(self, streamList):
        streams = []
        for stream in streamList:
            streams.append(CreateStreamDescription(stream))
            
        return self.impl.StopTransform(streams)
        
if __name__ == "__main__":
    # Test for AGNetworkService and venue soap interface.

    # Before running test; start a venue server on your local host.
    
    class FakeService(AGNetworkService):
        def __init__(self, name):
            AGNetworkService.__init__(self, name, 'Convert from 16kHz to 8kHz', '1.0')
            # Create in and out capabilities.
            config = {ServiceCapability.DEVICE_SAMPLE_RATE:'16000'}
            n1 = ServiceCapability(name, 'transform', 'audio', config)
            
            config = {ServiceCapability.DEVICE_SAMPLE_RATE:'8000'}
            n2 = ServiceCapability(name, 'transform', 'audio', config)
            
            self.inCapabilities = [n1.ToXML()]
            self.outCapabilities = [n2.ToXML()]

            # Start the service.
            self.Start(self)

        def StopTransform(self, streamList):
            return []
               
        def Transform(self, streamList):
            return []

    # Create the network service.
    service = FakeService('FakeService')

    # Test venue soap interface.
    vProxy = VenueIW('https://localhost:8000/Venues/default')
    nsd = AGNetworkServiceDescription(service.name, service.description, service.url, 'urls',
                                              service.inCapabilities, service.outCapabilities, service.version)
            
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

    result = nsProxy.Transform([])
    if not result == []:
        raise Exception, 'Transform failed'
    
    result = nsProxy.StopTransform([])
    if not result == []:
        raise Exception, 'Stop transform failed'
    
    service.Stop()
    
    
    

