#!/usr/bin/python2
#
import sys
from optparse import Option

from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.VenueServer import VenueServerIW

app = CmdlineApplication()

urlOption = Option("-u", "--url", dest="url", default=None,
		   help="URL to the server you want to shut down.")

app.AddCmdLineOption(urlOption)

try:
    args = app.Initialize("StopServer")
except Exception, e:
    print "Exception initializing toolkit:", e
    sys.exit(-1)

url = app.GetOption("url")
server = VenueServerIW(url)
server.Shutdown(0)
