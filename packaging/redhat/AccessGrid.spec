#
# The following are variables that are used throughout the rest of the
# spec file. If you see %{variable_name} this is where it's assigned
#
%define	name		AccessGrid
%define version		2.1.2
%define release		1
%define	prefix		/usr
%define sysconfdir	/etc/%{name}
%define sharedir	%{prefix}/share
%define gnomedir	%{sharedir}/gnome/apps
%define kdedir		%{sharedir}/applnk
%define aghome		/var/lib/ag
%define buildroot	/var/tmp/%{name}-%{version}

#
# The following defines the AccessGrid rpm
# Required: /usr/lib/python2.2
# Required: pyGlobus rpm installed
# Required: logging rpm installed
# Obsoletes: AccessGrid-2.0alpha
#

Summary:	The Access Grid Toolkit
Name:		%{name}
Version:	%{version}
Release:	%{release}
Copyright:	AGTPL
Group:		Utilities/System
URL:		http://www.accessgrid.org
Vendor:		Argonne National Laboratory
Source:		%{name}-%{version}.tar.gz
BuildRoot:	%{buildroot}
Requires:	/usr/bin/python2.2
Requires:	wxGTK
Requires:	wxPythonGTK-py2.2
Requires:	globus-accessgrid
Requires:	pyGlobus
Requires:	logging
Requires:	pyOpenSSL_AG
Obsoletes:	AccessGrid-2.0beta AccessGrid-2.1

%description
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the core components to start participating in the Access Grid.

#
# The following defines the AccessGrid-VenueClient rpm
# Requires: AccessGrid
# Obsoletes: AccessGrid-VenueClient-2.0alpha
#
%package VenueClient
Summary:	The Access Grid Toolkit Venue Client
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid = %{version}-%{release}
Obsoletes:	AccessGrid-VenueClient-2.0beta AccessGrid-VenueClient-2.1

%description VenueClient
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the components needed to connect to an Access Grid Venue.

#
# The following defines the AccessGrid-VenueServer rpm
# Requires: AccessGrid
# Obsoletes: AccessGrid-VenueServer-2.0alpha
#
%package VenueServer
Summary:	The Access Grid Toolkit Venue Server
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid = %{version}-%{release}
Obsoletes:	AccessGrid-VenueServer-2.0beta AccessGrid-VenueServer-2.1

%description VenueServer
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the components needed to create an Access Grid Venue and an Access Grid Venue Server.

#
# The following defines the AccessGrid-VideoProducer rpm
# Requires: AccessGrid
# Requires: AccessGrid-vic
# Obsoletes: AccessGrid-VideoProducer-2.0alpha
#
%package VideoProducer
Summary:	The Access Grid Toolkit Video Producer Service
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid = %{version}-%{release}
Requires:	AccessGrid-vic
Obsoletes:	AccessGrid-VideoProducer-2.0beta AccessGrid-VideoProducer-2.1

%description VideoProducer
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the components needed to run the Video Producer service. This service is responsible for capturing and transmitting an Access Grid Node's video.

#
# The following defines the AccessGrid-VideoConsumer rpm
# Requires: AccessGrid
# Obsoletes: AccessGrid-VideoConsumer-2.0alpha
#
%package VideoConsumer
Summary:	The Access Grid Toolkit Video Consumer Service
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid = %{version}-%{release}
Obsoletes:	AccessGrid-VideoConsumer-2.0beta AccessGrid-VideoConsumer-2.1

%description VideoConsumer
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the components needed to run the Video Consumer service. This service is responsible for receiving remote Access Grid Nodes' video.

#
# The following defines the AccessGrid-AudioService rpm
# Requires: AccessGrid
# Requires: AccessGrid-rat
# Obsoletes: AccessGrid-AudioService-2.0alpha
#
%package AudioService
Summary:	The Access Grid Toolkit Audio Service
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid = %{version}-%{release}
Requires:	AccessGrid-rat
Obsoletes:	AccessGrid-AudioService-2.0beta AccessGrid-AudioService-2.1

%description AudioService
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the components needed to run the Audio service. This service is responsible for capturing and transmitting your Access Grid Node's audio as well as receiving remote Access Grid Nodes' audio.

#
# The following defines the AccessGrid-BridgeServer rpm
# Requires: AccessGrid
#
%package BridgeServer
Summary:	The Access Grid Toolkit Bridge Server
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid = %{version}-%{release}

%description BridgeServer
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the components needed to run the Bridge Server.  This server is responsible for providing unicast connectivity to venue participants.

