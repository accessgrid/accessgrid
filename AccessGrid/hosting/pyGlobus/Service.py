
import sys
import classad
import time
import thread
import threading
from AG.services.xmlrpc import Client

class NoServiceMethodException(Exception):
    """No such method.

    An incoming XMLRPC request will raise this exception when a
    the request specifies a service id that is not registered with
    this server."""
    
    pass

class ClassAdParseError(Exception):
    """A ClassAdParseError is raised when the classad passed in a registry
    binding request does not parse."""
    pass


class RegistryBinding:
    """Registry Binding (internal class)

    A RegistryBinding instance is created when a service binds to a
    registry with the bind_to_registry method. The binding object
    keeps track of the registry handle and the classad being advertised
    to that registry. It also keeps a timer that handles the periodic
    soft-state reregistration of the service with the registry.

    Instance vars:

    self.service_ad
    ClassAd object for the service being advertised

    self.my_ad
    ClassAd object for the binding advertisement. This will look something
    like this:
        [
            service_ad = <registered service advertisement>;
            handle = "<handle to service>";
            last_update = <time of last update, Unix epoch (seconds since 1970)>
        ]
    

    """

    def __init__(self, service, class_ad, registry_url, frequency):

        parsed = classad.ClassAdParser().parseClassAd(class_ad)
        if parsed is None:
            raise ClassAdParseError()

        self.service = service
        self.registry = Client.Handle(registry_url, self.auth_callback)
        self.frequency = frequency
        
        self.service_ad = parsed
        self.my_ad = classad.ClassAd()
        self.my_ad.Insert("service_ad", self.service_ad)
        self.my_ad.InsertAttr("last_update", int(time.time()))
        self.my_ad.InsertAttr("handle", self.service.get_handle())

        # How long will we give it after the timeout before
        # the service reference is reaped..
        self.fudge = 3

        self.timer = None

    def auth_callback(self, server, g_handle, remote_user, context):
        print "registryBidning got auth_callback: slef=%s server=%s handle=%s remote_user=%s context=%s" % (
            self, server, g_handle, remote_user, context)
        return 1

    def bind(self):
        """Bind to the registry."""
        self.kick_registry()

    def kick_registry(self):

        """Send a registration message to the registry."""
        
        timeout = int(time.time() + self.frequency + self.fudge)

        print "Kicking registry with ", self.service.get_handle()
        self.registry.get_proxy().register_service(str(self.my_ad), self.service.get_handle(),
                                                   timeout)

        self.timer = threading.Timer(self.frequency, self.timeout)
        self.timer.setDaemon(1)
        self.timer.start()

    def update(self, classad, frequency):
        """Update the classsad or update frequency for this service."""

        parsed = classad.ClassAdParser().parseClassAd(classad)
        if parsed is None:
            raise ClassAdParseError()

        self.service_ad = parsed
        self.my_ad.Insert("service_ad", self.service_ad)
        self.my_ad.InsertAttr("last_update", int(time.time()))
        self.my_ad.InsertAttr("handle", self.service.get_url())

        self.frequency = frequency

        if self.timer is not None:
            self.timer.cancel()

        kick_registry()

    def timeout(self):
        """Timeout.

        Invoked when the registry update timer expires. Sends an update
        message to the registry via the kick_registry() method."""
        
        print "service timeout"
        self.kick_registry()

    def unbind(self):
        """Unbind from the registry.

        Sends an unregister_service RPC to the registry, and cancel the update timer."""
        
        self.registry.get_proxy().unregister_service(self.service.get_handle())
        
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None

    def __del__(self):
        print "RegistryBinding for %s deallocating, trying to unbind" % (self.service.get_handle())
        self.unbind()

class LocalRegistryBinding:
    """Local Registry Binding (internal class)

    A LocalRegistryBinding is created when a service is bound to an in-process
    registry. It is polymorphic with RegistryBinding, but does not share a common
    baseclass. This class holds the parsed class ads in the same manner as RegistryBinding,
    but does not include the mechanisms for automatic refresh, as an in-process registry
    does not require that.

    It also keeps an object reference to the registry, as passed in the constructor. This is
    later used in the unbind.

    """

    def __init__(self, service, class_ad, registry_obj, registry_url):

        parsed = classad.ClassAdParser().parseClassAd(class_ad)
        if parsed is None:
            raise ClassAdParseError()

        self.service = service

        self.registry_url = registry_url
        self.registry_obj = registry_obj
        
        self.service_ad = parsed
        self.my_ad = classad.ClassAd()
        self.my_ad.Insert("service_ad", self.service_ad)
        self.my_ad.InsertAttr("last_update", int(time.time()))
        self.my_ad.InsertAttr("handle", self.service.get_handle())


    def bind(self):
        """Bind to the registry."""

        self.registry_obj.register_local_service(str(self.my_ad), self.service.get_handle())

    def update(self, class_ad):
        """Update the classsad or update frequency for this service."""

        parsed = classad.ClassAdParser().parseClassAd(class_ad)
        if parsed is None:
            raise ClassAdParseError()


        self.service_ad = parsed
        self.my_ad.Insert("service_ad", self.service_ad)
        self.my_ad.InsertAttr("last_update", int(time.time()))
        self.my_ad.InsertAttr("handle", self.service.get_handle())

        self.bind()

    def unbind(self):
        """Unbind from the registry.
        """

        self.registry_obj.unregister_local_service(self.service.get_handle())

    def __del__(self):
        print "LocalRegistryBinding for %s deallocating, trying to unbind" % (self.service.get_handle())
        self.unbind()

