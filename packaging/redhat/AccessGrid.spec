%define	name		AccessGrid
%define	version		2.0alpha
%define	release		3
%define	prefix		/usr
%define sysconfdir	/etc/%{name}/config
%define sharedir	%{prefix}/share
%define gnomedir	%{sharedir}/gnome/apps
%define kdedir		%{sharedir}/applnk
%define buildroot	/var/tmp/%{name}-%{version}

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
Requires:	pyGlobus
Requires:	logging

%description
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the core components to start participating in the Access Grid.

%package VenueClient
Summary:	The Access Grid Toolkit Venue Client
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid

%description VenueClient
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the components needed to connect to an Access Grid Venue.

%package VenueServer
Summary:	The Access Grid Toolkit Venue Server
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid

%description VenueServer
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the components needed to create an Access Grid Venue and an Access Grid Venue Server.

%package VideoProducer
Summary:	The Access Grid Toolkit Video Producer Service
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid AccessGrid-vic

%description VideoProducer
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the components needed to run the Video Producer service. This service is responsible for capturing and transmitting an Access Grid Node's video.

%package VideoConsumer
Summary:	The Access Grid Toolkit Video Consumer Service
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid

%description VideoConsumer
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the components needed to run the Video Consumer service. This service is responsible for receiving remote Access Grid Nodes' video.

%package AudioService
Summary:	The Access Grid Toolkit Audio Service
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid AccessGrid-rat

%description AudioService
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the components needed to run the Audio service. This service is responsible for capturing and transmitting your Access Grid Node's audio as well as receiving remote Access Grid Nodes' audio.

%prep
%setup
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%build
python2.2 setup.py build

%install
python2.2 setup.py install --prefix=%{buildroot}%{prefix} --no-compile

%files
%doc %{sharedir}/doc/
%defattr(-,root,root)
%{prefix}/lib
%defattr(0755,root,root)
%{prefix}/bin/AGServiceManager.py
%defattr(0777,root,root)
%dir %{sharedir}/%{name}/local_services

%files VenueClient
%defattr(-,root,root)
%{prefix}/bin/AGNodeService.py
%{prefix}/bin/VenueClient.py
%{prefix}/bin/NodeManagement.py
%{sharedir}/%{name}/services/
%{gnomedir}/%{name}/.desktop
%{gnomedir}/%{name}/VenueClient.desktop
%{gnomedir}/%{name}/NodeManagement.desktop
%{kdedir}/%{name}/.desktop
%{kdedir}/%{name}/VenueClient.desktop
%{kdedir}/%{name}/NodeManagement.desktop


%files VenueServer
%defattr(-,root,root)
%{prefix}/bin/VenueManagement.py
%{prefix}/bin/VenueServer.py
%{prefix}/bin/VenuesServerRegistry.py
%{gnomedir}/%{name}/.desktop
%{gnomedir}/%{name}/VenueManagement.desktop
%{kdedir}/%{name}/.desktop
%{kdedir}/%{name}/VenueManagement.desktop
#
%files VideoProducer
%defattr(-,root,root)
%{prefix}/bin/SetupVideo.py
%defattr(0666,root,root)
%{sharedir}/%{name}/local_services/VideoProducerService.*

%files VideoConsumer
%defattr(0666,root,root)
%{sharedir}/%{name}/local_services/VideoConsumerService.*

%files AudioService
%defattr(0666,root,root)
%{prefix}/share/%{name}/local_services/AudioService.*

%post VenueClient
mkdir -p %{sysconfdir}
cat <<EOF > %{sysconfdir}/AGNodeService.cfg
[Node Configuration]
servicesDirectory = %{sharedir}/%{name}/services
configDirectory = %{sysconfdir}
defaultNodeConfiguration = defaultLinux
EOF

if [ ! -f %{sysconfdir}/defaultLinux ]; then
	cp %{sharedir}/doc/%{name}/defaultLinux %{sysconfdir}
fi

#%post
#import AccessGrid
#import AccessGrid.hosting
#import os
#import os.path
#import glob
#
#def modimport(module):
#    for module_file in glob.glob(module.__path__[0] + "\\*.py"):
#        __import__(module.__name__ + "." + os.path.basename(module_file[:-3]))
#
#modimport(AccessGrid)
#modimport(AccessGrid.hosting)

%clean
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%changelog

* Fri Feb 21 2003 Ti Leggett <leggett@mcs.anl.gov>
- Fixed where docs go
- Added default node configuration file

* Fri Feb 14 2003 Ti Leggett <leggett@mcs.anl.gov>
- Added postinstall for VenueClient to create AGNodeService config file

* Thu Feb 13 2004 Ti Leggett <leggett@mcs.anl.gov>
- Added SetupVideo.py to VideoProducer

* Fri Feb 06 2003 Ti Leggett <leggett@mcs.anl.gov>
- Modularized the RPMs

* Tue Feb 05 2003 Ti Leggett <leggett@mcs.anl.gov>
- This file was created

