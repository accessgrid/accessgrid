#!/usr/bin/python2

import os, sys
from optparse import Option

from AccessGrid.VenueServer import VenueServerIW
from AccessGrid.Venue import VenueIW
from AccessGrid.Toolkit import CmdlineApplication

doc ="""
This program gets the stream information from the venue.
"""
# Initialize
app = CmdlineApplication()

urlOption = Option("-u", "--url", dest="url", default=None,
                   help="Specify a venueserver url on the command line.")
app.AddCmdLineOption(urlOption)

args = app.Initialize()

venueServerUrl = app.GetOption("url")
venueServer = VenueServerIW(venueServerUrl)

vdl = venueServer.GetVenues()

for v in vdl:
    venueClient = VenueIW(v.uri)
    streams = venueClient.GetStaticStreams()

    if len(streams):
        print "\nVenue:", v.name
        for s in streams:
            print "%s: %s" % (s.capability.type, s.location)
