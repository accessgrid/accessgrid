import sys
import re

from AccessGrid.DataStore import GSIHTTPDownloadFile, HTTPDownloadFile

defaultURL = 'https://localhost:9011/test/JunoSetup.exe'

if len(sys.argv) > 1:
    url = sys.argv[1]
else:
    url = defaultURL
    
if re.search("^https:", url):
    GSIHTTPDownloadFile(url, r"\temp\foo.txt", None, None)
elif re.search("^http:", url):
    HTTPDownloadFile("ME", url, r"\temp\foo.txt", None, None)

