#!/usr/bin/python2
#
# This script will ping the specified event service to
# determine its upness
#
# Exit status:
# 0 - success
# 1 - timed out
# 2 - unknown failure (the exception prints)

import sys, os, time, threading
from Queue import Queue
from optparse import Option

from AccessGrid import Toolkit
from AccessGrid.Venue import VenueIW

app = Toolkit.CmdlineApplication()
urlOption = Option("-u", "--url", dest="url", metavar="URL",
	           default="https://localhost:8000/Venues/default", 
		   help="url to the venue to tset the event service.")
app.AddCmdLineOption(urlOption)
countOption = Option("--count", dest="count", metavar="COUNT",
	           default=3, 
		   help="number of times to test.")
app.AddCmdLineOption(countOption)
timeoutOption = Option("-t", "--timeout", dest="timeout", 
                   metavar="TIMEOUT", default=10,
		   help="timeout before ping fails.")
app.AddCmdLineOption(timeoutOption)

try:
    app.Initialize("SOAPServiceTester")
except Exception, e:
    print "Error initializing application."
    sys.exit(-1)

url = app.GetOption("url")
count = app.GetOption("count")
timeout = app.GetOption("timeout")

ret = 0
done = threading.Event()
queue = Queue()

def ping(url,count):
    proxy = VenueIW(url)
    try:
        if proxy._IsValid():
            ret = 0
    except Exception, e:
        print sys.exc_type, sys.exc_value
        ret = 2
    queue.put(ret)
    done.set()

start = time.time()

# Start the pinging thread
threading.Thread(target=ping,args=[url,count]).start()

# Wait the specified time
while(time.time() - start < timeout  and not done.isSet() ):
    time.sleep(1)

# Set return value
if done.isSet():
    ret = queue.get()
else:
    ret = 1
    
print "vs_ping returning", ret
os._exit(ret)
