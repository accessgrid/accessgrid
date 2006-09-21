#!/usr/bin/env python


import os
import sys
import urlparse
import stat

# add ftps to the list of protocols recognized by urlparse
# as using a network location (allows urlparse to parse
# ftps urls correctly)
urlparse.uses_netloc.append('ftps')

from AccessGrid import Log
log = Log.GetLogger('FTPSClient')
Log.SetDefaultLevel('FTPSClient', Log.DEBUG)


from M2Crypto import SSL, ftpslib, threading

# module defaults
DEFAULT_PROTOCOL = 'sslv23'


class UserCancelled(Exception): pass


bytes_received = 0
    
def FTPSDownloadFile(url,destination,
                     ssl_ctx=None,user=None,passw=None,
                     progressCB=None):
    """
    Download from the specified URL, storing the resulting file
    in the specified destination
    """
    log.debug('Entered FTPSDownloadFile: url=%s destination=%s',
                url, destination)

    if ssl_ctx is None:
        ssl_ctx = SSL.Context(DEFAULT_PROTOCOL)
    if user is None:  user = 'connectionid'
    if passw is None: passw = 'privateid'
    
    url = str(url)

    try:
        def cb(data,size,fl):
            try:
              global bytes_received
              fl.write(data)
              bytes_received += len(data)
              if progressCB:
                  cancelled = progressCB(float(bytes_received)/size,0)
                  if cancelled:
                      raise UserCancelled('User cancelled download')
            except UserCancelled:
              raise
            except:
              log.exception('Error in FTPSDownloadFile data callback')
              raise

        # parse url
        parts = urlparse.urlparse(url)
        hostport = parts[1]
        host,port=hostport.split(':')
        port = int(port)

        pathtofile = parts[2]

        # create ftp session
        f = ftpslib.FTP_TLS(ssl_ctx=ssl_ctx)
        #f.set_debuglevel(2)

        # connect to server and config connection
        f.connect(host,port)
        f.auth_tls()
        f.set_pasv(1)  
        f.prot_p()
        
        # login to server
        f.login(user,passw)

        # get file size
        siz = f.size(pathtofile)

        # open destination file and retrieve file contents
        fl = file(destination,'wb')
        callback = lambda data,size=siz,fp=fl: cb(data,size,fp)
        lin = f.retrbinary('retr %s' % pathtofile,callback)
        log.debug(lin)

        # transfer finished; close up
        if progressCB:
            progressCB(siz,1)
        fl.close()
        f.quit()
    except UserCancelled:
        raise
    except:
        log.exception('Error in FTPSDownloadFile')
        raise
        
class FileWrapper(file):

    def __init__(self,filename,mode,progressCB):
        file.__init__(self,filename,mode)
        self.filename = filename
        self.progressCB = progressCB
        
        self.size = os.stat(filename)[stat.ST_SIZE]
        self.bytesread = 0
        
    def read(self,numbytes):
        buf = file.read(self,numbytes)
        self.bytesread += len(buf)
        if self.progressCB:
            try:
                if self.size != 0:
                    cancelled = self.progressCB(self.filename,
                                float(self.bytesread)/float(self.size),
                                self.size,
                                0,0)
                    if cancelled:
                        raise UserCancelled('User cancelled upload')
            except UserCancelled:
                raise
            except:
                log.exception('Exception in progress callback')
        return buf
        
    
def FTPSUploadFile(localfile,url,
                   ssl_ctx=None,user=None,passw=None,
                   progressCB=None):
    """
    Upload the specified file to the specified URL
    """

    log.debug('Entered FTPSUploadFile: localfile=%s url=%s',
                localfile, url)

    if ssl_ctx is None:
        ssl_ctx = SSL.Context(DEFAULT_PROTOCOL)
    if user is None:  user = 'connectionid'
    if passw is None: passw = 'privateid'
    
    try:
        # parse url
        parts = urlparse.urlparse(url)
        hostport = parts[1]
        host,port=hostport.split(':')
        port = int(port)

        # create ftp session
        f = ftpslib.FTP_TLS(ssl_ctx=ssl_ctx)
        #f.set_debuglevel(2)
        
        # connect and login
        f.connect(host,port)
        f.auth_tls()
        f.set_pasv(1)  
        f.prot_p()
        f.login(user,passw)
        
        # open local file and transfer file
        fl = FileWrapper(localfile,'rb',progressCB)

        # change to target directory
        f.voidcmd('cwd %s' % str(parts[2]))
        
        # upload the file
        remotefile = os.path.split(localfile)[-1]
        lin = f.storbinary('stor %s' % remotefile, fl)
        log.debug(lin)
        
        if progressCB:
            try:
                progressCB(localfile,
                       1,
                       fl.size,
                       1,0)
            except:
                log.exception('Error in progress callback')
        
        # transfer finished; close up
        fl.close()
        f.quit()
        
    except UserCancelled:
        raise
    except:
        log.exception('Error in FTPSUploadFile')
        raise
    

if __name__ == '__main__':
    import time
    import shutil
    
    
    threading.init()
    
    def cb(percentDone,done):
        import time
        if percentDone >100:
            return
        num = int(percentDone * 10)
        print '-'*num,'\r',
        
    serverUrl = 'ftps://localhost:39021'
    if len(sys.argv) > 1:
        serverUrl = sys.argv[1]
        

    # set up test
    if sys.platform == 'win32':
        tmpdir = os.environ['TEMP']
    elif sys.platform in ['linux2','darwin']:
        tmpdir = '/tmp'
    fileToUpload = 'upload'
    uploadedFile = os.path.join(tmpdir,fileToUpload)
    downloadedFile = 'download'
    downloadsuccess = uploadsuccess = 0
    
    # - copy this file to a local file
    shutil.copyfile(sys.argv[0],fileToUpload)

    # - remove the file from the (presumed) ftp dir
    if os.path.exists(uploadedFile):
        os.remove(uploadedFile)
        
    # - remove the target download file
    if os.path.exists(downloadedFile):
        os.remove(downloadedFile)
    
        
    # Upload
    url = serverUrl
    print 'uploading', fileToUpload, 'to', url
    FTPSUploadFile(fileToUpload,url)

    # Compare local and uploaded files
    if os.path.exists(fileToUpload):
        f1 = file(fileToUpload).read()
        f2 = file(uploadedFile).read()
        if f1 == f2:
            uploadsuccess = 1
                
    if uploadsuccess:
        print "UPLOAD SUCCESS"
    else:
        print "UPLOAD FAILURE"
    
    
    # Download
    url = serverUrl + '/' + fileToUpload
    print 'downloading', url, 'to',downloadedFile
    FTPSDownloadFile(url,downloadedFile,progressCB=cb)
    
    # Compare remote and downloaded files
    if os.path.exists(downloadedFile):
        f1 = file(uploadedFile).read()
        f2 = file(downloadedFile).read()
        if f1 == f2:
            downloadsuccess = 1

    if downloadsuccess:
        print "DOWNLOAD SUCCESS"
    else:
        print "DOWNLOAD FAILURE"

    threading.cleanup()

