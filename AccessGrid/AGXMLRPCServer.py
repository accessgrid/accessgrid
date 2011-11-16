#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        AGXMLRPCServer.py
# Purpose:     Basic python xmlrpc server with minor modifications.  Also
#                includes an async xmlrpc server.
# Created:     2005/12/16
# RCS-ID:      $Id: AGXMLRPCServer.py,v 1.1 2011/11/16 05:08:03 chris Exp $
# Copyright:   (c) 2005,2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
__revision__ = "$Id: AGXMLRPCServer.py,v 1.1 2011/11/16 05:08:03 chris Exp $"

import sys
from DocXMLRPCServer import DocXMLRPCServer 
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler, SimpleXMLRPCDispatcher
import BaseHTTPServer
import socket
import traceback
import SocketServer

class AGXMLRPCServer(DocXMLRPCServer):
    def __init__(self, addr, requestHandler=SimpleXMLRPCRequestHandler, logRequests=1):
        self.allow_reuse_address = True
        DocXMLRPCServer.__init__(self, addr, requestHandler=requestHandler, logRequests=logRequests)

class AsyncAGXMLRPCServer(AGXMLRPCServer):
    # Makes a callback at regular intervals.
    def __init__(self, addr, intervalSecs=1, callback=None, requestHandler=SimpleXMLRPCRequestHandler, logRequests=1,clientTimeout=10):
        self.intervalSecs = intervalSecs
        self.callback = callback
        self.clientTimeout = clientTimeout
        AGXMLRPCServer.__init__(self, addr, requestHandler=requestHandler, logRequests=logRequests)

    def server_bind(self):
        #BaseHTTPServer.HTTPServer.server_bind(self)
        AGXMLRPCServer.server_bind(self)
        self.socket.settimeout(self.intervalSecs)
        self.running = True

    def get_request(self):
        while self.running:
            try:
                sock, addr = self.socket.accept()
                sock.settimeout(self.clientTimeout)
                return (sock, addr)
            except socket.timeout:
                pass

            # handle_timeout was introduced in python 2.6
            # in earlier python versions, call handle_timeout here to react to the timeout exception above
            if sys.version_info < (2,6):
                self.handle_timeout()

    def handle_timeout(self):
            try:
                if self.callback != None:
                    self.callback()
            # Allow keyboard interrupts to stop the server
            except KeyboardInterrupt:
                traceback.print_exc()
                raise KeyboardInterrupt
            except:
                traceback.print_exc()

    def run(self):
        self.running = True
        while self.running:
            try:
                self.handle_request()
            except KeyboardInterrupt:
                print "Caught keyboard interrupt.  Exiting."
                self.running = False
            except:
                traceback.print_exc()

    def stop(self):
        self.running = False

class AsyncAGXMLRPCServerThreaded(SocketServer.ThreadingMixIn,AsyncAGXMLRPCServer):
    pass
