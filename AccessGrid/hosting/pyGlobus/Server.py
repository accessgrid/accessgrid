import ServiceObject
import ServiceBase
import socket
import pyGlobus.io
from AGGSISOAP import SOAPProxy, SOAPServer, SOAPConfig

class SecureConnectionInfo:
    def __init__(self, context):

        initiator, acceptor, valid_time, mechanism_oid, flags, local_flag, open_flag = context.inquire()

        self.initiator = initiator
        self.acceptor = acceptor

    def get_remote_name(self):
        return self.initiator.display()

    def __repr__(self):
        return "SecureConnectionInfo(initiator=%s, acceptor=%s)"  % (self.initiator.display(), self.acceptor.display())

class Server:

    def __init__(self, port, auth_callback = None, debug = 0):
        """
        Create a pyGlobus/GSI server instance.
        """
        #
        # Create the SOAP server itself.
        #

        self._create_server(port, auth_callback, debug = debug)

        #
        # Register this object as the path dispatcher
        #
        self._server.registerPath(self)

        #
        # Seed for service id allocator.
        #
        self._next_service_id = 100

        self._path_map = {}

        self._running = 0

    def _create_server(self, port, server_auth_callback, debug = 0):

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
        config.debug = debug
        self._server = SOAPServer(('localhost', port),
                                  tcpAttr = attr,
                                  log = 0,
                                  config = config)

    def run(self):
        """
        Run the server.

        This method runs the server (that is, causes it to listen for
        and process incoming messages) in the current thread. It does
        not return.

        """

        self._running = 1

        while(self._running):
            self._server.handle_request()

        self._server.server_close()
        
    def run_in_thread(self):
        """
        Start the server in a new thread.

        This method causes the server to begin listening for and
        processing incoming messages in a new message-handling thread. It
        returns immediately.
        """

        server_thread = threading.Thread(target = self.run)
        server_thread.start()

    def stop(self):
        self._running = 0

    def create_service(self, service_class, 
                       pathId = None,
                       *args):
	"""
        Instantiate a new service.


	"""

        service_obj = self.create_service_object(pathId = pathId)

        if not issubclass(service_class, ServiceBase.ServiceBase):
            raise NotAServiceClassException

        #
        # Create the appliation's service object
        #

        appobj = apply(service_class, args)

        appobj._bind_to_service(service_obj)

	return appobj

    def create_service_object(self, pathId = None):
	"""
        Instantiate a new service object.

	This amounts to allocating a new service ID, and creating the
	service object with that ID. We also register that object in
	the dispatch table.


	"""

        if pathId is None:
            my_id = self.allocate_id()
        else:
            my_id = pathId

	# Create the service object

	service_obj = ServiceObject.ServiceObject(self, my_id)

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


