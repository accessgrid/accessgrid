%define	name		AccessGrid
%define	version		2.0beta
%define	release		1
%define	prefix		/usr
%define sysconfdir	/etc/%{name}
%define sharedir	%{prefix}/share
%define gnomedir	%{sharedir}/gnome/apps
%define kdedir		%{sharedir}/applnk
%define aghome		/var/lib/ag
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
Obsoletes:	AccessGrid-2.0alpha

%description
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the core components to start participating in the Access Grid.

%package VenueClient
Summary:	The Access Grid Toolkit Venue Client
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid
Obsoletes:	AccessGrid-VenueClient-2.0alpha

%description VenueClient
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the components needed to connect to an Access Grid Venue.

%package VenueServer
Summary:	The Access Grid Toolkit Venue Server
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid
Obsoletes:	AccessGrid-VenueServer-2.0alpha

%description VenueServer
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the components needed to create an Access Grid Venue and an Access Grid Venue Server.

%package VideoProducer
Summary:	The Access Grid Toolkit Video Producer Service
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid AccessGrid-vic
Obsoletes:	AccessGrid-VideoProducer-2.0alpha

%description VideoProducer
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the components needed to run the Video Producer service. This service is responsible for capturing and transmitting an Access Grid Node's video.

%package VideoConsumer
Summary:	The Access Grid Toolkit Video Consumer Service
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid
Obsoletes:	AccessGrid-VideoConsumer-2.0alpha

%description VideoConsumer
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the components needed to run the Video Consumer service. This service is responsible for receiving remote Access Grid Nodes' video.

%package AudioService
Summary:	The Access Grid Toolkit Audio Service
Version:	%{version}
Release:	%{release}
Group:		Utilities/System
Requires:	AccessGrid AccessGrid-rat
Obsoletes:	AccessGrid-AudioService-2.0alpha

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
mv %{buildroot}%{prefix}/etc %{buildroot}
mv %{buildroot}%{prefix}/var %{buildroot}

%files
%doc %{sharedir}/doc/
%defattr(-,root,root)
%{prefix}/lib
%defattr(0755,root,root)
%{prefix}/bin/AGServiceManager.py
/etc/init.d/agsm
%defattr(0755,ag,ag)
%dir %{aghome}/local_services
%defattr(0644,root,root)
%config %{sysconfdir}/AGServiceManager

%files VenueClient
%defattr(-,root,root)
%{prefix}/bin/AGNodeService.py
%{prefix}/bin/VenueClient.py
%{prefix}/bin/NodeManagement.py
%config %{sysconfdir}/AGNodeService
/etc/init.d/agns
%{sharedir}/%{name}/services/
%{gnomedir}/%{name}/.desktop
%{gnomedir}/%{name}/VenueClient.desktop
%{gnomedir}/%{name}/NodeManagement.desktop
%{kdedir}/%{name}/.desktop
%{kdedir}/%{name}/VenueClient.desktop
%{kdedir}/%{name}/NodeManagement.desktop
%defattr(0644,ag,ag)
%config %{sharedir}/%{name}/defaultLinux


%files VenueServer
%defattr(-,root,root)
%{prefix}/bin/VenueManagement.py
%{prefix}/bin/VenueServer.py
%{prefix}/bin/VenuesServerRegistry.py
%{gnomedir}/%{name}/.desktop
%{gnomedir}/%{name}/VenueManagement.desktop
%{kdedir}/%{name}/.desktop
%{kdedir}/%{name}/VenueManagement.desktop

%files VideoProducer
%defattr(-,root,root)
%{prefix}/bin/SetupVideo.py
%defattr(0664,ag,ag)
%{aghome}/local_services/VideoProducerService.*

%files VideoConsumer
%defattr(0664,ag,ag)
%{aghome}/local_services/VideoConsumerService.*

%files AudioService
%defattr(0664,ag,ag)
%{aghome}/local_services/AudioService.*

%pre
if [ ! -d %{aghome} ]; then
	/usr/sbin/groupadd -r ag
	/usr/sbin/useradd -r -m -d %{aghome} -g ag -c "Access Grid User" ag
fi

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

%post VenueClient
/sbin/chkconfig --add agns

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

%preun VenueClient
/sbin/chkconfig --del agns

%clean
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%changelog

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

