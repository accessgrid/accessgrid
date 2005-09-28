import urlparse
from ZSI.ServiceContainer import SOAPRequestHandler, ServiceSOAPBinding

class AGSOAPRequestHandler(SOAPRequestHandler):
    def log_message(self, format, *args):
        # default was:
        #sys.stderr.write("%s - - [%s] %s\n" %
        #                 (self.address_string(),
        #                  self.log_date_time_string(),
        #                  format%args))
        pass

class ServiceContainerBase:
    '''HTTPServer that stores service instances according 
    to POST values.  An action value is instance specific,
    and specifies an operation (function) of an instance.
    '''
    class NodeTree:
        '''Simple dictionary implementation of a node tree
        '''
        def __init__(self):
            self.__dict = {}

        def __str__(self):
            return str(self.__dict)

        def listNodes(self):
	        print self.__dict.keys()

        def getNode(self, url):
            path = urlparse.urlsplit(url)[2]
            if path.startswith("/"):
                path = path[1:]

            if self.__dict.has_key(path):
                return self.__dict[path]
            else:
                raise NoSuchService, 'No service(%s) in ServiceContainer' %path

        def setNode(self, service, url):
            path = urlparse.urlsplit(url)[2]
            if path.startswith("/"):
                path = path[1:]

            if not isinstance(service, ServiceSOAPBinding):
               raise TypeError, 'A Service must implement class ServiceSOAPBinding'
            if self.__dict.has_key(path):
                raise ServiceAlreadyPresent, 'Service(%s) already in ServiceContainer' % path
            else:
                self.__dict[path] = service

        def removeNode(self, url):
            path = urlparse.urlsplit(url)[2]
            if path.startswith("/"):
                path = path[1:]

            if self.__dict.has_key(path):
                node = self.__dict[path]
                del self.__dict[path]
                return node
            else:
                raise NoSuchService, 'No service(%s) in ServiceContainer' %path
            
    def __init__(self, server_address, services=[], RequestHandlerClass=AGSOAPRequestHandler):
        '''server_address -- 
           RequestHandlerClass -- 
        '''
        self._nodes = self.NodeTree()
        map(lambda s: self.setNode(s), services)
        
        self.RequestHandlerClass = RequestHandlerClass

    def __str__(self):
        return '%s(%s) nodes( %s )' %(self.__class__, id(self), str(self._nodes))

    def __call__(self, ps, post, action, address=None):
        '''ps -- ParsedSoap representing the request
           post -- HTTP POST --> instance
           action -- Soap Action header --> method
           address -- Address instance representing WS-Address 
        '''
        method = self.getCallBack(ps, post, action)
        if isinstance(method.im_self, SimpleWSResource):
            return method(ps, address)
        return method(ps)


    def setNode(self, service, url=None):
        if url is None: 
            url = service.getPost()
        self._nodes.setNode(service, url)

    def getNode(self, url):
        return self._nodes.getNode(url)

    def removeNode(self, url):
        self._nodes.removeNode(url)


from BaseHTTPServer import HTTPServer
class ServiceContainer(ServiceContainerBase,HTTPServer):
    def __init__(self, server_address, services=[], RequestHandlerClass=AGSOAPRequestHandler):
        '''server_address -- 
           RequestHandlerClass -- 
        '''
        ServiceContainerBase.__init__(self,server_address,services)
        HTTPServer.__init__(self, server_address, RequestHandlerClass)

import SocketServer
class ThreadingServiceContainer(SocketServer.ThreadingMixIn,ServiceContainer):
    def __init__(self, server_address, services=[]):
        ServiceContainer.__init__(self, server_address)
        
haveCryptoLib = 0
try:
    from M2Crypto import SSL
    haveCryptoLib = 1
except:
    pass
    
if haveCryptoLib:
    SSL.Connection.clientPostConnectionCheck = None
    SSL.Connection.serverPostConnectionCheck = None
    class SecureServiceContainer(ServiceContainerBase,SSL.SSLServer):
        def __init__(self, server_address,certfile,keyfile,caCertDir, services=[],RequestHandlerClass=AGSOAPRequestHandler):
            '''server_address -- 
               RequestHandlerClass -- 
            '''

            ServiceContainerBase.__init__(self,server_address,services,RequestHandlerClass)
            self.server_name, self.server_port = server_address

            context = SSL.Context()
            context.load_cert(certfile,keyfile)
            context.load_verify_locations(capath=caCertDir)
            context.set_verify(SSL.verify_peer, 10)
            SSL.SSLServer.__init__(self, server_address, 
                               self.RequestHandlerClass,
                               context)
            self._nodes = self.NodeTree()
            map(lambda s: self.setNode(s), services)

    class ThreadingSecureServiceContainer(SocketServer.ThreadingMixIn,SecureServiceContainer):
        def __init__(self, server_address,certfile,keyfile,caCertDir,services=[]):
            SecureServiceContainer.__init__(self, server_address,
                                            certfile,keyfile,
                                            caCertDir,
                                            services)
else:
    class ThreadingSecureServiceContainer:
        def __init__(self, *args):
            raise Exception("ThreadingServiceContainer not available; dependent libs not found!")

    
