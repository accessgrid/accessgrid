#-----------------------------------------------------------------------------
# Name:        TestVenueServerRegistry.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2002/18/12
# RCS-ID:      $Id: TestVenueServerRegistry.py,v 1.1 2002-12-18 05:20:46 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
from AccessGrid.hosting.pyGlobus import Server, ServiceBase
from AccessGrid.VenueServerRegistry import VenueServerRegistry
import ConfigParser

hostingEnvironment = Server.Server(8800)

venueServerRegistryService = hostingEnvironment.create_service(VenueServerRegistry)

print "Service running at: %s" % venueServerRegistryService.get_handle()

hostingEnvironment.run()