class NotBoundToRegistryException(Exception):
    """Raised if an attempt to unbind a service from a registry occurs when the service
    is not actually bound to that registry.
    """
    pass

class Service:
    """An XMLRPC service.

    A Service instance provides the communications endpoint for an
    XMLRPC service object. 

    Following is an example of the use of a Service object.

    First, we define a class and method that will handle an incoming
    XMLRPC request.

    class Handler:
        def __init__(self):
            # Usual instance setup

        def handle_method(self, marg1, marg2):
            # Handle the incoming method, invoked with 2 arguments.


    Now we create a server, listening on <port>. From that server we create a new
    service, create a handler, and bind the handler function to the service name:

    server = Server(port)
    service = server.create_service()
    handler = Handler()
    service.register_function(handler.handle_method, "handle_method")

    Note that we bind to handler.handle_method; this is a Python bound instance that
    will remember the handler instance that is associated with the method. If we wanted
    to define a function (not a class method) to handle the XMRPC call, it might look
    like this:

        def handler_func(marg1, marg2):
            # Handle the incoming method, invoked with 2 arguments.

    service.register_function(handler_func, "handle_method")

    If we wish to advertise this service with a registry, with a 30-second
    refresh, we would do the following:

        classad = "[ attribute = value ]"
        service.bind_to_registry(classad, "https://server.host.com:portnumber/svcid", 30)
    
    """

    def __init__(self, server, id):
        """Constructor

        Normal users shouldn't use this mechanism. Use server.create_service() instead.
        """
        
        
	self.server = server
	self.id = id
        self.function_map = {}
        self.binding_table = {}
        print "Created serivce ", self

    def __del__(self):
        print "Service deleting"

    def auth_callback(self, server, g_handle, remote_user, context):
        print "Service got auth_callback: slef=%s server=%s handle=%s remote_user=%s context=%s" % (
            self, server, g_handle, remote_user, context)
        return 1

    def get_path(self):
        """Return the path part of the service's URL."""
	path = "/%d" % (self.id)
	return path
    
    def get_handle(self):
        """Return the service's handle (as a URL)."""
	handle = self.server.get_url_base() + self.get_path()
        return handle

    def bind_to_registry(self, classad, registry_url, frequency):
        """Bind to a registry

        See if we have a binding for this registry yet. If so,
        update that binding with this information. Otherwise, 
        create a new binding.

        Arguments:

          classad - classified ad for this service
          registry_url - URL to the registry service we are binding to
          frequency - soft-state update interval, in seconds
        
        """

        try:
            binding = self.binding_table[registry_url]
            binding.update(classad, frequency)

        except KeyError:
            
            binding = RegistryBinding(self, classad, registry_url, frequency)
            binding.bind()
            self.binding_table[registry_url] = binding

    def bind_to_local_registry(self, class_ad, registry_obj, registry_url):
        """Bind to a local registry

        See if we have a binding for this registry yet. If so,
        update that binding with this information. Otherwise, 
        create a new binding.

        Arguments:

          class_ad - classified ad for this service
          registry_obj - Registry object
          registry_url - URL to the registry service we are binding to
        
        """

        try:
            binding = self.binding_table[registry_url]
            binding.update(class_ad)

        except KeyError:
            
            binding = LocalRegistryBinding(self, class_ad, registry_obj, registry_url)
            binding.bind()
            self.binding_table[registry_url] = binding

    def unbind_from_registry(self, registry_url):
        """Remove my registry binding."""
        
        try:
            binding = self.binding_registry[registry_url]

            binding.unbind()
            del self.binding_registry[registry_url]

        except KeyError:
            raise NotBoundToRegistryException()

    def register_functions(self, function_dict, pass_connection_info = 0):
        """Register these functions as XMLRPC handler methods.

        The function_dict is a dictionary where the key is the XMLRPC method name and
        the value is the handler to be bound to that name.
        """
        
        for name in function_dict.keys():
            func = function_dict[name]
            self.register_function(func, name, pass_connection_info)

    def register_function(self, function, name = None, pass_connection_info = 0):
        """Register a function to respond to XML-RPC requests.

        The optional name argument can be used to set a Unicode name
        for the function.

        If an instance is also registered then it will only be called
        if a matching function is not found.
        """

        if name is None:
            name = function.__name__
#        print "Service %s registers function %s as %s" % (self, function, name)
        self.function_map[name] = (function, pass_connection_info)

    def _lookup_method(self, method):

        print "Lookup method ", method

        func = None
        try:
            func, pass_connection_info = self.function_map[method]
            print "Found func ", func

        except KeyError:
            pass

        #        print "Service %s mapped %s to %s" % (self, method, func)

        if func is None:
            raise NoServiceMethodException()
        

        return func, pass_connection_info

