#-----------------------------------------------------------------------------
# Name:        setup.py
# Purpose:     This is the setup.py for the Access Grid python module.
#
# Author:      Ivan R. Judson
#
# Created:     2003/17/01
# RCS-ID:      $Id: setup.py,v 1.33 2003-09-10 18:46:47 turam Exp $
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
    version = '2.0RC1',
    description = "The Access Grid Toolkit",
    long_description = "The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.",
    author = "Argonne National Laboratory",
    author_email = "ag-info@mcs.anl.gov",
    url = "http://www.mcs.anl.gov/fl/research/accessgrid",
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
               r"bin/NodeSetupWizard.py",
               r"bin/CertificateRequestTool.py",
               r"bin/BridgeServer.py",
               r"services/network/QuickBridge/QuickBridge",
               r"sharedapps/MailcapSetup.py"
#               r"bin/VenuesServerRegistry.py"
              ],

# Data Files list -- these are things like the services, etc.
    data_files = [('etc/init.d',
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
                   [r"doc/VENUE_CLIENT_MANUAL_HTML/contents.htm",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/tableOfContents.htm",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML.htm"
                    ]
                   ),
                  ('share/doc/AccessGrid/Documentation/VenueClientManual/VenueClientManualHTML_files',
                   [r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/filelist.xml",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/header.htm",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image001.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image001.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image002.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image002.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image003.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image003.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image004.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image005.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image005.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image006.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image006.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image007.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image008.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image008.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image009.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image009.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image010.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image010.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image011.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image011.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image012.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image012.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image013.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image013.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image013.png",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image014.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image015.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image016.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image017.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image017.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image018.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image018.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image019.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image020.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image020.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image021.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image022.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image022.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image023.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image023.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image024.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image025.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image025.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image026.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image026.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image027.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image028.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image028.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image029.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image029.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image030.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image031.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image031.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image032.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image033.emz",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image034.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image035.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image036.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image037.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image038.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image039.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image040.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image055.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image058.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image059.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image061.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image062.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image064.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image065.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image066.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image070.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image071.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image072.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image076.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image077.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image078.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image079.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image080.gif",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image081.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/image082.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/oledata.mso",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/overview.jpg",
                    r"doc/VENUE_CLIENT_MANUAL_HTML/VenueClientManualHTML_files/Thumbs.db"
                    ]
                   )
                 ]
                  
)
