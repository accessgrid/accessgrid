#!/usr/bin/python2

import os, sys
import ConfigParser
from optparse import Option

from AccessGrid.Venue import VenueIW
from AccessGrid.Toolkit import CmdlineApplication

doc ="""
This program creates a fictional shared app in a venue then removes it.
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

# Enter the specified venue
print "Creating shared application."
appDesc = venueClient.CreateApplication("Charles and Ed's Model Editor",
                                        "Bio Shared Model Editory",
                                   "application/x-ag-shared-bio-model-editor")

print "Application url is: %s" % appDesc.uri

print "Destroying shared application."
venueClient.DestroyApplication(appDesc.id)
