%define name            VenueVNC
%define version         1.0
%define release         4
%define prefix          /usr
%define sharedir        %{prefix}/share/AccessGrid/applications/%{name}
%define buildroot       /var/tmp/%{name}-%{version}

%define mimetype        "application/x-ag-venuevnc"
#%define executable      "%{sharedir}/runvnc %s"
%define descrip         "Shared VNC scoped within a venue"
%define nametemplate    "%s.venuevnc"


Summary:        Access Grid %{name} Application
Name:           %{name}
Version:        %{version}
Release:        %{release}
Copyright:      AGTPL
Group:          Utilities/System
URL:            http://www.mcs.anl.gov/fl/research/accessgrid
Vendor:         Argonne National Laboratory
Source:         %{name}-%{version}.tar.gz
BuildRoot:      %{buildroot}

%description
Shared VNC scoped within a venue

%package Client
Summary:        Access Grid %{name} Client Application
Version:        %{version}
Release:        %{release}
Copyright:      AGTPL
Group:          Utilities/System
Requires:       /usr/bin/python2.2
Requires:       AccessGrid

%description Client
Shared VNC scoped within a venue

%package Server
Summary:        Access Grid %{name} Server Application
Version:        %{version}
Release:        %{release}
Copyright:      AGTPL
Group:          Utilities/System
Requires:       /usr/bin/python2.2
Requires:       AccessGrid

%description Server
Shared VNC scoped within a venue

%prep
%setup
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%install
mkdir -p %{buildroot}%{sharedir}
cp %{name}Client.py %{buildroot}%{sharedir}
#cp runvnc %{buildroot}%{sharedir}
cp vncviewer %{buildroot}%{sharedir}
cp server/%{name}Server.py %{buildroot}%{sharedir}
cp server/vncrandpwd %{buildroot}%{sharedir}
cp server/Xvnc %{buildroot}%{sharedir}
cp README %{buildroot}%{sharedir}

%files Client
%defattr(-,root,root)
%{sharedir}/%{name}Client.py
#%{sharedir}/runvnc
%{sharedir}/vncviewer

%files Server
%defattr(-,root,root)
%{sharedir}/%{name}Server.py
%{sharedir}/vncrandpwd
%{sharedir}/Xvnc

%post Client
#/usr/bin/MailcapSetup.py --system --mime-type %{mimetype} --executable %{executable} --description %{descrip} --nametemplate %{nametemplate}

%postun Client
#/usr/bin/MailcapSetup.py --system --uninstall --mime-type %{mimetype}

%clean
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%changelog
* Fri May 20 2003 Ti Leggett <leggett@mcs.anl.gov>
- This file was created


