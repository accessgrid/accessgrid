#-----------------------------------------------------------------------------
# Name:        setup.py
# Purpose:     This is the setup.py for the Access Grid python module.
# Created:     2003/17/01
# RCS-ID:      $Id: setup.py,v 1.62 2004-04-21 18:24:52 turam Exp $
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

# We pluck off the prefix, this is totally unkosher, but hey
dest = None
for arg in sys.argv[1:]:
    if string.find(arg, '--prefix') == 0:
        al = string.split(arg, '=')
        if len(al) == 2:
            dest = al[1]

# Generate epydoc documentation
if dest is not None:
    if sys.platform == 'win32':
        ep = os.path.join(os.path.dirname(sys.executable), "Scripts", "epydoc.py")
    else:
        ep = find_executable("epydoc")

    cmd = [sys.executable, ep, "--html", "-o",
           os.path.join("doc", "Developer"),
           "-n", "Access Grid Toolkit", "-u",
           "http://www.mcs.anl.gov/fl/research/accessgrid/", "AccessGrid"]
    print "cmd = ", cmd
    try:
        spawn(cmd, verbose=1)
    except Exception, e:
        print "** Error generating documentation"
        traceback.print_exc()

win32_scripts = list()
win32_data = [
    ('', [r'COPYING.txt', r'Install.WINDOWS', r'README', r'README-developers',
          r'TODO', r'VERSION', r'ChangeLog']), 
    ('bin', glob.glob('bin/*.py')),
    ('NodeServices', ''),
    ('SharedApplications', ''),
    ('doc/Developer', glob.glob('doc/Developer/*.*')),
    ('doc/Developer/private', glob.glob('doc/Developer/private/*.*')),
    ('doc/Developer/public', glob.glob('doc/Developer/public/*.*')),
    ('doc/VenueClientManual', glob.glob('doc/VenueClientManual/*.*')),
    ('doc/VenueClientManual/VenueClientManual_files',
     glob.glob('doc/VenueClientManual/VenueClientManual_files/*.*')),
    ('doc/VenueManagementManual', glob.glob('doc/VenueManagementManual/*.*')),
    ('doc/VenueManagementManual/VenueManagementManual_files',
     glob.glob('doc/VenueManagementManual/VenueManagementManual_files/*.*')),
    ('install', [r'packaging/windows/agicons.exe',
                 r'packaging/windows/msvcr70.dll']),
    ('config/CAcertificates',
     glob.glob('packaging/config/CAcertificates/*.*')),
    ]

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
                ]
               ),
              ('share/AccessGrid',
               [r"packaging/ag.ico"
                ]
               ),
              ('share/gnome/apps/AccessGrid',
               [r"packaging/linux/gnome/.desktop",
                r"packaging/linux/gnome/NodeManagement.desktop",
                r"packaging/linux/gnome/VenueClient.desktop",
                r"packaging/linux/gnome/VenueClient-PersonalNode.desktop",
                r"packaging/linux/gnome/VenueManagement.desktop"
                ]
               ),
              ('share/applnk/AccessGrid',
               [r"packaging/linux/kde/.desktop",
                r"packaging/linux/kde/NodeManagement.desktop",
                r"packaging/linux/kde/VenueClient.desktop",
                r"packaging/linux/kde/VenueClient-PersonalNode.desktop",
                r"packaging/linux/kde/VenueManagement.desktop"
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
               [r"doc/VenueClientManual/VenueClientManual.htm",
                r"doc/VenueClientManual/VenueClientManualHTML.htm",
                r"doc/VenueClientManual/1.htm"
                ]
               ),
              ('share/doc/AccessGrid/Documentation/VenueClientManual/VenueClientManual_files',
               glob.glob("doc/VenueClientManual/VenueClientManual_files/*")
               ),
              ('share/doc/AccessGrid/Documentation/VenueManagementManual',
               [r"doc/VenueManagementManual/VenueManagementManual.htm",
                r"doc/VenueManagementManual/VenueManagementManualHTML.htm",
                r"doc/VenueManagementManual/1.htm"
                ]
               ),
              ('share/doc/AccessGrid/Documentation/VenueManagementManual/VenueManagementManual_files',
               glob.glob("doc/VenueManagementManual/VenueManagementManual_files/*")
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
