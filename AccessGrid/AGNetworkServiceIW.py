from AccessGrid.hosting.SOAPInterface import SOAPIWrapper
from AccessGrid.Descriptions import CreateStreamDescription

class AGNetworkServiceIW(SOAPIWrapper):
    def __init__(self, url, faultHandler = None):
        SOAPIWrapper.__init__(self, url, faultHandler)
        
    def Transform(self, streamList):
        '''
        Method to transform a set of streams.

        ** Arguments **

        * streamList * A list of stream descriptions to transform.

        ** Returns **

        * streamList * A list of stream descriptions as result from transformation. 
        '''
        
        streams = self.proxy.Transform(streamList)
        retval = []

        if not streams or len(streams) < 1:
            return []
        
        for stream in streams:
            retval.append(CreateStreamDescription(stream))
           
        return retval

    def StopTransform(self, streamList):
        '''
        Stop transformation.

        ** Arguments **

        * streamList * A set of stream descriptions of streams we want to stop transforming.
        '''
        
        return self.proxy.StopTransform(streamList)
