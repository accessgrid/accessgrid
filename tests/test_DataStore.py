import os, sys, md5
from DataStore import HTTPSUploadFiles, HTTPSDownloadFile
from DataStore import HTTPUploadFiles, HTTPDownloadFile
from AccessGrid import Toolkit

#
# Test DataStore
#

localFile = sys.argv[0]
progressCB = None


app = Toolkit.CmdlineApplication.instance()
app.Initialize('dstest')

if app.GetOption('secure'):
    protocol = 'https'
    Upload = HTTPSUploadFiles
    Download = HTTPSDownloadFile
else:
    protocol = 'http'
    Upload = HTTPUploadFiles
    Download = HTTPDownloadFile

uploadURL = '%s://localhost:9999/uniqueId' % (protocol,)

try:
    print "Uploading file from %s to %s" % (localFile,uploadURL)
    Upload('', uploadURL, [localFile], progressCB)
except Exception,e:
    print "Exception on upload: ", e

numsecs = 2
print "sleeping for %d secs..." % numsecs
import time
time.sleep(numsecs)

uri = os.path.join(uploadURL,localFile)
destFile = localFile + '.download'
size = os.path.getsize(localFile)
f = file(localFile)
localFileContent = f.read()
f.close()
checksum = md5.new(localFileContent).hexdigest()


try:
    print "Downloading file %s to %s" % (localFile,destFile)
    Download('', uri,destFile, size, checksum)
    print "Removing downloaded file"
    os.remove(destFile)
except Exception,e:
    print "Exception on download: ", e

