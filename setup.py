#-----------------------------------------------------------------------------
# Name:        setup.py
# Purpose:     This is the setup.py for the Access Grid python module.
#
# Author:      Ivan R. Judson
#
# Created:     2003/17/01
# RCS-ID:      $Id: setup.py,v 1.4 2003-02-05 16:44:45 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
from distutils.core import setup

"""
    Setup script for the Access Grid Toolkit. The module is described by the set
    up below.
"""

setup(
# Distribution Meta-Data
    name = 'AGTk',
    fullname = 'AccessGrid Toolkit',
    version = '2.0',
    description="The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.",
    author_email="ag-info@mcs.anl.gov",
    url="http://www.accessgrid.org",

# Package list -- There's only one
    packages = ['AccessGrid'],

# Script list -- these are command line tools and programs    
    scripts = ['bin/VenueServer.py', 
               'bin/VenueClient.py', 
               'bin/VenueManagement.py',
               'bin/SetupVideo.py',
               'bin/AGNodeService.py',
               'bin/AGServiceManager.py',
               'bin/NodeManagement.py',
               'bin/VenueServerRegistry.py'
              ]
)