#-----------------------------------------------------------------------------
# Name:        setup.py
# Purpose:     This is the setup.py for the Access Grid python module.
# Created:     2003/17/01
# RCS-ID:      $Id: setup.py,v 1.73 2004-08-27 19:18:39 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
from distutils.core import setup
from distutils.spawn import spawn, find_executable
from distutils.sysconfig import get_config_vars

import os
import sys
import glob
import string
import traceback

"""
Setup script for the Access Grid Toolkit. The module is described
by the set up below.
"""

cdir = os.getcwd()

win32_scripts = list()
win32_data = [
    ('', [r'COPYING.txt', r'Install.WINDOWS', r'README', r'README-developers',
          r'TODO', r'VERSION', r'ChangeLog']), 
    ('bin', glob.glob('bin/*.py')),
    ('bin', glob.glob('tools/GoToVenue.py')),
    ('NodeServices', ''),
    ('SharedApplications', ''),
    ('doc/VenueClientManual', glob.glob('doc/VenueClientManual/*.*')),
    ('doc/VenueClientManual/VenueClientManual_files',
     glob.glob('doc/VenueClientManual/VenueClientManual_files/*.*')),
    ('doc/VenueManagementManual', glob.glob('doc/VenueManagementManual/*.*')),
    ('doc/VenueManagementManual/VenueManagementManual_files',
     glob.glob('doc/VenueManagementManual/VenueManagementManual_files/*.*')),
    ('install', [r'packaging/windows/agicons.exe',
                 r'packaging/windows/msvcr70.dll',
                 r'packaging/windows/msvcr71.dll']),
    ('config/CAcertificates',
     glob.glob('packaging/config/CAcertificates/*.*')),
    ]

linux_scripts = [ r"bin/VenueServer.py", 
                  r"bin/VenueClient.py", 
                  r"bin/VenueManagement.py",
                  r"bin/AGNodeService.py",
                  r"bin/AGServiceManager.py",
                  r"bin/NodeManagement.py",
                  r"bin/NodeSetupWizard.py",
                  r"bin/CertificateRequestTool.py",
                  r"bin/BridgeServer.py",
                  r"bin/certmgr.py",
                  r"bin/agpm.py",
                  ]

linux_data = [('etc/init.d',
               [r"packaging/linux/init.d/agns",
                r"packaging/linux/init.d/agsm"
                ]
               ),
              ('etc/AccessGrid/Config',
               [r"packaging/config/AGNodeService.cfg",
                ]
               ),
              ('etc/AccessGrid/Config/nodeConfig',
               [r"packaging/config/defaultLinux",
                ]
               ),
              ('etc/AccessGrid/Config/CAcertificates',
               filter(os.path.isfile, glob.glob('packaging/config/CAcertificates/*')),
               ),
              ('share/AccessGrid',
               [r"packaging/ag.ico"
                ]
               ),
               
              ('share/gnome/apps/AccessGrid',
               [
                r"packaging/linux/gnome/Readme.desktop",
                r"packaging/linux/gnome/VenueClient.desktop",
                r"packaging/linux/gnome/VenueClient-Debug.desktop",
                r"packaging/linux/gnome/VenueManagement.desktop",
                r"packaging/linux/gnome/CertificateRequestTool.desktop",
                ]
               ),
              ('share/gnome/apps/AccessGrid/Configure',
               [
                r"packaging/linux/gnome/NodeSetupWizard.desktop",
                r"packaging/linux/gnome/NodeManagement.desktop",
                ]
               ),
              ('share/gnome/apps/AccessGrid/Services',
               [
                r"packaging/linux/gnome/VenueServer.desktop",
                r"packaging/linux/gnome/VenueServer-Debug.desktop",
                r"packaging/linux/gnome/ServiceManager.desktop",
                r"packaging/linux/gnome/ServiceManager-Debug.desktop",
                r"packaging/linux/gnome/NodeService.desktop",
                r"packaging/linux/gnome/NodeService-Debug.desktop",
                ]
               ),
              ('share/gnome/apps/AccessGrid/Documentation',
               [
                r"packaging/linux/gnome/VenueClientManual.desktop",
                r"packaging/linux/gnome/VenueManagementManual.desktop",
                r"packaging/linux/gnome/License.desktop",
                ]
               ),
               
              ('share/applnk/AccessGrid',
               [
                r"packaging/linux/kde/Readme.desktop",
                r"packaging/linux/kde/VenueClient.desktop",
                r"packaging/linux/kde/VenueClient-Debug.desktop",
                r"packaging/linux/kde/VenueManagement.desktop",
                r"packaging/linux/kde/CertificateRequestTool.desktop",
                ]
               ),
              ('share/applnk/AccessGrid/Configure',
               [
                r"packaging/linux/kde/NodeSetupWizard.desktop",
                r"packaging/linux/kde/NodeManagement.desktop",
                ]
               ),
              ('share/applnk/AccessGrid/Services',
               [
                r"packaging/linux/kde/VenueServer.desktop",
                r"packaging/linux/kde/VenueServer-Debug.desktop",
                r"packaging/linux/kde/ServiceManager.desktop",
                r"packaging/linux/kde/ServiceManager-Debug.desktop",
                r"packaging/linux/kde/NodeService.desktop",
                r"packaging/linux/kde/NodeService-Debug.desktop",
                ]
               ),
              ('share/applnk/AccessGrid/Documentation',
               [
                r"packaging/linux/kde/VenueClientManual.desktop",
                r"packaging/linux/kde/VenueManagementManual.desktop",
                r"packaging/linux/kde/License.desktop",
                ]
               ),

              ('share/doc/AccessGrid',
               ["COPYING.txt",
                "Install.LINUX",
                "README",
                "README-developers",
                "TODO",
                "VERSION",
                "ChangeLog"
                ]
               ),
              ('bin', ['tools/GoToVenue.py']),
              ('share/doc/AccessGrid/Documentation/VenueClientManual',
               [r"doc/VenueClientManual/VenueClientManual.htm",
                r"doc/VenueClientManual/VenueClientManualHTML.htm",
                r"doc/VenueClientManual/1.htm"
                ]
               ),
              ('share/doc/AccessGrid/Documentation/VenueClientManual/VenueClientManual_files',
               filter(os.path.isfile, glob.glob("doc/VenueClientManual/VenueClientManual_files/*"))
               ),
              ('share/doc/AccessGrid/Documentation/VenueManagementManual',
               [r"doc/VenueManagementManual/VenueManagementManual.htm",
                r"doc/VenueManagementManual/VenueManagementManualHTML.htm",
                r"doc/VenueManagementManual/1.htm"
                ]
               ),
              ('share/doc/AccessGrid/Documentation/VenueManagementManual/VenueManagementManual_files',
               filter(os.path.isfile, glob.glob("doc/VenueManagementManual/VenueManagementManual_files/*"))
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
