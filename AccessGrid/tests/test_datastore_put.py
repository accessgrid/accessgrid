import sys
import re
from AccessGrid import Log

hdlr = Log.StreamHandler())
hdlr.setLevel(Log.DEBUG)
Log.HandleLoggers(Log.StreamHandler(), Log.GetDefaultLoggers())

sys.path.append(r"c:\home\olson\ag\dev\AccessGrid")

from  AccessGrid import DataStore

defaultURL = "https://localhost:9011/test"

if len(sys.argv) > 1:
    url = sys.argv[1]
else:
    url = defaultURL
    

files = [
     r"c:\temp\tarfile-0.6.5.zip",
         r"c:\boot.ini",
         r"c:\Program Files\Inno Setup 3\whatsnew.htm",
#         r"file name with spaces.txt",
#         r"c:\home\olson\ag\dev\AccessGrid\AccessGrid\put.py",
#          r"c:\temp\put.py",
         r"c:\home\olson\docs\AG\ag-2-design\datastore-simplified.doc"]

if re.search("^https:", url):
    x = DataStore.GSIHTTPUploadFiles(url, files, None)
elif re.search("^http:", url):
    x = DataStore.HTTPUploadFiles("ME", url, files, None)


