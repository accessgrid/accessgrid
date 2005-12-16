#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        AGXMLRPCServer.py
# Purpose:     Basic python xmlrpc server with minor modifications.  Also
#                includes an async xmlrpc server.
# Created:     2005/12/16
# RCS-ID:      $Id: AGXMLRPCServer.py,v 1.1 2005-12-16 20:40:47 eolson Exp $
# Copyright:   (c) 2005,2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
__revision__ = "$Id: AGXMLRPCServer.py,v 1.1 2005-12-16 20:40:47 eolson Exp $"

from DocXMLRPCServer import DocXMLRPCServer 
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler, SimpleXMLRPCDispatcher
import BaseHTTPServer
import socket
import traceback

class AGXMLRPCServer(DocXMLRPCServer):
    def __init__(self, addr, requestHandler=SimpleXMLRPCRequestHandler, logRequests=1):
        self.allow_reuse_address = True
        DocXMLRPCServer.__init__(self, addr, requestHandler=requestHandler, logRequests=logRequests)

class AsyncAGXMLRPCServer(AGXMLRPCServer):
    # Makes a callback at regular intervals.
    def __init__(self, addr, intervalSecs=1, callback=None, requestHandler=SimpleXMLRPCRequestHandler, logRequests=1):
        self.intervalSecs = intervalSecs
        self.callback = callback
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
                sock.settimeout(None)
                return (sock, addr)
            except socket.timeout:
                pass

            try:
                if self.callback != None:
                    self.callback()
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

