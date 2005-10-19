#!/usr/bin/env python


import os
import sys
import urlparse

# add ftps to the list of protocols recognized by urlparse
# as using a network location (allows urlparse to parse
# ftps urls correctly)
urlparse.uses_netloc.append('ftps')

from M2Crypto import SSL, ftpslib, threading

# module defaults
DEFAULT_PROTOCOL = 'sslv23'


bytes_received = 0
    
def FTPSDownloadFile(url,destination,size=None,checksum=None,
                     ssl_ctx=None,user=None,passw=None,
                     progressCB=None):
    """
    Download from the specified URL, storing the resulting file
    in the specified destination
    """

    if ssl_ctx is None:
        ssl_ctx = SSL.Context(DEFAULT_PROTOCOL)
    if user is None:  user = 'connectionid'
    if passw is None: passw = 'privateid'
    
    url = str(url)

    try:
        bytes_received = 0
        def cb(data,size,fl):
          try:
            global bytes_received
            fl.write(data)
            bytes_received += len(data)
            if progressCB:
                progressCB(float(bytes_received)/size,0)
          except:
            import traceback
            traceback.print_exc()

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

        # transfer finished; close up
        if progressCB:
            progressCB(siz,1)
        fl.close()
        f.quit()
    except:
        import traceback
        traceback.print_exc()
    
def FTPSUploadFile(localfile,url,size=None,checksum=None,
                   ssl_ctx=None,user=None,passw=None):
    """
    Upload the specified file to the specified URL
    """

    if ssl_ctx is None:
        ssl_ctx = SSL.Context(DEFAULT_PROTOCOL)
    if user is None:  user = 'connectionid'
    if passw is None: passw = 'privateid'
    
    try:
        # parse url
        parts = urlparse.urlparse(url)
        hostport = parts[1]
        print parts, hostport
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
        fl = file(localfile,'r')

        # change to target directory
        f.voidcmd('cwd %s' % str(parts[2]))
        
        # upload the file
        remotefile = localfile.split('/')[-1]
        f.storbinary('stor %s' % remotefile, fl)
        
        # transfer finished; close up
        fl.close()
        f.quit()
    except:
        import traceback
        traceback.print_exc()
    

if __name__ == '__main__':
    import time
    import shutil
    import os
    
    
    threading.init()
    
    def cb(percentDone,done):
        import time
        if percentDone >100:
            return
        num = int(percentDone * 10)
        print '-'*num,'\r',
        

    # set up test
    fileToUpload = 'upload'
    uploadedFile = os.path.join('/tmp',fileToUpload)
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
    
    url = 'ftps://localhost:39021/patch'
        
    # Upload
    url = 'ftps://localhost:39021/'
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
    url = 'ftps://localhost:39021/' + fileToUpload
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

