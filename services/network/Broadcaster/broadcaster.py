#-----------------------------------------------------------------------------
# Name:        broadcaster.py
# Purpose:     
# Created:     2005/05/01
# RCS-ID:      $Id: broadcaster.py,v 1.2 2005-01-19 20:26:27 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
This program delivers .sdp files via http. It also starts up multicast
to unicast bridges to deliver the content that's described by the sdp
file.
"""
import os
import sys
import socket
import shutil
import threading
import time

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from bridge import RTPReceiver

global bcast

class BroadcasterRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bcast
        # The address of the other end of the client is self.client_address
        # which is a tuple (address, port)
        fname = self.path[1:]
        if os.path.exists(fname):
            f = open(fname)
            lines = f.readlines()
            my_ip = bcast.get_host()
            aport = bcast.get_aport()
            vport = bcast.get_vport()

            bcast.add_client(self.client_address[0])
            
            self.send_response(200)
            self.send_header("Content-type", "application/sdp")
            self.send_header("Content-Length", str(os.fstat(f.fileno())[6]))
            self.send_header("Connection", "close")
            self.end_headers()

            for line in lines:
                line = line.replace("MYIPADDR", str(my_ip))
                line = line.replace("MYAUDIOPORT", str(aport))
                line = line.replace("MYVIDEOPORT", str(vport))
#                print line[:-1]
                self.wfile.write(line[:-1])
        else:
            self.send_error(404, "File %s not found" % fname)

    def log_message(self, format, *args):
        pass

class Broadcaster:
    def __init__(self, audio_addr, a_port, video_addr, v_port, http_port):
        self.audio_addr = audio_addr
        self.a_port = a_port
        self.video_addr = video_addr
        self.v_port = v_port
        self.http_port = http_port

        self.http = HTTPServer(('', http_port), BroadcasterRequestHandler)
        self.http_thread = threading.Thread(target=self.http.serve_forever,
                                            name="HTTP Thread")

        self.host = socket.gethostbyname(socket.gethostname())
        self.abridge = RTPReceiver(self.host, a_port)
        self.abridge.add_client(self.audio_addr, self.a_port, 1)
        
        self.vbridge = RTPReceiver(self.host, v_port)
        self.vbridge.add_client(self.video_addr, self.v_port, 1)

    def start(self):
        self.http_thread.start()
        self.abridge.start()
        self.vbridge.start()
        
    def stop(self):
        self.abridge.stop()
        self.vbridge.stop()
        self.http_thread.stop()

    def get_host(self):
        return self.host

    def get_aport(self):
        return self.a_port

    def get_vport(self):
        return self.v_port

    def add_client(self, addr):
        self.abridge.add_client(addr, int(self.a_port), 1)
        self.vbridge.add_client(addr, int(self.v_port), 1)
        
    def is_active(self):
        if self.vbridge.is_active() or self.abridge.is_active():
            return 1
        else:
            return 0

if __name__ == "__main__":
    global bcast
    bcast = Broadcaster("224.2.159.7", 57712,
                        "224.2.166.28", 64270, 9999)

    bcast.start()
    
    try:
        while bcast.is_active():
            time.sleep(2)
    except KeyboardInterrupt, k:
        print "Keyboard interrupt, quitting..."
        bcast.stop()
            

