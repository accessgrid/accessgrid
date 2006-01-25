from AccessGrid import Log
from AccessGrid.interfaces.AGNetworkService_client import AGNetworkServiceIW
from AccessGrid.Descriptions import Capability

class NetworkServicesManager:
    '''
    A manager class for available network services in a venue.  This class
    also includes a network service matcher that can select a chain of services
    to use for streams that do not match capabilities of a node.
    '''
    
    def __init__(self):
        '''
        Initiates the class. Creates a network service matcher and a dictionary
        to keep track of available network services.
        '''
        
        self.__services = dict()
        self.__matcher = NetworkServiceMatcher()
        self.log = Log.GetLogger('NetworkServicesManager')
        
    def RegisterService(self, networkServiceDescription):
        '''
        Registers a network service with the manager.

        ** Arguments **

        * networkServiceDescription * a description of the network service to add (AGNetworkServiceDescription).
        '''
        
        nsd = networkServiceDescription
        if not nsd:
            self.log.error("RegisterService: Missing network service parameter, failed to add service.")
            raise Exception, 'Missing network service parameter, failed to add service.'
                           
        if self.__services.has_key(nsd.uri):
            self.log.error('RegisterService: A service at url %s is already present, failed to add service.'
                           %nsd.uri)
            raise Exception, 'A service at url %s is already present, failed to add service.'%nsd.uri
        
        self.log.debug('RegisterService: Register network service %s'
                       %nsd.name)
        self.__services[nsd.uri] = nsd
        
        return nsd
        
    def UnRegisterService(self, networkServiceDescription):
        '''
        Removes a network service from the manager.

        ** Arguments **
        
        * networkServiceDescription * a description of the network service to add (AGNetworkServiceDescription).
        '''

        if not networkServiceDescription:
            self.log.error('UnRegisterService: Missing network service parameter, failed to remove service.')
            raise Exception, 'Missing network service description parameter'
            
        nid = networkServiceDescription.uri

        if self.__services.has_key(nid):

            self.log.debug('UnRegisterService: Unregister service %s'
                           %networkServiceDescription.name)
            del self.__services[nid]
        else:
            self.log.exception('UnRegisterService: Service %s is already unregistered'
                               %networkServiceDescription.uri)
            raise Exception, 'Service %s is already unregistered'%networkServiceDescription.uri
                
    def ResolveMismatch(self, streamList, nodeCapabilities):
        '''
        Matches streams to available network services. Uses network services to resolve
        mismatch between stream capabilities and capabilities of a node.

        ** Arguments **

        * streamList * a list of mismatched streams.

        * nodeCapabilities * capabilities of a node.

        ** Returns **

        * matchedStreams * a list of new streams that matches given node capabilities.
        
        '''
        self.log.debug('ResolveMismatch: Match streams to capabilities')
               
        if not nodeCapabilities:
            self.log.error('ResolveMismatch: Missing node capabilities parameter.')
            raise Exception, 'NetworkServicesManager.ResolveMismatch: Capability parameter is missing, can not complete matching'
        
        if not streamList:
            self.log.error('ResolveMismatch: Missing stream list parameter.')
            raise Exception, 'NetworkServicesManager.ResolveMismatch: Stream list parameter is missing, can not complete matching'
        
        matchedStreams = []
        
        # Returns a list containing tuple objects ([stream],[networkService]) that
        # describes a chain of services to use for a set of streams.
        if len(self.__services) > 0:
            self.log.debug("ResolveMismatch: we have network services, use matcher")
            streamServiceList = self.__matcher.Match(streamList,
                                                     nodeCapabilities,
                                                     self.__services.values())
        else:
            streamServiceList = []
            self.log.debug("ResolveMismatch: There are no network services available, ignore matching")
          

        # Resolve mismatches!
        for resolution in streamServiceList:
            self.log.debug('ResolveMismatch: Start transform')
            streams = resolution[0]
            netServices = resolution[1]
            
            # Perform the chain of stream transformation.
            # streams -> net service -> net service -> net service -> streams
            for service in netServices:
                self.log.debug('ResolveMismatch: Call transform method for services running at %s'%service.uri)
                netServiceProxy = AGNetworkServiceIW(service.uri)

                try:
                    streams = netServiceProxy.Transform(streams)
                except:
                    self.log.exception('ResolveMismatch: Transform for service %s failed'%service)
                    streams = []
        
            # Add new streams to list
            if len(streams)>0:
                matchedStreams.append((streams, service.uri))

        return matchedStreams
          
    def GetServices(self):
        '''
        Returns descriptions of all available network services.

        ** Returns **

        *services* a list of AGNetworkServiceDescriptions.
        '''
        
        return self.__services.values()


