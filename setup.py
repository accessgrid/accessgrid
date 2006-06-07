#-----------------------------------------------------------------------------
# Name:        setup.py
# Purpose:     This is the setup.py for the Access Grid python module.
# Created:     2003/17/01
# RCS-ID:      $Id: setup.py,v 1.106 2006-06-07 02:34:23 willing Exp $
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

# Generate interfaces
if os.environ.has_key('PYTHONPATH'):
    oldpath = os.environ['PYTHONPATH']
else:
    oldpath = ''
os.environ['PYTHONPATH'] = cdir
os.chdir(os.path.join(cdir,'tools'))
cmd = "%s %s"%(sys.executable, "GenerateInterfaces.py")
#print "cmd = ", cmd
os.system(cmd)

os.chdir(cdir)
os.environ['PYTHONPATH'] = oldpath


win32_scripts = list()
win32_data = [
    ('', [r'COPYING.txt', r'Install.WINDOWS', r'README', r'README-developers',
          r'TODO', r'VERSION', r'ChangeLog']), 
    ('bin', glob.glob('bin/*.py')),
    ('bin', [r'tools/GoToVenue.py', r'sharedapps/VenueVNC/server/VenueVNCServer.py', r'tools/runag.py']),
    ('NodeServices', ''),
    ('SharedApplications', ''),
    ('install', [r'packaging/windows/agicons.exe',
                 r'packaging/ag.ico',
                 r'packaging/windows/msvcr70.dll',
                 r'packaging/windows/msvcr71.dll',
                 r'packaging/windows/msvcr71d.dll']),
    ('config/CAcertificates',
     glob.glob('packaging/config/CAcertificates/*.*')),
    ('Config/nodeConfig',
     [r"packaging/config/default",
      ]
     ),
    ]

linux_scripts = [ r"bin/VenueServer.py", 
                  r"bin/VenueClient.py", 
                  r"bin/VenueManagement.py",
                  r"bin/AGServiceManager.py",
                  r"bin/NodeManagement.py",
                  r"bin/NodeSetupWizard.py",
                  r"bin/CertificateRequestTool.py",
                  r"bin/certmgr.py",
                  r"bin/agpm.py",
                  r"bin/Bridge.py",
                  r"tools/GoToVenue.py",
                  r"tools/ag-avahi-discover.py",
                  r"sharedapps/VenueVNC/server/VenueVNCServer.py",
                  ]

linux_data = [('etc/AccessGrid3/Config',
               [r"packaging/config/AGNodeService.cfg",
                ]
               ),
              ('etc/AccessGrid3/Config/nodeConfig',
               [r"packaging/config/default",
                ]
               ),
              ('etc/AccessGrid3/Config/CAcertificates',
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
              ]

mac_scripts = [ r"bin/VenueServer.py", 
                r"bin/VenueClient.py", 
                r"bin/VenueManagement.py",
                r"bin/AGServiceManager.py",
                r"bin/NodeManagement.py",
                r"bin/NodeSetupWizard.py",
                r"bin/CertificateRequestTool.py",
                r"bin/CertificateManager.py",
                r"bin/certmgr.py",
                r"bin/agpm.py",
                r"bin/AGLauncher.py",
                r"bin/Bridge.py",
                ]

mac_data =    [ 
              ('Config/nodeConfig',
               [r"packaging/config/default",
                ]
               ),
              ('Config/CAcertificates',
               filter(os.path.isfile, glob.glob('packaging/config/CAcertificates/*')),
               ),
              ('',
               [r"packaging/mac/AGTk.icns",
                "COPYING.txt"
                ]
               ),
              ('doc',
               ["COPYING.txt",
                "README",
                "README-developers",
                "TODO",
                "VERSION",
                "ChangeLog"
                ]
               ),
              ('bin', ['tools/GoToVenue.py', 'sharedapps/VenueVNC/server/VenueVNCServer.py', 'packaging/mac/findwx26']),
              ]

if sys.platform == 'win32':
    inst_scripts = win32_scripts
    inst_data = win32_data
elif sys.platform == 'darwin':
    inst_scripts = mac_scripts
    inst_data = mac_data
else:
    inst_scripts = linux_scripts
    inst_data = linux_data
    
packages = ['AccessGrid3.AccessGrid',
            'AccessGrid3.AccessGrid.hosting',
            'AccessGrid3.AccessGrid.hosting.SOAPpy',
            'AccessGrid3.AccessGrid.hosting.ZSI',
            'AccessGrid3.AccessGrid.tests',
            'AccessGrid3.AccessGrid.Security',
            'AccessGrid3.AccessGrid.Security.wxgui',
            'AccessGrid3.AccessGrid.Platform',
            'AccessGrid3.AccessGrid.wsdl',
            'AccessGrid3.AccessGrid.interfaces',
	    'AccessGrid3.AccessGrid.Registry',
	    'AccessGrid3.AccessGrid.Jabber',
	    'AccessGrid3.AccessGrid.Beacon',
	    'AccessGrid3.AccessGrid.FTPS'
            ]

# We only send the code for the platform we're building
if sys.platform == 'win32':
    packages.append('AccessGrid3.AccessGrid.Platform.win32')

if sys.platform == 'linux2' or sys.platform == 'darwin' or sys.platform == 'freebsd5' or sys.platform == 'freebsd6':
    packages.append('AccessGrid3.AccessGrid.Platform.unix')

setup (
    name = 'AGTk',
    fullname = 'AccessGrid Toolkit',
    version = '3.0',
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
    package_dir = {"AccessGrid3.AccessGrid" : "AccessGrid"},
    packages = packages,

    #
    # Script list -- these are command line tools and programs
    #   These end up in a system specific place:
    #   Windows: \Program Files\AGTk <version>\bin
    scripts = inst_scripts,

    #    Data Files list -- these are things like the services, etc.
    data_files = inst_data
)
