#-----------------------------------------------------------------------------
# Name:        VenueServerRegistry.py
# Purpose:     This is a registry for venues services.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenuesServerRegistry.py,v 1.1 2003-01-24 04:36:20 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

# Standard stuff

                         
if __name__ == "__main__":
    from AccessGrid.hosting.pyGlobus import Server, ServiceBase
    from AccessGrid.VenueServerRegistry import VenueServerRegistry
    import ConfigParser

    hostingEnvironment = Server.Server(8800)
    venueServerRegistryService = hostingEnvironment.create_service(VenueServerRegistry)

    print "Service running at: %s" % venueServerRegistryService.get_handle()

    hostingEnvironment.run()    
