#-----------------------------------------------------------------------------
# Name:        setup.py
# Purpose:     This is the setup.py for the Access Grid python module.
#
# Author:      Ivan R. Judson
#
# Created:     2003/17/01
# RCS-ID:      $Id: setup.py,v 1.41 2003-10-15 17:14:39 eolson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
from distutils.core import setup
import os
import sys
import glob

"""
Setup script for the Access Grid Toolkit. The module is described
by the set up below.
"""

win32_scripts = glob.glob('bin/*.py') + glob.glob('dist/bin/*.exe')
win32_data = list()

linux_scripts = [r"bin/VenueServer.py", 
                  r"bin/VenueClient.py", 
                  r"bin/VenueManagement.py",
                  r"bin/SetupVideo.py",
                  r"bin/AGNodeService.py",
                  r"bin/AGServiceManager.py",
                  r"bin/NodeManagement.py",
                  r"bin/NodeSetupWizard.py",
                  r"bin/CertificateRequestTool.py",
                  r"bin/BridgeServer.py",
                  r"bin/certmgr.py",
                  r"services/network/QuickBridge/QuickBridge",
                  ]

linux_data = [('etc/init.d',
               [r"packaging/linux/init.d/agns",
                r"packaging/linux/init.d/agsm"
                ]
               ),
              ('etc/AccessGrid',
               [r"packaging/config/AGNodeService.cfg",
                ]
               ),
              ('etc/AccessGrid/nodeConfig',
               [r"packaging/config/defaultLinux",
                r"packaging/config/defaultWindows"
                ]
               ),
              ('share/AccessGrid',
               [r"packaging/ag.ico"
                ]
               ),
              ('etc/AccessGrid/services',
               [r"services/node/AudioService.zip",
                r"services/node/VideoConsumerService.zip",
                r"services/node/VideoProducerService.zip"
                ]
               ),
              ('share/gnome/apps/AccessGrid',
               [r"packaging/gnome/.desktop",
                r"packaging/gnome/NodeManagement.desktop",
                r"packaging/gnome/VenueClient.desktop",
                r"packaging/gnome/VenueClient-PersonalNode.desktop",
                r"packaging/gnome/VenueManagement.desktop"
                ]
               ),
              ('share/applnk/AccessGrid',
               [r"packaging/kde/.desktop",
                r"packaging/kde/NodeManagement.desktop",
                r"packaging/kde/VenueClient.desktop",
                r"packaging/kde/VenueClient-PersonalNode.desktop",
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
              ('bin', []),
              ('share/doc/AccessGrid/Documentation/VenueClientManual',
               [r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManual.htm",
                r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML.htm",
                r"doc/VENUE_CLIENT_MANUAL_HTML/1.htm"
                ]
               ),
              ('share/doc/AccessGrid/Documentation/VenueClientManual/VenueClientManual_files',
               glob.glob("doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManual_files/*")
               )
              ]

if sys.platform == 'win32':
    inst_scripts = win32_scripts
    inst_data = win32_data
else:
    inst_scripts = linux_scripts
    inst_data = linux_data
    
setup (
    name = 'AGTk',
    fullname = 'AccessGrid Toolkit',
    version = '2.1.2',
    description = "The Access Grid Toolkit",
    long_description = """
The Access Grid Toolkit provides the necessary components
for users to participate in Access Grid based collaborations,
and also for developers to work on network services,
applications services and node services to extend the
functionality of the Access Grid.
""",
    author = "Argonne National Laboratory",
    author_email = "ag-dev@mcs.anl.gov",
    url = "http://www.mcs.anl.gov/fl/research/accessgrid",
    license = "AGTPL",

    #
    # Package list -- These files end up in $PYTHON\lib\site-packages
    #
    packages = ['AccessGrid',
                'AccessGrid.hosting',
                'AccessGrid.tests',
                'AccessGrid.hosting.pyGlobus',
                'AccessGrid.hosting.pyGlobus.tests'
                ],
    #
    # Script list -- these are command line tools and programs
    #   These end up in a system specific place:
    #   Windows: \Program Files\AGTk <version>\bin
    scripts = inst_scripts,

    #    Data Files list -- these are things like the services, etc.
    data_files = inst_data
)
