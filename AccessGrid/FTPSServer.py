#!/usr/bin/env python

# Standard Python library
import os
import sys
import threading
import urlparse
import urllib
import asyncore

# Medusa 
from FTPS import filesys
from FTPS import ftps_server

# M2Crypto
from M2Crypto import Rand, SSL

from AccessGrid import Log
log = Log.GetLogger('FTPSServer')
Log.SetDefaultLevel('FTPSServer', Log.DEBUG)

class authorizer:
    def __init__ (self, root='/',authorizecb=None):
        self.root = root
        self.authorizecb = authorizecb
        
    def authorize (self, channel, username, password):

        channel.read_only = 0
        if self.authorizecb and self.authorizecb(channel,username,password):
            return 1, 'Ok.', filesys.os_filesystem (self.root)
        else:
            return 0, 'Connection rejected.', None

class FTPSServer:
    '''
    FTPS Server wrapper
    '''
    def __init__(self,path,ssl_ctx,hostname=None,port=9021,authorizecb=None,activitycb=None):
        self.path = path
        self.ssl_ctx = ssl_ctx
        self.hostname = hostname
        self.port = int(port)
        self.authorizecb = authorizecb
        self.activitycb = activitycb
        self.timeout = 5
        
        self.ftps = None
        self.running = threading.Event()
        
    def run(self):
        '''
        Run the server
        '''
        self.running.set()
        
        fauthz = authorizer(self.path,self.authorizecb)
        self.ftps = ftps_server.ftp_tls_server(fauthz, self.ssl_ctx, port=self.port,callback=self.activitycb)
        while self.running.isSet():
            asyncore.poll(self.timeout,asyncore.socket_map)
        
    def run_in_thread(self):
        '''
        Run the server in a thread
        '''
        t = threading.Thread(name='ftps server',target=self.run)
        t.start()
        
    def stop(self):
        '''
        Stop the server
        '''
        self.running.clear()
        
    def GetUploadDescriptor(self,prefix):
        '''
        Get the upload URL for the server
        '''
        uploadDescriptor = '%s://%s:%d/%s' % ('ftps',
                                                 self.hostname,
                                                 self.port,
                                                 prefix)
        return uploadDescriptor
                                                 
    def GetDownloadDescriptor(self, prefix, fil):
        '''
        Get the download descriptor for the specified file
        '''
        return urlparse.urlunparse(("ftps",
                                    "%s:%d" % (self.hostname,
                                               self.port),
                                    "%s/%s" % (prefix, urllib.quote(fil)),
                                    "", "", ""))
                                    
        

if __name__ == '__main__':
    from M2Crypto.SSL import Context
    
    ssl_ctx = Context('sslv23')
    ssl_ctx.load_cert('server.pem')
    caDir = os.path.join(os.environ['HOME'],'.AccessGrid','Config','trustedCACerts')
    ssl_ctx.load_verify_locations(capath=caDir)
    
    def authorize(channel,user,passw):
        return 1
    
    ftps = FTPSServer('/tmp',ssl_ctx,port=39021,authorizecb=authorize)
    ftps.run()
    

    
    
    
        
    


