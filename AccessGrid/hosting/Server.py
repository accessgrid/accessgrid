"""
XMLRPC Services
"""

from AGGSISOAP import SOAPProxy, SOAPServer, SOAPConfig

from ServiceBase import ServiceBase

import socket
import threading
import handler

import traceback

from Service import Service

__all__ = ["Server", "InsecureServer"]

class NotAServiceClassException(Exception):
    pass

class NoServiceException(Exception):
    """No such service registered.

    An incoming SOAP request will raise this exception when a
    the request specifies a service id that is not registered with
    this server."""
    
    pass

class SecureConnectionInfo:
    def __init__(self, context):

        initiator, acceptor, valid_time, mechanism_oid, flags, local_flag, open_flag = context.inquire()

        self.initiator = initiator
        self.acceptor = acceptor

    def get_remote_name(self):
        return self.initiator.display()

    def __repr__(self):
        return "SecureConnectionInfo(initiator=%s, acceptor=%s)"  % (self.initiator.display(), self.acceptor.display())
        
class InsecureConnectionInfo:
    def __init__(self, connection):
        self.remote_info = connection.getpeername()
        self.local_info = connection.getsockname()

    def get_remote_name(self):
        return self.remote_info

    def __repr__(self):
        return "InsecureConnectionInfo(remote=%s, local=%s)" % (self.remote_info, self.local_info)

class ServerBase:

    """SOAP Server wrapper

    This class provides high-level SOAP services. In particular,
    it implements a bag-of-services model, where multiple services
    distinguished by URL are all served from a single port.

    (Whether this is a good idea or a bad idea may be up for
    debate; the main implication is that all services served
    by the same port will use the same underlying Globus transport
    options. If it is necessary to use different ports or trnasport
    attributes, multiple Servers can be created)    
    """

    def __init__(self):
        """
        Create a new Server. 
        """

	#
	# First set up the path -> instance map
	#
	
	self._path_map = {}

	#
	# And the service ID index.
	#

	self._next_service_id = 100

	#
	# We're all set. 
	#

    def run(self):
        """Run the server.

        This method runs the server (that is, causes it to listen for and process
        incoming messages) in the current thread. It does not return.
        """
        
	self._server.serve_forever()

    def run_in_thread(self):
        """Run the server in its own thread.

        Create a new thread and run the server in that thread. Returns immediately.
        """
        
        server_thread = threading.Thread(target = self.run)
        server_thread.start()

    def create_service(self, service_class = None, *args):
	""" 
	Instantiate a new service.        
	"""

        service_obj = self.create_service_object()

        #
        # Backward compatibility: if no class passed in, 
        # assume that this is pre-ServiceBase code.
        # Print a warning and continue.
        # After too long, this code and the = None in the
        # argument list should go away.
        #
        if service_class is None:
            tb = traceback.extract_stack()[0]

            file = tb[0]
            line = tb[1]
            print "WARNING: Old style create_service() invoked at %s:%d" % (file, line)
            return service_obj

            
        if not issubclass(service_class, ServiceBase):
            raise NotAServiceClassException

        #
        # Create the appliation's service object
        #

        appobj = apply(service_class, args)

        appobj._bind_to_service(service_obj)

	return appobj

    def create_service_object(self):
	""" Instantiate a new service object.

	This amounts to allocating a new service ID, and creating the service
	object with that ID. We also register that object in the dispatch table.

        
	"""

        my_id = self.allocate_id()
        
	# Create the service object
	
	service_obj = Service(self, my_id)

        #
	# Register with the method dispatcher
        #

	path = service_obj.get_path()
	self._path_map[path] = service_obj

	return service_obj

    def allocate_id(self):
        #
	# Allocate the ID
        #
        # This should probably change to code that returns a onetime
        # unique id; perhaps based on the index like this, plus a current time
        # and md5- or sha-digested. We'll leave it like this for
        # now in order to make the URLs simpler to look at.
        #
	
	next_id = self._next_service_id
	self._next_service_id = next_id + 1

        return next_id

    def lookup_path(self, method, path):
        """Dispatch an incoming XMLRPC message to the appropriate
        service object."""

        print "Server %s: Dispatch %s via path %s" % (self, method, path)
        try:
            service = self._path_map[path]
            print "Got service ", service
            m = service._lookup_method(method)
            print "Got method ", m
            return m
        except KeyError:
            print "service not found"
            raise NoServiceException
        except Exception, e:
            print "Other exception ", e

