#-----------------------------------------------------------------------------
# Name:        setup.py
# Purpose:     This is the setup.py for the Access Grid python module.
#
# Author:      Ivan R. Judson
#
# Created:     2003/17/01
# RCS-ID:      $Id: setup.py,v 1.7 2003-02-21 15:28:01 leggett Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
from distutils.core import setup
import os
import sys

"""
    Setup script for the Access Grid Toolkit. The module is described by the set
    up below.
"""

setup(
# Distribution Meta-Data
    name = 'AGTk',
    fullname = 'AccessGrid Toolkit',
    version = '2.0alpha',
    description = "The Access Grid Toolkit",
    long_description = "The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.",
    author = "Argonne National Laboratory",
    author_email = "ag-info@mcs.anl.gov",
    url = "http://www.accessgrid.org",
    license = "AGTPL",

# Package list -- There's only one
    packages = ['AccessGrid',
                r"AccessGrid/hosting",
                r"AccessGrid/hosting/pyGlobus"
                ],

# Script list -- these are command line tools and programs    
    scripts = [r"bin/VenueServer.py", 
               r"bin/VenueClient.py", 
               r"bin/VenueManagement.py",
               r"bin/SetupVideo.py",
               r"bin/AGNodeService.py",
               r"bin/AGServiceManager.py",
               r"bin/NodeManagement.py",
               r"bin/VenuesServerRegistry.py"
              ],

# Data Files list -- these are things like the services, etc.
    data_files = [('share/AccessGrid/local_services',
                   [r"AccessGrid/services/AudioService.py",
                    r"AccessGrid/services/AudioService.svc",
                    r"AccessGrid/services/VideoConsumerService.py",
                    r"AccessGrid/services/VideoConsumerService.svc",
                    r"AccessGrid/services/VideoProducerService.py",
                    r"AccessGrid/services/VideoProducerService.svc"
                    ]
                   ),
                  ('share/AccessGrid/services',
                   [r"AccessGrid/services/AudioService.zip",
                    r"AccessGrid/services/VideoConsumerService.zip",
                    r"AccessGrid/services/VideoProducerService.zip"
                    ]
                   ),
                  ('share/gnome/apps/AccessGrid',
                   [r"gnome/.desktop",
                    r"gnome/NodeManagement.desktop",
                    r"gnome/VenueClient.desktop",
                    r"gnome/VenueManagement.desktop"
                    ]
                   ),
                  ('share/applnk/AccessGrid',
                   [r"kde/.desktop",
                    r"kde/NodeManagement.desktop",
                    r"kde/VenueClient.desktop",
                    r"kde/VenueManagement.desktop"
                    ]
                   ),
                  ('doc',
                   ["COPYING.txt",
                    "INSTALL",
                    "README",
                    "TODO",
                    "VERSION"
                    ]
                   )
                  ]
                  
)
