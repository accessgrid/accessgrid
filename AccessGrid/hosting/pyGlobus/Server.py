#-----------------------------------------------------------------------------
# Name:        Server.py
# Purpose:     
#
# Author:      Robert D. Olson
#
# Created:     2003/29/01
# RCS-ID:      $Id: Server.py,v 1.9 2003-02-14 20:51:38 olson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket
from threading import Thread

import ServiceObject
import ServiceBase
import Utilities

from AGGSISOAP import SOAPProxy, SOAPServer, SOAPConfig

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

        if server_auth_callback is None:
            attr = Utilities.CreateTCPAttrAlwaysAuth()
        else:
            attr = Utilities.CreateTCPAttrCallbackAuth(server_auth_callback)

        config = SOAPConfig()
        config.debug = debug
        config.returnFaultInfo = 1
        config.dumpFaultInfo = 1
        self._server = SOAPServer(('localhost', port),
                                  tcpAttr = attr,
                                  log = 0,
                                  config = config)

    def Run(self):
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
        
    def RunInThread(self):
        """
        Start the server in a new thread.

        This method causes the server to begin listening for and
        processing incoming messages in a new message-handling thread. It
        returns immediately.
        """

        server_thread = Thread(target = self.run)
        server_thread.start()

    def Stop(self):
        self._running = 0

    def CreateService(self, service_class, 
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

    def CreateServiceObject(self, pathId = None):
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

    def AllocateId(self):
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

#        print "Server %s: Dispatch %s via path %s" % (self, method, path)
        try:
            service = self._path_map[path]
#            print "Got service ", service
            m = service._lookup_method(method)
#            print "Got method ", m
            return m
        except KeyError:
            # print "service not found"
            raise NoServiceException
        except Exception, e:
             "Other exception ", e

    def GetConnectionInfo(self, connection):
        return Utilities.SecureConnectionInfo(connection.get_security_context())

    def GetPort(self):
        """Return the port on which this server is listening. """
        return self._server.port

    def GetURLBase(self):
        """Return the base URL that represents this server. """

        hostname = Utilities.GetHostname()
        return "https://%s:%s" % (hostname, self.get_port())

    #
    # Mappings for different naming styles.
    #

    run = Run
    run_in_thread = RunInThread
    stop = Stop
    create_service = CreateService
    create_service_object = CreateServiceObject
    allocate_id = AllocateId
    get_port = GetPort
    get_url_base = GetURLBase
