#-----------------------------------------------------------------------------
# Name:        TestVenueManagementClient.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2002/17/12
# RCS-ID:      $Id: TestVenueManagementClient.py,v 1.1 2002-12-17 22:45:46 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from AccessGrid.hosting.pyGlobus import Client

VenueManagementSvc = Client.Handle('https://localhost:8000/100').get_proxy()

VenueManagementSvc.GetDefaultVenue()