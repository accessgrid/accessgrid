#-----------------------------------------------------------------------------
# Name:        setup.py
# Purpose:     This is the setup.py for the Access Grid python module.
# Created:     2003/17/01
# RCS-ID:      $Id: setup.py,v 1.45 2004-03-25 14:29:58 judson Exp $
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

win32_scripts = list()
win32_data = [('bin', glob.glob('bin/*.py')),]

linux_scripts = [ r"bin/VenueServer.py", 
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
                  r"bin/agpm.py",
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
               ),
              ('share/doc/AccessGrid/Documentation/VenueManagementManual',
               [r"doc/VENUE_MANAGEMENT_MANUAL_HTML/VenueManagementManual.htm",
                r"doc/VENUE_MANAGEMENT_MANUAL_HTML/VenueManagementManualHTML.htm",
                r"doc/VENUE_MANAGEMENT_MANUAL_HTML/11.htm"
                ]
               ),
              ('share/doc/AccessGrid/Documentation/VenueManagementManual/VenueManagementManual_files',
               glob.glob("doc/VENUE_MANAGEMENT_MANUAL_HTML/VenueManagementManual_files/*")
               )
              ]

if sys.platform == 'win32':
    inst_scripts = win32_scripts
    inst_data = win32_data
else:
    inst_scripts = linux_scripts
    inst_data = linux_data
    
packages = ['AccessGrid',
            'AccessGrid.hosting',
            'AccessGrid.hosting.SOAPpy',
            'AccessGrid.tests',
            'AccessGrid.Security',
            'AccessGrid.Security.wxgui',
            'AccessGrid.Platform',
            ]

# We only send the code for the platform we're building
if sys.platform == 'win32':
    packages.append('AccessGrid.Platform.win32')

if sys.platform == 'linux2' or sys.platform == 'darwin':
    packages.append('AccessGrid.Platform.unix')
    

setup (
    name = 'AGTk',
    fullname = 'AccessGrid Toolkit',
    version = '2.2',
    description = "The Access Grid Toolkit",
    long_description = """
The Access Grid Toolkit provides the necessary components
for users to participate in Access Grid based collaborations,
and also for developers to work on network services,
application services and node services to extend the
functionality of the Access Grid.
""",
    author = "Argonne National Laboratory",
    author_email = "ag-info@mcs.anl.gov",
    url = "http://www.mcs.anl.gov/fl/research/accessgrid",
    license = "AGTPL",

    #
    # Package list -- These files end up in $PYTHON\lib\site-packages
    #
    packages = packages,

    #
    # Script list -- these are command line tools and programs
    #   These end up in a system specific place:
    #   Windows: \Program Files\AGTk <version>\bin
    scripts = inst_scripts,

    #    Data Files list -- these are things like the services, etc.
    data_files = inst_data
)
