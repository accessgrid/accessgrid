#!/usr/bin/python2

import os, sys
from optparse import Option

from AccessGrid.Venue import VenueIW
from AccessGrid.Toolkit import CmdlineApplication

doc ="""
This program gets the stream information from the venue.
"""
# Initialize
app = CmdlineApplication()

urlOption = Option("-u", "--url", dest="url", default=None,
                   help="Specify a venue url on the command line.")
app.AddCmdLineOption(urlOption)

args = app.Initialize()

venueUrl = app.GetOption("url")

print "URL: ", venueUrl

if venueUrl is None:
    print "Exiting, no url specified."
    sys.exit(0)

venueClient = VenueIW(venueUrl)

streams = venueClient.GetStreams()

for s in streams:
    print "Stream: ", s.AsINIBlock()

