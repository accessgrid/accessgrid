#-----------------------------------------------------------------------------
# Name:        setup.py
# Purpose:     This is the setup.py for the Access Grid python module.
#
# Author:      Ivan R. Judson
#
# Created:     2003/17/01
# RCS-ID:      $Id: setup.py,v 1.22 2003-04-24 22:17:54 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
from distutils.core import setup
import os
import sys

"""
Setup script for the Access Grid Toolkit. The module is described
by the set up below.
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
    data_files = [('etc/init.d',
                   [r"packaging/linux/init.d/agns",
                    r"packaging/linux/init.d/agsm"
                    ]
                   ),
                  ('etc/AccessGrid',
                   [r"packaging/config/AGNodeService.cfg",
                    r"packaging/config/AGServiceManager.cfg"
                    ]
                   ),
                  ('share/AccessGrid/nodeConfig',
                   [r"packaging/config/defaultLinux",
                    r"packaging/config/defaultWindows"
                    ]
                   ),
                  ('var/lib/ag/local_services',
                   [r"services/node/AudioService.py",
                    r"services/node/AudioService.svc",
                    r"services/node/VideoConsumerService.py",
                    r"services/node/VideoConsumerService.svc",
                    r"services/node/VideoProducerService.py",
                    r"services/node/VideoProducerService.svc"
                    ]
                   ),
                  ('share/AccessGrid',
                   [r"packaging/windows/agicons.exe",
                    r"packaging/ag.ico"
                    ]
                   ),
                  ('share/AccessGrid/services',
                   [r"services/node/AudioService.zip",
                    r"services/node/VideoConsumerService.zip",
                    r"services/node/VideoProducerService.zip"
                    ]
                   ),
                  ('share/AccessGrid/packaging/windows',
                   [r"packaging/windows/Postinstall.py",
                    r"packaging/windows/AGNodeServicePostinstall.py",
                    r"packaging/windows/AGServiceManagerPostinstall.py"
                    ]
                   ),
                  ('share/gnome/apps/AccessGrid',
                   [r"packaging/gnome/.desktop",
                    r"packaging/gnome/NodeManagement.desktop",
                    r"packaging/gnome/VenueClient.desktop",
                    r"packaging/gnome/VenueManagement.desktop"
                    ]
                   ),
                  ('share/applnk/AccessGrid',
                   [r"packaging/kde/.desktop",
                    r"packaging/kde/NodeManagement.desktop",
                    r"packaging/kde/VenueClient.desktop",
                    r"packaging/kde/VenueManagement.desktop"
                    ]
                   ),
                  ('share/doc/AccessGrid',
                   ["COPYING.txt",
                    "INSTALL",
                    "README",
                    "TODO",
                    "VERSION"
                    ]
                   ),
                  ('bin', [])
                  ]
                  
)