class NetworkServiceMatcher:
    '''
    A class for finding the best chain of network services
    to resolve streams that do not match capabilities of a node.
    '''
    
    def __init__(self):
        self.log = Log.GetLogger('NetworkServiceMatcher')

    def __MatchInCapabilities(self, stream, services):
        '''
        For a given stream, find network services that have matching
        consumer capabilities.

        ** Arguments **
        
        * stream * Stream we want to match against.
        * services * A list of network services.

        ** Returns **

        *matchingServices* includes all matching services for a stream.
        '''
        
        matchingServices = []
        streamProducerCaps = filter(lambda x: x.role == Capability.PRODUCER, stream.capability)
                      
        # Create a list of all services that matches this stream.
        for service in services:
            netServiceConsumerCaps =  filter(lambda x: x.role == Capability.CONSUMER, service.capabilities)
            serviceMatch = 1
            for streamCap in streamProducerCaps:
                match = 0
                for cap in netServiceConsumerCaps :
                    if streamCap.matches(cap):
                        match = 1
                if not match:
                    serviceMatch = 0
                    break
            if (service not in matchingServices) and serviceMatch:
                # Do not add the same service twice
                matchingServices.append(service)
                  
        return matchingServices

    def __MatchOutCapabilities(self, services, capabilities):
        '''
        For given services, find all services that have out capabilities
        that matches the capabilities of a node.

        ** Arguments **

        *services* A list of network services.
        
        *capabilities* A set of capabilities describing a node.

        ** Returns **

        * matchingServices * A list of network services with matching out capability.
        '''
        
        matchingServices = []
        nodeConsumerCaps =  filter(lambda x: x.role == Capability.CONSUMER, capabilities)
        
        for service in services:
            netServiceProducerCaps = filter(lambda x: x.role == Capability.PRODUCER, service.capabilities)
            serviceMatch = 1
            for capability in nodeConsumerCaps:
                match = 0
                for serviceCap in netServiceProducerCaps:
                    # Match network service out capability with the node capability.
                    if serviceCap.matches(capability):
                        match = 1
                if not match:
                    serviceMatch = 0
                    break
                
            # Do not add the same service twice. 
            if (service not in matchingServices) and serviceMatch:
                matchingServices.append(service)

        return matchingServices

                        
    def Match(self, streams, capabilities, services):
        '''
        Finds network services that can resolve mismatches
        between a set of streams and the node capabilities.

        ** Arguments **

        * streams * Streams we want to match
        
        * capabilities * A set of capabilities describing a node.
        
        * services * A list of available network services.

        ** Returns **
        
        * streamServiceList* A list containing tuple objects ([stream],[service])
        that associates a set of streams with a chain of network services.
        '''
        
        # Check for service capability mismatch
        
        if not capabilities:
            self.log.exception('NetworkServiceMatcher.Match: Capability parameter is None.')
            raise Exception, 'NetworkServiceMatcher.Match: Capability parameter is None.'
        
        if len(services) < 1:
            self.log.exception('NetworkServiceMatcher.Match: Network services parameter contains an empty list.')
            raise Exception, 'NetworkServiceMatcher.Match: Network services parameter contains an empty list.'
               
        streamServiceList = []

        for stream in streams:

            # Find network services that have matching consumer capabilities compared to stream
            # producer capabilities.
            matchingServices = self.__MatchInCapabilities(stream, services)

            # From all network services that have matching consumer capabilities,
            # find those that also have matching producer capabilities compared to node
            # consumer capabilities.
            completeMatches = self.__MatchOutCapabilities(matchingServices, capabilities)

            # For now, use the first network service that has a complete match.
            # Later, we might want to make a smarter selection and send a set of
            # streams to a chain of services. 
            if len(completeMatches) > 0:
                # Associate the stream with the matching network service.
                listObject = ([stream],[completeMatches[0]])
                streamServiceList.append(listObject)
                                                
        # Return a dict with streams and corresponding network services that
        # can resolve capability mismatch.
        return streamServiceList

# To test
if __name__ == "__main__":

    class FakeService:
        def __init__(self):
            self.uri = "fakeUri"
            
    class FakeCapability:
        def __init__(self):
            pass
       
    class FakeStream:
        def __init__(self):
            self.capability = FakeCapability()

    fakeService = FakeService()
    
    cap1 = FakeCapability()
    cap2 = FakeCapability()
    fakeCapabilities = [cap1, cap2]

    s1 = FakeStream()
    s2 = FakeStream()
    fakeStreams = [s1, s2]

    nsm = NetworkServicesManager()
    nsm.RegisterService(fakeService)
    print nsm.ResolveMismatch(fakeStreams, fakeCapabilities)
    nsm.UnRegisterService(fakeService)
