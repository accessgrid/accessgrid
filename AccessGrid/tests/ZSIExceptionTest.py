#!/usr/bin/python

import sys
import socket
from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.interfaces.Venue_client import VenueIW

from AccessGrid.hosting import HostingException
from AccessGrid.hosting import GetHostingExceptionModuleAndClassName, ReraiseHostingException, GetHostingException, NotAuthorized, NoSuchService

app = CmdlineApplication.instance()
app.Initialize("ServiceTest")

try:
    url = sys.argv[1]
except:
    url = "https://localhost:8000/Venues/defa" # last letter is missing so an exception is raised

proxy = VenueIW(url)

try:
    desc = proxy.AsVenueDescription()
    print "Description:?", desc
except HostingException, e:
    #print e
    print "++++"
    print GetHostingExceptionModuleAndClassName(e)
    print "===="
    print GetHostingException(e)
    print "****"
    try:
        ReraiseHostingException(e)
    except NotAuthorized, e:
        print "caught reraised NotAuthorized exception"
    except NoSuchService, e:
        print "caught reraised NoSuchService exception"
    except Exception, e:
        print "caught reraised exception (did not match exception explicitly)" + str(e.__class__), e
except socket.error, e:
    print "Socket error:", e
    try:
        if 111 == e.args[0]:
            print "Unable to run this test.  Make sure the host, port, and protocol (i.e. https://localhost:8000) are correct in the following url:", url
    except:
        pass
except Exception, e:
    print "Didn't catch:", e
    print "HostingException", HostingException
    
