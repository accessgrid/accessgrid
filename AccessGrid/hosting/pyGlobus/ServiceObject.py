#-----------------------------------------------------------------------------
# Name:        ServiceObject.py
# Purpose:     
#
# Author:      Robert D. Olson
#
# Created:     2003/08/02
# RCS-ID:      $Id: ServiceObject.py,v 1.9 2003-04-28 17:58:29 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

from AccessGrid.hosting import AccessControl

class NoServiceMethodException(Exception):
    """
    No such method.

    An incoming SOAP request will raise this exception when a
    the request specifies a service id that is not registered with
    this server.
    """
    
    pass


class ServiceObject:
    """
    A SOAP service.

    A ServiceObject instance provides the communications endpoint for an
    SOAP service object. 

    Following is an example of the use of a Service object.

    First, we define a class and method that will handle an incoming
    SOAP request.

    class Handler:
        def __init__(self):
            # Usual instance setup

        def handle_method(self, marg1, marg2):
            # Handle the incoming method, invoked with 2 arguments.


    Now we create a server, listening on <port>. From that server we
    create a new service, create a handler, and bind the handler
    function to the service name:

    server = Server(port)
    service = server.create_service_object()
    handler = Handler()
    service.register_function(handler.handle_method, "handle_method")

    Note that we bind to handler.handle_method; this is a Python bound
    instance that will remember the handler instance that is
    associated with the method. If we wanted to define a function (not
    a class method) to handle the SOAP call, it might look like this:

        def handler_func(marg1, marg2):
            # Handle the incoming method, invoked with 2 arguments.

    service.register_function(handler_func, "handle_method")
    """

    def __init__(self, server, id):
        """
        Constructor

        Normal users shouldn't use this mechanism. Use
        server.create_service() instead.
        
        """
        
	self.server = server
        # This fixes the case where we pass a path from something like
        # urlparse.urlparse (which is probably an increasingly common case)
        if type(id) == str and id[0] == '/':
            self.id = id[1:]
        else:
            self.id = id
        self.function_map = {}
        self.binding_table = {}
        #        print "Created service ", self

        self.role_manager = None

        #
        # Handlers for internal methods for supporting Client.Handle.IsValid and Client.Handle.Implements().
        #

        self.RegisterFunction(self._IsValid, "_IsValid")
        self.RegisterFunction(self._Implements, "_Implements")
        

    def SetRoleManager(self, roleManager):
        """
        Set roleManager as the role manager for this service object.
        This will be queried by the security manager to determine the
        roles assigned to a user.
        """

        self.role_manager = roleManager

    def GetRoleManager(self):
        return self.role_manager
    

    def auth_callback(self, server, g_handle, remote_user, context):
        print "Service got auth_callback: slef=%s server=%s handle=%s remote_user=%s context=%s" % (
            self, server, g_handle, remote_user, context)
        return 1

    def GetPath(self):
        """Return the path part of the service's URL."""
        path = "/%s" % (self.id)
        return path
    
    def GetHandle(self):
        """Return the service's handle (as a URL)."""
        handle = self.server.get_url_base() + self.get_path()
        return handle

    def RegisterFunctions(self, function_dict, pass_connection_info = 0):
        """
        Register these functions as SOAP handler methods.

        The function_dict is a dictionary where the key is the SOAP
        method name and the value is the handler to be bound to that
        name.
        """
        
        for name in function_dict.keys():
            func = function_dict[name]
            self.register_function(func, name, pass_connection_info)

    def UnregisterFunctions(self, function_list):
        """
        Unregister these functions as SOAP handler methods.
        """
        
        for name in function_list:
            self.UnregisterFunction(name)

    def RegisterFunction(self, function, name = None,
                          pass_connection_info = 0):
        """
        Register a function to respond to SOAP requests.

        The optional name argument can be used to set a Unicode name
        for the function.

        If an instance is also registered then it will only be called
        if a matching function is not found.
        
        """

        if name is None:
            name = function.__name__

        # print "Service %s registers function %s as %s" % (self, function, name)

	wrapper = AccessControl.InvocationWrapper(function,
                                                  pass_connection_info, self)
        self.function_map[name] = (wrapper, 1)

        # self.function_map[name] = (function, pass_connection_info)

    def UnregisterFunction(self, name):
        """
        Unregister a function so it gets no more SOAP requests.
        """

        print "Service %s unregisters %s" % (self, name)

        if self.function_map.has_key(name):
            del self.function_map[name]

    def _lookup_method(self, method):
        """
        Look up method in the local method table.

        Returns the tuple (method_function, pass_connection_info)
        where method_function is the Python callable that was registered and
        pass_connection_info is true if the registered function desires
        to get connection-level information passed to it.
        """

        # print "Lookup method ", method

        func = None
        try:
            func, pass_connection_info = self.function_map[method]
            # print "Found func ", func

        except KeyError:
            pass

        # print "Service %s mapped %s to %s" % (self, method, func)

        if func is None:
            raise NoServiceMethodException()
        
        return func, pass_connection_info

    def _IsValid(self):
        """
        Method that just returns true.

        Used in the implementation of Client.Handle.IsValid().

        """

        return 1

    def _Implements(self, method):
        """
        Returns True if method is implemented here.

        Used in the implementation of Client.Handle.Implements().

        """

        try:
            info = self.function_map[method]
            return callable(info[0])
        except:
            return 0


    #
    # Mappings for different naming styles.
    #

    get_path = GetPath
    get_handle = GetHandle
    register_functions = RegisterFunctions
    register_function = RegisterFunction
