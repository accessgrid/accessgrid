from AccessGrid import Log
log = Log.GetLogger(Log.Hosting)
import urlparse
from ZSI.ServiceContainer import SOAPRequestHandler, ServiceSOAPBinding, NoSuchService

class AGSOAPRequestHandler(SOAPRequestHandler):
    def log_message(self, format, *args):
        # default was:
        #sys.stderr.write("%s - - [%s] %s\n" %
        #                 (self.address_string(),
        #                  self.log_date_time_string(),
        #                  format%args))
        pass

    def send_fault(self, f, code=500):
        log.error("%s", f)
        SOAPRequestHandler.send_fault(self, f, code)

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
    proto = 'http'
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
    from M2Crypto import SSL, Err, m2
    haveCryptoLib = 1
except:
    pass
    
if haveCryptoLib:
    def M2CryptoConnectionAccept(self):
        """
        Alternate implementation for M2Crypto.SSL.Connection.accept
        This implementation sets the read/write timeouts on the socket
        and checks for an error in the SSL accept.  Any time a
        client connects to the servers and doesn't finish the 
        SSL accept negotiations, the server is hung until the client
        goes away.  Timeouts fix this by only allowing a client to 
        hang the server for ten seconds.
        
        This functionality will be rolled back to the M2Crypto project
        as soon as possible.  When it appears in an M2Crypto release,
        we can do away with this patch.
        """
        sock, addr = self.socket.accept()
        ssl = SSL.Connection(self.ctx, sock)
        t = ssl.get_socket_read_timeout()
        t.sec = 10
        ssl.set_socket_read_timeout(t)
        ssl.set_socket_write_timeout(t)
        ssl.addr = addr
        ssl.setup_ssl()
        ssl.set_accept_state()
        ret = ssl.accept_ssl()
        err = m2.ssl_get_error(ssl.ssl,ret)
        if err != m2.ssl_error_none:
            ssl.socket.close()
            raise Err.SSLError(ret,addr)
        check = getattr(self, 'postConnectionCheck', self.serverPostConnectionCheck)
        if check is not None:
            if not check(self.get_peer_cert(), ssl.addr[0]):
                raise Checker.SSLVerificationError, 'post connection check failed'
        return ssl, addr

    SSL.Connection.accept = M2CryptoConnectionAccept
    SSL.Connection.clientPostConnectionCheck = None
    SSL.Connection.serverPostConnectionCheck = None
    class SecureServiceContainer(ServiceContainerBase,SSL.SSLServer):
        proto = 'https'
        def __init__(self, server_address,context, services=[],RequestHandlerClass=AGSOAPRequestHandler):
            '''server_address -- 
               RequestHandlerClass -- 
            '''

            ServiceContainerBase.__init__(self,server_address,services,RequestHandlerClass)
            self.server_name, self.server_port = server_address

            SSL.SSLServer.__init__(self, server_address, 
                               self.RequestHandlerClass,
                               context)
            self._nodes = self.NodeTree()
            map(lambda s: self.setNode(s), services)

        def handle_error(self, request=None, client_address=None):
            log.exception(request)
            SSL.SSLServer.handle_error(self,request,client_address)

    class ThreadingSecureServiceContainer(SocketServer.ThreadingMixIn,SecureServiceContainer):
        def __init__(self, server_address,context,services=[]):
            SecureServiceContainer.__init__(self, server_address,
                                            context,
                                            services)
else:
    class ThreadingSecureServiceContainer:
        def __init__(self, *args):
            raise Exception("ThreadingServiceContainer not available; dependent libs not found!")

    