import pyGlobus.io
import pyGlobus.ioc
import pyGlobus.utilc

class Server(ServerBase):
    """Globus Security-based Server

    Server.Server is a GSI-protected SOAP server.
    """

    def __init__(self, port, server_auth_callback = None):

        """Create an GSI-protected SOAP server.

        Arguments:

        port - port number desired for this service.
        server_auth_callback - Globus authorization callback for this server.

        An authorization callback takes the following arguments:

          user_data - data object passed by user when callback was registered
          g_handle - the GlobusIO handle for this connection
          identity - X.509 distinguished name of the certificate used on the
                incoming connection 
          context - the GSS context for the connection

        """



        #
        # Create the XMLRPC server itself.
        #

        self._create_server(port, server_auth_callback)

        #
        # Register this object as the path dispatcher
        #

        self._server.registerPath(self)

        ServerBase.__init__(self)

    def _create_server(self, port, server_auth_callback):

        #
        # Set up the TCP attributes to turn on GSSAPI and register
        # the server_auth_callback.
        #

        attr = pyGlobus.io.TCPIOAttr()

        attr.set_authentication_mode(pyGlobus.ioc.GLOBUS_IO_SECURE_AUTHENTICATION_MODE_GSSAPI)
        authdata = pyGlobus.io.AuthData()

        #
        # If we didn't register a callback, default to
        # allowing only processes with our identity. This may
        # not be correct, but only time will tell.
        #

        if server_auth_callback is not None:
            authdata.set_callback(server_auth_callback, self)
            authmode = pyGlobus.ioc.GLOBUS_IO_SECURE_AUTHORIZATION_MODE_CALLBACK
        else:
            authmode = pyGlobus.ioc.GLOBUS_IO_SECURE_AUTHORIZATION_MODE_SELF

        attr.set_authorization_mode(authmode, authdata)

        attr.set_delegation_mode(pyGlobus.ioc.GLOBUS_IO_SECURE_DELEGATION_MODE_NONE)
        attr.set_restrict_port(0)
        attr.set_reuseaddr(1)
        attr.set_nodelay(0)
        attr.set_channel_mode(pyGlobus.ioc.GLOBUS_IO_SECURE_CHANNEL_MODE_GSI_WRAP)


        config = SOAPConfig()
        config.debug = 1
        self._server = SOAPServer(('localhost', port),
                                  tcpAttr = attr,
                                  log = 1,
                                  config = config)

    def get_connection_info(self, connection):
        return SecureConnectionInfo(connection.get_security_context())

    def get_port(self):
        """Return the port on which this server is listening. """
        return self._server.port

    def get_url_base(self):
        """Return the base URL that represents this server. """
        ret, host = pyGlobus.utilc.get_hostname(256)
        if ret != 0:
            host = socket.getfqdn()
        return "https://%s:%s" % (host, self.get_port())


class InsecureServer(ServerBase):
    """Non-secured XMLRPC server.

    InsecureServer uses plain TCP sockets to implement a SOAP server.
    Interactions with InsecureServer instances take place in the clear, without
    encryption or secure authentication.
    """
    
    def __init__(self, port):
        """Constructor.

        Arguments:

          port - the port on which this server should listen. If port is passed
                 as 0, the operating system will pick a port at random.

        """

        #
	# Create the XMLRPC server itself.
	#

	self._create_server(port)

	#
	# Register this object as the dispatcher for the XMLRPC server
	#

	self._server.register_instance(self)

        ServerBase.__init__(self)
        
    def _create_server(self, port):
        """Internal method to create the actual server object."""

        self._server = SimpleXMLRPCServer(('', port),
                                          handler.DispatchPathXMLRPCRequestHandler,
                                          0
                                          )

    def get_connection_info(self, connection):
        return InsecureConnectionInfo(connection)
        
    def get_port(self):
        """Return the port on which this server is listening. """
	return self._server.socket.getsockname()[1]

    def get_url_base(self):
        """Return the base URL that represents this server. """
        return "http://%s:%s" % (socket.getfqdn(), self.get_port())


