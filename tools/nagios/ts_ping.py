#!/usr/bin/python2

#
# This script will ping the specified text service to
# determine its upness
#
# Exit status:
# 0 - success
# 1 - timed out
# 2 - connection failure
# 3 - unknown failure (the exception prints)

import os
import sys
import time
import threading
from Queue import Queue
from optparse import Option

from AccessGrid import Toolkit
from AccessGrid.GUID import GUID
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.TextClient import TextClient,TextClientConnectException

app = Toolkit.CmdlineApplication()

hostOption = Option("--host", dest="host", metavar="HOST",
	           default="localhost", 
		   help="hostanme the event service.")
app.AddCmdLineOption(hostOption)
portOption = Option("--port", dest="port", metavar="PORT", type="int",
	           default=8002, 
		   help="port of the event service.")
app.AddCmdLineOption(portOption)
channelOption = Option("--channel", dest="channel", metavar="CHANNEL",
	           default="Test", 
		   help="channel of the event service.")
app.AddCmdLineOption(channelOption)
countOption = Option("--count", dest="count", metavar="COUNT",
	           default=3, 
		   help="number of times to test.")
app.AddCmdLineOption(countOption)
timeoutOption = Option("-t", "--timeout", dest="timeout", 
                   metavar="TIMEOUT", default=10,
		   help="timeout before ping fails.")
app.AddCmdLineOption(timeoutOption)

try:
    app.Initialize("TextServiceTest")
except Exception, e:
    print "Exception initializing, ", e
    sys.exit(-1)

host = app.GetOption("host")
port = app.GetOption("port")
channel = app.GetOption("channel")
count = app.GetOption("count")
timeout = app.GetOption("timeout")

ret = 0
done = threading.Event()
queue = Queue()

def ping(host,port,count):
    try:
        # Create the text client
        profile = ClientProfile()
        textClient = TextClient(profile, (host, port))

        # Connect and send
        privId = str(GUID())
        textClient.Connect(channel, privId)
#         pubId = profile.GetPublicId()
#         for i in range(count):
#             textClient.Input("%s -- %d" % (pubId, i))
        queue.put(0)
    except TextClientConnectException, e:
        print "EXCEPTION in text", sys.exc_type, sys.exc_value
        queue.put(2)
    except:
        print sys.exc_type, sys.exc_value
        queue.put(3)
        
    done.set()

start = time.time()

# Start the pinging thread
threading.Thread(target=ping,args=[host,port,count]).start()

# Wait the specified time
while(time.time() - start < timeout  and not done.isSet() ):
    time.sleep(1)

# Set return value
if done.isSet():
    ret = queue.get()
else:
    ret = 1
    
print "ts_ping returning", ret
os._exit(ret)
