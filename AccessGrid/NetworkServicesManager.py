import xml.dom.minidom
from AccessGrid.ServiceCapability import ServiceCapability
from AccessGrid.AGNetworkServiceIW import AGNetworkServiceIW
from AccessGrid import Log

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
        self.log = Log.GetLogger(Log.VenueServer)
        
    def RegisterService(self, networkServiceDescription):
        '''
        Registers a network service with the manager.

        ** Arguments **

        * networkServiceDescription * a description of the network service to add (AGNetworkServiceDescription).
        '''
        
        nsd = networkServiceDescription
        if not nsd:
            self.log.error("RegisterService: Missing network service parameter, failed to add service.")
            raise 'Missing network service parameter, failed to add service.'
                           
        if self.__services.has_key(nsd.url):
            self.log.error('RegisterService: A service at url %s is already present, failed to add service.'
                           %nsd.url)
            raise 'A service at url %s is already present, failed to add service.'%nsd.url
        
        self.log.debug('RegisterService: Register network service %s'
                       %nsd.ToString())
        self.__services[nsd.url] = nsd
        
        return nsd
        
    def UnRegisterService(self, networkServiceDescription):
        '''
        Removes a network service from the manager.

        ** Arguments **
        
        * networkServiceDescription * a description of the network service to add (AGNetworkServiceDescription).
        '''

        if not networkServiceDescription:
            self.log.error('UnRegisterService: Missing network service parameter, failed to remove service.')
            raise 'Missing network service description parameter'
            
        id = networkServiceDescription.url

        if self.__services.has_key(id):
            self.log.debug('UnRegisterService: Unregister service %s'
                           %networkServiceDescription.ToString())
            del self.__services[id]
        else:
            self.log.exception('UnRegisterService: Service %s is already unregistered'
                               %networkServiceDescription.url)
            raise 'Service %s is already unregistered'%networkServiceDescription.url
                
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
        
        if not nodeCapabilities:
            self.log.error('ResolveMismatch: Missing node capabilities parameter.')
            raise 'NetworkServicesManager.Match: Capability parameter is missing, can not complete matching'
        
        if not streamList:
            self.log.error('ResolveMismatch: Missing stream list parameter.')
            raise 'NetworkServicesManager.Match: Stream list parameter is missing, can not complete matching'
            
        self.log.debug('Match: Match streams to capabilities')
       
        matchedStreams = []
        
        # Returns a list containing tuple objects ([stream],[networkService]) that
        # describes a chain of services to use for a set of streams.
        if len(self.__services) > 0:
            streamServiceList = self.__matcher.Match(streamList,
                                                     nodeCapabilities,
                                                     self.__services.values())
        else:
            streamServiceList = []
            self.log.info('Match: There are no network services available.')

        # Resolve mismatches!
        for resolution in streamServiceList:
            streams = resolution[0]
            netServices = resolution[1]
            
            # Perform the chain of stream transformation.
            # streams -> net service -> net service -> net service -> streams
            for service in netServices:
                netServiceProxy = AGNetworkServiceIW(service.url)

                try:
                    streams = netServiceProxy.Transform(streams)
                
                except:
                    self.log.exception('Match: Transform for service %s failed'%service.ToString())
                    streams = []
        
            # Add new streams to list
            matchedStreams.extend(streams)

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
        pass

    def __MatchInCapabilities(self, stream, services):
        '''
        For a given stream, find network services that have matching
        in capabilities.

        ** Arguments **
        
        * stream * Stream we want to match against.
        * services * A list of network services.

        ** Returns **

        *matchingServices* includes all matching services for a stream.
        '''
        
        matchingServices = []

        streamCap = ServiceCapability.CreateServiceCapability(stream.capability.xml)
                
        # Create a list of all services that matches this stream.
        for service in services:
            for cap in service.inCapabilities:
                serviceCap = ServiceCapability.CreateServiceCapability(cap)
        
                if streamCap.Matches(serviceCap):
                    
                    # Do not add the same service twice
                    if service not in matchingServices:
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
        
        for service in services:
            for cap in service.outCapabilities:
                serviceCap = ServiceCapability.CreateServiceCapability(cap)
                             
                for capability in capabilities:
                    myCap = ServiceCapability.CreateServiceCapability(capability.xml)

                    # Match network service out capability with the node capability.
                    if serviceCap.Matches(myCap):

                        # Do not add the same service twice. 
                        if service not in matchingServices:
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
        
        # Check client preferences mismatch
        # If client preference does not match any of my consumer
        # capabilities; ignore that preference.

        # Check for service capability mismatch

        if not capabilities:
            self.log.exception('NetworkServiceMatcher.Match: Capability parameter is None.')
            raise 'NetworkServiceMatcher.Match: Capability parameter is None.'
        
        if len(services) < 1:
            self.log.exception('NetworkServiceMatcher.Match: Network services parameter contains an empty list.')
            raise 'NetworkServiceMatcher.Match: Network services parameter contains an empty list.'
               
        streamServiceList = []

        for stream in streams:
            serviceToUse = None

            # Find network services that have matching in capabilities.
            matchingServices = self.__MatchInCapabilities(stream, services)

            # From all network services that have matching in capabilities,
            # find those that also have matching out capabilities
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

if __name__ == "__main__":
    nsm = NetworkServicesManager()

    ns = NetworkServiceDescription("TestNS", "Audio Transcoder", 'https://ns', 'https://vs',
                                   NetworkServiceCapability(), NetworkServiceCapability(), '1.0')
