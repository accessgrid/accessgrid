#-----------------------------------------------------------------------------
# Name:        broadcaster.py
# Purpose:     
# Created:     2005/05/01
# RCS-ID:      $Id: broadcaster.py,v 1.1 2005-01-08 04:19:14 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
This program delivers .sdp files via http. It also starts up multicast
to unicast bridges to deliver the content that's described by the sdp
file.
"""
import os
import shutil

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

class BroadcasterRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # The address of the other end of the client is self.client_address
        # which is a tuple (address, port)
        fname = self.path[1:]
        if os.path.exists(fname):
            f = open(fname)
            self.send_response(200)
            self.send_header("Content-type", "application/sdp")
            self.send_header("Content-Length", str(os.fstat(f.fileno())[6]))
            self.end_headers()
            shutil.copyfileobj(open(self.path[1:]), self.wfile)
        else:
            self.send_error(404, "File %s not found" % fname)

    def log_message(self, format, *args):
        pass
    
server = HTTPServer(('', 9999), BroadcasterRequestHandler)
server.serve_forever()
