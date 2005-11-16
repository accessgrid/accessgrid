#-----------------------------------------------------------------------------
# Name:        unittest_ftps.py
# Purpose:     
#
# Author:      Tom Uram
#   
# Created:     2003/05/14
# RCS-ID:      $Id: unittest_ftps.py,v 1.2 2005-11-16 22:52:23 turam Exp $
# Copyright:   (c) 2005
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import unittest


import time
import shutil
import os
import sys
import socket
import stat
import threading
import signal 

from M2Crypto import SSL, ftpslib, threading as m2threading
from AccessGrid.FTPSClient import FTPSUploadFile, FTPSDownloadFile
from AccessGrid.FTPSServer import FTPSServer

#  start server
host = socket.gethostbyname(socket.gethostname())
port = 9090
if sys.platform in ['linux2','darwin']:
    path = '/tmp'
else:
    path = os.environ['TEMP']
serverUrl = 'ftps://%s:%d' % (host,port)



pid = None
def StartProcess():
    global host,port,path,serverUrl,pid

    pid= os.spawnv(os.P_NOWAIT,
                   sys.executable,
                   [sys.executable,
                   '../AccessGrid/FTPSServer.py',
                    path,
                    str(port)])

def StopProcess():
    global pid
    if pid:
        os.kill(pid,signal.SIGKILL)

threading.Thread(target=StartProcess).start()
time.sleep(1)



class TestCase(unittest.TestCase):
    def __init__(self,*args):
    
        unittest.TestCase.__init__(self,*args)
        
        
        # define files to use for test
        self.fileToUpload = sys.argv[0]
        self.remotefilename = os.path.split(self.fileToUpload)[-1]
        self.remotefile = os.path.join(path,self.remotefilename)
        self.downloadUrl = '/'.join([serverUrl,self.remotefilename])
        self.downloadedFile = 'downloaded'
        self.filesize = os.stat(self.fileToUpload)[stat.ST_SIZE]
        
        # ensure clean state
        if os.path.exists(self.remotefile):
            os.remove(self.remotefile)
        if os.path.exists(self.downloadedFile):
            os.remove(self.downloadedFile)
        

    def test1Upload(self):
        print 'testUpload'
        FTPSUploadFile(self.fileToUpload,serverUrl)
        
        uploadedfilesize = os.stat(self.remotefile)[stat.ST_SIZE]
        print 'localfile [%s] remotefile [%s]' % (self.filesize,uploadedfilesize)            
        assert(self.filesize == uploadedfilesize)

    def test2Download(self):
        print 'testDownload'
        
        def cb(percent,done):
            pass#print percent
            
        # Download
        for i in range(100):
            FTPSDownloadFile(self.downloadUrl,
                         self.downloadedFile,
                         progressCB=cb)
                         
                         
            downloadedfilesize = os.stat(self.downloadedFile)[stat.ST_SIZE]
            #print 'remotefile [%s] localfile [%s]' % (self.filesize,downloadedfilesize)            
            assert(downloadedfilesize == self.filesize)
        
    def test99KillServer(self):
        StopProcess()


def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(TestCase)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    m2threading.init()
    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')
    m2threading.cleanup()

