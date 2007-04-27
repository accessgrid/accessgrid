#!/usr/bin/python

import os, sys
import ConfigParser
from optparse import Option

from AccessGrid.VenueClient import GetVenueClientUrls
from AccessGrid.interfaces.VenueClient_client import VenueClientIW
from AccessGrid.Platform import isWindows
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.Toolkit import CmdlineApplication

doc ="""
This program finds a local venue client then attempts to send the
client to the url specified on the command line or in the file
specified on the command line.

This program assumes the file is a ConfigParser compatible file with
the following format:

files should be named with the .vv3d suffix, such as: <venueid>.vv3d,
and should contain:

[description]
url = <url>

There may be more information in the file, but this is the only information
used by this program and so anything else is extraneous.
"""
# Initialize
app = CmdlineApplication()

urlOption = Option("-u", "--url", dest="url", default=None,
                   help="Specify a venue url on the command line.")
app.AddCmdLineOption(urlOption)
fileOption = Option("-f", "--file", dest="file", default=None,
                    help="Specify a file that contains a venue url.")
app.AddCmdLineOption(fileOption)

args = app.Initialize()

venueUrl = app.GetOption("url")
fileName = app.GetOption("file")

print "URL: ", venueUrl
print "FILE: ", fileName

"""

    There are four valid command line possibilities:

    GoToVenue3.py --url url 
    GoToVenue3.py --url url --file fileName (use url)
    GoToVenue3.py --file fileName
    GoToVenue3.py Mime-Encoded.vv3d file (from web link)
 
 
    Anything else is invalid
 
"""

if venueUrl is not None:
    #if we have a url specified, try to launch it    
    pass   

elif fileName is None and len(sys.argv) == 1:
    #in this case we have no --url, no --file, and no other command line args
    #invalid - exit
    print "Exiting, no url specified."
    sys.exit(0)
else:
    #only 2 valid cases left.
    #either either --file or mime-encodedfile directly on command line
    config = ConfigParser.ConfigParser()

    if fileName is not None:    
     config.readfp(open(fileName))
    else:
        config.readfp(open(sys.argv[1]))

    if config.has_section('description'):
        if config.has_option('description', 'url'):
            venueUrl = config.get('description', 'url')
        else:
            print "The venue description file is missing the url."
            sys.exit(-1)
    else:
        print "The venue description file is missing the description section."
        sys.exit(-1)
 
# Check for the venue client soap server url
venueClientUrlList = GetVenueClientUrls()

enteredVenue = 0
for venueClientUrl in venueClientUrlList:
    try:
        venueClient = VenueClientIW(venueClientUrl)
        venueClient.IsValid()

        # Enter the specified venue
        print "Sending venue client to venue..."
        venueClient.EnterVenue(venueUrl)
        enteredVenue = 1
        break
    except Exception,e:
        print 'Exception messaging VenueClient; venueUrl=%s exc=%s' % (venueClientUrl,e)
        enteredVenue = 0

if not enteredVenue:
    # Communicating with running venue client failed; 
    # launch the venue client, pointed at the specified venue
    print "Launching the venue client..."
    if isWindows():
        prog = "\"%s\"" % os.path.join(app.GetToolkitConfig().GetBinDir(),
	                       "VenueClient3.py")
    else:
        prog = "%s" % os.path.join(app.GetToolkitConfig().GetBinDir(),
	                       "VenueClient3.py")
    os.spawnv(os.P_NOWAIT, sys.executable, (sys.executable, prog,
                                             "--url", venueUrl))

