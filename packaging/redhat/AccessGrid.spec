%define	name		AccessGrid
%define	version		2.0alpha
%define	release		2
%define	prefix		/usr
%define sysconfdir	/etc/%{name}
%define gnomedir	/usr/share/gnome/apps
%define kdedir		/usr/share/applnk
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
%doc %{prefix}/doc/
%defattr(-,root,root)
%{prefix}/lib
%defattr(0755,root,root)
%{prefix}/bin/AGServiceManager.py

%files VenueClient
%defattr(-,root,root)
%{prefix}/bin/AGNodeService.py
%{prefix}/bin/VenueClient.py
%{prefix}/bin/NodeManagement.py
%{prefix}/share/AccessGrid/services/
%{gnomedir}/AccessGrid/.desktop
%{gnomedir}/AccessGrid/VenueClient.desktop
%{gnomedir}/AccessGrid/NodeManagement.desktop
%{kdedir}/AccessGrid/.desktop
%{kdedir}/AccessGrid/VenueClient.desktop
%{kdedir}/AccessGrid/NodeManagement.desktop


%files VenueServer
%defattr(-,root,root)
%{prefix}/bin/VenueManagement.py
%{prefix}/bin/VenueServer.py
%{prefix}/bin/VenuesServerRegistry.py
%{gnomedir}/AccessGrid/.desktop
%{gnomedir}/AccessGrid/VenueManagement.desktop
%{kdedir}/AccessGrid/.desktop
%{kdedir}/AccessGrid/VenueManagement.desktop
#
%files VideoProducer
%defattr(-,root,root)
%{prefix}/share/AccessGrid/local_services/VideoProducerService.*
%{prefix}/bin/SetupVideo.py

%files VideoConsumer
%defattr(-,root,root)
%{prefix}/share/AccessGrid/local_services/VideoConsumerService.*

%files AudioService
%defattr(-,root,root)
%{prefix}/share/AccessGrid/local_services/AudioService.*

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

* Thu Feb 13 2004 Ti Leggett <leggett@mcs.anl.gov>
- Added SetupVideo.py to VideoProducer

* Fri Feb 06 2003 Ti Leggett <leggett@mcs.anl.gov>
- Modularized the RPMs

* Tue Feb 05 2003 Ti Leggett <leggett@mcs.anl.gov>
- This file was created

