#!/usr/bin/env python

# Standard Python library
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
    def __init__(self,path,ssl_ctx,hostname=None,port=9021,dataports=None,authorizecb=None,activitycb=None):
        log.debug('  FTPSServer __init__: path=%s hostname=%s port=%s', 
                    path, hostname,port)
        self.path = path
        self.ssl_ctx = ssl_ctx
        self.hostname = hostname
        self.port = int(port)
        self.dataports = dataports
        self.authorizecb = authorizecb
        self.activitycb = activitycb
        self.timeout = 5
        
        self.ftps = None
        self.running = threading.Event()
        
    def run(self):
        '''
        Run the server
        '''
        log.debug('Entered FTPSServer.run')

        self.running.set()
        
        fauthz = authorizer(self.path,self.authorizecb)
        self.ftps = ftps_server.ftp_tls_server(fauthz, self.ssl_ctx, 
                                               port=self.port,
                                               dataports=self.dataports,
                                               callback=self.activitycb,
                                               log_obj=log)
        while self.running.isSet():
            try:
                asyncore.poll(self.timeout,asyncore.socket_map)
            except:
                log.exception('exception in FTPS server main loop')
        
    def run_in_thread(self):
        '''
        Run the server in a thread
        '''
        log.debug('Entered FTPSServer.run_in_thread')
        t = threading.Thread(name='ftps server',target=self.run)
        t.start()
        
    def stop(self):
        '''
        Stop the server
        '''
        log.debug('Entered FTPSServer.stop')
        self.running.clear()
        
    def GetUploadDescriptor(self,prefix):
        '''
        Get the upload URL for the server
        '''
        log.debug('Entered FTPSServer.GetUploadDescriptor')
        descriptor = '%s://%s:%d/%s' % ('ftps',
                                                 self.hostname,
                                                 self.port,
                                                 prefix)
        log.debug('  descriptor = %s', descriptor)
        return descriptor
                                                 
    def GetDownloadDescriptor(self, prefix, fil):
        '''
        Get the download descriptor for the specified file
        '''
        log.debug('Entered FTPSServer.GetDownloadDescriptor')
        descriptor = urlparse.urlunparse(("ftps",
                                    "%s:%d" % (self.hostname,
                                               self.port),
                                    "%s/%s" % (prefix, urllib.quote(fil)),
                                    "", "", ""))
        log.debug('  descriptor = %s', descriptor)
        return descriptor
                                    
        

if __name__ == '__main__':
    from M2Crypto.SSL import Context
    import socket
    
    ssl_ctx = Context('sslv23')
    ssl_ctx.load_cert('server.pem')
    # cheat to get the ca cert dir
    if sys.platform == 'win32':
        caDir = r'c:\\program files\\AGTk-2.4\\Config\CAcertificates'
    elif sys.platform == 'linux2':
        caDir = '/etc/AccessGrid/Config/CAcertificates'
    elif sys.platform == 'darwin':
        caDir = '/Applications/AccessGridToolkit.app/Contents/Resources/Config/CAcertificates/'
    else:
        print 'Unrecognized platform: ', sys.platform
        sys.exit(1)
    ssl_ctx.load_verify_locations(capath=caDir)
    ssl_ctx.set_cipher_list('LOW:TLSv1:@STRENGTH')
    ssl_ctx.set_verify(SSL.verify_peer,10)
    ssl_ctx.set_session_id_ctx('127.0.0.1:8006')
    
    def authorize(channel,user,passw):
        return 1
        
    root = sys.argv[1]
    port = sys.argv[2]
    
    hostname = socket.gethostbyname(socket.gethostname())
    print 'Server at: ftps://%s:%s, server dir %s' % ( hostname, port, root)
    
    ftps = FTPSServer(root,ssl_ctx,port=port,authorizecb=authorize)
    ftps.run()
    

    
    
    
        
    


