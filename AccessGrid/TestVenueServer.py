#-----------------------------------------------------------------------------
# Name:        TestVenueServer.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2002/17/12
# RCS-ID:      $Id: TestVenueServer.py,v 1.2 2002-12-17 22:45:46 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
from AccessGrid.hosting.pyGlobus import Server, ServiceBase
from AccessGrid.VenueServer import VenueServer
import ConfigParser

hostingEnvironment = Server.Server(8000)

venueService = hostingEnvironment.create_service(VenueServer)

print "Service running at: %s" % venueService.get_handle()

hostingEnvironment.run()
