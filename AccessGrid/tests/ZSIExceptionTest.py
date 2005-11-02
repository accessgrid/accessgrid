#!/usr/bin/python

import sys
from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.interfaces.Venue_client import VenueIW

from AccessGrid.hosting import HostingException
from AccessGrid.hosting import GetHostingExceptionModuleAndClassName, ReraiseHostingException, GetHostingException, NotAuthorized, NoSuchService

app = CmdlineApplication.instance()
app.Initialize("ServiceTest")

try:
    url = sys.argv[1]
except:
    url = "https://localhost:8000/Venues/defaul" # last letter is missing so an exception is raised

proxy = VenueIW(url)

try:
    print "Description:?", proxy.AsVenueDescription()
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
except Exception, e:
    print "Didn't catch:", e
    print "HostingException", HostingException
    
