#-----------------------------------------------------------------------------
# Name:        test_ServiceVersion.py
# Purpose:     
#
# Author:      Eric Olson
#
# Created:     2003/09/02
# RCS-ID:      
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
from AccessGrid.hosting.pyGlobus import Client
import sys

"""
All arguments for this test should be service urls.
If there are no arguments, this test assumes a default venue
server is running and checks the Version at the default
location for VenueServer and Venue.
"""

if __name__ == "__main__":       

    url_list = []

    for arg in sys.argv[1:]:
        url_list.append(arg)

    if len(url_list) < 1:
        url_list = ["https://localhost:8000/VenueServer", "https://localhost:8000/Venues/default"]

    for url in url_list:
        proxy = Client.Handle(url).get_proxy()
        ver = proxy.GetAGTkVersion()
        print "Version:", ver, " for ", url