#
# The following untars the source tarball and removes any previous build
# attempts
#

%prep
%setup
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

#
# The following builds the package using setup.py
# It starts by zipping up the services in the services directory
# then builds the package
#

%build
python2.2 packaging/makeServicePackages.py services/node
(cd services/network/QuickBridge; gcc -o QuickBridge QuickBridge.c)
python2.2 setup.py build


#
# The following installs the package in the buildroot,
# moves the etc directory to the "root" directory,
# moves the var directory to the "root" directory,
# until services are starting at boot)
#

%install
python2.2 setup.py install --prefix=%{buildroot}%{prefix} --no-compile
mv %{buildroot}%{prefix}/etc %{buildroot}
#mv %{buildroot}%{prefix}/var %{buildroot}
mkdir -p %{aghome}/local_services

#
# Define the files that are to go into the AccessGrid package
# - Mark documents as documents for rpm
# - Install python modules with default permissions
# - Install AGServiceManager.py and agsm service with executable permissions
# - Make a directory in the ag user's home (this should be done by whatever
#   is trying to write to that directory really)
#

%files
%defattr(-,root,root)
%{prefix}/lib
%{sharedir}/%{name}/ag.ico
%defattr(0755,root,root)
%{prefix}/bin/AGServiceManager.py
/etc/init.d/agsm
%defattr(0755,ag,ag)
%dir %{aghome}/local_services

#
# Define the files that are to go into the AccessGrid-VenueClient package
# - Install AGNodeService.py, VenueClient.py, and NodeManagement.py with
#   executable permissions
# - Install the AGNodeService config file and tag it as a config file
#   for rpm
# - Install the default node configuration, make it owned by ag, and tag it
#   as a config file for rpm
# - Install the GNOME and KDE menu items
#

%files VenueClient
%defattr(0755,root,root)
%{prefix}/bin/AGNodeService.py
%{prefix}/bin/VenueClient.py
%{prefix}/bin/NodeManagement.py
%{prefix}/bin/NodeSetupWizard.py
%{prefix}/bin/CertificateRequestTool.py
%{prefix}/bin/certmgr.py
%{prefix}/bin/SetupVideo.py
%{sharedir}/doc/AccessGrid
/etc/init.d/agns
%defattr(0644,root,root)
%config %{sysconfdir}/AGNodeService.cfg
%defattr(0644,ag,ag)
%config %{sysconfdir}/nodeConfig/defaultLinux
%defattr(-,root,root)
%{sysconfdir}/services/
%{gnomedir}/%{name}/.desktop
%{gnomedir}/%{name}/VenueClient.desktop
%{gnomedir}/%{name}/VenueClient-PersonalNode.desktop
%{gnomedir}/%{name}/NodeManagement.desktop
%{kdedir}/%{name}/.desktop
%{kdedir}/%{name}/VenueClient.desktop
%{kdedir}/%{name}/VenueClient-PersonalNode.desktop
%{kdedir}/%{name}/NodeManagement.desktop

#
# Define the files that are to go into the AccessGrid-VenueServer package
# - Install VenueManagement.py, VenueServer.py, and VenueServerRegistry.py
#   with executable permissions
# - Install the GNOME and KDE menu items
#

%files VenueServer
%defattr(0755,root,root)
%{prefix}/bin/VenueManagement.py
%{prefix}/bin/VenueServer.py
#%{prefix}/bin/VenuesServerRegistry.py
%defattr(-,root,root)
%{gnomedir}/%{name}/.desktop
%{gnomedir}/%{name}/VenueManagement.desktop
%{kdedir}/%{name}/.desktop
%{kdedir}/%{name}/VenueManagement.desktop

#
# Define the files that are to go into the AccessGrid-VideoProducer package
# - Install SetupVideo.py with executable permissions
# - Install the local service file and make them owned by user ag
#

#%files VideoProducer
#%defattr(0755,root,root)
#%{prefix}/bin/SetupVideo.py
#%defattr(0664,ag,ag)
#%{aghome}/local_services/VideoProducerService.*

#
# Define the files that are to go into the AccessGrid-VideoConsumer package
# - Install the local service file and make them owned by user ag
#

#%files VideoConsumer
#%defattr(0664,ag,ag)
#%{aghome}/local_services/VideoConsumerService.*

#
# Define the files that are to go into the AccessGrid-AudioService package
# - Install the local service file and make them owned by user ag
#

#%files AudioService
#%defattr(0664,ag,ag)
#%{aghome}/local_services/AudioService.*

