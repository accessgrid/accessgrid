#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueServerRegistry.py
# Purpose:     This is a registry for venues services.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenuesServerRegistry.py,v 1.4 2004-02-24 21:21:48 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

# Standard stuff

                         
if __name__ == "__main__":
    from AccessGrid.hosting import SecureServer as Server
    from AccessGrid.VenueServerRegistry import VenueServerRegistry
    import ConfigParser

    hostingEnvironment = Server.Server(8800)
    venueServerRegistryService = hostingEnvironment.registerObject(VenueServerRegistry)

    print "Service running at: %s" % venueServerRegistryService.get_handle()

    hostingEnvironment.run()    
