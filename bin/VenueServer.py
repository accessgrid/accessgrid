#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
# Author:      Ivan R. Judson
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.2 2003-01-24 19:48:24 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from AccessGrid.hosting.pyGlobus import Server, ServiceBase
from AccessGrid.VenueServer import VenueServer
import sys

port = 8000
if len(sys.argv)>1:
    port = int(sys.argv[1])

# First thing we do is create a hosting environment
hostingEnvironment = Server.Server(port)

# Then we create a VenueServer, giving it the hosting environment
venueServer = VenueServer(hostingEnvironment)

# Then we create the VenueServer service
serviceObject = hostingEnvironment.create_service_object(pathId = 'VenueServer')
venueServer._bind_to_service(serviceObject)

# Some simple output to advertise the location of the service
print "Service running at: %s" % venueServer.get_handle()

# We start the execution
hostingEnvironment.run()

# Exit cleanly
sys.exit(0)