#
# Define the files that are to go into the AccessGrid-AudioService package
# - Install the local service file and make them owned by user ag
#

%files BridgeServer
%defattr(0775,ag,ag)
%{prefix}/bin/BridgeServer.py
%{prefix}/bin/QuickBridge

#
# AccessGrid package preinstall commands
# If there is no ag user's home directory then there must not be an ag
# user and group so create them
#

%pre
/usr/sbin/useradd -c "Access Grid User" -r -m -d %{aghome} ag 2> /dev/null || :

#
# AccessGrid package postinstall commands
# - Make a file, /tmp/AccessGrid-Postinstall.py, run it, then delete.
#   This script will compile all the AccessGrid python modules
# - Add the agsm service to chkconfig
#

%post
cat <<EOF > /tmp/AccessGrid-Postinstall.py
#!/usr/bin/python2.2
import AccessGrid
import AccessGrid.hosting
import AccessGrid.hosting.pyGlobus
import os
import os.path
import glob
import sys

def modimport(module):
    for module_file in glob.glob(os.path.join(module.__path__[0], "*.py")):
	try:
            __import__(module.__name__ + "." + os.path.basename(module_file[:-3]))
	except:
	    pass

sys.stdout.write("Compiling Access Grid Python modules.... ")
modimport(AccessGrid)
modimport(AccessGrid.hosting)
modimport(AccessGrid.hosting.pyGlobus)
sys.stdout.write("Done\n")
EOF
chmod +x /tmp/AccessGrid-Postinstall.py
/tmp/AccessGrid-Postinstall.py
rm -f /tmp/AccessGrid-Postinstall.py
/sbin/chkconfig --add agsm

#
# AccessGrid-VenueClient package postinstall
# - Add the agns service to chkconfig
#

%post VenueClient
/sbin/chkconfig --add agns

#
# AccessGrid package pre-uninstall
# - Remove the agsm service from chkconfig
# - Create a file, /tmp/AccessGrid-Preuninstall.py, run it, then delete it.
#   This script will remove those compiled AccessGrid python modules

%preun
/sbin/chkconfig --del agsm
cat <<EOF > /tmp/AccessGrid-Preuninstall.py
#!/usr/bin/python2.2
import AccessGrid
import AccessGrid.hosting
import AccessGrid.hosting.pyGlobus
import os
import os.path
import glob

def delcompiled(module):
    for module_file in glob.glob(os.path.join(module.__path__[0], "*.pyc")):
        try:
            os.remove(module_file)
        except os.error:
            pass

delcompiled(AccessGrid.hosting.pyGlobus)
delcompiled(AccessGrid.hosting)
delcompiled(AccessGrid)
EOF
chmod +x /tmp/AccessGrid-Preuninstall.py
/tmp/AccessGrid-Preuninstall.py
rm -f /tmp/AccessGrid-Preuninstall.py

#
# AccessGrid-VenueClient pre-uninstall
# - Remove the agns service from chkconfig
#

%preun VenueClient
/sbin/chkconfig --del agns

#
# After the RPMs have been successfully built remove the temporary build
# space
#

%clean
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

#
# This is the ChangeLog. You should add to this if you do anything to this
# spec file
#

%changelog

* Fri May 16 2003 Ti Leggett <leggett@mcs.anl.gov>
- Fixed the ag user add problems (hopefully)
- Added MailcapSetup.py to the AccessGrid package

* Wed Mar 26 2003 Ti Leggett <leggett@mcs.anl.gov>
- Added a plethora of comments
- Fixed a few permissions for some install files
- Now removes the AccessGrid pre-uninstall script after it's run

* Thu Mar 13 2003 Ti Leggett <leggett@mcs.anl.gov>
- Added user and group creation in preinstall
- Added postinstall to compile python modules
- Services are added to chkconfig for starting
- Added preuninstall to remove compiled modules
- Move etc and var down a dir after python install so they're where they need to be

* Fri Feb 21 2003 Ti Leggett <leggett@mcs.anl.gov>
- Fixed where docs go
- Added default node configuration file

* Fri Feb 14 2003 Ti Leggett <leggett@mcs.anl.gov>
- Added postinstall for VenueClient to create AGNodeService config file

* Thu Feb 13 2003 Ti Leggett <leggett@mcs.anl.gov>
- Added SetupVideo.py to VideoProducer

* Fri Feb 06 2003 Ti Leggett <leggett@mcs.anl.gov>
- Modularized the RPMs

* Tue Feb 05 2003 Ti Leggett <leggett@mcs.anl.gov>
- This file was created

